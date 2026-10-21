// Refresh signed tvmalay.my tokens via headless Chromium CDP, then update channels.json.
// Called by proxy.py every REFRESH_SECONDS. Writes results back to channels.json.
// Usage: node refresh_tokens.js [--quiet] [channels_path]
let WebSocket;
try { WebSocket = global.WebSocket; } catch {}
if (!WebSocket) WebSocket = require('ws');
const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');
const path = require('path');

const QUIET = process.argv.includes('--quiet');
const channelsArg = process.argv.find(a => a.endsWith('.json') && !a.startsWith('--'));
const REPO = channelsArg ? path.dirname(channelsArg) : '/data';
const CH_PATH = channelsArg || path.join(REPO, 'channels.json');
const PORT = parseInt(process.env.CDP_PORT || '9222', 10);
const SECONDS_PER_PAGE = parseInt(process.env.PAGE_SECONDS || '12', 10);

const ID_MAP = {
  'cna': 'cna.sg', 'euronews': 'euronews.fr', 'dw': 'dw.de', 'nhk-world': 'nhkworld.jp',
  'arirang': 'arirang.kr', 'rt-international': 'rt.ru', 'taiwanplus': 'taiwanplus.tw',
  'the-indonesia-channel': 'indonesiachannel.id', 'fifa-plus': 'fifaplus.tv',
  'al-jazeera-english': 'aljazeeraenglish.qa', 'al-jazeera-english-live-hd': 'aljazeeraenglishhd.qa',
  'al-jazeera-arabic': 'aljazeeraarabic.qa', 'al-jazeera-arabic-hd': 'aljazeeraarabichd.qa',
};
const slugToId = s => ID_MAP[s] || s.replace(/-/g, '') + '.my';

// slugs for every tvmalay channel id (inverse of slugToId, MY channels only)
const ID_TO_SLUG = {};
for (const s of ['tv1','tv2','tv-okey','sukan-rtm','berita-rtm','tv3','8tv','tv9','drama-sangat',
  'bernama','tv-alhijrah','tv-ikim','usim-tv','didiktv-kpm','siara-tv','tvs','selangor-tv',
  'borneo-tv','mysport','mpl-malaysia','ppa-kl-cup','rakita','ai-fm','asyik-fm','bernama-radio',
  'best-fm','eight-fm','fly-fm','manis-fm','nasional-fm','radio-klasik','sabah-fm','sarawak-fm',
  'suria-fm','wai-fm','hot-fm','ikim-fm','kool-fm','minnal-fm','molek-fm','bernama-tv']) {
  ID_TO_SLUG[slugToId(s)] = s;
}

function getJSON(p) {
  return new Promise((res, rej) => {
    http.get({ host: '127.0.0.1', port: PORT, path: p }, r => {
      let b = '';
      r.on('data', d => b += d);
      r.on('end', () => { try { res(JSON.parse(b)); } catch (e) { rej(e); } });
    }).on('error', rej);
  });
}

function log(...a) { if (!QUIET) console.log(...a); }

async function main() {
  const doc = JSON.parse(fs.readFileSync(CH_PATH, 'utf8'));
  const byId = Object.fromEntries(doc.channels.map(c => [c.id, c]));
  const slugs = Object.entries(ID_TO_SLUG)
    .filter(([id]) => byId[id] && byId[id].url && (byId[id].source || '').includes('tvmalay'))
    .map(([, s]) => s);
  log(`${slugs.length} tvmalay channels to refresh`);

  const chrome = spawn('/usr/bin/chromium', [
    '--headless=new', '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage',
    `--remote-debugging-port=${PORT}`, '--user-data-dir=/tmp/chrome-proxy-profile',
    'about:blank'
  ], { stdio: 'ignore' });

  let targets = null;
  for (let i = 0; i < 60; i++) {
    try { targets = await getJSON('/json/list'); if (targets.length) break; } catch {}
    await new Promise(r => setTimeout(r, 500));
  }
  if (!targets || !targets.length) { console.error('no devtools target'); chrome.kill(); process.exit(1); }

  const ws = new WebSocket(targets[0].webSocketDebuggerUrl);
  await new Promise(r => ws.onopen = r);

  let id = 0;
  const pending = {};
  const hits = {};
  let cur = null;

  function send(method, params = {}) {
    return new Promise(res => {
      const mid = ++id;
      pending[mid] = res;
      ws.send(JSON.stringify({ id: mid, method, params }));
    });
  }
  ws.onmessage = ev => {
    const msg = JSON.parse(ev.data);
    if (msg.id && pending[msg.id]) { pending[msg.id](msg.result); delete pending[msg.id]; return; }
    if (msg.method === 'Network.requestWillBeSent' && cur) {
      const u = msg.params.request.url;
      if (u.split('?')[0].endsWith('.m3u8')) {
        hits[cur] = hits[cur] || [];
        if (!hits[cur].includes(u)) hits[cur].push(u);
      }
    }
  };

  await send('Network.enable', { maxPostDataSize: 1024 });
  await send('Page.enable');

  const now = new Date().toISOString().replace(/\.\d+Z$/, '+00:00');
  let updated = 0, failed = [];

  for (const slug of slugs) {
    cur = slug;
    hits[slug] = [];
    try {
      await send('Page.navigate', { url: `https://tvmalay.my/${slug}/` });
      await new Promise(r => setTimeout(r, SECONDS_PER_PAGE * 1000));
    } catch { /* keep going */ }
    const cid = slugToId(slug);
    const ch = byId[cid];
    const urls = hits[slug];
    if (urls.length) {
      // The player loads a master playlist, then a variant. The variant it
      // re-fetches is what headless Chromium plays (often 480p — no GPU).
      // Prefer the MASTER (has RESOLUTION lines) so players pick their best;
      // fall back to the most-replayed variant if no master was captured.
      const master = urls.find(u => {
        // masters are the first m3u8 whose path differs from re-fetched ones;
        // cheap check: masters are fetched exactly once
        return urls.filter(x => x.split('?')[0] === u.split('?')[0]).length === 1;
      });
      const variant = urls[urls.length - 1];
      ch.url = master || variant;
      ch.headers = { Origin: 'https://tvmalay.my', Referer: 'https://tvmalay.my/' };
      ch.status = 'ok';
      ch.last_checked = now;
      ch.alt_urls = [variant].filter(u => u !== ch.url);
      updated++;
      log(`${slug} ok (${master ? 'master' : 'variant'})`);
    } else {
      failed.push(slug);
      log(`${slug} FAILED`);
    }
  }

  doc.updated = now;
  fs.writeFileSync(CH_PATH, JSON.stringify(doc, null, 2) + '\n');
  log(`updated=${updated} failed=${failed.length}${failed.length ? ' (' + failed.join(',') + ')' : ''}`);
  ws.close();
  chrome.kill();
  process.exit(0);
}
main().catch(e => { console.error('ERR', e.message); process.exit(1); });
