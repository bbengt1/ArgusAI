import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: 'http',
        hostname: 'localhost',
        port: '8000',
        pathname: '/api/v1/thumbnails/**',
      },
    ],
    // Allow localhost for development
    dangerouslyAllowSVG: true,
    unoptimized: process.env.NODE_ENV === 'development',
  },
  // Proxy API requests to backend to avoid CORS issues
  async rewrites() {
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    return [
      {
        source: '/api/v1/:path*',
        destination: `${backendUrl}/api/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;
