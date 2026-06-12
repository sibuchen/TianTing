import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'standalone',
  allowedDevOrigins: ['127.0.0.1', 'localhost'],
  rewrites: async () => [
    {
      source: '/api/:path*',
      destination: 'http://localhost:2811/api/v1/:path*',
    },
  ],
};

export default nextConfig;
