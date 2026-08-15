#!/usr/bin/env python3
"""frontend/public/base.png (1024x1536) から 2.5D アバター用のレイヤー(webp)を生成する。

使い方（リポジトリのルートで実行）:
    pip install pillow opencv-python-headless numpy
    python tools/build_avatar_parts.py
    # 環境変数で入出力を変更可: WOLF_SRC / WOLF_OUT

出力: frontend/public/wolf/*.webp と parts.json
座標を調整したいときは下の EYE / MOUTH / JAW_BOX / EAR を編集して再実行する。
"""
import json, os
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFilter

SRC = os.environ.get("WOLF_SRC", "frontend/public/base.png")
OUT = os.environ.get("WOLF_OUT", "frontend/public/wolf")
os.makedirs(OUT, exist_ok=True)

base = Image.open(SRC).convert("RGB")
W, H = base.size

# ------------------------------------------------- 0. "Made with AI" バッジ除去
# 右上の白いバッジを検出し、背後（ぼけた障子）を平滑補完して消す
_g = cv2.cvtColor(np.array(base), cv2.COLOR_RGB2GRAY)
_roi = _g[0:150, 680:W]
_n, _lab, _st, _ = cv2.connectedComponentsWithStats(((_roi > 228) * 255).astype(np.uint8), 8)
if _n > 1:
    _i = 1 + int(np.argmax(_st[1:, cv2.CC_STAT_AREA]))
    if _st[_i, cv2.CC_STAT_AREA] > 3000:
        bx, by, bw, bh = _st[_i, :4]
        bx += 680
        bm = np.zeros((H, W), np.uint8)
        cv2.rectangle(bm, (bx - 26, by - 26), (bx + bw + 26, by + bh + 26), 255, -1)
        _src = cv2.cvtColor(np.array(base), cv2.COLOR_RGB2BGR)
        _sc = 8
        _sm = (cv2.resize(bm, (W // _sc, H // _sc), interpolation=cv2.INTER_AREA) > 8)
        _sm = cv2.dilate(_sm.astype(np.uint8) * 255, np.ones((3, 3), np.uint8), 1)
        _f = cv2.inpaint(cv2.resize(_src, (W // _sc, H // _sc), interpolation=cv2.INTER_AREA),
                         _sm, 6, cv2.INPAINT_TELEA)
        _f = cv2.cvtColor(cv2.resize(_f, (W, H), interpolation=cv2.INTER_CUBIC),
                          cv2.COLOR_BGR2RGB).astype(np.float32)
        _f += np.random.default_rng(11).normal(0, 3.4, (H, W, 1))
        _soft = np.array(Image.fromarray(bm).filter(
            ImageFilter.GaussianBlur(9))).astype(np.float32) / 255.0
        _out = np.array(base).astype(np.float32) * (1 - _soft[..., None]) + \
            np.clip(_f, 0, 255) * _soft[..., None]
        base = Image.fromarray(_out.astype(np.uint8))
        print(f"badge removed: x={bx} y={by} w={bw} h={bh}")

bgr = cv2.cvtColor(np.array(base), cv2.COLOR_RGB2BGR)

# ---------------------------------------------------------------- geometry
EYE = {
    "l": dict(box=(392, 420, 454, 468), c=(422, 448), r=(25, 18)),
    "r": dict(box=(570, 420, 632, 468), c=(600, 448), r=(25, 18)),
}
MOUTH = [(386, 621), (410, 624), (440, 630), (470, 634), (500, 636),
         (530, 635), (560, 630), (585, 624), (610, 618)]
JAW_BOX = (330, 610, 680, 730)
EAR = {
    "l": [(303, 100), (315, 112), (342, 150), (372, 192), (394, 232),
          (404, 268), (400, 316), (372, 344), (330, 350), (286, 344),
          (262, 300), (258, 250), (268, 196), (284, 148), (296, 118)],
    "r": [(703,  98), (692, 110), (666, 148), (638, 190), (616, 230),
          (604, 268), (606, 314), (632, 342), (676, 350), (720, 344),
          (744, 302), (748, 250), (740, 196), (726, 146), (712, 112)],
}


def feather(mask_img, blur):
    return mask_img.filter(ImageFilter.GaussianBlur(blur))


def cut(box, mask, name, src=None):
    """box=(x0,y0,x1,y1) のRGBAを mask(L, 全画面) で切り出して保存"""
    src = src if src is not None else base
    x0, y0, x1, y1 = box
    rgba = src.crop(box).convert("RGBA")
    rgba.putalpha(mask.crop(box))
    rgba.save(f"{OUT}/{name}.png")
    return dict(x=x0, y=y0, w=x1 - x0, h=y1 - y0)


meta = {"w": W, "h": H}

# ---------------------------------------------------------------- 1. 月
gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
_, bright = cv2.threshold(gray, 205, 255, cv2.THRESH_BINARY)
bright[400:, :] = 0
n, lab, stats, cent = cv2.connectedComponentsWithStats(bright, 8)
if n > 1:
    i = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    mx, my, mw, mh = stats[i, :4]
    meta["moon"] = dict(cx=int(mx + mw / 2), cy=int(my + mh / 2), r=int(max(mw, mh) / 2))
else:
    meta["moon"] = dict(cx=512, cy=140, r=75)

# ---------------------------------------------------------------- 2. 耳
ear_mask_all = Image.new("L", (W, H), 0)
d = ImageDraw.Draw(ear_mask_all)
for poly in EAR.values():
    d.polygon(poly, fill=255)
ear_mask_all_np = np.array(ear_mask_all)

# 耳を消した背景を補完する。
# 耳の背後は「ぼけた障子＋靄」でほぼ平滑なので、1/8 に縮小してから inpaint し、
# 拡大して戻す。これで TELEA 特有の筋状スメアが出ず、なめらかな階調で埋まる。
inp_mask = cv2.dilate(ear_mask_all_np, np.ones((9, 9), np.uint8), iterations=3)
SC = 8
small = cv2.resize(bgr, (W // SC, H // SC), interpolation=cv2.INTER_AREA)
smask = (cv2.resize(inp_mask, (W // SC, H // SC),
                    interpolation=cv2.INTER_AREA) > 8).astype(np.uint8) * 255
smask = cv2.dilate(smask, np.ones((3, 3), np.uint8), iterations=1)
filled = cv2.inpaint(small, smask, 6, cv2.INPAINT_TELEA)
filled = cv2.resize(filled, (W, H), interpolation=cv2.INTER_CUBIC)
filled = cv2.cvtColor(filled, cv2.COLOR_BGR2RGB).astype(np.float32)
# フィルムグレインを足して原画のざらつきに馴染ませる
grain = np.random.default_rng(3).normal(0, 3.4, (H, W, 1))
filled = np.clip(filled + grain, 0, 255)
blend = np.array(base).astype(np.float32)
soft = np.array(feather(Image.fromarray(inp_mask), 10)).astype(np.float32) / 255.0
blend = (blend * (1 - soft[..., None]) + filled * soft[..., None]).astype(np.uint8)
Image.fromarray(blend).save(f"{OUT}/body.png")

for k, poly in EAR.items():
    m = Image.new("L", (W, H), 0)
    dd = ImageDraw.Draw(m)
    dd.polygon(poly, fill=255)
    m = feather(m, 2.5)
    xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
    box = (min(xs) - 8, min(ys) - 8, max(xs) + 8, max(ys) + 8)
    meta[f"ear_{k}"] = cut(box, m, f"ear_{k}")
    # 回転ピボット = 耳の付け根中央
    meta[f"ear_{k}"]["pivot"] = [int(np.mean(xs)), max(ys) - 6]

# ---------------------------------------------------------------- 3. 目
for k, e in EYE.items():
    cx, cy = e["c"]; rx, ry = e["r"]; box = e["box"]

    # 3-1 虹彩レイヤー
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=255)
    m = feather(m, 1.2)
    meta[f"iris_{k}"] = cut((cx - rx - 4, cy - ry - 4, cx + rx + 4, cy + ry + 4), m, f"iris_{k}")
    meta[f"iris_{k}"]["cx"] = cx; meta[f"iris_{k}"]["cy"] = cy

    # 3-2 眼窩（虹彩を消した目の内側）: 目尻の暗色で埋める
    im_np = cv2.cvtColor(np.array(base), cv2.COLOR_RGB2BGR)
    om = np.zeros((H, W), np.uint8)
    cv2.ellipse(om, (cx, cy), (rx + 3, ry + 3), 0, 0, 360, 255, -1)
    socket = cv2.inpaint(im_np, om, 8, cv2.INPAINT_NS)
    socket = Image.fromarray(cv2.cvtColor(socket, cv2.COLOR_BGR2RGB))
    sm = Image.new("L", (W, H), 0)
    ImageDraw.Draw(sm).ellipse((cx - rx - 6, cy - ry - 5, cx + rx + 6, cy + ry + 5), fill=255)
    sm = feather(sm, 2)
    meta[f"socket_{k}"] = cut((cx - rx - 10, cy - ry - 10, cx + rx + 10, cy + ry + 10),
                              sm, f"socket_{k}", src=socket)

    # 3-3 まぶた（閉じ目）
    # 目の上下の実際の毛色を縦方向に補間して「まぶたの面」を作り、まつ毛の弧を描く
    pad = 18
    lid_box = (cx - rx - pad, cy - ry - pad, cx + rx + pad, cy + ry + pad)
    lx0, ly0, lx1, ly1 = lid_box
    lw, lh = lx1 - lx0, ly1 - ly0
    # まぶたの面 = 目のすぐ上（眉まわり）の毛並みをそのまま流用する。
    # CSS 側で transform-origin:top / scaleY(0→1) すると「毛が降りてくる」= 閉眼に見える。
    arr = np.array(base)
    lid_patch = Image.fromarray(arr[ly0 - lh:ly0, lx0:lx1].copy())
    lid_patch = lid_patch.filter(ImageFilter.GaussianBlur(0.5)).convert("RGB")

    # まつ毛の弧を 4倍スーパーサンプリングで描く（ジャギー防止）
    S = 4
    ov = Image.new("RGBA", (lw * S, lh * S), (0, 0, 0, 0))
    do = ImageDraw.Draw(ov)
    pcx, pcy = (cx - lx0) * S, (cy - ly0) * S
    arc = [(pcx + tt * (rx + 7) * S, pcy + (5 - 2.0 * (1 - tt * tt) + 1.8 * tt) * S)
           for tt in np.linspace(-1, 1, 41)]
    do.line(arc, fill=(60, 47, 42, 230), width=int(2.6 * S), joint="curve")
    do.line([(x, y + 3.2 * S) for x, y in arc], fill=(214, 200, 178, 95),
            width=int(1.6 * S), joint="curve")
    ov = ov.resize((lw, lh), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.35))
    # 端をなじませる（弧の両端をフェード）
    fade = Image.new("L", (lw, lh), 0)
    ImageDraw.Draw(fade).ellipse((2, -lh, lw - 3, lh * 2), fill=255)
    fade = feather(fade, 4)
    ov.putalpha(Image.fromarray(
        (np.array(ov.split()[3]).astype(np.float32) * np.array(fade) / 255).astype(np.uint8)))
    lid_patch = lid_patch.convert("RGBA")
    lid_patch.alpha_composite(ov)

    lmask = Image.new("L", (lw, lh), 0)
    ImageDraw.Draw(lmask).rounded_rectangle((6, 6, lw - 7, lh - 7), radius=16, fill=255)
    lmask = feather(lmask, 7)
    lid_patch.putalpha(lmask)
    lid_patch.save(f"{OUT}/lid_{k}.png")
    meta[f"lid_{k}"] = dict(x=lx0, y=ly0, w=lw, h=lh)

# ---------------------------------------------------------------- 4. 口（下顎）
jx0, jy0, jx1, jy1 = JAW_BOX
jm = Image.new("L", (W, H), 0)
dj = ImageDraw.Draw(jm)
poly = MOUTH + [(jx1, jy1), (jx0, jy1)]
dj.polygon(poly, fill=255)
jm = feather(jm, 4)
meta["jaw"] = cut(JAW_BOX, jm, "jaw")
meta["mouth_line"] = MOUTH

# 口内（下顎を下げたときに覗く暗部）: 口ラインに沿った縦グラデ帯
S = 4
mh_ = 34
mo = Image.new("RGBA", ((jx1 - jx0) * S, mh_ * S), (0, 0, 0, 0))
dm = ImageDraw.Draw(mo)
for i in range(mh_ * S):
    a = int(238 * max(0.0, 1 - (i / (mh_ * S)) ** 1.35))
    dm.line([(0, i), ((jx1 - jx0) * S, i)], fill=(30, 18, 16, a))
mo = mo.resize((jx1 - jx0, mh_), Image.LANCZOS)
# 口ラインより上を切り落とす（上端が口の合わせ目に一致するように）
cm = Image.new("L", ((jx1 - jx0) * S, mh_ * S), 0)
dcm = ImageDraw.Draw(cm)
dcm.polygon([((x - jx0) * S, (y - jy0 - (610 - jy0)) * S) for x, y in MOUTH] +
            [((jx1 - jx0) * S, mh_ * S), (0, mh_ * S)], fill=255)
cm = cm.resize((jx1 - jx0, mh_), Image.LANCZOS).filter(ImageFilter.GaussianBlur(1.0))
side = Image.new("L", (jx1 - jx0, mh_), 0)
ImageDraw.Draw(side).rounded_rectangle((8, -20, jx1 - jx0 - 9, mh_ + 20), radius=24, fill=255)
side = feather(side, 9)
mo.putalpha(Image.fromarray((np.array(mo.split()[3]).astype(np.float32) *
                             np.array(cm) / 255 * np.array(side) / 255).astype(np.uint8)))
mo.save(f"{OUT}/mouth_dark.png")
meta["mouth_dark"] = dict(x=jx0, y=jy0, w=jx1 - jx0, h=mh_)

with open(f"{OUT}/parts.json", "w") as f:
    json.dump(meta, f, indent=1)
print(json.dumps(meta, indent=1))

# ---------------------------------------------------------------- 5. WebP 出力
# フロントは *.webp を読み込む。中間の PNG は削除する。
import glob
total = 0
for f in sorted(glob.glob(f"{OUT}/*.png")):
    dst = f[:-4] + ".webp"
    Image.open(f).save(dst, "WEBP", quality=88, method=6)
    total += os.path.getsize(dst)
    os.remove(f)
print(f"webp: {len(glob.glob(f'{OUT}/*.webp'))} files, {total // 1024} KB -> {OUT}/")
