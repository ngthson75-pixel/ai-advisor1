import { getUserId } from '../utils/userSession';
import React, { useState, useEffect } from 'react';
import { MessageCircle, TrendingUp, Trash2, PlusCircle } from 'lucide-react';

const AIPortfolioManager = () => {
  // ✅ User isolation
  const [userId] = useState(() => getUserId());
  
  const [portfolio, setPortfolio] = useState([]);
  const [chatHistory, setChatHistory] = useState([]);
  const [userMessage, setUserMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  // ✅ NEW: Thêm cash field
  const [cash, setCash] = useState('');
  
  const [newStock, setNewStock] = useState({
    ticker: '',
    quantity: '',
    price: ''
    // ❌ REMOVED: currentPrice - sẽ auto-fetch
  });

  const API_BASE = import.meta.env.VITE_API_URL || 'https://ai-advisor1-backend.onrender.com/api';

  // Fetch portfolio on mount
  useEffect(() => {
    fetchPortfolio();
    fetchChatHistory();
  }, [userId]);

  const fetchPortfolio = async () => {
    try {
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
      const response = await fetch(`${API_BASE}/chat/history?user_id=${userId}`);
      const data = await response.json();
      
      if (data.success) {
        setChatHistory(data.history || []);
      }
    } catch (error) {
      console.error('Error fetching chat:', error);
    }
  };

  // ✅ NEW: Auto-fetch current price
  const fetchCurrentPrice = async (ticker) => {
    try {
      const response = await fetch(`${API_BASE}/stock/current-price?ticker=${ticker}`);
      const data = await response.json();
      
      if (data.success && data.price) {
        console.log(`✅ Fetched ${ticker} price: ${data.price}`);
        return data.price;
      }
      return null;
    } catch (error) {
      console.error('Error fetching price:', error);
      return null;
    }
  };

  const handleAddStock = async (e) => {
    e.preventDefault();
    
    if (!newStock.ticker || !newStock.quantity || !newStock.price) {
      alert('Vui lòng điền đầy đủ thông tin');
      return;
    }

    setIsLoading(true);

    try {
      // ✅ Auto-fetch current price
      const currentPrice = await fetchCurrentPrice(newStock.ticker.toUpperCase());
      
      const response = await fetch(`${API_BASE}/portfolio`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          ticker: newStock.ticker.toUpperCase(),
          quantity: parseInt(newStock.quantity),
          price: parseFloat(newStock.price),
          current_price: currentPrice || parseFloat(newStock.price) // Fallback to entry price
        })
      });

      const data = await response.json();
      
      if (data.success) {
        fetchPortfolio();
        setNewStock({ ticker: '', quantity: '', price: '' });
        
        // Success message
        const priceMsg = currentPrice 
          ? `Giá hiện tại: ${currentPrice.toLocaleString()} VND (tự động cập nhật)`
          : 'Sử dụng giá mua làm giá hiện tại';
        alert(`✅ Đã thêm ${newStock.ticker.toUpperCase()}!\n${priceMsg}`);
      } else {
        alert('Error: ' + data.error);
      }
    } catch (error) {
      console.error('Error adding stock:', error);
      alert('Lỗi khi thêm cổ phiếu');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteStock = async (ticker) => {
    if (!confirm(`Xóa ${ticker} khỏi danh mục?`)) return;

    try {
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
      const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          message: userMessage,
          portfolio: portfolio.map(s => ({
            ticker: s.ticker,
            quantity: s.quantity,
            avg_price: s.avg_price,
            current_price: s.current_price || s.avg_price
          }))
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

  // Calculate total value (using current_price if available)
  const totalInvested = portfolio.reduce((sum, stock) => 
    sum + (stock.quantity * stock.avg_price), 0
  );
  
  const totalCurrentValue = portfolio.reduce((sum, stock) => 
    sum + (stock.quantity * (stock.current_price || stock.avg_price)), 0
  );
  
  const totalPnL = totalCurrentValue - totalInvested;
  const totalPnLPercent = totalInvested > 0 ? (totalPnL / totalInvested * 100) : 0;

  return (
    <div className="portfolio-manager">
      <div className="portfolio-header">
        <h2>
          <TrendingUp size={24} />
          Quản trị đầu tư bằng AI
        </h2>
        {/* ✅ UPDATED subtitle */}
        <p style={{ fontSize: '14px', color: '#94a3b8', marginTop: '8px' }}>
          Hãy chia sẻ danh mục của bạn và hỏi đáp mua bán để AI hỗ trợ quản lý danh mục và kiểm soát FOMO hay HOẢNG SỢ
        </p>
      </div>

      <div className="portfolio-container">
        {/* Portfolio Section */}
        <div className="portfolio-section">
          <h3>Danh mục của bạn</h3>
          
          {/* ✅ FORM DỌC như cũ */}
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
            
            {/* ✅ NEW: Tiền mặt riêng biệt phía dưới */}
            <input
              type="number"
              placeholder="Tiền mặt khả dụng (VD: 50000000)"
              value={cash}
              onChange={(e) => setCash(e.target.value)}
              style={{ marginTop: '12px', borderTop: '1px solid #334155', paddingTop: '12px' }}
            />
            
            {/* ✅ Button phía dưới */}
            <button type="submit" disabled={isLoading}>
              <PlusCircle size={18} />
              {isLoading ? 'Đang xử lý...' : 'Thêm vị thế'}
            </button>
          </form>

          {portfolio.length === 0 ? (
            <div className="empty-state">
              <p>Danh mục trống. Thêm cổ phiếu đầu tiên!</p>
            </div>
          ) : (
            <>
              {/* ✅ IMPROVED: P/L cho từng mã */}
              <div className="portfolio-list">
                {portfolio.map((stock) => {
                  const currentPrice = stock.current_price || stock.avg_price;
                  const invested = stock.quantity * stock.avg_price;
                  const currentValue = stock.quantity * currentPrice;
                  const pnl = currentValue - invested;
                  const pnlPercent = (pnl / invested) * 100;
                  
                  return (
                    <div key={stock.ticker} className="stock-item">
                      <div className="stock-info">
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <strong style={{ fontSize: '16px' }}>{stock.ticker}</strong>
                          <span style={{ 
                            color: pnl >= 0 ? '#10b981' : '#ef4444',
                            fontWeight: 'bold',
                            fontSize: '15px'
                          }}>
                            {pnl >= 0 ? '+' : ''}{pnl.toLocaleString()} VND ({pnl >= 0 ? '+' : ''}{pnlPercent.toFixed(2)}%)
                          </span>
                        </div>
                        
                        <div style={{ fontSize: '13px', color: '#94a3b8', marginTop: '4px' }}>
                          {stock.quantity} CP × {stock.avg_price.toLocaleString()} VND = {invested.toLocaleString()} VND
                        </div>
                        
                        <div style={{ fontSize: '13px', color: '#cbd5e1', marginTop: '2px' }}>
                          Giá hiện tại: {currentPrice.toLocaleString()} VND | Giá trị: {currentValue.toLocaleString()} VND
                        </div>
                      </div>
                      <button 
                        onClick={() => handleDeleteStock(stock.ticker)}
                        className="delete-btn"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  );
                })}
              </div>
              
              {/* ✅ IMPROVED: Tổng danh mục với P/L */}
              <div className="portfolio-total">
                <div style={{ marginBottom: '8px' }}>
                  <strong>Tổng đầu tư:</strong>
                  <span>{totalInvested.toLocaleString()} VND</span>
                </div>
                <div style={{ marginBottom: '8px' }}>
                  <strong>Giá trị hiện tại:</strong>
                  <span>{totalCurrentValue.toLocaleString()} VND</span>
                </div>
                {cash && (
                  <div style={{ marginBottom: '8px' }}>
                    <strong>Tiền mặt:</strong>
                    <span>{parseFloat(cash).toLocaleString()} VND</span>
                  </div>
                )}
                <div style={{ 
                  paddingTop: '8px', 
                  borderTop: '1px solid #475569',
                  fontWeight: 'bold',
                  fontSize: '16px'
                }}>
                  <strong>Lãi/Lỗ:</strong>
                  <span style={{ color: totalPnL >= 0 ? '#10b981' : '#ef4444' }}>
                    {totalPnL >= 0 ? '+' : ''}{totalPnL.toLocaleString()} VND ({totalPnL >= 0 ? '+' : ''}{totalPnLPercent.toFixed(2)}%)
                  </span>
                </div>
                {cash && (
                  <div style={{ marginTop: '8px', fontSize: '14px', color: '#94a3b8' }}>
                    Tổng tài sản: {(totalCurrentValue + parseFloat(cash)).toLocaleString()} VND
                  </div>
                )}
              </div>
            </>
          )}
        </div>

        {/* AI Chat Section */}
        <div className="chat-section">
          <h3>
            <MessageCircle size={20} />
            {/* ✅ REMOVED "(Gemini)" */}
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
