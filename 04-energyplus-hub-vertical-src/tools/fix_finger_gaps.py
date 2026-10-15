"""Make the leftover white background between the waving hand's fingers transparent.
Works only inside the hand box (original 323x483 coords x4). Pure white (low saturation, bright) -> alpha 0.
The thin anti-aliased band between white and skin is un-mixed: alpha = share of skin along the white->skin
colour line, colour = local skin (decontaminated), so no light fringe remains on a dark background.
usage: fix_finger_gaps.py in_4x.png out_4x.png [mask_preview.png]"""
import sys, subprocess, numpy as np
src, dst = sys.argv[1], sys.argv[2]
prev = sys.argv[3] if len(sys.argv) > 3 else None
W, H = 1292, 1932
raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', src, '-f', 'rawvideo', '-pix_fmt', 'rgba', '-'], capture_output=True, check=True).stdout
img = np.frombuffer(raw, np.uint8).reshape(H, W, 4).copy()
Y0, Y1, X0, X1 = 420, 680, 70, 370          # hand box: original x 17..92, y 105..170
reg = img[Y0:Y1, X0:X1].astype(np.float32)
rgb, a = reg[..., :3], reg[..., 3]
mx, mn = rgb.max(-1), rgb.min(-1); sat = (mx - mn) / np.maximum(mx, 1)
skin = (sat > 0.24) & (a > 200)
white = (sat < 0.12) & (mn > 200) & (a > 0)

def box3(x):
    p = np.pad(x, [(1, 1), (1, 1)] + [(0, 0)] * (x.ndim - 2), mode='edge')
    return sum(p[dy:dy + x.shape[0], dx:dx + x.shape[1]] for dy in range(3) for dx in range(3))
def dilate(m, n):
    for _ in range(n): m = box3(m.astype(np.float32)) > 0
    return m
def diffuse(src_mask, iters):
    f = rgb * src_mask[..., None]; m = src_mask.astype(np.float32)
    for _ in range(iters):
        s, c = box3(f), box3(m); new = (m == 0) & (c > 0)
        f[new] = s[new] / c[new][:, None]; m[new] = 1
    return f, m > 0

band = dilate(white, 6) & ~white & ~skin & (a > 0)        # transition pixels touching the white
F, okF = diffuse(skin, 24)                                 # local skin colour
B, okB = diffuse(white, 24)                                # local white colour
d = F - B; t = ((rgb - B) * d).sum(-1) / np.maximum((d * d).sum(-1), 1.0)
alpha_skin = np.clip(t, 0, 1)
new_a = a.copy(); new_rgb = rgb.copy()
new_a[white] = 0
sel = band & okF & okB
new_a[sel] = a[sel] * alpha_skin[sel]
new_rgb[sel] = F[sel]
new_rgb[white & okF] = F[white & okF]                      # colour under alpha 0 = skin (no halo when scaled)
img[Y0:Y1, X0:X1, :3] = np.clip(new_rgb, 0, 255).round().astype(np.uint8)
img[Y0:Y1, X0:X1, 3] = np.clip(new_a, 0, 255).round().astype(np.uint8)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{W}x{H}', '-i', '-', dst], input=img.tobytes(), check=True)
print(f'white px -> transparent: {int(white.sum())}, edge px un-mixed: {int(sel.sum())}, skin px untouched: {int(skin.sum())}')
if prev:  # red = removed, yellow = un-mixed edge
    pv = reg[..., :3].copy(); pv[white] = (255, 0, 0); pv[sel] = (255, 220, 0)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{X1 - X0}x{Y1 - Y0}', '-i', '-',
                    '-vf', 'scale=iw*2:ih*2:flags=neighbor', prev], input=np.clip(pv, 0, 255).astype(np.uint8).tobytes(), check=True)
