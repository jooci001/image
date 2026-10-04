const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');
(async () => {
  const [,, out, fromS, toS, fps='30'] = process.argv;
  const FPS=+fps, start=+(fromS||0), end=+(toS||60);
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' }).catch(()=>chromium.launch());
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  await page.goto('file://' + path.resolve(__dirname, process.env.SCENE||'scene.html'));
  await page.evaluate(async () => {
    const srcs=[...document.querySelectorAll('[style*=url]')].map(e=>e.style.backgroundImage.slice(5,-2)).concat(['img/hands.jpg','img/chars33.jpg','img/brainstorm.jpg','img/signal.jpg','img/s40top.jpg','img/s42top.jpg','img/wrapA.jpg','img/map45.jpg','img/wall44.jpg']);
    await Promise.all(srcs.map(s=>new Promise(r=>{const i=new Image();i.onload=i.onerror=r;i.src=s;})));
    await document.fonts.ready;
  });
  const ff = spawn('ffmpeg', ['-v','error','-y','-f','image2pipe','-c:v','mjpeg','-framerate',String(FPS),'-i','-',
    '-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',out], {stdio:['pipe','inherit','inherit']});
  const n0=Math.round(start*FPS), n1=Math.round(end*FPS);
  for (let i=n0;i<n1;i++){
    await page.evaluate(t=>window.render(t), i/FPS);
    if(i%150===0) await page.waitForTimeout(60);
    const buf = await page.screenshot({ type:'jpeg', quality:92 });
    if(!ff.stdin.write(buf)) await new Promise(r=>ff.stdin.once('drain',r));
  }
  ff.stdin.end(); await new Promise(r=>ff.on('close',r)); await browser.close();
})();
