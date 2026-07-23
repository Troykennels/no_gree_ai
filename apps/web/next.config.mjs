/** @type {import('next').NextConfig} */
const nextConfig = {
  // "standalone" is only for a Docker/self-hosted build. On Vercel it must be
  // OFF or Vercel looks in the wrong place and serves a 404. Opt in via env.
  output: process.env.NEXT_OUTPUT_STANDALONE ? "standalone" : undefined,
  reactStrictMode: true,
  eslint: { ignoreDuringBuilds: true },
};

export default nextConfig;
