"""Quality search at a fixed average bitrate.
Each config: x264 2-pass from the lossless master; pass 2 repeated (1-kbps steps, then tiny qcomp nudges if the
integer-kbps targets bracket the window) until the average video bitrate lands in [LO, HI) bps.
Quality: PSNR-Y / SSIM-Y vs the master, frame-aligned through raw decodes.
usage: enc_search.py master.mkv master.y workdir config_name [config_name ...]"""
import subprocess, sys, os, time, json, re
src, master_y, work = sys.argv[1], sys.argv[2], sys.argv[3]
names = [n for n in sys.argv[4:] if not n.startswith('measure:')]
measure = [n[8:] for n in sys.argv[4:] if n.startswith('measure:')]
LO, HI, DUR, W, H = 669000, 669500, 10.0, 540, 1650
BASE = dict(keyint=300, **{'min-keyint': 30}, **{'b-pyramid': 'normal'}, **{'b-adapt': 2})
CONFIGS = {
  'A_veryslow_base': ('veryslow', 'animation', dict(ref=4, bframes=5, **{'aq-mode': 3, 'aq-strength': 0.8})),
  'B_placebo':       ('placebo', 'animation', dict(ref=8, bframes=8, **{'aq-mode': 3, 'aq-strength': 0.8})),
  'C_placebo_aq10':  ('placebo', 'animation', dict(ref=8, bframes=8, **{'aq-mode': 3, 'aq-strength': 1.0})),
  'D_placebo_psy0':  ('placebo', 'animation', dict(ref=8, bframes=8, **{'aq-mode': 3, 'aq-strength': 0.8, 'psy-rd': '0.0,0.0'})),
  'E_placebo_qc75':  ('placebo', 'animation', dict(ref=8, bframes=8, **{'aq-mode': 3, 'aq-strength': 0.8, 'qcomp': 0.75})),
  'F_placebo_aq06':  ('placebo', 'animation', dict(ref=8, bframes=8, **{'aq-mode': 3, 'aq-strength': 0.6})),
  'G_placebo_ref9':  ('placebo', 'animation', dict(ref=9, bframes=8, **{'aq-mode': 3, 'aq-strength': 0.8})),
  'H_placebo_bf16':  ('placebo', 'animation', dict(ref=8, bframes=16, **{'aq-mode': 3, 'aq-strength': 0.8})),
  'I_placebo_dbm1':  ('placebo', 'animation', dict(ref=8, bframes=8, **{'aq-mode': 3, 'aq-strength': 0.8, 'deblock': '0,0'})),
  'K_placebo_qc50':  ('placebo', 'animation', dict(ref=8, bframes=8, **{'aq-mode': 3, 'aq-strength': 0.8, 'qcomp': 0.5})),
  'L_placebo_psy02': ('placebo', 'animation', dict(ref=8, bframes=8, **{'aq-mode': 3, 'aq-strength': 0.8, 'psy-rd': '0.2,0.0'})),
  'M_psy0_aq06':           ('placebo', 'animation', dict(ref=8, bframes=8, **{'aq-mode': 3, 'aq-strength': 0.6, 'psy-rd': '0.0,0.0'})),
  'N_psy0_aq06_qc50':      ('placebo', 'animation', dict(ref=8, bframes=8, **{'aq-mode': 3, 'aq-strength': 0.6, 'psy-rd': '0.0,0.0', 'qcomp': 0.5})),
  'O_psy02_aq06_qc50':     ('placebo', 'animation', dict(ref=8, bframes=8, **{'aq-mode': 3, 'aq-strength': 0.6, 'psy-rd': '0.2,0.0', 'qcomp': 0.5})),
  'P_psy0_aq06_qc50_db0':  ('placebo', 'animation', dict(ref=8, bframes=8, **{'aq-mode': 3, 'aq-strength': 0.6, 'psy-rd': '0.0,0.0', 'qcomp': 0.5, 'deblock': '0,0'})),
  'R_psy0_aq04_qc50':      ('placebo', 'animation', dict(ref=8, bframes=8, **{'aq-mode': 3, 'aq-strength': 0.4, 'psy-rd': '0.0,0.0', 'qcomp': 0.5})),
}

def params(d):
    return ':'.join(f'{k}={v}' for k, v in {**BASE, **d}.items())

