import type { NextConfig } from "next";

// FastAPI (backend/main.py) runs on its own port, but the browser only ever talks to this app's origin.
// Every /api/* request the frontend makes is transparently proxied to the backend server-side, so there's
// one localhost URL for the whole app and no CORS involved. Override the target with BACKEND_URL if the
// backend runs somewhere else.
const BACKEND_URL = process.env.BACKEND_URL ?? "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${BACKEND_URL}/api/:path*` }];
  },
};

export default nextConfig;
