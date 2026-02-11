import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  define: {
    'import.meta.env.VITE_API_URL': JSON.stringify('https://ai-advisor1-backend.onrender.com/api'),
    'import.meta.env.VITE_ENVIRONMENT': JSON.stringify('production'),
    'import.meta.env.VITE_APP_NAME': JSON.stringify('AI Advisor')
  }
})
