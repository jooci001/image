"""4x super-resolution of an RGBA PNG with Real-ESRGAN x4plus (ncnn, CPU).
RGB: transparent pixels are first filled by edge extension so the model never sees a hard
colour step at the silhouette (avoids dark/white fringes). Alpha: upscaled by the same model
(as a grey image) for crisp edges. Processed in padded tiles to bound memory.
usage: esr_up.py model.param model.bin in.png out.png"""
import sys, subprocess, numpy as np, ncnn

param, binf, src, dst = sys.argv[1:5]
SC, TILE, PAD = 4, 128, 12

def probe(path):
    out = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=width,height', '-of', 'csv=p=0', path],
                         capture_output=True, text=True, check=True).stdout.strip().split(',')
    return int(out[0]), int(out[1])

W, H = probe(src)
raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', src, '-f', 'rawvideo', '-pix_fmt', 'rgba', '-'],
                     capture_output=True, check=True).stdout
img = np.frombuffer(raw, np.uint8).reshape(H, W, 4)
rgb = img[..., :3].astype(np.float32); a = img[..., 3].astype(np.float32)

# --- edge extension of colour into transparent areas ---
mask = (a > 200).astype(np.float32)
fill = rgb * mask[..., None]
def box3(x):
    p = np.pad(x, [(1, 1), (1, 1)] + [(0, 0)] * (x.ndim - 2), mode='edge')
    return sum(p[dy:dy + x.shape[0], dx:dx + x.shape[1]] for dy in range(3) for dx in range(3))
m = mask.copy()
for _ in range(24):
    s = box3(fill); c = box3(m)
    new = (m == 0) & (c > 0)
    fill[new] = s[new] / c[new][:, None]; m[new] = 1
    if m.min() == 1: break
if m.min() == 0:
    mean = fill[m == 1].mean(0); fill[m == 0] = mean
# keep original colours where the pixel is (semi-)opaque
w = (a / 255.0)[..., None]
rgb_in = np.clip(rgb * w + fill * (1 - w), 0, 255).astype(np.uint8)

net = ncnn.Net()
net.opt.use_vulkan_compute = False
net.opt.num_threads = 4
net.load_param(param); net.load_model(binf)

def run(rgb8):
    h, w_ = rgb8.shape[:2]
    out = np.zeros((h * SC, w_ * SC, 3), np.float32)
    for y0 in range(0, h, TILE):
        for x0 in range(0, w_, TILE):
            y1, x1 = min(y0 + TILE, h), min(x0 + TILE, w_)
            py0, px0, py1, px1 = max(0, y0 - PAD), max(0, x0 - PAD), min(h, y1 + PAD), min(w_, x1 + PAD)
            tile = np.ascontiguousarray(rgb8[py0:py1, px0:px1])
            mi = ncnn.Mat.from_pixels(tile, ncnn.Mat.PixelType.PIXEL_RGB, tile.shape[1], tile.shape[0])
            mi.substract_mean_normalize([], [1 / 255.0] * 3)
            ex = net.create_extractor(); ex.input('data', mi)
            _, mo = ex.extract('output')
            o = np.array(mo).transpose(1, 2, 0)  # HWC, 0..1
            oy, ox = (y0 - py0) * SC, (x0 - px0) * SC
            out[y0 * SC:y1 * SC, x0 * SC:x1 * SC] = o[oy:oy + (y1 - y0) * SC, ox:ox + (x1 - x0) * SC]
    return np.clip(out * 255.0, 0, 255)

up_rgb = run(rgb_in)
up_a = run(np.repeat(img[..., 3:4], 3, axis=2)).mean(2)
outimg = np.dstack([up_rgb, up_a]).round().astype(np.uint8)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{W * SC}x{H * SC}', '-i', '-', dst],
               input=outimg.tobytes(), check=True)
print('ok', W * SC, H * SC)
