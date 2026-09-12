import type { NextConfig } from "next";

// API hedefi — dev'de localhost, production'da https://api.clarere.com
// (Vercel'de Environment Variable olarak verilir: API_PROXY_TARGET)
const apiTarget = (process.env.API_PROXY_TARGET ?? "http://127.0.0.1:4000").replace(/\/$/, "");

// connect-src: kendi origin + backend (Paddle.js CDN'i script-src'te)
const connectSrc = [
  "'self'",
  apiTarget,
  "https://api.clarere.com",
  "https://cdn.paddle.com",
  "https://*.paddle.com",
  "http://localhost:*",
  "http://127.0.0.1:*",
  "ws://localhost:*",
  "ws://127.0.0.1:*",
].join(" ");

const securityHeaders = [
  { key: "X-Frame-Options", value: "DENY" },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
  {
    key: "Content-Security-Policy",
    value: [
      "default-src 'self'",
      "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.paddle.com https://*.paddle.com",
      "style-src 'self' 'unsafe-inline'",
      "img-src 'self' data: blob:",
      "font-src 'self'",
      `connect-src ${connectSrc}`,
      "frame-src https://*.paddle.com",
    ].join("; "),
  },
];

const nextConfig: NextConfig = {
  output: "standalone", // Docker production build (küçük imaj)
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: securityHeaders,
      },
    ];
  },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        // Server-side proxy → CORS gerekmez, X-Username/Authorization header'ları korunur
        destination: `${apiTarget}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
