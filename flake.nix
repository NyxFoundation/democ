{
  description = "nyxis demo studio — 素材づくりから編集・書き出しまでを固定する";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
      fonts = pkgs.makeFontsConf {
        fontDirectories = [ pkgs.noto-fonts-cjk-sans pkgs.noto-fonts-cjk-serif ];
      };
    in {
      devShells.${system}.default = pkgs.mkShell {
        packages = with pkgs; [
          # 編集と書き出し
          mlt            # melt。.mlt を描画する
          ffmpeg
          kdenlive       # .mlt を人が開いて直す
          shotcut        # 同上。好みで
          opentimelineio # 他形式へ渡すとき

          # 素材づくり
          blender        # 3D。bpy で -b から叩く
          freecad
          openscad
          inkscape

          # 画面素材と足回り
          uv python3 gnumake
        ];

        # Blender の日本語テキストと matplotlib の豆腐よけ
        FONTCONFIG_FILE = fonts;

        shellHook = ''
          echo "studio: melt $(melt --version 2>/dev/null | head -1 | cut -d' ' -f2) / blender $(blender --version 2>/dev/null | head -1 | cut -d' ' -f2)"
          echo "make        — 素材 → タイムライン → 書き出し"
          echo "make open   — 生成した .mlt を Kdenlive で開く"
        '';
      };
    };
}
