"""2-pass x264 encode of the lossless master to an exact average video bitrate.
The average (video bytes x 8 / duration) must land in [lo, hi) bps so Windows shows the target kbps for both
'데이터 속도' and '총 비트 전송률' (no audio track). Pass 1 runs once; pass 2 is repeated with a corrected -b:v.
usage: enc_kbps.py master.mkv out.mp4 target_bps lo hi"""
import subprocess, sys, os, struct
src, out, target, lo, hi = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
DUR = 10.0
work = os.path.dirname(os.path.abspath(out)) or '.'
plog = os.path.join(work, 'x264_2pass')
X264 = ':'.join(['keyint=300', 'min-keyint=30', 'ref=4', 'bframes=5', 'b-pyramid=normal', 'b-adapt=2',
                 'aq-mode=3', 'aq-strength=0.8'])
common = ['-c:v', 'libx264', '-preset', 'veryslow', '-tune', 'animation', '-profile:v', 'high', '-level:v', '4.0',
          '-x264-params', X264, '-pix_fmt', 'yuv420p', '-r', '30', '-fps_mode', 'cfr',
          '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv', '-an']

def run(args):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src] + args, check=True, cwd=work)

def video_bytes(path):
    o = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v', '-show_entries', 'packet=size', '-of', 'csv=p=0', path],
                       capture_output=True, text=True, check=True).stdout.split()
    return sum(int(x) for x in o), len(o)

run(common + ['-b:v', str(target), '-pass', '1', '-passlogfile', plog, '-f', 'null', '/dev/null'])
b = target
for it in range(1, 9):
    run(common + ['-b:v', str(b), '-pass', '2', '-passlogfile', plog, '-movflags', '+faststart', out])
    nbytes, nfr = video_bytes(out)
    actual = nbytes * 8 / DUR
    print(f'iter {it}: -b:v {b} -> {nfr} frames, {nbytes} video bytes, average {actual:.0f} bps', flush=True)
    if lo <= actual < hi:
        print('OK'); break
    b = int(round(b * ((lo + hi) / 2) / actual))
else:
    print('did not converge'); sys.exit(1)
