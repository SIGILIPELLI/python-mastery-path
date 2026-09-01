// WhatsApp bridge for the vremployee virtual employee.
//
// - Links to the owner's WhatsApp account via QR (whatsapp-web.js / LocalAuth).
// - Command channel is the owner's self-chat ("Message yourself"): any message
//   the owner sends to themselves is treated as a command. Bridge replies are
//   prefixed with BOT_PREFIX and ignored on the way back in, so no loops.
// - Built-ins: status / tasks, ping, new, help. Anything else is run through
//   `claude -p` headless in the workspace root and the result is sent back.
// - Local HTTP endpoint (127.0.0.1:PORT, POST /send, plain-text body) lets
//   other sessions and scheduled tasks push status updates to WhatsApp.

const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode');
const qrcodeTerminal = require('qrcode-terminal');
const http = require('http');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const BRIDGE_DIR = __dirname;
const ROOT = path.resolve(BRIDGE_DIR, '..');
const CONFIG = JSON.parse(fs.readFileSync(path.join(BRIDGE_DIR, 'config.json'), 'utf8'));
const BOT_PREFIX = CONFIG.botPrefix || '\u{1F916}'; // 🤖
const QR_FILE = path.join(BRIDGE_DIR, 'qr.png');
const STATE_FILE = path.join(BRIDGE_DIR, 'state.json');
const MAX_MSG_CHARS = 3500;
const MAX_CHUNKS = 3;

let state = {};
try { state = JSON.parse(fs.readFileSync(STATE_FILE, 'utf8')); } catch {}
const saveState = () => fs.writeFileSync(STATE_FILE, JSON.stringify(state, null, 2));

const log = (...args) => console.log(new Date().toISOString(), ...args);

const client = new Client({
  authStrategy: new LocalAuth({ dataPath: path.join(BRIDGE_DIR, '.wwebjs_auth') }),
  puppeteer: { headless: true, args: ['--no-sandbox', '--disable-dev-shm-usage'] },
});

const myId = () => client.info.wid._serialized;

async function send(text) {
  const body = `${BOT_PREFIX} ${text}`;
  // Chunk long replies so WhatsApp stays readable.
  const chunks = [];
  for (let i = 0; i < body.length && chunks.length < MAX_CHUNKS; i += MAX_MSG_CHARS) {
    chunks.push(body.slice(i, i + MAX_MSG_CHARS));
  }
  if (body.length > MAX_CHUNKS * MAX_MSG_CHARS) {
    chunks[chunks.length - 1] += '\n…(truncated — full output is on the Mac)';
  }
  for (const chunk of chunks) {
    await client.sendMessage(myId(), chunk.startsWith(BOT_PREFIX) ? chunk : `${BOT_PREFIX} ${chunk}`);
  }
}

// ---------- built-in: task ledger summary ----------

function taskSummary() {
  const md = fs.readFileSync(path.join(ROOT, 'TASKS.md'), 'utf8');
  const rows = md.split('\n')
    .filter((l) => /^\|\s*\d+\s*\|/.test(l))
    .map((l) => {
      const cells = l.split('|').map((c) => c.trim());
      return { num: cells[1], task: cells[2], status: cells[3], date: cells[4] };
    });
  const counts = {};
  for (const r of rows) {
    const key = r.status.replace(/\*/g, '').split('—')[0].trim();
    counts[key] = (counts[key] || 0) + 1;
  }
  const active = rows.filter((r) => !/^Done/.test(r.status));
  const lines = [];
  lines.push(`Task ledger: ${rows.length} tasks — ` +
    Object.entries(counts).map(([k, v]) => `${v} ${k}`).join(', '));
  if (active.length) {
    lines.push('', 'Open items:');
    for (const r of active) {
      const name = r.task.length > 90 ? r.task.slice(0, 87) + '…' : r.task;
      lines.push(`• #${r.num} [${r.status}] ${name}`);
    }
  } else {
    lines.push('', 'Nothing open — everything is Done.');
  }
  lines.push('', 'Reply with any instruction to run it, or "help" for commands.');
  return lines.join('\n');
}

// ---------- claude runner (serialized queue) ----------

let queue = Promise.resolve();
let queueDepth = 0;

