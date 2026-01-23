/**
 * USER SESSION MANAGEMENT
 * 
 * Tạo unique user ID cho mỗi browser
 * Giải quyết vấn đề: Tất cả users đang share data vì dùng user_id=1
 * 
 * Owner: Nguyễn Thanh Sơn
 * Email: ngthson75@gmail.com
 */

const USER_ID_KEY = 'ai_advisor_user_id';
const USER_EMAIL_KEY = 'ai_advisor_user_email';

/**
 * Get or create unique user ID
 * 
 * @returns {string} Unique user ID (e.g., "user_1705987234_abc123")
 */
export const getUserId = () => {
  let userId = localStorage.getItem(USER_ID_KEY);
  
  if (!userId) {
    // Generate unique ID: user_timestamp_random
    const timestamp = Date.now();
    const random = Math.random().toString(36).substr(2, 9);
    userId = `user_${timestamp}_${random}`;
    
    localStorage.setItem(USER_ID_KEY, userId);
    
    console.log('✅ New user session created:', userId);
  }
  
  return userId;
};

/**
 * Clear user session (logout)
 */
export const clearUserSession = () => {
  localStorage.removeItem(USER_ID_KEY);
  localStorage.removeItem(USER_EMAIL_KEY);
  console.log('🗑️ User session cleared');
};

/**
 * Check if user has active session
 * 
 * @returns {boolean}
 */
export const hasUserSession = () => {
  return !!localStorage.getItem(USER_ID_KEY);
};

/**
 * Get user email (if set)
 * 
 * @returns {string|null}
 */
export const getUserEmail = () => {
  return localStorage.getItem(USER_EMAIL_KEY);
};

/**
 * Set user email (for future email-based login)
 * 
 * @param {string} email
 */
export const setUserEmail = (email) => {
  localStorage.setItem(USER_EMAIL_KEY, email);
};

/**
 * Debug: Show user info
 */
export const debugUserSession = () => {
  console.log('👤 USER SESSION DEBUG:');
  console.log('   User ID:', getUserId());
  console.log('   Email:', getUserEmail() || 'Not set');
  console.log('   Has session:', hasUserSession());
};

// Auto-initialize on import
if (typeof window !== 'undefined') {
  // Ensure user ID exists
  getUserId();
}

export default {
  getUserId,
  clearUserSession,
  hasUserSession,
  getUserEmail,
  setUserEmail,
  debugUserSession
};
