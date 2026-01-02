/** @type {import('next').NextConfig} */
const nextConfig = {
  webpack: (config, { isServer }) => {
    // Fix for react-runner webpack URL resolution issues
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        path: false,
        url: false,
      };
      
      // Handle react-runner's module resolution
      config.resolve.alias = {
        ...config.resolve.alias,
      };
    }
    
    return config;
  },
}

module.exports = nextConfig

