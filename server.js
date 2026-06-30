const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = Number(process.env.PORT || 8080);
const OPENCLAW_GATEWAY = process.env.OPENCLAW_GATEWAY || 'http://127.0.0.1:18789';
const LIVE_AGENT_API = process.env.LIVE_AGENT_API || 'http://127.0.0.1:8003';
const OPENCLAW_TOKEN = process.env.OPENCLAW_TOKEN || '2ec777c61f588861712e0d7d9da2cf909fb2b4f45c954be9';

function cors(res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
}

function serveFile(res, fileName, contentType) {
  const filePath = path.join(__dirname, fileName);
  fs.readFile(filePath, (err, data) => {
    if (err) {
      res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
      res.end('File not found');
      return;
    }
    res.writeHead(200, { 'Content-Type': contentType });
    res.end(data);
  });
}

function proxy(req, res, targetBase, targetPath, extraHeaders = {}) {
  const target = new URL(targetPath, targetBase);
  const headers = {
    ...req.headers,
    host: target.host,
    ...extraHeaders,
  };
  delete headers['content-length'];

  const options = {
    hostname: target.hostname,
    port: target.port,
    path: target.pathname + target.search,
    method: req.method,
    headers,
  };

  const proxyReq = http.request(options, (proxyRes) => {
    const responseHeaders = { ...proxyRes.headers };
    if (targetPath === '/analyze_sse') {
      responseHeaders['content-type'] = 'text/event-stream; charset=utf-8';
      responseHeaders['cache-control'] = 'no-cache';
      responseHeaders.connection = 'keep-alive';
      responseHeaders['x-accel-buffering'] = 'no';
    }
    cors(res);
    res.writeHead(proxyRes.statusCode || 502, responseHeaders);
    proxyRes.on('data', (chunk) => res.write(chunk));
    proxyRes.on('end', () => res.end());
  });

  proxyReq.on('error', (err) => {
    cors(res);
    res.writeHead(502, { 'Content-Type': 'application/json; charset=utf-8' });
    res.end(JSON.stringify({ error: err.message }));
  });

  req.pipe(proxyReq);
}

const server = http.createServer((req, res) => {
  cors(res);

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  const url = new URL(req.url, `http://${req.headers.host}`);

  if (url.pathname === '/' || url.pathname === '/chat.html') {
    serveFile(res, 'chat.html', 'text/html; charset=utf-8');
    return;
  }

  if (url.pathname === '/health' && req.method === 'GET') {
    proxy(req, res, LIVE_AGENT_API, '/health');
    return;
  }

  if (url.pathname === '/analyze_sse' && req.method === 'POST') {
    proxy(req, res, LIVE_AGENT_API, '/analyze_sse');
    return;
  }

  if (url.pathname === '/generate_ppt' && req.method === 'POST') {
    proxy(req, res, LIVE_AGENT_API, '/generate_ppt');
    return;
  }

  if (url.pathname === '/v1/chat/completions' && req.method === 'POST') {
    proxy(req, res, OPENCLAW_GATEWAY, '/v1/chat/completions', {
      Authorization: 'Bearer ' + OPENCLAW_TOKEN,
    });
    return;
  }

  if (url.pathname === '/v1/models' && req.method === 'GET') {
    proxy(req, res, OPENCLAW_GATEWAY, '/v1/models', {
      Authorization: 'Bearer ' + OPENCLAW_TOKEN,
    });
    return;
  }

  res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
  res.end('Not found');
});

server.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}/chat.html`);
  console.log(`Live agent API proxy: ${LIVE_AGENT_API}`);
});
