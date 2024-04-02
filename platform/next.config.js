/** @type {import('next').NextConfig} */

const { version } = require('./package.json');

const dns = require("dns");
dns.setDefaultResultOrder("ipv4first")

module.exports = {
  experimental: {
    appDir: true,
    // other experimental configurations if needed
  },
  publicRuntimeConfig: {
    "version": version,
  },
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        // This rewrite will handle the specific /api/auth path
        // It will resolve to the Next.js API route
        source: '/api/auth/:path*',
        destination: '/api/auth/:path*' // Assuming your Next.js API route is structured like this
      },
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL}/api/:path*`
      },
  
    ]
  },
}

// Verify if NEXT_PUBLIC_API_URL is set
if (!process.env.NEXT_PUBLIC_API_URL) {
  throw new Error(
    "Please define the NEXT_PUBLIC_API_URL environment variable inside .env.local"
  );
}


// Injected content via Sentry wizard below

const { withSentryConfig } = require("@sentry/nextjs");

module.exports = withSentryConfig(
  module.exports,
  {
    // For all available options, see:
    // https://github.com/getsentry/sentry-webpack-plugin#options

    // Suppresses source map uploading logs during build
    silent: true,
    org: "phospho",
    project: "platform",
  },
  {
    // For all available options, see:
    // https://docs.sentry.io/platforms/javascript/guides/nextjs/manual-setup/

    // Upload a larger set of source maps for prettier stack traces (increases build time)
    widenClientFileUpload: true,

    // Transpiles SDK to be compatible with IE11 (increases bundle size)
    transpileClientSDK: true,

    // Routes browser requests to Sentry through a Next.js rewrite to circumvent ad-blockers (increases server load)
    tunnelRoute: "/monitoring",

    // Hides source maps from generated client bundles
    hideSourceMaps: true,

    // Automatically tree-shake Sentry logger statements to reduce bundle size
    disableLogger: true,

    // Enables automatic instrumentation of Vercel Cron Monitors.
    // See the following for more information:
    // https://docs.sentry.io/product/crons/
    // https://vercel.com/docs/cron-jobs
    automaticVercelMonitors: true,
  }
);