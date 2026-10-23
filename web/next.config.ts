import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Mantiene el build limitado a esta aplicación incluso en un ZIP sin Git.
  turbopack: { root: process.cwd() },
  // Los datos de cada periodo se leen del disco en build (data/periodos/*.json).
  outputFileTracingIncludes: { "/**": ["./data/periodos/**", "./data/sprint2.json"] },
};

export default nextConfig;
