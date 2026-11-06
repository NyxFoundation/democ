"""Chromium を起こす。Playwright の同梱ブラウザが無い機械（NixOS など）でも通す。"""

import glob
import os
import shutil


def launch_chromium(p, **kw):
    env = os.environ.get("DEMO_CHROMIUM")
    err = None
    if not env:
        try:
            return p.chromium.launch(**kw)
        except Exception as e:
            err = e
    names = ("chromium", "chromium-browser", "google-chrome-stable", "google-chrome")
    cands = ([env] if env else []) + [c for c in map(shutil.which, names) if c]
    cands += sorted(glob.glob("/nix/store/*-chromium-*/bin/chromium"), reverse=True)
    for exe in cands:
        try:
            b = p.chromium.launch(executable_path=exe, **kw)
            print(f"[demo] chromium: {exe}")
            return b
        except Exception as e:
            err = e
    raise SystemExit(f"chromium を起動できない ({err})。"
                     " playwright install chromium するか DEMO_CHROMIUM を指す。")
