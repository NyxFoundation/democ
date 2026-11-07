# demo-creator
#
#   make edit N=nyxis   組んでブラウザで開く。文言を詰めるときはここから
#   make watch N=nyxis  保存するたびに組み直す（ブラウザは F5）
#   make                demos/*.yaml → 録画 → タイムライン → out/demo.mp4
#   make screens        YAML から HTML を組んで録り直す
#   make snaps          止め絵で確かめる（動きで隠れる崩れはこれでしか見えない）
#   make html           HTML だけ組む（ブラウザで開いて文言を詰める）
#   make 3d             assets/3d/*.py を Blender で焼く
#   make preview        melt で再生する
#   make open           Kdenlive で out/edit.mlt を開く
#   make new NAME=foo   templates/starter.yaml から新しいデモを作る
#
# melt が PATH に無ければ nix develop を噛ませるので、素の端末から叩いてよい。
# 生成物は全部 out/ に入り、git には入らない。

SHELL := /bin/bash
.DEFAULT_GOAL := render

# melt と ffmpeg だけの軽い shell。Blender と GUI は full にある
FLAKE := --no-write-lock-file "path:$(CURDIR)"
ifeq ($(shell command -v melt 2>/dev/null),)
  IN := nix develop $(FLAKE) -c
else
  IN :=
endif
FULL := nix develop $(FLAKE)#full -c
PY := uv run --quiet --with pyyaml --with playwright python3

OUT      := out
TIMELINE := $(OUT)/edit.mlt
MOVIE    := $(OUT)/demo.mp4

SPECS    := $(wildcard demos/*.yaml)
PAGES    := $(patsubst demos/%.yaml,$(OUT)/screens/%.html,$(SPECS))
SCREENS  := $(patsubst demos/%.yaml,$(OUT)/screens/%.mp4,$(SPECS))
ENGINE   := $(wildcard engine/*.css engine/*.js engine/scenes/*)
BLEND    := $(wildcard assets/3d/*.py)
RENDERS  := $(patsubst assets/3d/%.py,$(OUT)/3d/%.mp4,$(BLEND))

# 配布用。an=1 は音声なし。色の指定は足さない——素材のまま通すのが一番狂わない
ENCODE := vcodec=libx264 crf=18 preset=slow pix_fmt=yuv420p an=1

.PHONY: render timeline html screens snaps 3d edit watch preview open shell shell-full new clean help

render: $(MOVIE)

$(MOVIE): $(TIMELINE)
	$(IN) melt $(TIMELINE) -consumer avformat:$@ $(ENCODE)
	@ls -lh $@

timeline: $(TIMELINE)
$(TIMELINE): edit/timeline.py $(SCREENS)
	$(PY) edit/timeline.py

# YAML → 1 枚の HTML。使ったシーンの CSS と JS だけが埋め込まれる
html: $(PAGES)
$(OUT)/screens/%.html: demos/%.yaml tools/build.py tools/highlight.py $(ENGINE)
	$(PY) tools/build.py $< -o $@

# HTML は毎回同じ絵を出すので、文言を直したら録り直すだけでよい
screens: $(SCREENS)
$(OUT)/screens/%.mp4: $(OUT)/screens/%.html tools/record.py tools/browser.py
	$(PY) tools/record.py $< --out $@

# 文言を詰める往復。組み直しは 0.3 秒なので、保存 → F5 で足りる
N ?= $(basename $(notdir $(firstword $(SPECS))))
edit: $(OUT)/screens/$(N).html
	@(xdg-open $(OUT)/screens/$(N).html >/dev/null 2>&1 &) ; \
	 echo "demos/$(N).yaml を直して make html。ブラウザは F5 で入れ替わる"
	@echo "数字キーで場面を飛べる。r で頭から"

watch:
	@echo "demos/$(N).yaml を見ている。止めるのは Ctrl-C"
	@last=""; while :; do \
	  now=$$(cat demos/$(N).yaml engine/engine.* engine/scenes/* 2>/dev/null | cksum); \
	  if [ "$$now" != "$$last" ]; then last="$$now"; $(MAKE) --no-print-directory html; fi; \
	  sleep 1; \
	done

snaps: $(PAGES)
	$(foreach h,$(PAGES),$(PY) tools/snap.py $(h);)

# 3D 素材。assets/3d/*.py は bpy を書いた Blender スクリプト
3d: $(RENDERS)
$(OUT)/3d/%.mp4: assets/3d/%.py
	@mkdir -p $(OUT)/3d
	$(FULL) blender --background --python $< -- --out $@

preview: $(TIMELINE)
	$(IN) melt $(TIMELINE)

open: $(TIMELINE)
	$(FULL) kdenlive $(TIMELINE) &

new:
	@test -n "$(NAME)" || { echo "make new NAME=<名前>"; exit 1; }
	@test ! -e demos/$(NAME).yaml || { echo "demos/$(NAME).yaml は既にある"; exit 1; }
	@cp templates/starter.yaml demos/$(NAME).yaml
	@echo "demos/$(NAME).yaml を作った。文言を書いたら make html で確かめる"

shell:
	nix develop $(FLAKE)
shell-full:
	nix develop $(FLAKE)#full

clean:
	rm -rf $(OUT)

help:
	@sed -n '2,13p' $(MAKEFILE_LIST)
