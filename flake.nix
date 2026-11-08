{
  description = "demo-creator — 素材づくりから編集・書き出しまでを固定する";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
      fonts = pkgs.makeFontsConf {
        fontDirectories = [ pkgs.noto-fonts-cjk-sans pkgs.noto-fonts-cjk-serif pkgs.dejavu_fonts pkgs.liberation_ttf ];
      };
      # 毎回使うものだけ。重いものを既定に混ぜると最初の make が止まって見える
      # 素の mlt には Qt モジュールが無く qimage / qtext が使えない。
      # 静止画を置くときに要るので Qt 付きの方を取る
      core = with pkgs; [ kdePackages.mlt ffmpeg uv python3 gnumake chromium nodejs ];
      # kdenlive はトップレベルに無い。KDE のパッケージセットの下にいる
      authoring = with pkgs; [
        blender kdePackages.kdenlive shotcut freecad openscad inkscape
      ];
    in {
      devShells.${system} = {
        default = pkgs.mkShell {
          name = "demo-creator";
          packages = core;
          FONTCONFIG_FILE = fonts;
        };
        # make 3d と make open が使う。GUI と 3D が要るときだけ
        full = pkgs.mkShell {
          name = "demo-creator-full";
          packages = core ++ authoring;
          FONTCONFIG_FILE = fonts;
        };
      };
    };
}
