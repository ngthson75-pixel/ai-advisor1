// config.js - API Configuration
// Place this in: frontend/src/config.js

const config = {
  // API Base URL - change based on environment
  API_BASE_URL: import.meta.env.PROD 
    ? 'https://ai-advisor1-backend.onrender.com/api'  // Production backend on Render
    : 'http://localhost:10000/api',  // Local development
  
  // Frontend URL
  FRONTEND_URL: import.meta.env.PROD
    ? 'https://ai-advisor.vn'  // Your new domain!
    : 'http://localhost:5173',
  
  // Telegram Bot (if using)
  TELEGRAM_BOT_TOKEN: '8447350659:AAGyvRMGvXRs3VloDo0wk_zbXYhlPAsxaXs',
  TELEGRAM_CHAT_ID: '6421252178',
  
  // App Info
  APP_NAME: 'AI Advisor',
  APP_VERSION: '1.0.0',
  
  // Features
  FEATURES: {
    SIGNALS_AUTO_REFRESH: true,
    SIGNALS_REFRESH_INTERVAL: 5 * 60 * 1000, // 5 minutes
    ENABLE_NOTIFICATIONS: true,
  }
};

export default config;
