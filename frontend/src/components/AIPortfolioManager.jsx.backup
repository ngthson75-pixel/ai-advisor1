import React, { useState, useEffect } from 'react';

const API_BASE = 'https://ai-advisor1-backend.onrender.com/api';

// Generate unique user ID
const generateUserId = () => {
  const timestamp = Date.now();
  const randomStr = Math.random().toString(36).substring(2, 15);
  return `user_${timestamp}_${randomStr}`;
};

// Get or create user session
const getUserId = () => {
  let userId = localStorage.getItem('ai_advisor_user_id');
  if (!userId) {
    userId = generateUserId();
    localStorage.setItem('ai_advisor_user_id', userId);
    console.log('✅ New user session created:', userId);
  }
  return userId;
};

const AIPortfolioManager = () => {
  const [userId] = useState(getUserId());
  
  // Portfolio state
  const [portfolio, setPortfolio] = useState([]);
  const [cash, setCash] = useState(0);
  const [totalValue, setTotalValue] = useState(0);
  const [totalPL, setTotalPL] = useState(0);
  const [totalPLPercent, setTotalPLPercent] = useState(0);
  
  // Form state
  const [ticker, setTicker] = useState('');
  const [quantity, setQuantity] = useState('');
  const [price, setPrice] = useState('');
  const [cashInput, setCashInput] = useState('');
  
  // Chat state
  const [chatHistory, setChatHistory] = useState([]);
  const [userMessage, setUserMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isFetchingPrice, setIsFetchingPrice] = useState(false);

  // Fetch portfolio on mount
  useEffect(() => {
    fetchPortfolio();
    fetchChatHistory();
  }, [userId]);

  // Recalculate totals when portfolio changes
  useEffect(() => {
    calculateTotals();
  }, [portfolio, cash]);

  const fetchPortfolio = async () => {
    try {
      const response = await fetch(`${API_BASE}/portfolio?user_id=${userId}`);
      const data = await response.json();
      
      if (data.success) {
        setPortfolio(data.portfolio || []);
        setCash(data.cash || 0);
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
        setChatHistory(data.chat_history || []);
      }
    } catch (error) {
      console.error('Error fetching chat history:', error);
    }
  };

  const calculateTotals = () => {
    let invested = 0;
    let current = 0;

    portfolio.forEach(stock => {
      invested += stock.cost || 0;
      current += stock.current_value || 0;
    });

    const pl = current - invested;
    const plPercent = invested > 0 ? (pl / invested) * 100 : 0;
    
    setTotalValue(current + cash);
    setTotalPL(pl);
    setTotalPLPercent(plPercent);
  };

  const handleAddStock = async (e) => {
    e.preventDefault();
    
    if (!ticker || !quantity || !price) {
      alert('Vui lòng điền đầy đủ thông tin');
      return;
    }

    const tickerUpper = ticker.toUpperCase();
    
    try {
      setIsFetchingPrice(true);
      
      // Fetch current EOD price
      const priceResponse = await fetch(`${API_BASE}/stock/current-price?ticker=${tickerUpper}`);
      const priceData = await priceResponse.json();
      
      const currentPrice = priceData.success ? priceData.price : parseFloat(price);
      
      // Add to portfolio
      const response = await fetch(`${API_BASE}/portfolio`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          ticker: tickerUpper,
          quantity: parseInt(quantity),
          price: parseFloat(price),
          current_price: currentPrice
        })
      });

      const data = await response.json();
      
      if (data.success) {
        // Refresh portfolio
        await fetchPortfolio();
        
        // Clear form
        setTicker('');
        setQuantity('');
        setPrice('');
        
        alert(`✅ Đã thêm ${tickerUpper} vào danh mục!`);
      } else {
        alert(`❌ Lỗi: ${data.error}`);
      }
    } catch (error) {
      console.error('Error adding stock:', error);
      alert('❌ Không thể thêm cổ phiếu');
    } finally {
      setIsFetchingPrice(false);
    }
  };

  const handleUpdateCash = async (e) => {
    e.preventDefault();
    
    if (!cashInput) {
      alert('Vui lòng nhập số tiền');
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/cash`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          cash_amount: parseFloat(cashInput)
        })
      });

      const data = await response.json();
      
      if (data.success) {
        await fetchPortfolio();
        setCashInput('');
        alert('✅ Đã cập nhật tiền mặt!');
      } else {
        alert(`❌ Lỗi: ${data.error}`);
      }
    } catch (error) {
      console.error('Error updating cash:', error);
      alert('❌ Không thể cập nhật tiền mặt');
    }
  };

  const handleDeleteStock = async (ticker) => {
    if (!confirm(`Xóa ${ticker} khỏi danh mục?`)) return;

    try {
      const response = await fetch(`${API_BASE}/portfolio/${ticker}?user_id=${userId}`, {
        method: 'DELETE'
      });

      const data = await response.json();
      
      if (data.success) {
        await fetchPortfolio();
        alert(`✅ Đã xóa ${ticker}`);
      }
    } catch (error) {
      console.error('Error deleting stock:', error);
      alert('❌ Không thể xóa cổ phiếu');
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    
    if (!userMessage.trim()) return;

    const message = userMessage.trim();
    setUserMessage('');
    setIsLoading(true);

    // Build portfolio context with P&L
    const portfolioContext = {
      total_value: totalValue,
      cash: cash,
      stocks_value: totalValue - cash,
      total_pl: totalPL,
      total_pl_percent: totalPLPercent,
      holdings: portfolio.map(stock => ({
        ticker: stock.ticker,
        quantity: stock.quantity,
        avg_price: stock.avg_price,
        current_price: stock.current_price,
        pl_amount: stock.pl_amount,
        pl_percent: stock.pl_pct
      }))
    };

    try {
      const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          message: message,
          portfolio_context: JSON.stringify(portfolioContext)
        })
      });

      const data = await response.json();
      
      if (data.success) {
        setChatHistory([...chatHistory, {
          message: message,
          response: data.response,
          created_at: new Date().toISOString()
        }]);
      } else {
        alert(`❌ Lỗi: ${data.error}`);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      alert('❌ Không thể gửi tin nhắn');
    } finally {
      setIsLoading(false);
    }
  };

  const formatNumber = (num) => {
    return new Intl.NumberFormat('vi-VN').format(num);
  };

  const formatPercent = (num) => {
    return num >= 0 ? `+${num.toFixed(2)}%` : `${num.toFixed(2)}%`;
  };

  return (
    <div style={{
      padding: '20px',
      backgroundColor: '#000',
      minHeight: '100vh',
      color: '#fff'
    }}>
      <div style={{
        maxWidth: '1400px',
        margin: '0 auto'
      }}>
        {/* Header */}
        <div style={{ marginBottom: '30px' }}>
          <h2 style={{ 
            fontSize: '28px', 
            fontWeight: '600',
            marginBottom: '10px',
            color: '#fff'
          }}>
            📊 Quản trị đầu tư bằng AI
          </h2>
          <p style={{ 
            fontSize: '14px', 
            color: '#888',
            marginBottom: '5px'
          }}>
            Hãy chia sẻ danh mục của bạn và hỏi đáp mua bán để AI hỗ trợ quản lý danh mục và kiểm soát FOMO hay HOẢNG SỢ
          </p>
          <p style={{ 
            fontSize: '12px', 
            color: '#555' 
          }}>
            👤 User ID: {userId.substring(0, 30)}...
          </p>
        </div>

        {/* Main Content - 2 Columns */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '30px'
        }}>
          {/* Left Column - Portfolio */}
          <div>
            {/* Portfolio Summary */}
            <div style={{
              backgroundColor: '#1a1a1a',
              padding: '20px',
              borderRadius: '8px',
              marginBottom: '20px'
            }}>
              <h3 style={{ fontSize: '18px', marginBottom: '15px', color: '#fff' }}>
                💼 Tổng quan danh mục
              </h3>
              <div style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: '15px'
              }}>
                <div>
                  <div style={{ fontSize: '12px', color: '#888', marginBottom: '5px' }}>
                    Tổng tài sản
                  </div>
                  <div style={{ fontSize: '20px', fontWeight: '600', color: '#fff' }}>
                    {formatNumber(totalValue)} VND
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '12px', color: '#888', marginBottom: '5px' }}>
                    Tiền mặt
                  </div>
                  <div style={{ fontSize: '20px', fontWeight: '600', color: '#4CAF50' }}>
                    {formatNumber(cash)} VND
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '12px', color: '#888', marginBottom: '5px' }}>
                    Lãi/Lỗ
                  </div>
                  <div style={{ 
                    fontSize: '20px', 
                    fontWeight: '600',
                    color: totalPL >= 0 ? '#4CAF50' : '#f44336'
                  }}>
                    {totalPL >= 0 ? '+' : ''}{formatNumber(totalPL)} VND
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '12px', color: '#888', marginBottom: '5px' }}>
                    % Lãi/Lỗ
                  </div>
                  <div style={{ 
                    fontSize: '20px', 
                    fontWeight: '600',
                    color: totalPLPercent >= 0 ? '#4CAF50' : '#f44336'
                  }}>
                    {formatPercent(totalPLPercent)}
                  </div>
                </div>
              </div>
            </div>

            {/* Add Stock Form */}
            <div style={{
              backgroundColor: '#1a1a1a',
              padding: '20px',
              borderRadius: '8px',
              marginBottom: '20px'
            }}>
              <h3 style={{ fontSize: '16px', marginBottom: '15px', color: '#fff' }}>
                ➕ Thêm cổ phiếu
              </h3>
              <form onSubmit={handleAddStock}>
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr 1fr',
                  gap: '10px',
                  marginBottom: '10px'
                }}>
                  <input
                    type="text"
                    placeholder="Mã (VD: VCB)"
                    value={ticker}
                    onChange={(e) => setTicker(e.target.value.toUpperCase())}
                    style={{
                      padding: '10px',
                      backgroundColor: '#000',
                      border: '1px solid #333',
                      borderRadius: '4px',
                      color: '#fff',
                      fontSize: '14px'
                    }}
                  />
                  <input
                    type="number"
                    placeholder="Số lượng (VD: 100)"
                    value={quantity}
                    onChange={(e) => setQuantity(e.target.value)}
                    style={{
                      padding: '10px',
                      backgroundColor: '#000',
                      border: '1px solid #333',
                      borderRadius: '4px',
                      color: '#fff',
                      fontSize: '14px'
                    }}
                  />
                  <input
                    type="number"
                    placeholder="Giá mua (VD: 85000)"
                    value={price}
                    onChange={(e) => setPrice(e.target.value)}
                    style={{
                      padding: '10px',
                      backgroundColor: '#000',
                      border: '1px solid #333',
                      borderRadius: '4px',
                      color: '#fff',
                      fontSize: '14px'
                    }}
                  />
                </div>
                <button
                  type="submit"
                  disabled={isFetchingPrice}
                  style={{
                    width: '100%',
                    padding: '12px',
                    backgroundColor: isFetchingPrice ? '#555' : '#2196F3',
                    color: '#fff',
                    border: 'none',
                    borderRadius: '4px',
                    fontSize: '14px',
                    fontWeight: '600',
                    cursor: isFetchingPrice ? 'not-allowed' : 'pointer',
                    transition: 'background-color 0.2s'
                  }}
                  onMouseOver={(e) => !isFetchingPrice && (e.target.style.backgroundColor = '#1976D2')}
                  onMouseOut={(e) => !isFetchingPrice && (e.target.style.backgroundColor = '#2196F3')}
                >
                  {isFetchingPrice ? '⏳ Đang lấy giá...' : '+ Thêm'}
                </button>
              </form>
            </div>

            {/* Update Cash */}
            <div style={{
              backgroundColor: '#1a1a1a',
              padding: '20px',
              borderRadius: '8px',
              marginBottom: '20px'
            }}>
              <h3 style={{ fontSize: '16px', marginBottom: '15px', color: '#fff' }}>
                💰 Cập nhật tiền mặt
              </h3>
              <form onSubmit={handleUpdateCash}>
                <div style={{ display: 'flex', gap: '10px' }}>
                  <input
                    type="number"
                    placeholder="Số tiền (VD: 50000000)"
                    value={cashInput}
                    onChange={(e) => setCashInput(e.target.value)}
                    style={{
                      flex: 1,
                      padding: '10px',
                      backgroundColor: '#000',
                      border: '1px solid #333',
                      borderRadius: '4px',
                      color: '#fff',
                      fontSize: '14px'
                    }}
                  />
                  <button
                    type="submit"
                    style={{
                      padding: '10px 20px',
                      backgroundColor: '#4CAF50',
                      color: '#fff',
                      border: 'none',
                      borderRadius: '4px',
                      fontSize: '14px',
                      fontWeight: '600',
                      cursor: 'pointer',
                      transition: 'background-color 0.2s'
                    }}
                    onMouseOver={(e) => e.target.style.backgroundColor = '#45a049'}
                    onMouseOut={(e) => e.target.style.backgroundColor = '#4CAF50'}
                  >
                    Cập nhật
                  </button>
                </div>
              </form>
            </div>

            {/* Portfolio List */}
            <div style={{
              backgroundColor: '#1a1a1a',
              padding: '20px',
              borderRadius: '8px'
            }}>
              <h3 style={{ fontSize: '16px', marginBottom: '15px', color: '#fff' }}>
                📋 Danh mục cổ phiếu ({portfolio.length})
              </h3>
              {portfolio.length === 0 ? (
                <p style={{ color: '#888', fontSize: '14px', textAlign: 'center', padding: '20px' }}>
                  Danh mục trống. Thêm cổ phiếu đầu tiên!
                </p>
              ) : (
                <div style={{ 
                  maxHeight: '400px', 
                  overflowY: 'auto' 
                }}>
                  {portfolio.map((stock) => (
                    <div
                      key={stock.id}
                      style={{
                        backgroundColor: '#000',
                        padding: '15px',
                        borderRadius: '6px',
                        marginBottom: '10px',
                        border: '1px solid #333'
                      }}
                    >
                      <div style={{ 
                        display: 'flex', 
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        marginBottom: '10px'
                      }}>
                        <div style={{ fontSize: '16px', fontWeight: '600', color: '#fff' }}>
                          {stock.ticker}
                        </div>
                        <button
                          onClick={() => handleDeleteStock(stock.ticker)}
                          style={{
                            padding: '5px 10px',
                            backgroundColor: '#f44336',
                            color: '#fff',
                            border: 'none',
                            borderRadius: '4px',
                            fontSize: '12px',
                            cursor: 'pointer'
                          }}
                        >
                          Xóa
                        </button>
                      </div>
                      <div style={{
                        display: 'grid',
                        gridTemplateColumns: '1fr 1fr',
                        gap: '10px',
                        fontSize: '13px',
                        color: '#888'
                      }}>
                        <div>
                          <span>SL: </span>
                          <span style={{ color: '#fff' }}>{stock.quantity}</span>
                        </div>
                        <div>
                          <span>Giá mua: </span>
                          <span style={{ color: '#fff' }}>{formatNumber(stock.avg_price)}</span>
                        </div>
                        <div>
                          <span>Giá hiện tại: </span>
                          <span style={{ color: '#fff' }}>{formatNumber(stock.current_price)}</span>
                        </div>
                        <div>
                          <span>Giá trị: </span>
                          <span style={{ color: '#fff' }}>{formatNumber(stock.current_value)}</span>
                        </div>
                        <div>
                          <span>L/L: </span>
                          <span style={{ 
                            color: stock.pl_amount >= 0 ? '#4CAF50' : '#f44336',
                            fontWeight: '600'
                          }}>
                            {stock.pl_amount >= 0 ? '+' : ''}{formatNumber(stock.pl_amount)}
                          </span>
                        </div>
                        <div>
                          <span>%: </span>
                          <span style={{ 
                            color: stock.pl_pct >= 0 ? '#4CAF50' : '#f44336',
                            fontWeight: '600'
                          }}>
                            {formatPercent(stock.pl_pct)}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Right Column - AI Chat */}
          <div>
            <div style={{
              backgroundColor: '#1a1a1a',
              padding: '20px',
              borderRadius: '8px',
              height: 'calc(100vh - 180px)',
              display: 'flex',
              flexDirection: 'column'
            }}>
              <h3 style={{ fontSize: '16px', marginBottom: '15px', color: '#fff' }}>
                💬 Tư vấn AI
              </h3>
              
              {/* Chat History */}
              <div style={{
                flex: 1,
                overflowY: 'auto',
                marginBottom: '15px',
                paddingRight: '10px'
              }}>
                {chatHistory.length === 0 ? (
                  <div style={{
                    textAlign: 'center',
                    padding: '40px 20px',
                    color: '#888'
                  }}>
                    <div style={{ fontSize: '48px', marginBottom: '15px' }}>🤖</div>
                    <p style={{ fontSize: '14px', marginBottom: '10px' }}>
                      Xin chào! Tôi là AI Advisor của bạn.
                    </p>
                    <p style={{ fontSize: '13px', color: '#666' }}>
                      Hãy bắt đầu bằng cách:
                    </p>
                    <ol style={{
                      textAlign: 'left',
                      display: 'inline-block',
                      fontSize: '13px',
                      color: '#666',
                      marginTop: '10px'
                    }}>
                      <li>Nhập vốn đầu tư của bạn</li>
                      <li>Thêm các vị thế hiện tại (nếu có)</li>
                      <li>Đặt câu hỏi hoặc yêu cầu phân tích</li>
                    </ol>
                    <p style={{ 
                      fontSize: '12px', 
                      color: '#555',
                      marginTop: '20px',
                      fontStyle: 'italic'
                    }}>
                      Tôi sẽ phân tích danh mục và tư vấn chiến lược phù hợp! 🚀
                    </p>
                  </div>
                ) : (
                  chatHistory.map((chat, index) => (
                    <div key={index} style={{ marginBottom: '20px' }}>
                      {/* User Message */}
                      <div style={{
                        backgroundColor: '#2196F3',
                        padding: '12px 15px',
                        borderRadius: '8px',
                        marginBottom: '10px',
                        maxWidth: '80%',
                        marginLeft: 'auto'
                      }}>
                        <div style={{ fontSize: '13px', color: '#fff' }}>
                          {chat.message}
                        </div>
                      </div>
                      
                      {/* AI Response */}
                      <div style={{
                        backgroundColor: '#000',
                        padding: '12px 15px',
                        borderRadius: '8px',
                        border: '1px solid #333',
                        maxWidth: '80%'
                      }}>
                        <div style={{ fontSize: '13px', color: '#fff', whiteSpace: 'pre-wrap' }}>
                          {chat.response}
                        </div>
                      </div>
                    </div>
                  ))
                )}
                {isLoading && (
                  <div style={{
                    backgroundColor: '#000',
                    padding: '12px 15px',
                    borderRadius: '8px',
                    border: '1px solid #333',
                    maxWidth: '80%'
                  }}>
                    <div style={{ fontSize: '13px', color: '#888' }}>
                      ⏳ AI đang suy nghĩ...
                    </div>
                  </div>
                )}
              </div>

              {/* Chat Input */}
              <form onSubmit={handleSendMessage}>
                <div style={{ display: 'flex', gap: '10px' }}>
                  <input
                    type="text"
                    placeholder="Đặt câu hỏi cho AI (VD: Tôi nên mua hay bán VCB?)"
                    value={userMessage}
                    onChange={(e) => setUserMessage(e.target.value)}
                    disabled={isLoading}
                    style={{
                      flex: 1,
                      padding: '12px',
                      backgroundColor: '#000',
                      border: '1px solid #333',
                      borderRadius: '4px',
                      color: '#fff',
                      fontSize: '14px'
                    }}
                  />
                  <button
                    type="submit"
                    disabled={isLoading || !userMessage.trim()}
                    style={{
                      padding: '12px 24px',
                      backgroundColor: isLoading || !userMessage.trim() ? '#555' : '#2196F3',
                      color: '#fff',
                      border: 'none',
                      borderRadius: '4px',
                      fontSize: '14px',
                      fontWeight: '600',
                      cursor: isLoading || !userMessage.trim() ? 'not-allowed' : 'pointer',
                      transition: 'background-color 0.2s'
                    }}
                    onMouseOver={(e) => !isLoading && userMessage.trim() && (e.target.style.backgroundColor = '#1976D2')}
                    onMouseOut={(e) => !isLoading && userMessage.trim() && (e.target.style.backgroundColor = '#2196F3')}
                  >
                    {isLoading ? '⏳' : '➤'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AIPortfolioManager;
