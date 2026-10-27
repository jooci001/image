// Lossless 2x (deviceScaleFactor 2) PNG frames -> 540x1650 lanczos-supersampled yuv420p, stored losslessly (FFV1)
// as the master for low-bitrate delivery encodes. usage: node render_lossless.js out.mkv [fps] [dur]
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');
(async () => {
  const [,, out, fps = '30', dur = '10'] = process.argv;
  const FPS = +fps, N = Math.round(+dur * FPS);
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const page = await browser.newPage({ viewport: { width: 540, height: 1650 }, deviceScaleFactor: 2 });
  await page.goto('file://' + path.resolve(__dirname, 'scene.html'));
  await page.evaluate(async () => { await document.fonts.ready; await Promise.all([...document.images].map(i => i.decode().catch(() => {}))); });
  await page.waitForTimeout(300);
  const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-c:v', 'png', '-framerate', String(FPS), '-i', '-',
    '-vf', 'scale=540:1650:flags=lanczos+accurate_rnd+full_chroma_int:out_color_matrix=bt709:out_range=tv,format=yuv420p',
    '-c:v', 'ffv1', '-level', '3', '-g', '1', '-slices', '4', '-slicecrc', '1',
    '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  for (let i = 0; i < N; i++) {
    await page.evaluate(t => window.render(t), i / FPS);
    const buf = await page.screenshot({ type: 'png' });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r)); await browser.close();
})();
