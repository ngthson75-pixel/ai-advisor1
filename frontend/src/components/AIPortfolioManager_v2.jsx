import React, { useState, useEffect } from 'react';
import { TrendingUp, DollarSign, PieChart, MessageSquare, Send, Plus, Trash2, BarChart3, AlertCircle, Wallet } from 'lucide-react';

const API_BASE = 'https://ai-advisor1-backend.onrender.com/api';
const USER_ID = 1;

export default function AIPortfolioManager() {
  const [portfolio, setPortfolio] = useState([]);
  const [cash, setCash] = useState(0);
  const [chatHistory, setChatHistory] = useState([]);
  const [userMessage, setUserMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Form state
  const [newStock, setNewStock] = useState({
    ticker: '',
    quantity: '',
    price: ''
  });
  
  const [cashInput, setCashInput] = useState('');

  // Fetch portfolio with P&L
  const fetchPortfolio = async () => {
    try {
      const response = await fetch(`${API_BASE}/portfolio?user_id=${USER_ID}`);
      const data = await response.json();
      
      if (data.success) {
        setPortfolio(data.portfolio || []);
        setCash(data.cash || 0);
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
      setError('Vui lòng điền đầy đủ thông tin');
      setTimeout(() => setError(null), 3000);
      return;
    }

    try {
      setLoading(true);
      setError(null);

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
        await fetchPortfolio();
      } else {
        setError(data.error || 'Không thể thêm cổ phiếu');
      }
    } catch (err) {
      setError('Lỗi: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  // Handle key down
  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      e.stopPropagation();
      handleAddStock();
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
      } else {
        setError(data.error || 'Không thể xóa');
      }
    } catch (err) {
      setError('Lỗi: ' + err.message);
    }
  };

  // Update cash
  const handleUpdateCash = async () => {
    const amount = parseFloat(cashInput);
    
    if (isNaN(amount) || amount < 0) {
      setError('Số tiền không hợp lệ');
      setTimeout(() => setError(null), 3000);
      return;
    }

    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/cash`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: USER_ID,
          cash: amount
        })
      });

      const data = await response.json();
      if (data.success) {
        setCash(data.cash);
        setCashInput('');
      } else {
        setError(data.error || 'Không thể cập nhật tiền mặt');
      }
    } catch (err) {
      setError('Lỗi: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  // Send chat message
  const handleSendMessage = async () => {
    if (!userMessage.trim()) return;

    const currentMessage = userMessage;
    setUserMessage('');

    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: USER_ID,
          message: currentMessage
        })
      });

      const data = await response.json();
      
      if (data.success) {
        setChatHistory([...chatHistory, {
          message: currentMessage,
          response: data.response
        }]);
      } else {
        setError(data.error || 'AI không phản hồi');
        setUserMessage(currentMessage);
      }
    } catch (err) {
      setError('Lỗi: ' + err.message);
      setUserMessage(currentMessage);
    } finally {
      setLoading(false);
    }
  };

  // Handle chat key down
  const handleChatKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      e.stopPropagation();
      handleSendMessage();
    }
  };

  // Calculate totals
  const totalCost = portfolio.reduce((sum, stock) => 
    sum + (stock?.cost || 0), 0
  );
  
  const totalValue = portfolio.reduce((sum, stock) => 
    sum + (stock?.current_value || 0), 0
  );
  
  const totalPL = totalValue - totalCost;
  const totalPLPct = totalCost > 0 ? (totalPL / totalCost * 100) : 0;
  
  const totalAssets = totalValue + cash;
  const stockRatio = totalAssets > 0 ? (totalValue / totalAssets * 100) : 0;
  const cashRatio = totalAssets > 0 ? (cash / totalAssets * 100) : 0;

  return (
    <div className="portfolio-manager">
      <div className="container">
        {/* Error Banner */}
        {error && (
          <div className="error-banner">
            <AlertCircle size={20} />
            <span>{error}</span>
            <button onClick={() => setError(null)}>✕</button>
          </div>
        )}

        {/* Header */}
        <div className="header">
          <div>
            <h1 className="title">
              <BarChart3 size={32} />
              Danh Mục Đầu Tư
            </h1>
            <p className="subtitle">Quản lý danh mục với phân tích AI</p>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon" style={{ background: '#22c55e20' }}>
              <DollarSign size={24} style={{ color: '#22c55e' }} />
            </div>
            <div>
              <div className="stat-label">Tổng tài sản</div>
              <div className="stat-value">{totalAssets.toLocaleString()} VND</div>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon" style={{ background: totalPL >= 0 ? '#22c55e20' : '#ef444420' }}>
              <TrendingUp size={24} style={{ color: totalPL >= 0 ? '#22c55e' : '#ef4444' }} />
            </div>
            <div>
              <div className="stat-label">Lãi/Lỗ</div>
              <div className="stat-value" style={{ color: totalPL >= 0 ? '#22c55e' : '#ef4444' }}>
                {totalPL >= 0 ? '+' : ''}{totalPL.toLocaleString()} VND
                <span style={{ fontSize: '14px', marginLeft: '5px' }}>
                  ({totalPLPct >= 0 ? '+' : ''}{totalPLPct.toFixed(2)}%)
                </span>
              </div>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon" style={{ background: '#3b82f620' }}>
              <PieChart size={24} style={{ color: '#3b82f6' }} />
            </div>
            <div>
              <div className="stat-label">Phân bổ</div>
              <div className="stat-value" style={{ fontSize: '14px' }}>
                {stockRatio.toFixed(1)}% CP / {cashRatio.toFixed(1)}% TM
              </div>
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

            {/* Add Stock Form */}
            <div className="add-stock-form">
              <input
                type="text"
                placeholder="Mã CP (VD: VCB)"
                value={newStock.ticker}
                onChange={(e) => setNewStock({...newStock, ticker: e.target.value})}
                onKeyDown={handleKeyDown}
                className="input"
                style={{ flex: 1 }}
                disabled={loading}
              />
              <input
                type="number"
                placeholder="Số lượng"
                value={newStock.quantity}
                onChange={(e) => setNewStock({...newStock, quantity: e.target.value})}
                onKeyDown={handleKeyDown}
                className="input"
                style={{ flex: 1 }}
                disabled={loading}
              />
              <input
                type="number"
                placeholder="Giá (VND)"
                value={newStock.price}
                onChange={(e) => setNewStock({...newStock, price: e.target.value})}
                onKeyDown={handleKeyDown}
                className="input"
                style={{ flex: 1 }}
                disabled={loading}
              />
              <button 
                onClick={handleAddStock}
                className="btn-primary"
                disabled={loading}
              >
                {loading ? 'Đang thêm...' : 'Thêm'}
              </button>
            </div>

            {/* Cash Section */}
            <div className="cash-section">
              <div className="section-header" style={{ marginTop: '20px', marginBottom: '15px' }}>
                <h3 className="section-title" style={{ fontSize: '16px' }}>
                  <Wallet size={18} />
                  Tiền mặt
                </h3>
              </div>
              
              <div className="cash-display">
                <div className="cash-amount">
                  <span style={{ color: '#94a3b8', fontSize: '13px' }}>Số dư:</span>
                  <span style={{ color: '#22c55e', fontSize: '20px', fontWeight: 'bold', marginLeft: '10px' }}>
                    {cash.toLocaleString()} VND
                  </span>
                </div>
                
                <div className="cash-input-group">
                  <input
                    type="number"
                    placeholder="Nhập số tiền mặt"
                    value={cashInput}
                    onChange={(e) => setCashInput(e.target.value)}
                    className="input"
                    style={{ flex: 1 }}
                    disabled={loading}
                  />
                  <button
                    onClick={handleUpdateCash}
                    className="btn-secondary"
                    disabled={loading}
                  >
                    Cập nhật
                  </button>
                </div>
              </div>
            </div>

            {/* Portfolio List */}
            <div className="section-header" style={{ marginTop: '30px' }}>
              <h2 className="section-title">Danh mục cổ phiếu</h2>
            </div>

            {portfolio.length === 0 ? (
              <div className="empty-state">
                <PieChart size={48} style={{ color: '#64748b', marginBottom: '10px' }} />
                <p>Chưa có cổ phiếu nào</p>
              </div>
            ) : (
              <div className="stocks-list">
                {portfolio.map((stock, idx) => {
                  const ticker = stock?.ticker || 'N/A';
                  const quantity = stock?.quantity || 0;
                  const avgPrice = stock?.avg_price || 0;
                  const currentPrice = stock?.current_price || avgPrice;
                  const plAmount = stock?.pl_amount || 0;
                  const plPct = stock?.pl_pct || 0;
                  const isProfit = plAmount >= 0;

                  return (
                    <div key={idx} className="stock-item">
                      <div className="stock-info">
                        <div className="stock-header">
                          <div className="stock-ticker">{ticker}</div>
                          <div className="stock-pl" style={{ color: isProfit ? '#22c55e' : '#ef4444' }}>
                            {isProfit ? '+' : ''}{plPct.toFixed(2)}%
                          </div>
                        </div>
                        <div className="stock-details">
                          {quantity} CP × Mua {avgPrice.toLocaleString()} VND
                        </div>
                        <div className="stock-current">
                          Hiện tại: {currentPrice.toLocaleString()} VND
                          <span style={{ 
                            marginLeft: '10px',
                            color: isProfit ? '#22c55e' : '#ef4444',
                            fontSize: '12px'
                          }}>
                            ({isProfit ? '+' : ''}{plAmount.toLocaleString()} VND)
                          </span>
                        </div>
                      </div>
                      <button
                        onClick={() => handleDeleteStock(ticker)}
                        className="btn-delete"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  );
                })}
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
              Phân tích danh mục và tư vấn đầu tư
            </div>

            {/* Chat History */}
            <div className="chat-history">
              {chatHistory.length === 0 ? (
                <div className="empty-state">
                  <MessageSquare size={48} style={{ color: '#64748b' }} />
                  <p style={{ marginTop: '10px' }}>
                    Hỏi AI về danh mục của bạn
                  </p>
                  <p style={{ fontSize: '13px', color: '#64748b', marginTop: '5px' }}>
                    VD: "Phân tích rủi ro danh mục của tôi"
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
                onKeyDown={handleChatKeyDown}
                className="input"
                disabled={loading}
              />
              <button
                onClick={handleSendMessage}
                disabled={loading || !userMessage.trim()}
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

        .error-banner {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 15px 20px;
          background: #ef444420;
          border: 1px solid #ef4444;
          border-radius: 8px;
          color: #ef4444;
          margin-bottom: 20px;
          font-size: 14px;
        }

        .error-banner button {
          background: none;
          border: none;
          color: #ef4444;
          cursor: pointer;
          font-size: 20px;
          padding: 0;
          width: 24px;
          height: 24px;
          margin-left: auto;
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
          font-size: 20px;
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
          margin: 0;
        }

        .add-stock-form {
          display: flex;
          gap: 10px;
          flex-wrap: wrap;
        }

        .cash-section {
          margin-top: 20px;
          padding-top: 20px;
          border-top: 1px solid #334155;
        }

        .cash-display {
          display: flex;
          flex-direction: column;
          gap: 15px;
        }

        .cash-amount {
          display: flex;
          align-items: center;
          padding: 15px;
          background: #0f172a;
          border: 1px solid #334155;
          border-radius: 8px;
        }

        .cash-input-group {
          display: flex;
          gap: 10px;
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

        .input:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .input::placeholder {
          color: #64748b;
        }

        .btn-primary, .btn-secondary {
          padding: 12px 24px;
          background: #3b82f6;
          color: white;
          border: none;
          border-radius: 8px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
          white-space: nowrap;
        }

        .btn-secondary {
          background: #22c55e;
        }

        .btn-primary:hover:not(:disabled), .btn-secondary:hover:not(:disabled) {
          opacity: 0.9;
        }

        .btn-primary:disabled, .btn-secondary:disabled {
          opacity: 0.6;
          cursor: not-allowed;
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

        .stock-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }

        .stock-ticker {
          color: #3b82f6;
          font-weight: bold;
          font-size: 18px;
        }

        .stock-pl {
          font-weight: 700;
          font-size: 16px;
        }

        .stock-details {
          color: #94a3b8;
          font-size: 13px;
          margin-bottom: 4px;
        }

        .stock-current {
          color: #e2e8f0;
          font-size: 14px;
          font-weight: 500;
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
          line-height: 1.6;
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

        .btn-send:hover:not(:disabled) {
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
