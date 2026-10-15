// Renders every frame with only one group visible on a transparent page and streams the alpha
// channel to ffmpeg, so edge clipping can be measured offline. usage: node check_bounds.js char|text out.gray
const { chromium } = require('playwright'); const { spawn } = require('child_process'); const path = require('path');
(async () => {
  const [,, mode, out] = process.argv;
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const p = await b.newPage({ viewport: { width: 540, height: 1650 } });
  await p.goto('file://' + path.resolve(__dirname, 'scene.html'));
  await p.evaluate(async (mode) => {
    await document.fonts.ready; await Promise.all([...document.images].map(i => i.decode().catch(() => {})));
    document.documentElement.style.background = 'transparent'; document.body.style.background = 'transparent';
    const keep = mode === 'char' ? ['char'] : ['l4', 'l4g', 'l5'];
    for (const el of document.body.children) if (el.tagName !== 'SCRIPT' && !keep.includes(el.id)) el.style.visibility = 'hidden';
  }, mode);
  const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-c:v', 'png', '-i', '-', '-vf', 'alphaextract', '-f', 'rawvideo', '-pix_fmt', 'gray', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  for (let i = 0; i < 300; i++) {
    await p.evaluate(t => window.render(t), i / 30);
    const buf = await p.screenshot({ type: 'png', omitBackground: true });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r)); await b.close();
})();
