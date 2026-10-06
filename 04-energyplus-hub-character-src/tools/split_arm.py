"""Split the character PNG into body and waving-arm layers (both at 3x, lanczos-upscaled)."""
import numpy as np, subprocess, sys
src, outdir = sys.argv[1], sys.argv[2]
W, H = 323, 483
raw = subprocess.run(['ffmpeg','-v','error','-i',src,'-f','rawvideo','-pix_fmt','rgba','-'],capture_output=True,check=True).stdout
img = np.frombuffer(raw, np.uint8).reshape(H, W, 4).copy()
ARM = [(24,110),(92,110),(94,150),(98,170),(102,188),(106,204),(102,228),(86,236),(68,224),(56,198),(40,170),(22,150)]
def inpoly(poly, w, h):
    ys, xs = np.mgrid[0:h, 0:w]; x = xs + .5; y = ys + .5; ins = np.zeros((h, w), bool)
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % n]
        c = ((y1 > y) != (y2 > y)) & (x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-9) + x1)
        ins ^= c
    return ins
arm = inpoly(ARM, W, H)
# keep a joint overlap (near elbow/cuff) in the body layer so rotation never opens a gap
yy, xx = np.mgrid[0:H, 0:W]; joint = ((xx - 98) / 13.0) ** 2 + ((yy - 210) / 24.0) ** 2 < 1
armimg = img.copy(); armimg[~arm, 3] = 0
body = img.copy(); body[arm & ~joint, 3] = 0
def save(a, name):
    p = subprocess.run(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgba','-s',f'{W}x{H}','-i','-',
                        '-vf','scale=iw*3:ih*3:flags=lanczos,unsharp=5:5:0.6',f'{outdir}/{name}.png'], input=a.tobytes(), check=True)
save(armimg, 'arm'); save(body, 'body')
dbg = img.copy(); dbg[arm, 0] = 255; dbg[joint & arm, 2] = 255
save(dbg, 'debug')
print('ok, pivot (3x):', 98*3, 214*3)
