// Lossless 2x (deviceScaleFactor 2) PNG frames -> two H.264 outputs from one pass:
//   out1: 1650x540  (lanczos downscale = supersampled), out2: 3300x1080 (2x master). BT.709 tagged.
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');
(async () => {
  const [,, out1, out2, fps = '30', dur = '10'] = process.argv;
  const FPS = +fps, N = Math.round(+dur * FPS);
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const page = await browser.newPage({ viewport: { width: 1650, height: 540 }, deviceScaleFactor: 2 });
  await page.goto('file://' + path.resolve(__dirname, 'scene.html'));
  await page.evaluate(async () => { await document.fonts.ready; await Promise.all([...document.images].map(i => i.decode().catch(() => {}))); });
  await page.waitForTimeout(300);
  const enc = ['-c:v', 'libx264', '-preset', 'slow', '-crf', '12', '-tune', 'animation', '-profile:v', 'high', '-pix_fmt', 'yuv420p',
    '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv', '-r', String(FPS), '-movflags', '+faststart'];
  const sc = 'flags=lanczos+accurate_rnd+full_chroma_int:out_color_matrix=bt709:out_range=tv';
  const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-c:v', 'png', '-framerate', String(FPS), '-i', '-',
    '-filter_complex', `[0:v]split=2[a][b];[a]scale=1650:540:${sc},format=yuv420p[o1];[b]scale=3300:1080:${sc},format=yuv420p[o2]`,
    '-map', '[o1]', ...enc, out1, '-map', '[o2]', ...enc, out2], { stdio: ['pipe', 'inherit', 'inherit'] });
  for (let i = 0; i < N; i++) {
    await page.evaluate(t => window.render(t), i / FPS);
    const buf = await page.screenshot({ type: 'png' });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r)); await browser.close();
})();
