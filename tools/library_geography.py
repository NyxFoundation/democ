"""Register public elevation and satellite tiles in a shared Mercator mosaic."""
import hashlib
import json
import math
from pathlib import Path
import subprocess

import yaml
from library_assets import REGISTRY


def prepare_terrain(name, out):
    asset=yaml.safe_load(REGISTRY.read_text())['assets'][name]
    count_x,count_y=asset['tile_count'];origin_x,origin_y=asset['tile_origin'];zoom=asset['tile_zoom']
    folder=Path(out)/'assets'/Path(asset['filename']).parent
    targets={}
    for kind,extension in [('dem','png'),('satellite','jpg')]:
        nx,ny=asset.get('satellite_count',[count_x,count_y]) if kind=='satellite' else [count_x,count_y]
        ox,oy=asset.get('satellite_origin',[origin_x,origin_y]) if kind=='satellite' else [origin_x,origin_y]
        layer_zoom=asset.get('satellite_zoom',zoom) if kind=='satellite' else zoom
        if (ox/2**layer_zoom,oy/2**layer_zoom,nx/2**layer_zoom,ny/2**layer_zoom)!=(origin_x/2**zoom,origin_y/2**zoom,count_x/2**zoom,count_y/2**zoom):
            raise ValueError('Elevation and imagery must cover the same Mercator bounds')
        files=[folder/f'{kind}-{ox+x}-{oy+y}.{extension}' for y in range(ny) for x in range(nx)]
        signature=hashlib.sha256(b''.join(p.read_bytes() for p in files)).hexdigest()
        target=folder/f'{kind}-mosaic.png';stamp=target.with_suffix('.json')
        if not target.exists() or not stamp.exists() or json.loads(stamp.read_text())['source_sha256']!=signature:
            layout='|'.join(f'{x*256}_{y*256}' for y in range(ny) for x in range(nx))
            command=['ffmpeg','-v','error','-y','-filter_complex_threads','2']
            for file in files:command+=['-threads','1','-i',str(file)]
            command+=['-filter_complex',f'xstack=inputs={len(files)}:layout={layout}:fill=black',
                      '-frames:v','1','-pix_fmt','rgb24',str(target)]
            subprocess.run(command,check=True)
            stamp.write_text(json.dumps({'source_sha256':signature,'tile_zoom':layer_zoom,'tile_origin':[ox,oy],
                                         'tile_count':[nx,ny],'credit':asset['usage']},indent=2))
        targets[kind]=str(target.resolve())
    center_y=origin_y+count_y/2
    latitude=math.atan(math.sinh(math.pi*(1-2*center_y/2**zoom)))
    meters=40075016.68557849/2**zoom*count_x*math.cos(latitude)
    return {'terrain_path':targets['dem'],'texture_path':targets['satellite'],
            'terrain_meters_per_unit':meters/18}
