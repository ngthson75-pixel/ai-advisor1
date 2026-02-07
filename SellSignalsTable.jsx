/**
 * SELL SIGNALS TABLE COMPONENT
 * Hiển thị tín hiệu bán với column "Lý do bán" rõ ràng
 * 
 * Features:
 * - 🟢 Chốt lời (Take Profit) - Màu xanh
 * - 🔴 Cắt lỗ (Stop Loss) - Màu đỏ
 * - Tính P/L tự động
 * - Responsive design
 */

import React, { useState, useEffect } from 'react';

const SellSignalsTable = () => {
  const [signals, setSignals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch SELL signals from API
  useEffect(() => {
    fetchSellSignals();
  }, []);

  const fetchSellSignals = async () => {
    try {
      setLoading(true);
      const response = await fetch('https://ai-advisor1-backend.onrender.com/api/signals?action=SELL');
      
      if (!response.ok) {
        throw new Error('Failed to fetch signals');
      }

      const data = await response.json();
      setSignals(data.signals || []);
      setError(null);
    } catch (err) {
      console.error('Error fetching sell signals:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Format exit reason với icon và màu sắc
  const getExitReasonDisplay = (strategy) => {
    const reasons = {
      'STOP_LOSS': {
        text: 'Cắt lỗ (SL)',
        icon: '🔴',
        bgColor: 'bg-red-50',
        textColor: 'text-red-700',
        borderColor: 'border-red-200'
      },
      'TAKE_PROFIT': {
        text: 'Chốt lời (TP)',
        icon: '🟢',
        bgColor: 'bg-green-50',
        textColor: 'text-green-700',
        borderColor: 'border-green-200'
      },
      'MA20_BREAK': {
        text: 'Phá MA20',
        icon: '🟡',
        bgColor: 'bg-yellow-50',
        textColor: 'text-yellow-700',
        borderColor: 'border-yellow-200'
      }
    };

    return reasons[strategy] || {
      text: 'Khác',
      icon: '⚪',
      bgColor: 'bg-gray-50',
      textColor: 'text-gray-700',
      borderColor: 'border-gray-200'
    };
  };

  // Calculate P/L
  const calculatePL = (entryPrice, exitPrice) => {
    if (!exitPrice) return null;
    
    const pl = exitPrice - entryPrice;
    const plPercent = ((pl / entryPrice) * 100).toFixed(2);
    
    return {
      value: pl,
      percent: plPercent,
      isProfit: pl >= 0
    };
  };

  // Format currency
  const formatCurrency = (value) => {
    return new Intl.NumberFormat('vi-VN', {
      style: 'decimal',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  // Format date
  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    return new Intl.DateTimeFormat('vi-VN', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    }).format(date);
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
        ❌ Lỗi tải dữ liệu: {error}
      </div>
    );
  }

  if (signals.length === 0) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
        <p className="text-gray-500 text-lg">📊 Chưa có tín hiệu bán</p>
        <p className="text-gray-400 text-sm mt-2">
          Tín hiệu bán sẽ xuất hiện khi cổ phiếu chạm Stop Loss hoặc Take Profit
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 bg-gradient-to-r from-blue-500 to-blue-600 text-white">
        <h2 className="text-xl font-bold">Tín hiệu BÁN</h2>
        <p className="text-blue-100 text-sm mt-1">
          {signals.length} tín hiệu • Cập nhật: {formatDate(new Date())}
        </p>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Mã CP
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Giá vào
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Giá ra
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Lãi/Lỗ
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Lý do bán
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Ngày
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {signals.map((signal, index) => {
              const exitReason = getExitReasonDisplay(signal.strategy);
              const pl = calculatePL(signal.entry_price, signal.stop_loss); // Temporary: using SL as exit
              
              return (
                <tr 
                  key={index} 
                  className="hover:bg-gray-50 transition-colors duration-150"
                >
                  {/* Ticker */}
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="text-sm font-bold text-gray-900">
                        {signal.ticker}
                      </div>
                    </div>
                  </td>

                  {/* Entry Price */}
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      {formatCurrency(signal.entry_price)}
                    </div>
                    <div className="text-xs text-gray-500">VND</div>
                  </td>

                  {/* Exit Price */}
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-semibold text-gray-900">
                      {signal.stop_loss ? formatCurrency(signal.stop_loss) : '-'}
                    </div>
                    <div className="text-xs text-gray-500">VND</div>
                  </td>

                  {/* P/L */}
                  <td className="px-6 py-4 whitespace-nowrap">
                    {pl ? (
                      <div>
                        <div className={`text-sm font-bold ${pl.isProfit ? 'text-green-600' : 'text-red-600'}`}>
                          {pl.isProfit ? '+' : ''}{formatCurrency(pl.value)}
                        </div>
                        <div className={`text-xs font-semibold ${pl.isProfit ? 'text-green-500' : 'text-red-500'}`}>
                          ({pl.isProfit ? '+' : ''}{pl.percent}%)
                        </div>
                      </div>
                    ) : (
                      <div className="text-sm text-gray-400">-</div>
                    )}
                  </td>

                  {/* Exit Reason - MAIN COLUMN */}
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`
                      inline-flex items-center px-3 py-1.5 rounded-full text-sm font-medium border
                      ${exitReason.bgColor} ${exitReason.textColor} ${exitReason.borderColor}
                    `}>
                      <span className="mr-1.5 text-base">{exitReason.icon}</span>
                      {exitReason.text}
                    </span>
                  </td>

                  {/* Date */}
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-500">
                      {formatDate(signal.date)}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Footer Statistics */}
      <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <div className="text-2xl font-bold text-gray-900">{signals.length}</div>
            <div className="text-xs text-gray-500">Tổng tín hiệu</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-red-600">
              {signals.filter(s => s.strategy === 'STOP_LOSS').length}
            </div>
            <div className="text-xs text-gray-500">Cắt lỗ</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-green-600">
              {signals.filter(s => s.strategy === 'TAKE_PROFIT').length}
            </div>
            <div className="text-xs text-gray-500">Chốt lời</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SellSignalsTable;
