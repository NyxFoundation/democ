# demo-creator
#
#   make edit N=nyxis   組んでブラウザで開く。文言を詰めるときはここから
#   make watch N=nyxis  保存するたびに組み直す（ブラウザは F5）
#   make                demos/*/ → 録画 → タイムライン → out/<デモ>/demo.mp4
#   make screens        組んで録り直す（中身が変わったシーンだけ）
#   make snaps          止め絵で確かめる（動きで隠れる崩れはこれでしか見えない）
#   make layers         画面を部品ごとの透過 PNG に切り出す
#   make blend          .blend だけ作り直す（レンダーしない）
#   make 3d             その部品を Blender で 3D に置いて撮る
#   make open N=nyxis   Kdenlive で開く
#   make new NAME=foo   templates/starter.yaml から新しいデモを作る
#
# 生成物は out/<デモ>/ の下にまとまる。git には入らない。
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

OUT    := out
# デモ 1 本 = demos/<名前>/ 一式。台本は demos/<名前>/<名前>.yaml
DEMOS  := $(foreach d,$(notdir $(wildcard demos/*)),\
            $(if $(wildcard demos/$(d)/$(d).yaml),$(d),))
ENGINE := $(wildcard engine/*.css engine/*.js engine/scenes/*)
N      ?= $(firstword $(DEMOS))

# 配布用。an=1 は音声なし。色の指定は足さない——素材のまま通すのが一番狂わない
ENCODE := vcodec=libx264 crf=18 preset=slow pix_fmt=yuv420p an=1

PAGES   :=
SCREENS :=
MOVIES  :=
LAYERS  :=
RENDERS :=

# --- デモ 1 本ぶんの道筋 ----------------------------------------------------
define DEMO_RULES
$(OUT)/$(1)/page.html: demos/$(1)/$(1).yaml tools/build.py tools/highlight.py $$(ENGINE)
	$$(PY) tools/build.py $$< -o $$@

# HTML は毎回同じ絵を出すので、中身が変わったシーンだけ録り直せばよい
$(OUT)/$(1)/screens/index.json: $(OUT)/$(1)/page.html tools/record.py tools/browser.py
	$$(PY) tools/record.py $$< --out $(OUT)/$(1)/screens

$(OUT)/$(1)/edit.mlt: edit/timeline.py edit/kdenlive.py $(OUT)/$(1)/screens/index.json FORCE
	$$(PY) edit/timeline.py $(1)

$(OUT)/$(1)/demo.mp4: $(OUT)/$(1)/edit.mlt
	$$(IN) melt $$< -consumer avformat:$$@ $$(ENCODE)
	@ls -lh $$@

PAGES   += $(OUT)/$(1)/page.html
SCREENS += $(OUT)/$(1)/screens/index.json
MOVIES  += $(OUT)/$(1)/demo.mp4
endef
$(foreach d,$(DEMOS),$(eval $(call DEMO_RULES,$(d))))

# --- 3D ショット 1 本ぶん（demos/<デモ>/layers/<ショット>.yaml と shots/<ショット>.py）---
define SHOT_RULES
$(OUT)/$(1)/layers/$(2)/layers.json: demos/$(1)/layers/$(2).yaml $(OUT)/$(1)/page.html tools/layers.py
	$$(PY) tools/layers.py $$<

$(OUT)/$(1)/3d/$(2).mp4: demos/$(1)/shots/$(2).py $(OUT)/$(1)/layers/$(2)/layers.json
	@mkdir -p $(OUT)/$(1)/3d
	$$(BL) blender -b -P $$< -- --layers $(OUT)/$(1)/layers/$(2) \
	  --out $(OUT)/$(1)/3d/$(2) --blend $(OUT)/$(1)/3d/$(2).blend
	$$(IN) ffmpeg -y -loglevel error -framerate 25 \
	  -i $(OUT)/$(1)/3d/$(2)/f%04d.png -c:v libx264 -crf 18 -pix_fmt yuv420p $$@
	@ls -lh $$@

$(OUT)/$(1)/3d/$(2).blend: demos/$(1)/shots/$(2).py $(OUT)/$(1)/layers/$(2)/layers.json
	@mkdir -p $(OUT)/$(1)/3d
	$$(BL) blender -b -P $$< -- --layers $(OUT)/$(1)/layers/$(2) \
	  --blend $$@ --no-render

LAYERS  += $(OUT)/$(1)/layers/$(2)/layers.json
RENDERS += $(OUT)/$(1)/3d/$(2).mp4
BLENDS  += $(OUT)/$(1)/3d/$(2).blend
endef
$(foreach d,$(DEMOS),$(foreach s,$(notdir $(basename $(wildcard demos/$(d)/layers/*.yaml))),\
  $(eval $(call SHOT_RULES,$(d),$(s)))))

.PHONY: render timeline html screens snaps layers blend 3d edit watch preview open \
        shell shell-full new clean help FORCE

render:  $(MOVIES)
timeline: $(foreach d,$(DEMOS),$(OUT)/$(d)/edit.mlt)
html:    $(PAGES)
screens: $(SCREENS)
layers:  $(LAYERS)
3d:      $(RENDERS)
blend:   $(BLENDS)

snaps: $(PAGES)
	$(foreach p,$(PAGES),$(PY) tools/snap.py $(p) --out $(dir $(p))snaps;)

# 文言を詰める往復。組み直しは 0.3 秒なので、保存 → F5 で足りる
edit: $(OUT)/$(N)/page.html
	@(xdg-open $(OUT)/$(N)/page.html >/dev/null 2>&1 &) ; \
	 echo "demos/$(N)/$(N).yaml を直して make html。ブラウザは F5 で入れ替わる"
	@echo "数字キーで場面を飛べる。r で頭から"

watch:
	@echo "demos/$(N)/$(N).yaml を見ている。止めるのは Ctrl-C"
	@last=""; while :; do \
	  now=$$(cat demos/$(N)/$(N).yaml engine/engine.* engine/scenes/* 2>/dev/null | cksum); \
	  if [ "$$now" != "$$last" ]; then last="$$now"; $(MAKE) --no-print-directory html; fi; \
	  sleep 1; \
	done

preview: $(OUT)/$(N)/edit.mlt
	$(IN) melt $(OUT)/$(N)/edit.mlt

# Kdenlive は素の MLT を開けないので、方言で書いた方を渡す
open: $(OUT)/$(N)/edit.mlt
	$(KD) kdenlive $(OUT)/$(N)/edit.kdenlive &

new:
	@test -n "$(NAME)" || { echo "make new NAME=<名前>"; exit 1; }
	@test ! -e demos/$(NAME) || { echo "demos/$(NAME) は既にある"; exit 1; }
	@mkdir -p demos/$(NAME)/layers demos/$(NAME)/shots
	@cp templates/starter.yaml demos/$(NAME)/$(NAME).yaml
	@echo "demos/$(NAME)/$(NAME).yaml を作った。文言を書いたら make html で確かめる"

shell:
	nix develop $(FLAKE)
shell-full:
	nix develop $(FLAKE)$(HASH)full

FORCE:

clean:
	rm -rf $(OUT)

help:
	@sed -n '2,13p' $(MAKEFILE_LIST)
