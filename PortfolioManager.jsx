import React, { useState, useEffect, useRef } from 'react';
import { Send, Trash2, Plus, TrendingUp, DollarSign, BarChart3, Sparkles } from 'lucide-react';

const PortfolioManager = () => {
  // Portfolio state
  const [portfolio, setPortfolio] = useState([]);
  const [newStock, setNewStock] = useState({ ticker: '', quantity: '', price: '' });
  
  // Chat state
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [hasGemini, setHasGemini] = useState(false);
  
  const chatEndRef = useRef(null);
  const userId = 1; // TODO: Get from auth context
  
  const API_BASE = process.env.REACT_APP_API_URL || 'https://ai-advisor1-backend.onrender.com/api';

  // Load portfolio on mount
  useEffect(() => {
    loadPortfolio();
    loadChatHistory();
  }, []);

  // Auto-scroll chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // ============================================================================
  // PORTFOLIO FUNCTIONS
  // ============================================================================

  const loadPortfolio = async () => {
    try {
      const response = await fetch(`${API_BASE}/portfolio?user_id=${userId}`);
      const data = await response.json();
      
      if (data.success) {
        setPortfolio(data.portfolio);
      }
    } catch (error) {
      console.error('Error loading portfolio:', error);
    }
  };

  const addStock = async () => {
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
        setNewStock({ ticker: '', quantity: '', price: '' });
        loadPortfolio();
      }
    } catch (error) {
      console.error('Error adding stock:', error);
      alert('Lỗi khi thêm cổ phiếu');
    }
  };

  const removeStock = async (ticker) => {
    if (!confirm(`Xóa ${ticker} khỏi danh mục?`)) return;

    try {
      const response = await fetch(`${API_BASE}/portfolio/${ticker}?user_id=${userId}`, {
        method: 'DELETE'
      });

      const data = await response.json();
      
      if (data.success) {
        loadPortfolio();
      }
    } catch (error) {
      console.error('Error removing stock:', error);
    }
  };

  // ============================================================================
  // CHAT FUNCTIONS
  // ============================================================================

  const loadChatHistory = async () => {
    try {
      const response = await fetch(`${API_BASE}/chat/history?user_id=${userId}`);
      const data = await response.json();
      
      if (data.success && data.history.length > 0) {
        const formattedHistory = data.history.flatMap(item => [
          { text: item.message, sender: 'user' },
          { text: item.response, sender: 'ai' }
        ]);
        setMessages(formattedHistory);
      }
    } catch (error) {
      console.error('Error loading chat history:', error);
    }
  };

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = input;
    setInput('');
    setMessages(prev => [...prev, { text: userMessage, sender: 'user' }]);
    setIsLoading(true);

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
        setMessages(prev => [...prev, { text: data.response, sender: 'ai' }]);
        setHasGemini(data.hasGemini);
      } else {
        setMessages(prev => [...prev, { 
          text: 'Xin lỗi, đã có lỗi xảy ra. Vui lòng thử lại.', 
          sender: 'ai' 
        }]);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => [...prev, { 
        text: 'Lỗi kết nối. Vui lòng kiểm tra mạng và thử lại.', 
        sender: 'ai' 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const clearHistory = async () => {
    if (!confirm('Xóa toàn bộ lịch sử chat?')) return;

    try {
      const response = await fetch(`${API_BASE}/chat/history?user_id=${userId}`, {
        method: 'DELETE'
      });

      const data = await response.json();
      
      if (data.success) {
        setMessages([]);
      }
    } catch (error) {
      console.error('Error clearing history:', error);
    }
  };

  // ============================================================================
  // CALCULATIONS
  // ============================================================================

  const calculatePortfolioStats = () => {
    const totalValue = portfolio.reduce((sum, stock) => 
      sum + (stock.quantity * stock.avgPrice), 0
    );
    
    return {
      totalValue,
      stockCount: portfolio.length,
      totalShares: portfolio.reduce((sum, stock) => sum + stock.quantity, 0)
    };
  };

  const stats = calculatePortfolioStats();

  // ============================================================================
  // RENDER
  // ============================================================================

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* LEFT: PORTFOLIO */}
        <div className="space-y-6">
          {/* Header */}
          <div className="bg-gradient-to-r from-purple-600 to-blue-600 rounded-xl p-6 text-white">
            <h2 className="text-2xl font-bold mb-2 flex items-center gap-2">
              <BarChart3 className="w-6 h-6" />
              Danh Mục Đầu Tư
            </h2>
            <p className="opacity-90">Quản lý danh mục của bạn</p>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-white rounded-lg p-4 shadow">
              <div className="flex items-center gap-2 text-gray-600 text-sm mb-1">
                <DollarSign className="w-4 h-4" />
                Tổng giá trị
              </div>
              <div className="text-2xl font-bold text-gray-900">
                {stats.totalValue.toLocaleString('vi-VN')}
              </div>
            </div>
            
            <div className="bg-white rounded-lg p-4 shadow">
              <div className="flex items-center gap-2 text-gray-600 text-sm mb-1">
                <TrendingUp className="w-4 h-4" />
                Số mã
              </div>
              <div className="text-2xl font-bold text-gray-900">
                {stats.stockCount}
              </div>
            </div>
            
            <div className="bg-white rounded-lg p-4 shadow">
              <div className="flex items-center gap-2 text-gray-600 text-sm mb-1">
                <BarChart3 className="w-4 h-4" />
                Tổng CP
              </div>
              <div className="text-2xl font-bold text-gray-900">
                {stats.totalShares}
              </div>
            </div>
          </div>

          {/* Add Stock Form */}
          <div className="bg-white rounded-lg p-6 shadow">
            <h3 className="font-semibold mb-4 flex items-center gap-2">
              <Plus className="w-5 h-5" />
              Thêm Cổ Phiếu
            </h3>
            
            <div className="space-y-3">
              <input
                type="text"
                placeholder="Mã CP (VD: VCB)"
                value={newStock.ticker}
                onChange={(e) => setNewStock({...newStock, ticker: e.target.value.toUpperCase()})}
                className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
              
              <div className="grid grid-cols-2 gap-3">
                <input
                  type="number"
                  placeholder="Số lượng"
                  value={newStock.quantity}
                  onChange={(e) => setNewStock({...newStock, quantity: e.target.value})}
                  className="px-4 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
                
                <input
                  type="number"
                  placeholder="Giá (VND)"
                  value={newStock.price}
                  onChange={(e) => setNewStock({...newStock, price: e.target.value})}
                  className="px-4 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>
              
              <button
                onClick={addStock}
                className="w-full bg-gradient-to-r from-purple-600 to-blue-600 text-white py-2 rounded-lg hover:shadow-lg transition-all flex items-center justify-center gap-2"
              >
                <Plus className="w-5 h-5" />
                Thêm vào danh mục
              </button>
            </div>
          </div>

          {/* Portfolio List */}
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="p-4 bg-gray-50 border-b">
              <h3 className="font-semibold">Danh mục hiện tại</h3>
            </div>
            
            <div className="divide-y max-h-96 overflow-y-auto">
              {portfolio.length === 0 ? (
                <div className="p-8 text-center text-gray-500">
                  Chưa có cổ phiếu nào
                </div>
              ) : (
                portfolio.map((stock) => (
                  <div key={stock.ticker} className="p-4 hover:bg-gray-50 transition-colors">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-semibold text-lg">{stock.ticker}</div>
                        <div className="text-sm text-gray-600">
                          {stock.quantity} CP @ {stock.avgPrice.toLocaleString('vi-VN')} VND
                        </div>
                      </div>
                      
                      <div className="text-right">
                        <div className="font-semibold text-purple-600">
                          {(stock.quantity * stock.avgPrice).toLocaleString('vi-VN')} VND
                        </div>
                        <button
                          onClick={() => removeStock(stock.ticker)}
                          className="mt-1 text-red-500 hover:text-red-700 text-sm flex items-center gap-1"
                        >
                          <Trash2 className="w-4 h-4" />
                          Xóa
                        </button>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* RIGHT: AI CHAT */}
        <div className="space-y-6">
          {/* Header */}
          <div className="bg-gradient-to-r from-green-600 to-teal-600 rounded-xl p-6 text-white">
            <h2 className="text-2xl font-bold mb-2 flex items-center gap-2">
              <Sparkles className="w-6 h-6" />
              AI Advisor
              {hasGemini && <span className="text-xs bg-white/20 px-2 py-1 rounded">Powered by Gemini</span>}
            </h2>
            <p className="opacity-90">Tư vấn thông minh về danh mục</p>
          </div>

          {/* Chat Container */}
          <div className="bg-white rounded-lg shadow flex flex-col" style={{height: '600px'}}>
            {/* Chat Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.length === 0 ? (
                <div className="h-full flex items-center justify-center text-gray-500">
                  <div className="text-center">
                    <Sparkles className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                    <p>Hỏi AI Advisor về danh mục của bạn</p>
                    <p className="text-sm mt-2">VD: "Phân tích danh mục của tôi"</p>
                  </div>
                </div>
              ) : (
                messages.map((msg, idx) => (
                  <div
                    key={idx}
                    className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[80%] rounded-lg p-3 ${
                        msg.sender === 'user'
                          ? 'bg-purple-600 text-white'
                          : 'bg-gray-100 text-gray-900'
                      }`}
                    >
                      <div className="whitespace-pre-wrap">{msg.text}</div>
                    </div>
                  </div>
                ))
              )}
              
              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-gray-100 rounded-lg p-3">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={chatEndRef} />
            </div>

            {/* Input Area */}
            <div className="border-t p-4">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && !isLoading && sendMessage()}
                  placeholder="Hỏi AI về danh mục..."
                  disabled={isLoading}
                  className="flex-1 px-4 py-2 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent disabled:opacity-50"
                />
                
                <button
                  onClick={sendMessage}
                  disabled={isLoading || !input.trim()}
                  className="bg-gradient-to-r from-green-600 to-teal-600 text-white px-6 py-2 rounded-lg hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  <Send className="w-5 h-5" />
                  Gửi
                </button>
              </div>
              
              {messages.length > 0 && (
                <button
                  onClick={clearHistory}
                  className="mt-2 text-sm text-red-500 hover:text-red-700 flex items-center gap-1"
                >
                  <Trash2 className="w-4 h-4" />
                  Xóa lịch sử chat
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PortfolioManager;