function runClaude(prompt) {
  const wrapped =
    `${prompt}\n\n` +
    `(This message arrived via WhatsApp from the owner through whatsapp-bridge, ` +
    `running headless in the vremployee workspace. Reply in plain WhatsApp-friendly ` +
    `text: short and concise, no markdown headings or tables. Follow CLAUDE.md; ` +
    `anything the operating charter requires confirmation for must NOT be executed — ` +
    `instead say what needs confirming and that it can be approved in a Claude Code ` +
    `session on the Mac.)`;

  const args = ['-p', wrapped, '--output-format', 'json', ...(CONFIG.claudeArgs || [])];
  if (state.sessionId) args.push('--resume', state.sessionId);

  return new Promise((resolve) => {
    const child = spawn(CONFIG.claudePath, args, { cwd: ROOT, env: process.env });
    let out = '', err = '';
    const timer = setTimeout(() => {
      child.kill('SIGKILL');
      resolve({ text: `Timed out after ${CONFIG.timeoutMinutes} min. The task may still be worth running from the Mac directly.` });
    }, CONFIG.timeoutMinutes * 60 * 1000);
    child.stdout.on('data', (d) => (out += d));
    child.stderr.on('data', (d) => (err += d));
    child.on('close', (code) => {
      clearTimeout(timer);
      try {
        const parsed = JSON.parse(out);
        if (parsed.session_id) { state.sessionId = parsed.session_id; saveState(); }
        resolve({ text: parsed.result || '(empty result)' });
      } catch {
        if (state.sessionId && /No conversation found|session/i.test(err + out) && code !== 0) {
          // Stale session id — drop it so the next message starts fresh.
          delete state.sessionId; saveState();
        }
        resolve({ text: code === 0 ? (out.trim() || '(no output)') : `claude exited with code ${code}: ${(err || out).trim().slice(0, 1500)}` });
      }
    });
  });
}

// ---------- command handling ----------

async function handleCommand(body) {
  const cmd = body.toLowerCase();
  if (cmd === 'ping') return send('pong — bridge is up on the Mac.');
  if (cmd === 'help') {
    return send(
      'Commands:\n' +
      '• status / tasks — summary of TASKS.md\n' +
      '• new — start a fresh Claude session (forget chat context)\n' +
      '• ping — check the bridge is alive\n' +
      'Anything else is sent to Claude Code in the vremployee workspace and the answer comes back here. Long tasks can take minutes.'
    );
  }
  if (cmd === 'status' || cmd === 'tasks') {
    try { return send(taskSummary()); }
    catch (e) { return send(`Could not read TASKS.md: ${e.message}`); }
  }
  if (cmd === 'new') {
    delete state.sessionId; saveState();
    return send('Fresh session started — next message begins a new Claude conversation.');
  }

  queueDepth++;
  await send(queueDepth > 1
    ? `Queued (${queueDepth - 1} ahead). I'll reply when it's done.`
    : 'Working on it — I\'ll reply when done. Long tasks can take a few minutes.');
  queue = queue.then(async () => {
    try {
      const { text } = await runClaude(body);
      await send(text);
    } catch (e) {
      await send(`Error: ${e.message}`);
    } finally {
      queueDepth--;
    }
  });
  return queue;
}

// ---------- wiring ----------

client.on('qr', async (qr) => {
  qrcodeTerminal.generate(qr, { small: true });
  await qrcode.toFile(QR_FILE, qr, { width: 500 });
  log(`QR code saved to ${QR_FILE} — scan via WhatsApp > Settings > Linked Devices > Link a Device`);
});

client.on('authenticated', () => log('Authenticated.'));
client.on('loading_screen', (percent, message) => log(`Loading: ${percent}% ${message || ''}`));
client.on('change_state', (s) => log(`State change: ${s}`));
client.on('auth_failure', (m) => log(`AUTH FAILURE: ${m}`));

// Periodic state probe until ready — surfaces where startup hangs (e.g. under launchd).
const probe = setInterval(async () => {
  if (client.info) return clearInterval(probe);
  try { log(`state probe: ${await client.getState()}`); }
  catch (e) { log(`state probe error: ${e.message.split('\n')[0]}`); }
}, 15000);

// Ready watchdog: under launchd the library's post-auth ready flow can stall
// silently even though the page is CONNECTED and evaluations work. Replay the
// same steps Client.js runs (inject utils -> client.info -> listeners -> READY)
// manually if ready hasn't fired a while after authentication.
const { LoadUtils } = require('whatsapp-web.js/src/util/Injected/Utils');
const ClientInfo = require('whatsapp-web.js/src/structures/ClientInfo');
const InterfaceController = require('whatsapp-web.js/src/util/InterfaceController');

const withTimeout = (p, ms, label) => Promise.race([
  p, new Promise((_, rej) => setTimeout(() => rej(new Error(`${label} timed out after ${ms}ms`)), ms)),
]);

async function forceReady() {
  const page = client.pupPage;
  const state = await withTimeout(client.getState(), 15000, 'getState');
  if (state !== 'CONNECTED') throw new Error(`state is ${state}, not CONNECTED`);
  const injected = await withTimeout(page.evaluate('window.WWebJS != undefined'), 15000, 'injection check');
  if (!injected) {
    log('watchdog: WWebJS not injected — running LoadUtils');
    await withTimeout(page.evaluate(LoadUtils), 30000, 'LoadUtils');
  }
  log('watchdog: fetching client info');
  const info = await withTimeout(page.evaluate(() => ({
    ...window.require('WAWebConnModel').Conn.serialize(),
    wid: window.require('WAWebUserPrefsMeUser').getMaybeMePnUser() ||
         window.require('WAWebUserPrefsMeUser').getMaybeMeLidUser(),
  })), 30000, 'client info fetch');
  client.info = new ClientInfo(client, info);
  client.interface = new InterfaceController(client);
  log('watchdog: attaching event listeners');
  await withTimeout(client.attachEventListeners(), 30000, 'attachEventListeners');
  client.emit('ready');
  log('watchdog: READY (synthesized)');
}

