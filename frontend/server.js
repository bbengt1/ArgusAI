/* eslint-disable @typescript-eslint/no-require-imports */
/**
 * Custom HTTPS server for Next.js production
 *
 * This server enables HTTPS for the Next.js frontend using the same
 * SSL certificates configured for the backend. It also handles WebSocket
 * proxying for live camera streams (Story P16-2).
 *
 * Uses http-proxy for proper WebSocket handling.
 *
 * Usage:
 *   SSL_CERT_FILE=/path/to/cert.pem SSL_KEY_FILE=/path/to/key.pem node server.js
 *
 * Environment variables:
 *   SSL_CERT_FILE - Path to SSL certificate file (required)
 *   SSL_KEY_FILE  - Path to SSL private key file (required)
 *   PORT          - Port to listen on (default: 3000)
 *   HOSTNAME      - Hostname to bind to (default: 0.0.0.0)
 *   BACKEND_URL   - Backend URL for API/WebSocket proxying (default: http://localhost:8000)
 */

const { createServer } = require('https');
const { parse } = require('url');
const next = require('next');
const fs = require('fs');
const httpProxy = require('http-proxy');

const dev = process.env.NODE_ENV !== 'production';
const hostname = process.env.HOSTNAME || '0.0.0.0';
const port = parseInt(process.env.PORT || '3000', 10);

// Backend URL for WebSocket proxying
const backendUrl = process.env.BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// SSL certificate paths from environment variables
const certFile = process.env.SSL_CERT_FILE;
const keyFile = process.env.SSL_KEY_FILE;

// Validate SSL configuration
if (!certFile || !keyFile) {
  console.error('Error: SSL_CERT_FILE and SSL_KEY_FILE environment variables are required');
  console.error('Usage: SSL_CERT_FILE=/path/to/cert.pem SSL_KEY_FILE=/path/to/key.pem node server.js');
  process.exit(1);
}

// Check if certificate files exist
if (!fs.existsSync(certFile)) {
  console.error(`Error: Certificate file not found: ${certFile}`);
  process.exit(1);
}

if (!fs.existsSync(keyFile)) {
  console.error(`Error: Key file not found: ${keyFile}`);
  process.exit(1);
}

// Read SSL certificates
const httpsOptions = {
  cert: fs.readFileSync(certFile),
  key: fs.readFileSync(keyFile),
};

// Create WebSocket proxy
const wsProxy = httpProxy.createProxyServer({
  target: backendUrl,
  ws: true,
  changeOrigin: true,
});

// Log proxy errors and events for debugging
wsProxy.on('error', (err, req, res) => {
  console.error('WebSocket proxy error:', err.message, err.stack);
  if (res && res.writeHead) {
    res.writeHead(502);
    res.end('Proxy error');
  }
});

wsProxy.on('proxyReqWs', (proxyReq, req, socket) => {
  console.log(`WebSocket proxy: ${req.url} -> ${backendUrl}`);
});

wsProxy.on('open', (proxySocket) => {
  console.log('WebSocket proxy: connection opened to backend');
});

wsProxy.on('close', (res, socket, head) => {
  console.log('WebSocket proxy: connection closed');
});

// Initialize Next.js app
const app = next({ dev, hostname, port });
const handle = app.getRequestHandler();

// Create HTTPS server
const server = createServer(httpsOptions, async (req, res) => {
  try {
    const parsedUrl = parse(req.url, true);
    await handle(req, res, parsedUrl);
  } catch (err) {
    console.error('Error occurred handling', req.url, err);
    res.statusCode = 500;
    res.end('Internal Server Error');
  }
});

// Check if a path should be proxied to our backend WebSocket
function isProxiedWebSocketPath(pathname) {
  return (pathname.startsWith('/api/v1/cameras/') && pathname.endsWith('/stream')) ||
    pathname === '/ws' || pathname.startsWith('/ws/');
}

// Handle WebSocket upgrades BEFORE Next.js initializes
server.on('upgrade', (req, socket, head) => {
  const { pathname } = parse(req.url, true);

  // Only proxy paths we want to handle
  if (!isProxiedWebSocketPath(pathname)) {
    // Let Next.js handle other WebSocket connections (like HMR in dev mode)
    return;
  }

  console.log(`WebSocket upgrade: ${pathname} -> backend`);

  // Use http-proxy for proper WebSocket proxying
  wsProxy.ws(req, socket, head);
});

// Now prepare Next.js and start the server
app.prepare().then(() => {
  server
    .once('error', (err) => {
      console.error('Server error:', err);
      process.exit(1);
    })
    .listen(port, hostname, () => {
      console.log(`> Ready on https://${hostname}:${port}`);
      console.log(`> SSL Certificate: ${certFile}`);
      console.log(`> Backend WebSocket proxy: ${backendUrl}`);
    });
});
