import { getUserId } from '../utils/userSession';
import React, { useState, useEffect } from 'react';
import { MessageCircle, TrendingUp, Trash2, PlusCircle } from 'lucide-react';

const AIPortfolioManager = () => {
  // ✅ FIX: Mỗi user có ID riêng thay vì hardcode user_id=1
  const [userId] = useState(() => getUserId());
  
  const [portfolio, setPortfolio] = useState([]);
  const [chatHistory, setChatHistory] = useState([]);
  const [userMessage, setUserMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  const [newStock, setNewStock] = useState({
    ticker: '',
    quantity: '',
    price: ''
  });

  const API_BASE = import.meta.env.VITE_API_URL || 'https://ai-advisor1-backend.onrender.com/api';

  // Debug: Show user ID (remove in production)
  useEffect(() => {
    debugUserSession();
  }, []);

  // Fetch portfolio on mount
  useEffect(() => {
    fetchPortfolio();
    fetchChatHistory();
  }, [userId]); // Re-fetch khi userId thay đổi

  const fetchPortfolio = async () => {
    try {
      // ✅ FIX: Sử dụng userId riêng thay vì user_id=1
      const response = await fetch(`${API_BASE}/portfolio?user_id=${userId}`);
      const data = await response.json();
      
      if (data.success) {
        setPortfolio(data.portfolio || []);
      }
    } catch (error) {
      console.error('Error fetching portfolio:', error);
    }
  };

  const fetchChatHistory = async () => {
    try {
      // ✅ FIX: Lấy chat history riêng của user
      const response = await fetch(`${API_BASE}/chat/history?user_id=${userId}`);
      const data = await response.json();
      
      if (data.success) {
        setChatHistory(data.history || []);
      }
    } catch (error) {
      console.error('Error fetching chat:', error);
    }
  };

  const handleAddStock = async (e) => {
    e.preventDefault();
    
    if (!newStock.ticker || !newStock.quantity || !newStock.price) {
      alert('Vui lòng điền đầy đủ thông tin');
      return;
    }

    try {
      // ✅ FIX: Thêm stock vào portfolio riêng của user
      const response = await fetch(`${API_BASE}/portfolio`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId, // ✅ User ID riêng
          ticker: newStock.ticker.toUpperCase(),
          quantity: parseInt(newStock.quantity),
          price: parseFloat(newStock.price)
        })
      });

      const data = await response.json();
      
      if (data.success) {
        fetchPortfolio();
        setNewStock({ ticker: '', quantity: '', price: '' });
      } else {
        alert('Error: ' + data.error);
      }
    } catch (error) {
      console.error('Error adding stock:', error);
      alert('Lỗi khi thêm cổ phiếu');
    }
  };

  const handleDeleteStock = async (ticker) => {
    if (!confirm(`Xóa ${ticker} khỏi danh mục?`)) return;

    try {
      // ✅ FIX: Xóa stock từ portfolio riêng của user
      const response = await fetch(
        `${API_BASE}/portfolio/${ticker}?user_id=${userId}`,
        { method: 'DELETE' }
      );

      const data = await response.json();
      
      if (data.success) {
        fetchPortfolio();
      }
    } catch (error) {
      console.error('Error deleting stock:', error);
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    
    if (!userMessage.trim()) return;

    setIsLoading(true);

    try {
      // ✅ FIX: Gửi message với user context riêng
      const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,  // ✅ User ID riêng
          message: userMessage,
          portfolio: portfolio.map(s => s.ticker) // Context: portfolio của user
        })
      });

      const data = await response.json();
      
      if (data.success) {
        setChatHistory([...chatHistory, {
          message: userMessage,
          response: data.response,
          timestamp: new Date().toISOString()
        }]);
        setUserMessage('');
      } else {
        alert('Error: ' + data.error);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      alert('Lỗi khi gửi tin nhắn');
    } finally {
      setIsLoading(false);
    }
  };

  // Calculate total value
  const totalValue = portfolio.reduce((sum, stock) => 
    sum + (stock.quantity * stock.avg_price), 0
  );

  return (
    <div className="portfolio-manager">
      <div className="portfolio-header">
        <h2>
          <TrendingUp size={24} />
          Quản trị đầu tư bằng AI
        </h2>
        <p style={{fontSize: '14px', color: '#94a3b8', marginTop: '8px'}}>
          Hãy chia sẻ danh mục của bạn và hỏi đáp mua bán để AI hỗ trợ quản lý danh mục và kiểm soát FOMO hay HOẢNG SỢ
        </p>
        {/* Debug info - Remove in production */}
        <div className="user-info" style={{fontSize: '0.8em', color: '#666'}}>
          👤 User ID: {userId.substring(0, 20)}...
        </div>
      </div>

      <div className="portfolio-container">
        {/* Portfolio Section */}
        <div className="portfolio-section">
          <h3>Danh mục của bạn</h3>
          
          <form onSubmit={handleAddStock} className="add-stock-form">
            <input
              type="text"
              placeholder="Mã chứng khoán (VD: VCB)"
              value={newStock.ticker}
              onChange={(e) => setNewStock({...newStock, ticker: e.target.value})}
            />
            <input
              type="number"
              placeholder="Số lượng (VD: 100)"
              value={newStock.quantity}
              onChange={(e) => setNewStock({...newStock, quantity: e.target.value})}
            />
            <input
              type="number"
              placeholder="Giá mua (VD: 85000)"
              value={newStock.price}
              onChange={(e) => setNewStock({...newStock, price: e.target.value})}
            />
            <button type="submit">
              <PlusCircle size={18} />
              Thêm
            </button>
          </form>

          {portfolio.length === 0 ? (
            <div className="empty-state">
              <p>Danh mục trống. Thêm cổ phiếu đầu tiên!</p>
            </div>
          ) : (
            <>
              <div className="portfolio-list">
                {portfolio.map((stock) => (
                  <div key={stock.ticker} className="stock-item">
                    <div className="stock-info">
                      <strong>{stock.ticker}</strong>
                      <span>{stock.quantity} CP × {stock.avg_price.toLocaleString()} = {(stock.quantity * stock.avg_price).toLocaleString()} VND</span>
                    </div>
                    <button 
                      onClick={() => handleDeleteStock(stock.ticker)}
                      className="delete-btn"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                ))}
              </div>
              
              <div className="portfolio-total">
                <strong>Tổng giá trị:</strong>
                <span>{totalValue.toLocaleString()} VND</span>
              </div>
            </>
          )}
        </div>

        {/* AI Chat Section */}
        <div className="chat-section">
          <h3>
            <MessageCircle size={20} />
            Tư vấn AI
          </h3>

          <div className="chat-history">
            {chatHistory.length === 0 ? (
              <div className="empty-state">
                <p>Hỏi AI về danh mục của bạn!</p>
              </div>
            ) : (
              chatHistory.map((chat, idx) => (
                <div key={idx} className="chat-message">
                  <div className="user-message">
                    <strong>Bạn:</strong> {chat.message}
                  </div>
                  <div className="ai-message">
                    <strong>AI:</strong> {chat.response}
                  </div>
                </div>
              ))
            )}
          </div>

          <form onSubmit={handleSendMessage} className="chat-input-form">
            <input
              type="text"
              placeholder="Hỏi AI về danh mục..."
              value={userMessage}
              onChange={(e) => setUserMessage(e.target.value)}
              disabled={isLoading}
            />
            <button type="submit" disabled={isLoading}>
              {isLoading ? 'Đang xử lý...' : 'Gửi'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default AIPortfolioManager;