def ff(args, log=None):
    r = subprocess.run(['ffmpeg', '-v', 'warning', '-y', '-i', src] + args, cwd=work, capture_output=True, text=True)
    if r.returncode: raise RuntimeError(r.stderr[-400:])
    return r.stderr

def vbytes(path):
    o = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v', '-show_entries', 'packet=size', '-of', 'csv=p=0', path],
                       capture_output=True, text=True, check=True).stdout.split()
    return sum(map(int, o))

def common(preset, tune, d):
    return ['-c:v', 'libx264', '-preset', preset, '-tune', tune, '-profile:v', 'high', '-level:v', '4.0', '-x264-params', params(d),
            '-pix_fmt', 'yuv420p', '-r', '30', '-fps_mode', 'cfr', '-colorspace', 'bt709', '-color_primaries', 'bt709',
            '-color_trc', 'bt709', '-color_range', 'tv', '-an']

def quality(path):
    y = os.path.join(work, 'cand.y')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', path, '-vf', 'extractplanes=y', '-f', 'rawvideo', '-pix_fmt', 'gray', y], check=True)
    raw = ['-f', 'rawvideo', '-pix_fmt', 'gray', '-s', f'{W}x{H}', '-r', '30']
    out = subprocess.run(['ffmpeg', '-hide_banner'] + raw + ['-i', y] + raw + ['-i', master_y,
                          '-lavfi', '[0][1]ssim;[0][1]psnr', '-f', 'null', '-'], capture_output=True, text=True).stderr
    ssim = float(re.search(r'SSIM .*All:([0-9.]+)', out).group(1)); psnr = float(re.search(r'PSNR .*average:([0-9.]+)', out).group(1))
    return psnr, ssim

results = {}
for mpath in measure:
    p, s_ = quality(mpath); print(f'{os.path.basename(mpath)}: avg {vbytes(mpath)*8/DUR:.0f} bps | PSNR-Y {p:.3f} dB | SSIM-Y {s_:.5f}', flush=True)
for name in names:
    preset, tune, d = CONFIGS[name]
    try:
        out = os.path.join(work, f'{name}.mp4'); plog = os.path.join(work, f'plog_{name}')
        t0 = time.time(); kb = 671; warn = ''
        warn += ff(common(preset, tune, d) + ['-b:v', f'{kb}k', '-pass', '1', '-passlogfile', plog, '-f', 'null', '/dev/null'])
        tried = {}; nudge = 0; dd = dict(d); nudging = False; q0 = float(d.get('qcomp', 0.6))
        for it in range(1 if os.environ.get('FIXED') else 18):
            warn += ff(common(preset, tune, dd) + ['-b:v', f'{kb}k', '-pass', '2', '-passlogfile', plog, '-movflags', '+faststart', out])
            act = vbytes(out) * 8 / DUR
            print(f'  {name} it{it}: {kb}k qcomp={dd.get("qcomp", q0)} -> {act:.0f} bps', flush=True)
            if LO <= act < HI: break
            if not nudging:
                tried[kb] = act
                below = [k for k, v in tried.items() if v < LO]; above = [k for k, v in tried.items() if v >= HI]
                if below and above and max(below) + 1 in above:          # 1-kbps steps bracket the window
                    nudging = True; kb = min((max(below), max(below) + 1), key=lambda k: abs(tried[k] - (LO + HI) / 2))
                else:
                    kb += 1 if act < LO else -1; continue
            nudge += 1
            dd = dict(d, qcomp=round(q0 + 0.002 * ((nudge + 1) // 2) * (1 if nudge % 2 else -1), 3))
        else:
            if not os.environ.get('FIXED'): print(f'  {name}: did not converge'); continue
        p, s = quality(out)
        dt = time.time() - t0
        lw = [l for l in warn.splitlines() if 'x264' in l and 'warning' in l]
        results[name] = dict(kbps_target=kb, bps=round(act), psnr_y=p, ssim_y=s, secs=round(dt), warnings=lw[:3])
        print(f'{name}: avg {act:.0f} bps | PSNR-Y {p:.3f} dB | SSIM-Y {s:.5f} | {dt:.0f}s | warnings: {lw[:2]}', flush=True)
    except RuntimeError as e:
        print(f'{name}: FAILED {e}', flush=True)
json.dump(results, open(os.path.join(work, 'search_results.json'), 'a'), ensure_ascii=False); open(os.path.join(work, 'search_results.json'), 'a').write('\n')
