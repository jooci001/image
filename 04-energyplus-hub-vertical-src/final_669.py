"""Final max-quality encode at an exact average bitrate (Windows shows 669kbps for data rate and total bitrate).
Config N (from enc_search.py): x264 placebo + tune animation, ref 8, bframes 8, aq-mode 3 @0.6, psy-rd off, qcomp 0.5.
Pass 2 is stepped in 1-kbps targets; if they bracket the window, the highest target below it is kept and the gap is
filled with an SEI user-data message in the first access unit (metadata only: decoded pictures are unchanged, which
is verified). Finally the file is stream-copied so the MP4 'btrt' box records max = avg = actual bitrate.
usage: final_669.py master.mkv out.mp4"""
import subprocess, sys, os, hashlib
src, out = sys.argv[1], sys.argv[2]
work = os.path.dirname(os.path.abspath(out))
LO, HI, MID, DUR = 669000, 669500, 669250, 10.0
X264 = 'keyint=300:min-keyint=30:b-pyramid=normal:b-adapt=2:ref=8:bframes=8:aq-mode=3:aq-strength=0.6:psy-rd=0.0,0.0:qcomp=0.5'
COMMON = ['-c:v', 'libx264', '-preset', 'placebo', '-tune', 'animation', '-profile:v', 'high', '-level:v', '4.0', '-x264-params', X264,
          '-pix_fmt', 'yuv420p', '-r', '30', '-fps_mode', 'cfr', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709',
          '-color_range', 'tv', '-an']
UUID = '4750434c-5458-4550-4c55-534855423034'          # ASCII-safe bytes (no 0x00), identifies this padding message
TEXT = 'GS Caltex energy plus Hub | 04 vertical 540x1650 30fps 10s | avg 669kbps | '

def ff(args, inp=src):
    r = subprocess.run(['ffmpeg', '-v', 'warning', '-y', '-i', inp] + args, cwd=work, capture_output=True, text=True)
    if r.returncode: sys.exit(r.stderr[-600:])
    return r.stderr
def vbytes(p):
    o = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v', '-show_entries', 'packet=size', '-of', 'csv=p=0', p],
                       capture_output=True, text=True, check=True).stdout.split()
    return sum(map(int, o))
def frames_md5(p):
    r = subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-f', 'rawvideo', '-pix_fmt', 'yuv420p', '-'], capture_output=True, check=True).stdout
    return hashlib.md5(r).hexdigest(), len(r)

plog = os.path.join(work, 'plog_final'); enc = os.path.join(work, 'final_enc.mp4')
kb = 676
print(ff(COMMON + ['-b:v', f'{kb}k', '-pass', '1', '-passlogfile', plog, '-f', 'null', '/dev/null']).strip() or 'pass 1 ok', flush=True)
tried = {}
while True:
    if kb not in tried:
        ff(COMMON + ['-b:v', f'{kb}k', '-pass', '2', '-passlogfile', plog, '-movflags', '+faststart', enc])
        tried[kb] = vbytes(enc) * 8 / DUR
        print(f'pass 2 @ {kb}k -> {tried[kb]:.0f} bps', flush=True)
    a = tried[kb]
    if LO <= a < HI: best = kb; break
    below = [k for k, v in tried.items() if v < LO]; above = [k for k, v in tried.items() if v >= HI]
    if below and above and max(below) + 1 in above:
        best = max(below); break
    kb += 1 if a < LO else -1
if best != kb or not (LO <= tried[best] < HI):      # re-encode the chosen target (enc holds the last trial)
    ff(COMMON + ['-b:v', f'{best}k', '-pass', '2', '-passlogfile', plog, '-movflags', '+faststart', enc])
base_bytes = vbytes(enc); actual = base_bytes * 8 / DUR
print(f'chosen target {best}k -> {actual:.0f} bps', flush=True)

final = out
if LO <= actual < HI:
    ff(['-map', '0:v', '-c', 'copy', '-movflags', '+faststart', final], inp=enc)
else:
    need = round((MID - actual) * DUR / 8)            # bytes to add
    L = max(1, need - 24)
    for _ in range(6):
        s = (TEXT * 40)[:L]
        ff(['-map', '0:v', '-c', 'copy', '-bsf:v', f'h264_metadata=sei_user_data={UUID}+{s}', '-movflags', '+faststart', final], inp=enc)
        added = vbytes(final) - base_bytes
        got = vbytes(final) * 8 / DUR
        print(f'  SEI pad: string {L} B -> +{added} B -> {got:.0f} bps', flush=True)
        if LO <= got < HI: break
        L += need - added
    else:
        sys.exit('padding did not land')
m1, n1 = frames_md5(enc); m2, n2 = frames_md5(final)
print(f'decoded frames identical with/without padding: {m1 == m2} ({n1 // (540 * 1650 * 3 // 2)} frames)')
print(f'final average: {vbytes(final) * 8 / DUR:.0f} bps')
