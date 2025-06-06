/** @type {import(next).NextConfig} */
const nextConfig = {
    images: {
        remotePatterns: [
            {
                protocol: 'http',
                hostname: 'localhost',
                port: '3000',
                pathname: '/**',
            },
            {
                protocol: 'http',
                hostname: 'backend_c',
                port: '8000',
                pathname: '/**',
            },
        ],
    },
}
export default nextConfig