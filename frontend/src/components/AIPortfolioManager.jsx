import React, { useState, useEffect } from 'react';
import { MessageCircle, TrendingUp, Trash2, PlusCircle } from 'lucide-react';

// Simple version to test if component loads
const AIPortfolioManager = () => {
  const [error, setError] = useState(null);
  const [userId] = useState(() => {
    // Inline getUserId to avoid import issues
    let id = localStorage.getItem('ai_advisor_user_id');
    if (!id) {
      id = `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      localStorage.setItem('ai_advisor_user_id', id);
    }
    return id;
  });
  
  const [portfolio, setPortfolio] = useState([]);
  const [chatHistory, setChatHistory] = useState([]);
  const [userMessage, setUserMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  const [newStock, setNewStock] = useState({
    ticker: '',
    quantity: '',
    price: ''
  });

  const API_BASE = 'https://ai-advisor1-backend.onrender.com/api';

  // Error boundary
  useEffect(() => {
    console.log('✅ AIPortfolioManager mounted successfully');
    console.log('User ID:', userId);
  }, []);

  useEffect(() => {
    fetchPortfolio();
    fetchChatHistory();
  }, [userId]);

  const fetchPortfolio = async () => {
    try {
      console.log('Fetching portfolio for user:', userId);
      const response = await fetch(`${API_BASE}/portfolio?user_id=${userId}`);
      const data = await response.json();
      
      if (data.success) {
        setPortfolio(data.portfolio || []);
        console.log('Portfolio loaded:', data.portfolio);
      }
    } catch (error) {
      console.error('Error fetching portfolio:', error);
      setError('Lỗi tải danh mục: ' + error.message);
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

  const handleAddStock = async (e) => {
    e.preventDefault();
    
    if (!newStock.ticker || !newStock.quantity || !newStock.price) {
      alert('Vui lòng điền đầy đủ thông tin');
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/portfolio`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
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
          portfolio: portfolio.map(s => s.ticker)
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

  const totalValue = portfolio.reduce((sum, stock) => 
    sum + (stock.quantity * stock.avg_price), 0
  );

  // Show error if any
  if (error) {
    return (
      <div style={{padding: '40px', background: '#fee', color: '#c00', borderRadius: '8px'}}>
        <h2>⚠️ Lỗi</h2>
        <p>{error}</p>
        <button onClick={() => window.location.reload()}>Tải lại trang</button>
      </div>
    );
  }

  return (
    <div className="portfolio-manager" style={{
      background: '#f8f9fa',
      minHeight: '100vh',
      padding: '20px',
      color: '#000'
    }}>
      <div className="portfolio-header">
        <h2 style={{color: '#000', marginBottom: '10px'}}>
          <TrendingUp size={24} style={{display: 'inline', marginRight: '10px'}} />
          Quản trị Danh mục Đầu tư
        </h2>
        <p style={{fontSize: '0.9em', color: '#666'}}>User ID: {userId.substring(0, 25)}...</p>
      </div>

      <div className="portfolio-container" style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: '20px',
        marginTop: '30px'
      }}>
        {/* Portfolio Section */}
        <div className="portfolio-section" style={{
          background: 'white',
          padding: '20px',
          borderRadius: '8px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
        }}>
          <h3 style={{color: '#000', marginBottom: '20px'}}>Danh mục của bạn</h3>
          
          <form onSubmit={handleAddStock} style={{marginBottom: '20px'}}>
            <div style={{display: 'flex', gap: '10px', marginBottom: '10px'}}>
              <input
                type="text"
                placeholder="Mã CK (VD: VCB)"
                value={newStock.ticker}
                onChange={(e) => setNewStock({...newStock, ticker: e.target.value})}
                style={{flex: 1, padding: '10px', border: '1px solid #ddd', borderRadius: '4px'}}
              />
              <input
                type="number"
                placeholder="Số lượng"
                value={newStock.quantity}
                onChange={(e) => setNewStock({...newStock, quantity: e.target.value})}
                style={{flex: 1, padding: '10px', border: '1px solid #ddd', borderRadius: '4px'}}
              />
            </div>
            <div style={{display: 'flex', gap: '10px'}}>
              <input
                type="number"
                placeholder="Giá trung bình"
                value={newStock.price}
                onChange={(e) => setNewStock({...newStock, price: e.target.value})}
                style={{flex: 1, padding: '10px', border: '1px solid #ddd', borderRadius: '4px'}}
              />
              <button type="submit" style={{
                padding: '10px 20px',
                background: '#007bff',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}>
                <PlusCircle size={18} style={{display: 'inline', marginRight: '5px'}} />
                Thêm
              </button>
            </div>
          </form>

          {portfolio.length === 0 ? (
            <div style={{padding: '20px', textAlign: 'center', color: '#666'}}>
              <p>Danh mục trống. Thêm cổ phiếu đầu tiên!</p>
            </div>
          ) : (
            <>
              <div style={{marginBottom: '20px'}}>
                {portfolio.map((stock) => (
                  <div key={stock.ticker} style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '15px',
                    marginBottom: '10px',
                    background: '#f8f9fa',
                    borderRadius: '4px'
                  }}>
                    <div>
                      <strong style={{color: '#000', fontSize: '1.1em'}}>{stock.ticker}</strong>
                      <div style={{fontSize: '0.9em', color: '#666'}}>
                        {stock.quantity} CP × {stock.avg_price.toLocaleString()} = {(stock.quantity * stock.avg_price).toLocaleString()} VND
                      </div>
                    </div>
                    <button 
                      onClick={() => handleDeleteStock(stock.ticker)}
                      style={{
                        background: '#dc3545',
                        color: 'white',
                        border: 'none',
                        padding: '8px 12px',
                        borderRadius: '4px',
                        cursor: 'pointer'
                      }}
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                ))}
              </div>
              
              <div style={{
                padding: '15px',
                background: '#e9ecef',
                borderRadius: '4px',
                display: 'flex',
                justifyContent: 'space-between'
              }}>
                <strong style={{color: '#000'}}>Tổng giá trị:</strong>
                <strong style={{color: '#28a745'}}>{totalValue.toLocaleString()} VND</strong>
              </div>
            </>
          )}
        </div>

        {/* AI Chat Section */}
        <div className="chat-section" style={{
          background: 'white',
          padding: '20px',
          borderRadius: '8px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
          display: 'flex',
          flexDirection: 'column',
          height: '600px'
        }}>
          <h3 style={{color: '#000', marginBottom: '20px'}}>
            <MessageCircle size={20} style={{display: 'inline', marginRight: '10px'}} />
            Tư vấn AI
          </h3>

          <div style={{
            flex: 1,
            overflowY: 'auto',
            marginBottom: '20px',
            padding: '10px',
            background: '#f8f9fa',
            borderRadius: '4px'
          }}>
            {chatHistory.length === 0 ? (
              <div style={{padding: '20px', textAlign: 'center', color: '#666'}}>
                <p>Hỏi AI về danh mục của bạn!</p>
              </div>
            ) : (
              chatHistory.map((chat, idx) => (
                <div key={idx} style={{marginBottom: '15px'}}>
                  <div style={{
                    padding: '10px',
                    background: '#e3f2fd',
                    borderRadius: '4px',
                    marginBottom: '5px'
                  }}>
                    <strong style={{color: '#1976d2'}}>Bạn:</strong> {chat.message}
                  </div>
                  <div style={{
                    padding: '10px',
                    background: '#fff',
                    border: '1px solid #ddd',
                    borderRadius: '4px'
                  }}>
                    <strong style={{color: '#388e3c'}}>AI:</strong> {chat.response}
                  </div>
                </div>
              ))
            )}
          </div>

          <form onSubmit={handleSendMessage} style={{display: 'flex', gap: '10px'}}>
            <input
              type="text"
              placeholder="Hỏi AI về danh mục..."
              value={userMessage}
              onChange={(e) => setUserMessage(e.target.value)}
              disabled={isLoading}
              style={{
                flex: 1,
                padding: '10px',
                border: '1px solid #ddd',
                borderRadius: '4px'
              }}
            />
            <button type="submit" disabled={isLoading} style={{
              padding: '10px 20px',
              background: isLoading ? '#6c757d' : '#28a745',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: isLoading ? 'not-allowed' : 'pointer'
            }}>
              {isLoading ? 'Đang xử lý...' : 'Gửi'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default AIPortfolioManager;
