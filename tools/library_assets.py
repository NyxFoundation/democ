"""Download manifest-listed source assets into the ignored local library cache."""
import hashlib
import json
import os
import ssl
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

import yaml

REGISTRY = Path(__file__).resolve().parents[1] / 'templates/library/assets.yaml'


def tls_context():
    context = ssl.create_default_context()
    # uv's Python can look for cert.pem while NixOS supplies a PEM bundle under
    # certs/. Load the system trust bundle; keep certificate verification enabled.
    if not ssl.get_default_verify_paths().cafile and not any(
            os.environ.get(name) for name in ('SSL_CERT_FILE', 'SSL_CERT_DIR')):
        for bundle in ('/etc/ssl/certs/ca-certificates.crt',
                       '/etc/pki/tls/certs/ca-bundle.crt'):
            if Path(bundle).is_file():
                context.load_verify_locations(cafile=bundle)
                break
    return context


def acquire_assets(names, out):
    registry = yaml.safe_load(REGISTRY.read_text())['assets']
    cache = Path(out) / 'assets'
    cache.mkdir(parents=True, exist_ok=True)
    resolved = {}
    context = tls_context()
    for name in names:
        asset = registry[name]
        files = {asset['filename']: asset['url'], **asset.get('dependencies', {})}
        hashes = {}
        for filename, url in files.items():
            if Path(filename).is_absolute() or '..' in Path(filename).parts:
                raise ValueError('Asset path must remain within its cache')
            path = cache / filename
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                print(f'asset: {name}/{filename}', flush=True)
                request = Request(url, headers={'User-Agent': 'democ/1.0'})
                with urlopen(request, timeout=120, context=context) as response:
                    data = response.read()
                temporary = path.with_suffix(path.suffix + '.partial')
                temporary.write_bytes(data)
                temporary.replace(path)
            hashes[filename] = hashlib.sha256(path.read_bytes()).hexdigest()
        target = cache / asset['filename']
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        if asset.get('sha256') and digest != asset['sha256']:
            raise ValueError(f'Asset checksum mismatch: {name}')
        metadata = dict(asset, id=name, sha256=digest, files_sha256=hashes,
                        checked_at=datetime.now(timezone.utc).isoformat())
        target.with_suffix(target.suffix + '.json').write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2))
        resolved[name] = target.resolve()
    return resolved
