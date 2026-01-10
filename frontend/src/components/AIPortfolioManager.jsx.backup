import React, { useState, useEffect } from 'react';
import { TrendingUp, DollarSign, PieChart, MessageSquare, Send, Plus, Trash2, BarChart3 } from 'lucide-react';

const API_BASE = 'https://ai-advisor1-backend.onrender.com/api';
const USER_ID = 1;

export default function AIPortfolioManager() {
  const [portfolio, setPortfolio] = useState([]);
  const [chatHistory, setChatHistory] = useState([]);
  const [userMessage, setUserMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [addingStock, setAddingStock] = useState(false);

  // Form state
  const [newStock, setNewStock] = useState({
    ticker: '',
    quantity: '',
    price: ''
  });

  // Fetch portfolio
  const fetchPortfolio = async () => {
    try {
      const response = await fetch(`${API_BASE}/portfolio?user_id=${USER_ID}`);
      const data = await response.json();
      if (data.success) {
        setPortfolio(data.portfolio || []);
      }
    } catch (err) {
      console.error('Error fetching portfolio:', err);
    }
  };

  // Fetch chat history
  const fetchChatHistory = async () => {
    try {
      const response = await fetch(`${API_BASE}/chat/history?user_id=${USER_ID}`);
      const data = await response.json();
      if (data.success) {
        setChatHistory(data.history || []);
      }
    } catch (err) {
      console.error('Error fetching chat:', err);
    }
  };

  useEffect(() => {
    fetchPortfolio();
    fetchChatHistory();
  }, []);

  // Add stock
  const handleAddStock = async () => {
    if (!newStock.ticker || !newStock.quantity || !newStock.price) {
      alert('Vui lòng điền đầy đủ thông tin');
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/portfolio`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: USER_ID,
          ticker: newStock.ticker.toUpperCase(),
          quantity: parseInt(newStock.quantity),
          price: parseFloat(newStock.price)
        })
      });

      const data = await response.json();
      if (data.success) {
        setNewStock({ ticker: '', quantity: '', price: '' });
        setAddingStock(false);
        await fetchPortfolio();
      } else {
        alert('Lỗi: ' + (data.error || 'Không thể thêm cổ phiếu'));
      }
    } catch (err) {
      alert('Lỗi kết nối: ' + err.message);
    }
  };

  // Delete stock
  const handleDeleteStock = async (ticker) => {
    if (!confirm(`Xóa ${ticker} khỏi danh mục?`)) return;

    try {
      const response = await fetch(`${API_BASE}/portfolio/${ticker}?user_id=${USER_ID}`, {
        method: 'DELETE'
      });

      const data = await response.json();
      if (data.success) {
        await fetchPortfolio();
      }
    } catch (err) {
      alert('Lỗi: ' + err.message);
    }
  };

  // Send chat message
  const handleSendMessage = async () => {
    if (!userMessage.trim()) return;

    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: USER_ID,
          message: userMessage
        })
      });

      const data = await response.json();
      if (data.success) {
        setChatHistory([...chatHistory, {
          message: userMessage,
          response: data.response
        }]);
        setUserMessage('');
      }
    } catch (err) {
      alert('Lỗi: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  // Calculate total value
  const totalValue = portfolio.reduce((sum, stock) => 
    sum + (stock.quantity * stock.avg_price), 0
  );

  const totalStocks = portfolio.reduce((sum, stock) => sum + stock.quantity, 0);

  return (
    <div className="portfolio-manager">
      <div className="container">
        {/* Header */}
        <div className="header">
          <div>
            <h1 className="title">
              <BarChart3 size={32} />
              Danh Mục Đầu Tư
            </h1>
            <p className="subtitle">Quản lý danh mục của bạn</p>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon" style={{ background: '#22c55e20' }}>
              <DollarSign size={24} style={{ color: '#22c55e' }} />
            </div>
            <div>
              <div className="stat-label">Tổng giá trị</div>
              <div className="stat-value">{totalValue.toLocaleString()} VND</div>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon" style={{ background: '#3b82f620' }}>
              <TrendingUp size={24} style={{ color: '#3b82f6' }} />
            </div>
            <div>
              <div className="stat-label">Số mã</div>
              <div className="stat-value">{portfolio.length}</div>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon" style={{ background: '#f59e0b20' }}>
              <PieChart size={24} style={{ color: '#f59e0b' }} />
            </div>
            <div>
              <div className="stat-label">Tổng CP</div>
              <div className="stat-value">{totalStocks}</div>
            </div>
          </div>
        </div>

        {/* Main Grid */}
        <div className="main-grid">
          {/* Portfolio Section */}
          <div className="section">
            <div className="section-header">
              <h2 className="section-title">
                <Plus size={20} />
                Thêm Cổ Phiếu
              </h2>
            </div>

            <div className="add-stock-form">
              <input
                type="text"
                placeholder="Mã CP (VD: VCB)"
                value={newStock.ticker}
                onChange={(e) => setNewStock({...newStock, ticker: e.target.value})}
                className="input"
                style={{ flex: 1 }}
              />
              <input
                type="number"
                placeholder="Số lượng"
                value={newStock.quantity}
                onChange={(e) => setNewStock({...newStock, quantity: e.target.value})}
                className="input"
                style={{ flex: 1 }}
              />
              <input
                type="number"
                placeholder="Giá (VND)"
                value={newStock.price}
                onChange={(e) => setNewStock({...newStock, price: e.target.value})}
                className="input"
                style={{ flex: 1 }}
              />
              <button onClick={handleAddStock} className="btn-primary">
                Thêm vào danh mục
              </button>
            </div>

            {/* Portfolio List */}
            <div className="section-header" style={{ marginTop: '30px' }}>
              <h2 className="section-title">Danh mục hiện tại</h2>
            </div>

            {portfolio.length === 0 ? (
              <div className="empty-state">
                <PieChart size={48} style={{ color: '#64748b', marginBottom: '10px' }} />
                <p>Chưa có cổ phiếu nào</p>
              </div>
            ) : (
              <div className="stocks-list">
                {portfolio.map((stock, idx) => (
                  <div key={idx} className="stock-item">
                    <div className="stock-info">
                      <div className="stock-ticker">{stock.ticker}</div>
                      <div className="stock-details">
                        {stock.quantity} CP × {stock.avg_price.toLocaleString()} VND
                      </div>
                    </div>
                    <div className="stock-actions">
                      <div className="stock-value">
                        {(stock.quantity * stock.avg_price).toLocaleString()} VND
                      </div>
                      <button
                        onClick={() => handleDeleteStock(stock.ticker)}
                        className="btn-delete"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* AI Chat Section */}
          <div className="section">
            <div className="section-header">
              <h2 className="section-title">
                <MessageSquare size={20} />
                AI Advisor
              </h2>
            </div>

            <div className="chat-subtitle">
              Tư vấn thông minh về danh mục
            </div>

            {/* Chat History */}
            <div className="chat-history">
              {chatHistory.length === 0 ? (
                <div className="empty-state">
                  <MessageSquare size={48} style={{ color: '#64748b' }} />
                  <p style={{ marginTop: '10px' }}>
                    Hỏi AI Advisor về danh mục của bạn
                  </p>
                  <p style={{ fontSize: '13px', color: '#64748b', marginTop: '5px' }}>
                    VD: "Phân tích danh mục của tôi"
                  </p>
                </div>
              ) : (
                chatHistory.map((chat, idx) => (
                  <div key={idx} className="chat-messages">
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

            {/* Chat Input */}
            <div className="chat-input-container">
              <input
                type="text"
                placeholder="Hỏi AI về danh mục..."
                value={userMessage}
                onChange={(e) => setUserMessage(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                className="input"
                disabled={loading}
              />
              <button
                onClick={handleSendMessage}
                disabled={loading}
                className="btn-send"
              >
                <Send size={18} />
              </button>
            </div>
          </div>
        </div>
      </div>

      <style jsx>{`
        .portfolio-manager {
          min-height: 100vh;
          background: #0f172a;
          padding: 20px;
        }

        .container {
          max-width: 1400px;
          margin: 0 auto;
        }

        .header {
          margin-bottom: 30px;
        }

        .title {
          display: flex;
          align-items: center;
          gap: 12px;
          color: white;
          font-size: 28px;
          margin-bottom: 8px;
        }

        .subtitle {
          color: #94a3b8;
          font-size: 15px;
        }

        .stats-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 20px;
          margin-bottom: 30px;
        }

        .stat-card {
          background: #1e293b;
          border: 1px solid #334155;
          border-radius: 12px;
          padding: 20px;
          display: flex;
          align-items: center;
          gap: 15px;
        }

        .stat-icon {
          width: 48px;
          height: 48px;
          border-radius: 10px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .stat-label {
          color: #94a3b8;
          font-size: 13px;
          margin-bottom: 5px;
        }

        .stat-value {
          color: white;
          font-size: 22px;
          font-weight: bold;
        }

        .main-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 20px;
        }

        .section {
          background: #1e293b;
          border: 1px solid #334155;
          border-radius: 12px;
          padding: 25px;
        }

        .section-header {
          margin-bottom: 20px;
        }

        .section-title {
          display: flex;
          align-items: center;
          gap: 10px;
          color: white;
          font-size: 18px;
          font-weight: 600;
        }

        .add-stock-form {
          display: flex;
          gap: 10px;
          flex-wrap: wrap;
        }

        .input {
          padding: 12px 16px;
          background: #0f172a;
          border: 1px solid #334155;
          border-radius: 8px;
          color: white;
          font-size: 14px;
          transition: all 0.2s;
        }

        .input:focus {
          outline: none;
          border-color: #3b82f6;
        }

        .input::placeholder {
          color: #64748b;
        }

        .btn-primary {
          padding: 12px 24px;
          background: #3b82f6;
          color: white;
          border: none;
          border-radius: 8px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
        }

        .btn-primary:hover {
          background: #2563eb;
        }

        .stocks-list {
          display: flex;
          flex-direction: column;
          gap: 10px;
        }

        .stock-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 15px;
          background: #0f172a;
          border: 1px solid #334155;
          border-radius: 8px;
        }

        .stock-info {
          flex: 1;
        }

        .stock-ticker {
          color: #3b82f6;
          font-weight: bold;
          font-size: 16px;
          margin-bottom: 4px;
        }

        .stock-details {
          color: #94a3b8;
          font-size: 13px;
        }

        .stock-actions {
          display: flex;
          align-items: center;
          gap: 15px;
        }

        .stock-value {
          color: #22c55e;
          font-weight: 600;
          font-size: 15px;
        }

        .btn-delete {
          padding: 8px;
          background: #ef444420;
          border: 1px solid #ef4444;
          border-radius: 6px;
          color: #ef4444;
          cursor: pointer;
          transition: all 0.2s;
        }

        .btn-delete:hover {
          background: #ef4444;
          color: white;
        }

        .chat-subtitle {
          color: #94a3b8;
          font-size: 14px;
          margin-bottom: 20px;
        }

        .chat-history {
          height: 400px;
          overflow-y: auto;
          padding: 15px;
          background: #0f172a;
          border: 1px solid #334155;
          border-radius: 8px;
          margin-bottom: 15px;
        }

        .chat-messages {
          margin-bottom: 20px;
        }

        .user-message {
          padding: 12px;
          background: #3b82f620;
          border-left: 3px solid #3b82f6;
          border-radius: 6px;
          margin-bottom: 10px;
          color: white;
          font-size: 14px;
        }

        .ai-message {
          padding: 12px;
          background: #22c55e20;
          border-left: 3px solid #22c55e;
          border-radius: 6px;
          color: white;
          font-size: 14px;
        }

        .chat-input-container {
          display: flex;
          gap: 10px;
        }

        .btn-send {
          padding: 12px 16px;
          background: #3b82f6;
          border: none;
          border-radius: 8px;
          color: white;
          cursor: pointer;
          transition: all 0.2s;
        }

        .btn-send:hover {
          background: #2563eb;
        }

        .btn-send:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .empty-state {
          text-align: center;
          padding: 60px 20px;
          color: #64748b;
        }

        @media (max-width: 1024px) {
          .main-grid {
            grid-template-columns: 1fr;
          }
        }

        @media (max-width: 768px) {
          .add-stock-form {
            flex-direction: column;
          }

          .input {
            width: 100%;
          }

          .stats-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
}