let sawAuth = false;
client.on('authenticated', () => { sawAuth = true; });
const watchdog = setInterval(async () => {
  if (client.info) return clearInterval(watchdog);
  if (!sawAuth) return;
  log('watchdog: authenticated but not ready — forcing ready sequence');
  try { await forceReady(); clearInterval(watchdog); }
  catch (e) { log(`watchdog failed at: ${e.message}`); }
}, 30000);

process.on('unhandledRejection', (r) => log('unhandledRejection:', r instanceof Error ? r.message : r));

// Graceful shutdown — without this, SIGTERM is swallowed and supervisors
// (launchd, kill) leave a zombie holding the port and the Chromium profile.
let shuttingDown = false;
async function shutdown(sig) {
  if (shuttingDown) return;
  shuttingDown = true;
  log(`${sig} received — shutting down`);
  setTimeout(() => process.exit(0), 8000).unref(); // hard exit if destroy hangs
  try { server.close(); } catch {}
  try { await client.destroy(); } catch {}
  process.exit(0);
}
process.on('SIGTERM', () => shutdown('SIGTERM'));
process.on('SIGINT', () => shutdown('SIGINT'));

// All ids that mean "me". The self-chat mixes formats depending on the sending
// device: phone-sent texts arrive @c.us -> @lid, bridge-sent ones @lid -> @lid.
const selfIds = new Set();

client.on('ready', async () => {
  try { fs.unlinkSync(QR_FILE); } catch {}
  selfIds.add(myId());
  try {
    const ids = await client.pupPage.evaluate(() => ({
      pn: window.require('WAWebUserPrefsMeUser').getMaybeMePnUser()?._serialized,
      lid: window.require('WAWebUserPrefsMeUser').getMaybeMeLidUser()?._serialized,
    }));
    for (const id of Object.values(ids)) if (id) selfIds.add(id);
  } catch (e) { log(`self-id lookup failed (falling back to wid only): ${e.message}`); }
  log(`READY — linked as ${myId()}, self ids: ${[...selfIds].join(', ')}. Command channel: the "Message yourself" chat.`);
});

client.on('disconnected', (reason) => {
  log('Disconnected:', reason, '— exiting so the supervisor restarts us.');
  process.exit(1);
});

client.on('message_create', async (msg) => {
  try {
    log(`msg event: from=${msg.from} to=${msg.to} fromMe=${msg.fromMe} body="${(msg.body || '').slice(0, 40)}"`);
    if (!client.info) return;
    // Self-chat only: a message I sent whose recipient is any of my own ids.
    if (!msg.fromMe || !(selfIds.has(msg.to) || msg.to === msg.from)) return;
    const body = (msg.body || '').trim();
    if (!body || body.startsWith(BOT_PREFIX)) return; // ignore our own replies
    log(`Command: ${body.slice(0, 120)}`);
    await handleCommand(body);
  } catch (e) {
    log('handler error:', e);
    try { await send(`Error: ${e.message}`); } catch {}
  }
});

// ---------- local notify endpoint ----------

const server = http.createServer((req, res) => {
  if (req.method === 'GET' && req.url === '/health') {
    const ready = !!client.info;
    res.writeHead(ready ? 200 : 503, { 'Content-Type': 'text/plain' });
    return res.end(ready ? 'ready' : 'starting');
  }
  if (req.method === 'POST' && req.url === '/test-inbound') {
    // Debug: send an UNPREFIXED message to the self-chat, which loops back
    // through WhatsApp and exercises the real inbound command path.
    let body = '';
    req.on('data', (d) => (body += d));
    req.on('end', async () => {
      if (!client.info) { res.writeHead(503); return res.end('not ready'); }
      await client.sendMessage(myId(), body.trim() || 'ping');
      res.writeHead(200); res.end('injected');
    });
    return;
  }
  if (req.method === 'POST' && req.url === '/send') {
    let body = '';
    req.on('data', (d) => (body += d));
    req.on('end', async () => {
      const text = body.trim();
      if (!text) { res.writeHead(400); return res.end('empty body'); }
      if (!client.info) { res.writeHead(503); return res.end('whatsapp not ready'); }
      try {
        await send(text);
        res.writeHead(200); res.end('sent');
      } catch (e) {
        res.writeHead(500); res.end(String(e.message));
      }
    });
    return;
  }
  res.writeHead(404); res.end();
});
server.listen(CONFIG.port, '127.0.0.1', () =>
  log(`Notify endpoint on http://127.0.0.1:${CONFIG.port} (POST /send, GET /health)`));

client.initialize();
