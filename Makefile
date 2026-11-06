# demo-creator
#
#   make            素材 → タイムライン → 書き出し
#   make screens    assets/screens/*.html を録り直す
#   make 3d         assets/3d/*.py を Blender で焼く
#   make preview    melt で再生して確かめる
#   make open       Kdenlive で .mlt を開く（人が直す用）
#   make shell      devShell に入る
#
# devShell の外から叩いても動く。melt が PATH に無ければ nix develop を噛ませる。
# nyxis ディレクトリが親リポジトリで未追跡でも動くよう flake は path: で指す。

SHELL := /bin/bash
.DEFAULT_GOAL := render

ifeq ($(shell command -v melt 2>/dev/null),)
  IN := nix develop --no-write-lock-file "path:$(CURDIR)" -c
else
  IN :=
endif

OUT      := out
TIMELINE := $(OUT)/edit.mlt
MOVIE    := $(OUT)/demo.mp4

HTML     := $(wildcard assets/screens/*.html)
SCREENS  := $(patsubst assets/screens/%.html,$(OUT)/screens/%.mp4,$(HTML))
BLEND    := $(wildcard assets/3d/*.py)
RENDERS  := $(patsubst assets/3d/%.py,$(OUT)/3d/%.mp4,$(BLEND))

# 配布用。an=1 は音声なし。色の指定は足さない——素材のまま通すのが一番狂わない
ENCODE := vcodec=libx264 crf=18 preset=slow pix_fmt=yuv420p an=1

.PHONY: render timeline screens 3d preview open shell snaps clean help

render: $(MOVIE)

$(MOVIE): $(TIMELINE)
	$(IN) melt $(TIMELINE) -consumer avformat:$@ $(ENCODE)
	@ls -lh $@

timeline: $(TIMELINE)
$(TIMELINE): edit/timeline.py $(SCREENS)
	$(IN) python3 edit/timeline.py

# 画面素材。HTML は毎回同じ絵を出すので、直したら録り直すだけでよい
screens: $(SCREENS)
$(OUT)/screens/%.mp4: assets/screens/%.html tools/record.py
	uv run --with playwright python tools/record.py $< --out $@

# 止め絵の確認。動きで隠れるレイアウト崩れはこれでしか見えない
snaps: $(HTML)
	$(foreach h,$(HTML),uv run --with playwright python tools/snap.py $(h);)

# 3D 素材。assets/3d/*.py は bpy を書いた Blender スクリプト
3d: $(RENDERS)
$(OUT)/3d/%.mp4: assets/3d/%.py
	@mkdir -p $(OUT)/3d
	$(IN) blender --background --python $< -- --out $@

preview: $(TIMELINE)
	$(IN) melt $(TIMELINE)

open: $(TIMELINE)
	$(IN) kdenlive $(TIMELINE) &

shell:
	nix develop --no-write-lock-file "path:$(CURDIR)"

clean:
	rm -rf $(OUT)

help:
	@sed -n '2,10p' $(MAKEFILE_LIST)
