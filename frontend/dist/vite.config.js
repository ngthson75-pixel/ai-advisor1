// vite.config.js
export default {
  build: {
    rollupOptions: {
      output: {
        // Add hash to filenames
        entryFileNames: 'assets/[name].[hash].js',
        chunkFileNames: 'assets/[name].[hash].js',
        assetFileNames: 'assets/[name].[hash].[ext]'
      }
    }
  }
}
```

**Result:**
```
Before: main.js (always same name - cached!)
After:  main.a3f2b1c9.js (new hash each build - never cached!)