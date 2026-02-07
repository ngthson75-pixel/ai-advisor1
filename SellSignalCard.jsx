/**
 * SELL SIGNALS CARD LAYOUT
 * Mobile-responsive card view cho tín hiệu bán
 * Dùng thay table trên mobile
 */

import React from 'react';

const SellSignalCard = ({ signal }) => {
  // Format exit reason
  const getExitReasonDisplay = (strategy) => {
    const reasons = {
      'STOP_LOSS': {
        text: 'Cắt lỗ (SL)',
        icon: '🔴',
        bgColor: 'bg-red-50',
        textColor: 'text-red-700',
        borderColor: 'border-red-300'
      },
      'TAKE_PROFIT': {
        text: 'Chốt lời (TP)',
        icon: '🟢',
        bgColor: 'bg-green-50',
        textColor: 'text-green-700',
        borderColor: 'border-green-300'
      }
    };
    return reasons[strategy] || {
      text: 'Khác',
      icon: '⚪',
      bgColor: 'bg-gray-50',
      textColor: 'text-gray-700',
      borderColor: 'border-gray-300'
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

  const exitReason = getExitReasonDisplay(signal.strategy);
  const pl = calculatePL(signal.entry_price, signal.stop_loss);

  return (
    <div className={`
      bg-white rounded-lg shadow-md p-4 mb-4
      border-l-4 transition-all duration-200 hover:shadow-lg
      ${exitReason.bgColor === 'bg-red-50' ? 'border-red-500' : 'border-green-500'}
    `}>
      {/* Header */}
      <div className="flex justify-between items-start mb-3">
        <div>
          <h3 className="text-lg font-bold text-gray-900">{signal.ticker}</h3>
          <p className="text-sm text-gray-500">
            {new Date(signal.date).toLocaleDateString('vi-VN')}
          </p>
        </div>

        {/* Exit Reason Badge */}
        <span className={`
          inline-flex items-center px-3 py-1.5 rounded-full text-sm font-medium border
          ${exitReason.bgColor} ${exitReason.textColor} ${exitReason.borderColor}
        `}>
          <span className="mr-1">{exitReason.icon}</span>
          {exitReason.text}
        </span>
      </div>

      {/* Price Info */}
      <div className="grid grid-cols-2 gap-4 mb-3">
        <div className="bg-gray-50 rounded-lg p-3">
          <p className="text-xs text-gray-500 mb-1">Giá vào</p>
          <p className="text-base font-semibold text-gray-900">
            {signal.entry_price.toLocaleString('vi-VN')}
          </p>
          <p className="text-xs text-gray-400">VND</p>
        </div>
        <div className="bg-gray-50 rounded-lg p-3">
          <p className="text-xs text-gray-500 mb-1">Giá ra</p>
          <p className="text-base font-semibold text-gray-900">
            {signal.stop_loss ? signal.stop_loss.toLocaleString('vi-VN') : '-'}
          </p>
          <p className="text-xs text-gray-400">VND</p>
        </div>
      </div>

      {/* P/L Section */}
      {pl && (
        <div className={`
          p-3 rounded-lg border-2
          ${pl.isProfit ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}
        `}>
          <p className="text-xs text-gray-600 mb-1">Lãi/Lỗ</p>
          <div className="flex justify-between items-center">
            <p className={`text-xl font-bold ${pl.isProfit ? 'text-green-600' : 'text-red-600'}`}>
              {pl.isProfit ? '+' : ''}{pl.value.toLocaleString('vi-VN')} VND
            </p>
            <p className={`text-lg font-bold ${pl.isProfit ? 'text-green-600' : 'text-red-600'}`}>
              {pl.isProfit ? '+' : ''}{pl.percent}%
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

// Main component with responsive layout
const SellSignalsResponsive = ({ signals }) => {
  return (
    <div>
      {/* Desktop: Table view */}
      <div className="hidden md:block">
        <SellSignalsTable signals={signals} />
      </div>

      {/* Mobile: Card view */}
      <div className="block md:hidden">
        <div className="px-4 py-4 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-t-lg">
          <h2 className="text-xl font-bold">Tín hiệu BÁN</h2>
          <p className="text-blue-100 text-sm mt-1">
            {signals.length} tín hiệu
          </p>
        </div>
        
        <div className="p-4 bg-gray-50">
          {signals.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500">📊 Chưa có tín hiệu bán</p>
            </div>
          ) : (
            signals.map((signal, index) => (
              <SellSignalCard key={index} signal={signal} />
            ))
          )}
        </div>

        {/* Mobile Statistics */}
        <div className="px-4 py-4 bg-white border-t border-gray-200 rounded-b-lg">
          <div className="grid grid-cols-3 gap-2 text-center">
            <div>
              <div className="text-xl font-bold text-gray-900">{signals.length}</div>
              <div className="text-xs text-gray-500">Tổng</div>
            </div>
            <div>
              <div className="text-xl font-bold text-red-600">
                {signals.filter(s => s.strategy === 'STOP_LOSS').length}
              </div>
              <div className="text-xs text-gray-500">Cắt lỗ</div>
            </div>
            <div>
              <div className="text-xl font-bold text-green-600">
                {signals.filter(s => s.strategy === 'TAKE_PROFIT').length}
              </div>
              <div className="text-xs text-gray-500">Chốt lời</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export { SellSignalCard, SellSignalsResponsive };
export default SellSignalsResponsive;
