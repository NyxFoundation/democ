# democ
#
#   make new N=foo [FROM=nyxis]  out/foo/ に作業場を作る（台本もここ）
#   make edit N=foo              組んでブラウザで開く。文言を詰めるときはここから
#   make watch N=foo             保存するたびに組み直す（ブラウザは F5）
#   make                         out/*/ → 録画 → タイムライン → build/demo.mp4
#   make screens                 組んで録り直す（中身が変わったシーンだけ）
#   make snaps                   止め絵で確かめる
#   make layers                  画面を部品ごとの透過 PNG に切り出す
#   make blend                   .blend だけ作り直す（レンダーしない）
#   make 3d                      その部品を Blender で 3D に置いて撮る
#   make open N=foo              Kdenlive で開く（尺と順番を触る）
#   make example N=foo           examples/foo/ に台本一式を写して commit できるようにする
#
# このリポジトリにあるのは道具だけ。デモ 1 本ぶんは out/<名前>/ に置き、git には入らない。
# 残したくなったら make example で examples/ へ写す。
#
#   out/foo/                     ← 作業場（git 管理外）
#     foo.yaml                     台本。文字を直すのはここ
#     notes.md  layers/  shots/
#     build/                       生成物（parts/ screens/ 3d/ …）。make clean はここだけ
#
# melt / blender / kdenlive は PATH にあればそれを使い、無ければ nix develop を噛ませる。

SHELL := /bin/bash
.DEFAULT_GOAL := render

FLAKE := --no-write-lock-file "path:$(CURDIR)"
# # は Makefile ではコメントの始まりなので、flake の属性指定は変数に逃がす
HASH := \#
FULL := nix develop $(FLAKE)$(HASH)full -c
ifeq ($(shell command -v melt 2>/dev/null),)
  IN := nix develop $(FLAKE) -c
else
  IN :=
endif
# .blend は開く版と同じ版で書かないと「expect loss of data」の警告が出る
ifeq ($(shell command -v blender 2>/dev/null),)
  BL := $(FULL) blender
else
  BL :=
endif
ifeq ($(shell command -v kdenlive 2>/dev/null),)
  KD := $(FULL) kdenlive
else
  KD :=
endif
PY := uv run --quiet --with pyyaml --with playwright python3

# 製品動画の参考カットと再現テンプレート。既存デモの作業場とは独立。
LIBRARY_ID := $(if $(ID),--id $(ID),)
.PHONY: library library-list library-collect library-render library-catalog library-check
library:
	$(PY) tools/template_library.py all $(LIBRARY_ID)
library-list:
	$(PY) tools/template_library.py list $(LIBRARY_ID)
library-collect:
	$(PY) tools/template_library.py collect $(LIBRARY_ID)
library-render:
	$(PY) tools/template_library.py render $(LIBRARY_ID)
library-catalog:
	$(PY) tools/template_library.py catalog
library-check:
	$(PY) tools/template_library.py verify $(LIBRARY_ID)

.PHONY: library-materials library-materials-list
library-materials:
	$(PY) tools/library_materials.py all $(LIBRARY_ID)
library-materials-list:
	$(PY) tools/library_materials.py list $(LIBRARY_ID)

.PHONY: readme-demos
readme-demos:
	$(PY) tools/readme_demos.py $(LIBRARY_ID)

