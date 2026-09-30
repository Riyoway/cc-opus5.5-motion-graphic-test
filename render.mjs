// node render.mjs [stills t1,t2,...]  -> renders reel.html frame-by-frame into ffmpeg
import { chromium } from 'playwright-core';
import { spawn } from 'node:child_process';
import { writeFileSync } from 'node:fs';
import { homedir } from 'node:os';

const exe = `${homedir()}/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe`;
const browser = await chromium.launch({ executablePath: exe });
const WORKERS = 6, TOTAL = 900;
const pages = await Promise.all(Array.from({ length: WORKERS }, async () => {
  const p = await (await browser.newContext()).newPage();
  await p.goto(new URL('reel.html?render', import.meta.url).href); return p; }));
const grab = async (p, f) => Buffer.from((await p.evaluate(f => window.grabFrame(f), f)).split(',')[1], 'base64');

if (process.argv[2] === 'stills') {
  const ts = process.argv[3].split(',').map(Number);
  await Promise.all(ts.map((t, i) => grab(pages[i % WORKERS], Math.round(t * 60)).then(b => writeFileSync(`stills/s_${t}.png`, b))));
} else {
  const ff = spawn('ffmpeg', ['-y', '-f', 'image2pipe', '-framerate', '60', '-c:v', 'png', '-i', '-', '-i', 'soundtrack.wav',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '14', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '256k',
    '-movflags', '+faststart', '-shortest', 'showreel.mp4'], { stdio: ['pipe', 'inherit', 'inherit'] });
  const buf = new Map(); let next = 0, f = 0; const t0 = Date.now();
  await Promise.all(pages.map(async p => { while (f < TOTAL) { const i = f++; buf.set(i, await grab(p, i));
    while (buf.has(next)) { ff.stdin.write(buf.get(next)); buf.delete(next++); if (next % 60 === 0) console.error(`frame ${next}/${TOTAL} ${((Date.now() - t0) / 1000).toFixed(0)}s`); } } }));
  ff.stdin.end(); await new Promise(r => ff.on('close', r));
}
await browser.close();
