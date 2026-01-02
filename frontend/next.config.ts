import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enable standalone output for Docker deployment (Story P10-2.2)
  // Creates a minimal production bundle that includes only necessary files
  output: 'standalone',
  images: {
    // Disable image optimization for self-hosted deployments
    // This allows images from any hostname (localhost, IP, custom domain)
    unoptimized: true,
    dangerouslyAllowSVG: true,
  },
  // Proxy API requests to backend to avoid CORS issues
  // NOTE: When using custom server.js (SSL mode), all proxying including
  // WebSocket upgrades is handled in server.js, NOT here.
  // This rewrite config is only used for `npm run dev` (non-SSL mode).
  async rewrites() {
    const backendUrl = process.env.BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    // In production with custom server.js, these rewrites are bypassed
    // because server.js handles requests before Next.js sees them
    return [
      {
        source: '/api/v1/:path*',
        destination: `${backendUrl}/api/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;