OUT    := out
# デモ 1 本 = out/<名前>/ 一式。台本は out/<名前>/<名前>.yaml
DEMOS  := $(foreach d,$(notdir $(wildcard $(OUT)/*)),\
            $(if $(wildcard $(OUT)/$(d)/$(d).yaml),$(d),))
ENGINE := $(wildcard engine/*.css engine/*.js engine/scenes/*)
SOURCE_UI := $(shell find templates/library/source-ui -path '*/node_modules' -prune -o -type f -print)
N      ?= $(firstword $(DEMOS))

# 配布用。an=1 は音声なし。色の指定は足さない——素材のまま通すのが一番狂わない
ENCODE := vcodec=libx264 crf=18 preset=slow pix_fmt=yuv420p an=1

PAGES   :=
SCREENS :=
MOVIES  :=
LAYERS  :=
RENDERS :=
BLENDS  :=

# --- デモ 1 本ぶんの道筋 ----------------------------------------------------
define DEMO_RULES
$(OUT)/$(1)/build/page.html: $(OUT)/$(1)/$(1).yaml tools/build.py tools/highlight.py tools/source_ui.py $$(ENGINE) $$(SOURCE_UI)
	$$(PY) tools/build.py $$< -o $$@

# HTML は毎回同じ絵を出すので、中身が変わったシーンだけ録り直せばよい
$(OUT)/$(1)/build/screens/index.json: $(OUT)/$(1)/build/page.html tools/record.py tools/browser.py
	$$(PY) tools/record.py $$< --out $(OUT)/$(1)/build/screens

$(OUT)/$(1)/build/edit.mlt: edit/timeline.py edit/kdenlive.py edit/dissolve.py edit/retime.py \
                            $(OUT)/$(1)/build/screens/index.json FORCE
	$$(PY) edit/timeline.py $(1)

$(OUT)/$(1)/build/demo.mp4: $(OUT)/$(1)/build/edit.mlt
	$$(IN) melt $$< -consumer avformat:$$@ $$(ENCODE)
	@ls -lh $$@

PAGES   += $(OUT)/$(1)/build/page.html
SCREENS += $(OUT)/$(1)/build/screens/index.json
MOVIES  += $(OUT)/$(1)/build/demo.mp4
endef
$(foreach d,$(DEMOS),$(eval $(call DEMO_RULES,$(d))))

# --- 3D ショット 1 本ぶん（out/<デモ>/layers/<名前>.yaml と shots/<名前>.py）---
define SHOT_RULES
$(OUT)/$(1)/build/parts/$(2)/layers.json: $(OUT)/$(1)/layers/$(2).yaml \
                                           $(OUT)/$(1)/build/page.html tools/layers.py
	$$(PY) tools/layers.py $$<

$(OUT)/$(1)/build/3d/$(2).mp4: $(OUT)/$(1)/shots/$(2).py $(OUT)/$(1)/build/parts/$(2)/layers.json
	@mkdir -p $(OUT)/$(1)/build/3d
	$$(BL) blender -b -P $$< -- --layers $(OUT)/$(1)/build/parts/$(2) \
	  --out $(OUT)/$(1)/build/3d/$(2) --blend $(OUT)/$(1)/build/3d/$(2).blend
	$$(IN) ffmpeg -y -loglevel error -framerate 25 \
	  -i $(OUT)/$(1)/build/3d/$(2)/f%04d.png -c:v libx264 -crf 18 -pix_fmt yuv420p $$@
	@ls -lh $$@

$(OUT)/$(1)/build/3d/$(2).blend: $(OUT)/$(1)/shots/$(2).py $(OUT)/$(1)/build/parts/$(2)/layers.json
	@mkdir -p $(OUT)/$(1)/build/3d
	$$(BL) blender -b -P $$< -- --layers $(OUT)/$(1)/build/parts/$(2) \
	  --blend $$@ --no-render

LAYERS  += $(OUT)/$(1)/build/parts/$(2)/layers.json
RENDERS += $(OUT)/$(1)/build/3d/$(2).mp4
BLENDS  += $(OUT)/$(1)/build/3d/$(2).blend
endef
$(foreach d,$(DEMOS),$(foreach s,$(notdir $(basename $(wildcard $(OUT)/$(d)/layers/*.yaml))),\
  $(eval $(call SHOT_RULES,$(d),$(s)))))

.PHONY: render timeline html screens snaps layers blend 3d edit watch preview open \
        new example shell shell-full clean help FORCE

render: $(MOVIES)
	@test -n "$(DEMOS)" || echo "out/ にデモがない。make new N=foo FROM=nyxis で作る"
timeline: $(foreach d,$(DEMOS),$(OUT)/$(d)/build/edit.mlt)
html:    $(PAGES)
screens: $(SCREENS)
layers:  $(LAYERS)
3d:      $(RENDERS)
blend:   $(BLENDS)

snaps: $(PAGES)
	$(foreach p,$(PAGES),$(PY) tools/snap.py $(p) --out $(dir $(p))snaps;)

# 文言を詰める往復。組み直しは 0.3 秒なので、保存 → F5 で足りる
edit: $(OUT)/$(N)/build/page.html
	@(xdg-open $(OUT)/$(N)/build/page.html >/dev/null 2>&1 &) ; \
	 echo "out/$(N)/$(N).yaml を直して make html。ブラウザは F5 で入れ替わる"
	@echo "数字キーで場面を飛べる。r で頭から"

watch:
	@echo "out/$(N)/$(N).yaml を見ている。止めるのは Ctrl-C"
	@last=""; while :; do \
	  now=$$(cat $(OUT)/$(N)/$(N).yaml engine/engine.* engine/scenes/* 2>/dev/null | cksum); \
	  if [ "$$now" != "$$last" ]; then last="$$now"; $(MAKE) --no-print-directory html; fi; \
	  sleep 1; \
	done

preview: $(OUT)/$(N)/build/edit.mlt
	$(IN) melt $(OUT)/$(N)/build/edit.mlt

# Kdenlive は素の MLT を開けないので、方言で書いた方を渡す
open: $(OUT)/$(N)/build/edit.mlt
	$(KD) kdenlive $(OUT)/$(N)/build/edit.kdenlive &

# 作業場を作る。FROM を指定すると examples/<FROM>/ から写す
new:
	@test -n "$(N)" || { echo "make new N=<名前> [FROM=<例>]"; exit 1; }
	@test ! -e $(OUT)/$(N) || { echo "$(OUT)/$(N) は既にある"; exit 1; }
	@mkdir -p $(OUT)/$(N)/layers $(OUT)/$(N)/shots
	@if [ -n "$(FROM)" ]; then \
	  test -d examples/$(FROM) || { echo "examples/$(FROM) が無い"; exit 1; }; \
	  cp -r examples/$(FROM)/. $(OUT)/$(N)/; \
	  mv $(OUT)/$(N)/$(FROM).yaml $(OUT)/$(N)/$(N).yaml 2>/dev/null || true; \
	else \
	  cp templates/starter.yaml $(OUT)/$(N)/$(N).yaml; \
	fi
	@echo "out/$(N)/$(N).yaml を作った。文言を書いたら make edit N=$(N) で確かめる"

# 残したくなったら examples/ へ写す。写るのは台本一式だけで、生成物は入らない
example:
	@test -n "$(N)" || { echo "make example N=<名前>"; exit 1; }
	@test -f $(OUT)/$(N)/$(N).yaml || { echo "out/$(N)/$(N).yaml が無い"; exit 1; }
	@mkdir -p examples/$(N)
	@rsync -a --delete --exclude build/ $(OUT)/$(N)/ examples/$(N)/
	@echo "examples/$(N)/ に写した。git add して commit できる"
	@find examples/$(N) -type f | sort

shell:
	nix develop $(FLAKE)
shell-full:
	nix develop $(FLAKE)$(HASH)full

FORCE:

# 消すのは生成物だけ。台本は消さない
clean:
	rm -rf $(OUT)/*/build

help:
	@sed -n '2,16p' $(MAKEFILE_LIST)
