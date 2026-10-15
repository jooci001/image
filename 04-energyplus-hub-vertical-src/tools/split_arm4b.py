"""Split a 4x-upscaled character PNG into a waving forearm layer (drawn BEHIND) and a body layer (drawn in FRONT).
The sleeve cuff stays on the body, so it naturally covers the base of the forearm while it rotates.
- arm  = hand + forearm: polygon (original 323x483 coords x4); in the elbow band only skin-coloured pixels
- body = original minus the arm pixels
- the forearm base is extended under the cuff with edge-extended skin colour (hidden by the cuff)
usage: split_arm4b.py char_4x.png outdir"""
import numpy as np, subprocess, sys
src, outdir = sys.argv[1], sys.argv[2]
S = 4; W, H = 323 * S, 483 * S
raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', src, '-f', 'rawvideo', '-pix_fmt', 'rgba', '-'], capture_output=True, check=True).stdout
img = np.frombuffer(raw, np.uint8).reshape(H, W, 4).copy()
ys, xs = np.mgrid[0:H, 0:W]; X = xs + .5; Y = ys + .5

def poly(pts):
    pts = [(x * S, y * S) for x, y in pts]; m = np.zeros((H, W), bool)
    for i in range(len(pts)):
        x1, y1 = pts[i]; x2, y2 = pts[(i + 1) % len(pts)]
        m ^= ((y1 > Y) != (y2 > Y)) & (X < (x2 - x1) * (Y - y1) / (y2 - y1 + 1e-9) + x1)
    return m

# generous region: hand + forearm, reaching into the cuff on the right
P = poly([(22, 108), (94, 108), (96, 150), (98, 172), (104, 186), (110, 204), (106, 230), (86, 238), (66, 226), (54, 198), (38, 170), (20, 150)])
r, g, b, a = [img[..., i].astype(np.int16) for i in range(4)]
skin = (r - b > 28) & (r > g) & (r > 120)
band = Y > 168 * S                      # elbow band: keep only skin (cuff/shirt stay on the body)
arm = P & (a > 0) & (~band | skin)
# drop small specks of skin-classified pixels inside the cuff (keep the component connected to the hand)
from collections import deque
lab = np.zeros((H, W), np.uint8); q = deque()
# seed: opaque skin pixel nearest the palm centre (original ~ x61, y157)
cy, cx = 157 * S, 61 * S
cand = np.argwhere(arm[cy - 40:cy + 40, cx - 40:cx + 40] & skin[cy - 40:cy + 40, cx - 40:cx + 40] & (a[cy - 40:cy + 40, cx - 40:cx + 40] > 250))
assert len(cand), 'no palm seed found'
k = np.argmin(((cand - 40) ** 2).sum(1)); sy, sx = cy - 40 + int(cand[k][0]), cx - 40 + int(cand[k][1])
lab[sy, sx] = 1; q.append((sy, sx))
while q:
    y, x = q.popleft()
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        ny, nx = y + dy, x + dx
        if 0 <= ny < H and 0 <= nx < W and arm[ny, nx] and not lab[ny, nx]:
            lab[ny, nx] = 1; q.append((ny, nx))
arm = lab.astype(bool)

body = img.copy(); body[arm, 3] = 0
armimg = np.zeros_like(img); armimg[arm] = img[arm]
# extend forearm base under the cuff (region hidden by the cuff on the body layer)
E = poly([(84, 184), (104, 186), (112, 204), (108, 230), (86, 230)]) & ~arm & (body[..., 3] > 200)  # only where the cuff/sleeve hides it
fill = armimg[..., :3].astype(np.float32) * arm[..., None]; m = arm.astype(np.float32)
def box3(x):
    p = np.pad(x, [(1, 1), (1, 1)] + [(0, 0)] * (x.ndim - 2), mode='edge')
    return sum(p[dy:dy + x.shape[0], dx:dx + x.shape[1]] for dy in range(3) for dx in range(3))
y0, y1, x0, x1 = 176 * S, 236 * S, 76 * S, 116 * S          # work only around the elbow
f, mm, e = fill[y0:y1, x0:x1], m[y0:y1, x0:x1], E[y0:y1, x0:x1]
for _ in range(120):
    s = box3(f); c = box3(mm); new = (mm == 0) & (c > 0) & e
    if not new.any(): break
    f[new] = s[new] / c[new][:, None]; mm[new] = 1
ext = np.zeros((H, W), bool); ext[y0:y1, x0:x1] = (mm == 1) & e
# hidden base gets the forearm's average lit skin tone (a peek then reads as arm, not shadow)
lum = 0.299 * r + 0.587 * g + 0.114 * b
lit = arm & band & (lum > np.percentile(lum[arm & band], 50))
tone = img[lit][:, :3].astype(np.float32).mean(0)
armimg[ext, :3] = np.clip(tone, 0, 255).astype(np.uint8); armimg[ext, 3] = 255
for arr, name in ((armimg, 'arm4b'), (body, 'body4b')):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{W}x{H}', '-i', '-', f'{outdir}/{name}.png'], input=arr.tobytes(), check=True)
print('ok arm px', int(arm.sum()), 'ext px', int(ext.sum()), 'pivot(4x):', 93 * S, 208 * S)
