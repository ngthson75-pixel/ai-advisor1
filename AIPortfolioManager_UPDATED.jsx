import React, { useState, useEffect } from 'react';
import { TrendingUp, MessageSquare, Send, Trash2, DollarSign, PieChart } from 'lucide-react';

const API_BASE = 'https://ai-advisor1-backend.onrender.com/api';

export default function AIPortfolioManager() {
  const [portfolio, setPortfolio] = useState([]);
  const [cash, setCash] = useState(0);
  const [loading, setLoading] = useState(false);
  
  // Form states
  const [ticker, setTicker] = useState('');
  const [quantity, setQuantity] = useState('');
  const [price, setPrice] = useState('');
  const [cashInput, setCashInput] = useState('');
  
  // Chat states
  const [chatHistory, setChatHistory] = useState([]);
  const [message, setMessage] = useState('');
  const [chatLoading, setChatLoading] = useState(false);

  const userId = 1; // Default user for demo

  // Fetch portfolio on mount
  useEffect(() => {
    fetchPortfolio();
    fetchCash();
    fetchChatHistory();
  }, []);

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

  const fetchCash = async () => {
    try {
      const response = await fetch(`${API_BASE}/cash?user_id=${userId}`);
      const data = await response.json();
      if (data.success) {
        setCash(data.cash || 0);
        setCashInput(data.cash || 0);
      }
    } catch (error) {
      console.error('Error fetching cash:', error);
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
      console.error('Error fetching chat history:', error);
    }
  };

  const addStock = async (e) => {
    e.preventDefault();
    if (!ticker || !quantity || !price) {
      alert('Vui lòng điền đầy đủ thông tin');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/portfolio`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          ticker: ticker.toUpperCase(),
          quantity: parseInt(quantity),
          price: parseFloat(price)
        })
      });

      const data = await response.json();
      if (data.success) {
        setTicker('');
        setQuantity('');
        setPrice('');
        fetchPortfolio();
      } else {
        alert('Lỗi: ' + (data.error || 'Không thể thêm cổ phiếu'));
      }
    } catch (error) {
      console.error('Error adding stock:', error);
      alert('Lỗi kết nối');
    } finally {
      setLoading(false);
    }
  };

  const deleteStock = async (ticker) => {
    if (!confirm(`Xóa ${ticker} khỏi danh mục?`)) return;

    try {
      const response = await fetch(`${API_BASE}/portfolio/${ticker}?user_id=${userId}`, {
        method: 'DELETE'
      });

      const data = await response.json();
      if (data.success) {
        fetchPortfolio();
      }
    } catch (error) {
      console.error('Error deleting stock:', error);
      alert('Lỗi kết nối');
    }
  };

  const updateCash = async (e) => {
    e.preventDefault();
    
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/cash`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          cash: parseFloat(cashInput) || 0
        })
      });

      const data = await response.json();
      if (data.success) {
        setCash(data.cash);
        alert('Đã cập nhật tiền mặt!');
      }
    } catch (error) {
      console.error('Error updating cash:', error);
      alert('Lỗi kết nối');
    } finally {
      setLoading(false);
    }
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!message.trim()) return;

    const userMessage = message.trim();
    setMessage('');
    setChatLoading(true);

    // Add user message to chat
    setChatHistory(prev => [...prev, { message: userMessage, response: '...' }]);

    try {
      const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          message: userMessage
        })
      });

      const data = await response.json();
      if (data.success) {
        // Update last message with actual response
        setChatHistory(prev => {
          const updated = [...prev];
          updated[updated.length - 1] = {
            message: userMessage,
            response: data.response
          };
          return updated;
        });
      } else {
        setChatHistory(prev => {
          const updated = [...prev];
          updated[updated.length - 1] = {
            message: userMessage,
            response: 'Xin lỗi, có lỗi xảy ra.'
          };
          return updated;
        });
      }
    } catch (error) {
      console.error('Error sending message:', error);
      setChatHistory(prev => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          message: userMessage,
          response: 'Lỗi kết nối.'
        };
        return updated;
      });
    } finally {
      setChatLoading(false);
    }
  };

  // Calculate totals
  const totalStockValue = portfolio.reduce((sum, stock) => sum + (stock.current_value || 0), 0);
  const totalCost = portfolio.reduce((sum, stock) => sum + (stock.cost || 0), 0);
  const totalPL = totalStockValue - totalCost;
  const totalPLPct = totalCost > 0 ? (totalPL / totalCost * 100) : 0;
  const totalAssets = totalStockValue + cash;
  const stockAllocation = totalAssets > 0 ? (totalStockValue / totalAssets * 100) : 0;
  const cashAllocation = totalAssets > 0 ? (cash / totalAssets * 100) : 0;

  return (
    <div style={{ 
      maxWidth: '1400px', 
      margin: '0 auto', 
      padding: '20px',
      backgroundColor: '#0a0e27',
      minHeight: '100vh'
    }}>
      {/* Header */}
      <div style={{ marginBottom: '30px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
          <TrendingUp size={32} color="#3b82f6" />
          <h1 style={{ 
            fontSize: '28px', 
            fontWeight: 'bold',
            color: '#fff',
            margin: 0
          }}>
            Danh Mục Đầu Tư
          </h1>
        </div>
        <p style={{ 
          fontSize: '14px', 
          color: '#94a3b8',
          margin: '10px 0 0 0',
          lineHeight: '1.5'
        }}>
          Hãy cập nhật danh mục của quý vị vào đây và hỏi AI để AI tư vấn và hỗ trợ kiểm soát tâm lý tránh FOMO và HOẢNG SỢ.
        </p>
      </div>

      {/* Summary Cards */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '15px',
        marginBottom: '30px'
      }}>
        <div style={{
          background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
          padding: '20px',
          borderRadius: '12px',
          border: '1px solid #1e293b'
        }}>
          <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '8px' }}>Tổng tài sản</div>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#fff' }}>
            {totalAssets.toLocaleString('vi-VN')} ₫
          </div>
        </div>

        <div style={{
          background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
          padding: '20px',
          borderRadius: '12px',
          border: '1px solid #1e293b'
        }}>
          <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '8px' }}>Giá trị CP</div>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#3b82f6' }}>
            {totalStockValue.toLocaleString('vi-VN')} ₫
          </div>
        </div>

        <div style={{
          background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
          padding: '20px',
          borderRadius: '12px',
          border: '1px solid #1e293b'
        }}>
          <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '8px' }}>Tiền mặt</div>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#10b981' }}>
            {cash.toLocaleString('vi-VN')} ₫
          </div>
        </div>

        <div style={{
          background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
          padding: '20px',
          borderRadius: '12px',
          border: '1px solid #1e293b'
        }}>
          <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '8px' }}>Lãi/Lỗ</div>
          <div style={{ 
            fontSize: '24px', 
            fontWeight: 'bold',
            color: totalPL >= 0 ? '#10b981' : '#ef4444'
          }}>
            {totalPL >= 0 ? '+' : ''}{totalPL.toLocaleString('vi-VN')} ₫
          </div>
          <div style={{ 
            fontSize: '12px',
            color: totalPL >= 0 ? '#10b981' : '#ef4444',
            marginTop: '4px'
          }}>
            {totalPL >= 0 ? '+' : ''}{totalPLPct.toFixed(2)}%
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        {/* Left Column - Portfolio */}
        <div>
          {/* Add Stock Form */}
          <div style={{
            background: '#1e293b',
            padding: '20px',
            borderRadius: '12px',
            marginBottom: '20px',
            border: '1px solid #334155'
          }}>
            <h3 style={{ color: '#fff', marginBottom: '15px', fontSize: '18px' }}>Thêm Cổ Phiếu</h3>
            <form onSubmit={addStock}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '15px' }}>
                <input
                  type="text"
                  placeholder="Mã CP (VD: VCB)"
                  value={ticker}
                  onChange={(e) => setTicker(e.target.value.toUpperCase())}
                  style={{
                    padding: '10px',
                    borderRadius: '8px',
                    border: '1px solid #475569',
                    background: '#0f172a',
                    color: '#fff',
                    fontSize: '14px'
                  }}
                />
                <input
                  type="number"
                  placeholder="Số lượng"
                  value={quantity}
                  onChange={(e) => setQuantity(e.target.value)}
                  style={{
                    padding: '10px',
                    borderRadius: '8px',
                    border: '1px solid #475569',
                    background: '#0f172a',
                    color: '#fff',
                    fontSize: '14px'
                  }}
                />
              </div>
              <input
                type="number"
                placeholder="Giá mua (VND)"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                style={{
                  width: '100%',
                  padding: '10px',
                  borderRadius: '8px',
                  border: '1px solid #475569',
                  background: '#0f172a',
                  color: '#fff',
                  fontSize: '14px',
                  marginBottom: '15px'
                }}
              />
              <button
                type="submit"
                disabled={loading}
                style={{
                  width: '100%',
                  padding: '12px',
                  background: loading ? '#475569' : '#3b82f6',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '14px',
                  fontWeight: '600',
                  cursor: loading ? 'not-allowed' : 'pointer'
                }}
              >
                {loading ? 'Đang thêm...' : 'Thêm vào danh mục'}
              </button>
            </form>
          </div>

          {/* Cash Management */}
          <div style={{
            background: '#1e293b',
            padding: '20px',
            borderRadius: '12px',
            marginBottom: '20px',
            border: '1px solid #334155'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '15px' }}>
              <DollarSign size={20} color="#10b981" />
              <h3 style={{ color: '#fff', margin: 0, fontSize: '18px' }}>Tiền Mặt</h3>
            </div>
            <form onSubmit={updateCash}>
              <input
                type="number"
                placeholder="Số tiền (VND)"
                value={cashInput}
                onChange={(e) => setCashInput(e.target.value)}
                style={{
                  width: '100%',
                  padding: '10px',
                  borderRadius: '8px',
                  border: '1px solid #475569',
                  background: '#0f172a',
                  color: '#fff',
                  fontSize: '14px',
                  marginBottom: '15px'
                }}
              />
              <button
                type="submit"
                disabled={loading}
                style={{
                  width: '100%',
                  padding: '12px',
                  background: loading ? '#475569' : '#10b981',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '14px',
                  fontWeight: '600',
                  cursor: loading ? 'not-allowed' : 'pointer'
                }}
              >
                {loading ? 'Đang cập nhật...' : 'Cập nhật tiền mặt'}
              </button>
            </form>
          </div>

          {/* Portfolio Table */}
          <div style={{
            background: '#1e293b',
            padding: '20px',
            borderRadius: '12px',
            border: '1px solid #334155'
          }}>
            <h3 style={{ color: '#fff', marginBottom: '15px', fontSize: '18px' }}>Danh Mục Cổ Phiếu</h3>
            
            {portfolio.length === 0 ? (
              <div style={{ 
                textAlign: 'center', 
                padding: '40px', 
                color: '#64748b' 
              }}>
                Chưa có cổ phiếu nào. Thêm cổ phiếu đầu tiên!
              </div>
            ) : (
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid #334155' }}>
                      <th style={{ padding: '12px', textAlign: 'left', color: '#94a3b8', fontSize: '12px' }}>Mã CP</th>
                      <th style={{ padding: '12px', textAlign: 'right', color: '#94a3b8', fontSize: '12px' }}>SL</th>
                      <th style={{ padding: '12px', textAlign: 'right', color: '#94a3b8', fontSize: '12px' }}>Giá mua</th>
                      <th style={{ padding: '12px', textAlign: 'right', color: '#94a3b8', fontSize: '12px' }}>Hiện tại</th>
                      <th style={{ padding: '12px', textAlign: 'right', color: '#94a3b8', fontSize: '12px' }}>L/L</th>
                      <th style={{ padding: '12px', textAlign: 'center', color: '#94a3b8', fontSize: '12px' }}></th>
                    </tr>
                  </thead>
                  <tbody>
                    {portfolio.map((stock) => (
                      <tr key={stock.ticker} style={{ borderBottom: '1px solid #334155' }}>
                        <td style={{ padding: '12px', color: '#fff', fontWeight: '600' }}>{stock.ticker}</td>
                        <td style={{ padding: '12px', textAlign: 'right', color: '#fff' }}>{stock.quantity}</td>
                        <td style={{ padding: '12px', textAlign: 'right', color: '#fff' }}>
                          {stock.avg_price.toLocaleString('vi-VN')}
                        </td>
                        <td style={{ padding: '12px', textAlign: 'right', color: '#3b82f6', fontWeight: '600' }}>
                          {stock.current_price.toLocaleString('vi-VN')}
                        </td>
                        <td style={{ 
                          padding: '12px', 
                          textAlign: 'right',
                          color: stock.pl_pct >= 0 ? '#10b981' : '#ef4444',
                          fontWeight: '600'
                        }}>
                          {stock.pl_pct >= 0 ? '+' : ''}{stock.pl_pct.toFixed(2)}%
                          <div style={{ fontSize: '11px', marginTop: '2px' }}>
                            {stock.pl_amount >= 0 ? '+' : ''}{stock.pl_amount.toLocaleString('vi-VN')} ₫
                          </div>
                        </td>
                        <td style={{ padding: '12px', textAlign: 'center' }}>
                          <button
                            onClick={() => deleteStock(stock.ticker)}
                            style={{
                              background: 'transparent',
                              border: 'none',
                              color: '#ef4444',
                              cursor: 'pointer',
                              padding: '4px'
                            }}
                          >
                            <Trash2 size={16} />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Allocation */}
            {totalAssets > 0 && (
              <div style={{ marginTop: '20px', paddingTop: '20px', borderTop: '1px solid #334155' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
                  <PieChart size={16} color="#3b82f6" />
                  <span style={{ color: '#94a3b8', fontSize: '12px' }}>Phân bổ tài sản</span>
                </div>
                <div style={{ display: 'flex', gap: '10px' }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '4px' }}>Cổ phiếu</div>
                    <div style={{ fontSize: '16px', color: '#3b82f6', fontWeight: '600' }}>
                      {stockAllocation.toFixed(1)}%
                    </div>
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '4px' }}>Tiền mặt</div>
                    <div style={{ fontSize: '16px', color: '#10b981', fontWeight: '600' }}>
                      {cashAllocation.toFixed(1)}%
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Column - AI Chat */}
        <div>
          <div style={{
            background: '#1e293b',
            padding: '20px',
            borderRadius: '12px',
            border: '1px solid #334155',
            height: 'calc(100vh - 140px)',
            display: 'flex',
            flexDirection: 'column'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '15px' }}>
              <MessageSquare size={20} color="#3b82f6" />
              <h3 style={{ color: '#fff', margin: 0, fontSize: '18px' }}>
                Quản lý danh mục với phân tích AI
              </h3>
            </div>

            <p style={{ 
              fontSize: '13px', 
              color: '#94a3b8',
              marginBottom: '15px',
              lineHeight: '1.5'
            }}>
              Hãy cập nhật danh mục của quý vị vào đây và hỏi AI để AI tư vấn và hỗ trợ kiểm soát tâm lý tránh FOMO và HOẢNG SỢ.
            </p>

            {/* Chat History */}
            <div style={{
              flex: 1,
              overflowY: 'auto',
              marginBottom: '15px',
              padding: '15px',
              background: '#0f172a',
              borderRadius: '8px'
            }}>
              {chatHistory.length === 0 ? (
                <div style={{ 
                  textAlign: 'center', 
                  padding: '40px', 
                  color: '#64748b' 
                }}>
                  Bắt đầu cuộc trò chuyện với AI Advisor
                </div>
              ) : (
                chatHistory.map((chat, index) => (
                  <div key={index} style={{ marginBottom: '20px' }}>
                    {/* User Message */}
                    <div style={{
                      background: '#1e40af',
                      padding: '10px 12px',
                      borderRadius: '8px',
                      marginBottom: '8px',
                      maxWidth: '80%',
                      marginLeft: 'auto'
                    }}>
                      <div style={{ fontSize: '13px', color: '#fff' }}>{chat.message}</div>
                    </div>

                    {/* AI Response */}
                    <div style={{
                      background: '#334155',
                      padding: '10px 12px',
                      borderRadius: '8px',
                      maxWidth: '80%'
                    }}>
                      <div style={{ fontSize: '13px', color: '#fff', whiteSpace: 'pre-wrap' }}>
                        {chat.response}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* Chat Input */}
            <form onSubmit={sendMessage} style={{ display: 'flex', gap: '10px' }}>
              <input
                type="text"
                placeholder="Hỏi AI về danh mục của bạn..."
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                disabled={chatLoading}
                style={{
                  flex: 1,
                  padding: '12px',
                  borderRadius: '8px',
                  border: '1px solid #475569',
                  background: '#0f172a',
                  color: '#fff',
                  fontSize: '14px'
                }}
              />
              <button
                type="submit"
                disabled={chatLoading || !message.trim()}
                style={{
                  padding: '12px 20px',
                  background: chatLoading || !message.trim() ? '#475569' : '#3b82f6',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: chatLoading || !message.trim() ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}
              >
                <Send size={18} />
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
