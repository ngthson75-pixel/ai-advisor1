// api.js - API Service Layer
// Place this in: frontend/src/services/api.js

import config from '../config';

const API_BASE_URL = config.API_BASE_URL;

// Helper function for API calls
async function fetchAPI(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',
    },
  };
  
  try {
    const response = await fetch(url, { ...defaultOptions, ...options });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
}

// Signals API
export const signalsAPI = {
  // Get all signals
  getAll: async (filters = {}) => {
    const params = new URLSearchParams(filters);
    return fetchAPI(`/signals?${params}`);
  },
  
  // Get signals by strategy
  getByStrategy: async (strategy) => {
    return fetchAPI(`/signals?strategy=${strategy}`);
  },
  
  // Get signal detail
  getDetail: async (ticker) => {
    return fetchAPI(`/signals/${ticker}`);
  },
  
  // Get summary
  getSummary: async () => {
    return fetchAPI('/signals/summary');
  },
  
  // Upload signals (admin)
  upload: async (data) => {
    return fetchAPI('/signals/upload', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
};

// Health check
export const healthCheck = async () => {
  try {
    const response = await fetch(`${API_BASE_URL.replace('/api', '')}/health`);
    return await response.json();
  } catch (error) {
    return { status: 'error', error: error.message };
  }
};

export default {
  signals: signalsAPI,
  health: healthCheck,
};
