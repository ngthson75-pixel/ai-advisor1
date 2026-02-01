import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  
  server: {
    port: 5173
  },
  
  test: {
    // Enable globals (describe, it, expect)
    globals: true,
    
    // Use jsdom for DOM testing
    environment: 'jsdom',
    
    // Setup file
    setupFiles: './src/setupTests.js',
    
    // Coverage configuration
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/setupTests.js',
        '**/*.spec.js',
        '**/*.test.js',
      ]
    },
    
    // Test match patterns
    include: [
      'src/**/*.{test,spec}.{js,jsx}',
      'tests/**/*.{test,spec}.{js,jsx}'
    ],
    
    // Timeout
    testTimeout: 10000,
  }
})
