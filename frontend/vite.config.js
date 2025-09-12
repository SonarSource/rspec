import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  base: '/rspec',
  root: '.',
  server: {
    port: 3000,
    open: '/rspec'
  },
  preview: {
    port: 4173,
    open: '/rspec'
  },
  build: {
    outDir: 'build',
    assetsDir: 'static',
    sourcemap: true
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  define: {
    'process.env': {}
  },
  envPrefix: 'REACT_APP_',
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/setupTests.ts',
    include: ['src/**/*.test.{js,ts,jsx,tsx}'],
    exclude: ['**/incomplete-rules-repo/**'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'lcov', 'html'],
      exclude: [
        'node_modules/**',
        'build/**',
        'public/**',
        '**/*.test.{js,ts,jsx,tsx}',
        '**/*.config.{js,ts}',
        '**/coverage/**'
      ]
    }
  },
})
