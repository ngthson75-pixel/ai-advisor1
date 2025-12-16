import Anthropic from '@anthropic-ai/sdk';
import type { NextApiRequest, NextApiResponse } from 'next';

const anthropic = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY,
});

// Mock stock data (trong production sẽ lấy từ VNDirect/SSI API)
const MOCK_STOCKS = [
  { code: 'MBB', price: 24000, volume: 12500000, change: -1.2, rsi: 45, macd: 'neutral' },
  { code: 'VNM', price: 85200, volume: 3200000, change: -0.8, rsi: 32, macd: 'bullish' },
  { code: 'HPG', price: 24500, volume: 18900000, change: 2.3, rsi: 58, macd: 'neutral' },
  { code: 'FPT', price: 128500, volume: 2100000, change: 5.8, rsi: 78, macd: 'bearish' },
  { code: 'VCB', price: 96200, volume: 5400000, change: -2.1, rsi: 42, macd: 'neutral' },
  { code: 'VIC', price: 42300, volume: 8700000, change: 1.5, rsi: 55, macd: 'bullish' },
];

interface SignalRequest {
  stockCode?: string;
  analysisType?: 'buy' | 'sell' | 'all';
}

interface SignalResponse {
  signals: any[];
  timestamp: string;
  error?: string;
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<SignalResponse>
) {
  if (req.method !== 'POST') {
    return res.status(405).json({ 
      signals: [], 
      timestamp: new Date().toISOString(),
      error: 'Method not allowed' 
    });
  }

  try {
    const { stockCode, analysisType = 'all' } = req.body as SignalRequest;

    // Filter stocks to analyze
    const stocksToAnalyze = stockCode 
      ? MOCK_STOCKS.filter(s => s.code === stockCode)
      : MOCK_STOCKS;

    // Analyze each stock with Claude AI
    const signals = await Promise.all(
      stocksToAnalyze.map(async (stock) => {
        const prompt = `Bạn là chuyên gia phân tích chứng khoán Việt Nam. Hãy phân tích cổ phiếu ${stock.code} với dữ liệu sau:

Giá hiện tại: ${stock.price.toLocaleString('vi-VN')} VND
Volume: ${stock.volume.toLocaleString('vi-VN')}
Biến động: ${stock.change}%
RSI: ${stock.rsi}
MACD: ${stock.macd}

Hãy đưa ra:
1. TÍN HIỆU: MUA/BÁN/GIỮ
2. SCORE: 0-100 (độ mạnh của tín hiệu)
3. XÁC SUẤT THÀNH CÔNG: %
4. PHÂN TÍCH CHI TIẾT: Giải thích lý do (2-3 câu)
5. STOP LOSS: Giá nên cắt lỗ
6. TAKE PROFIT: Giá nên chốt lời
7. MAX DRAWDOWN: % có thể chấp nhận

Trả lời theo format JSON:
{
  "signal": "MUA/BÁN/GIỮ",
  "signalType": "Day Trade/Swing T+/Position",
  "score": 70,
  "probability": 75,
  "analysis": "Giải thích chi tiết...",
  "entryPrice": ${stock.price},
  "stopLoss": giá,
  "takeProfit": giá,
  "maxDrawdown": 10,
  "positionSize": 10
}`;

        try {
          const message = await anthropic.messages.create({
            model: 'claude-sonnet-4-20250514',
            max_tokens: 1000,
            messages: [{
              role: 'user',
              content: prompt
            }]
          });

          // Extract JSON from Claude's response
          const content = message.content[0];
          if (content.type === 'text') {
            // Try to extract JSON from the response
            const jsonMatch = content.text.match(/\{[\s\S]*\}/);
            if (jsonMatch) {
              const aiResponse = JSON.parse(jsonMatch[0]);
              
              return {
                stockCode: stock.code,
                currentPrice: stock.price,
                signal: aiResponse.signal || 'GIỮ',
                signalType: aiResponse.signalType || 'Swing T+',
                score: aiResponse.score || 50,
                probability: aiResponse.probability || 50,
                analysis: aiResponse.analysis || 'Đang phân tích...',
                entryPrice: aiResponse.entryPrice || stock.price,
                stopLoss: aiResponse.stopLoss || Math.round(stock.price * 0.95),
                takeProfit: aiResponse.takeProfit || Math.round(stock.price * 1.08),
                maxDrawdown: aiResponse.maxDrawdown || 10,
                positionSize: aiResponse.positionSize || 10,
                timestamp: new Date().toISOString(),
                rsi: stock.rsi,
                macd: stock.macd,
                volume: stock.volume,
                change: stock.change
              };
            }
          }

          // Fallback if AI response parsing fails
          return generateFallbackSignal(stock);
        } catch (aiError) {
          console.error(`AI Error for ${stock.code}:`, aiError);
          return generateFallbackSignal(stock);
        }
      })
    );

    // Filter by analysis type
    const filteredSignals = analysisType === 'all' 
      ? signals 
      : signals.filter(s => {
          if (analysisType === 'buy') return s.signal === 'MUA';
          if (analysisType === 'sell') return s.signal === 'BÁN';
          return true;
        });

    res.status(200).json({
      signals: filteredSignals,
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('API Error:', error);
    res.status(500).json({
      signals: [],
      timestamp: new Date().toISOString(),
      error: 'Internal server error'
    });
  }
}

// Fallback signal generation nếu AI fails
function generateFallbackSignal(stock: any) {
  let signal = 'GIỮ';
  let signalType = 'Swing T+';
  let score = 50;
  let probability = 50;
  let analysis = '';

  // Simple rule-based logic
  if (stock.rsi < 35 && stock.macd === 'bullish') {
    signal = 'MUA';
    signalType = 'Swing T+';
    score = 70 + Math.floor(Math.random() * 15);
    probability = 70 + Math.floor(Math.random() * 15);
    analysis = `RSI đang ở vùng oversold (${stock.rsi}), MACD cho tín hiệu tích cực. Có thể xem xét mua vào vùng giá hiện tại.`;
  } else if (stock.rsi > 70 && stock.change > 5) {
    signal = 'BÁN';
    signalType = 'Take Profit';
    score = 75 + Math.floor(Math.random() * 15);
    probability = 75 + Math.floor(Math.random() * 15);
    analysis = `RSI đang ở vùng overbought (${stock.rsi}), cổ phiếu đã tăng ${stock.change}%. Nên chốt lời một phần.`;
  } else {
    analysis = `Cổ phiếu đang trong xu hướng trung tính. RSI ${stock.rsi}, ${stock.macd} trend. Chờ tín hiệu rõ ràng hơn.`;
  }

  return {
    stockCode: stock.code,
    currentPrice: stock.price,
    signal,
    signalType,
    score,
    probability,
    analysis,
    entryPrice: stock.price,
    stopLoss: Math.round(stock.price * 0.95),
    takeProfit: Math.round(stock.price * 1.08),
    maxDrawdown: 10,
    positionSize: 10,
    timestamp: new Date().toISOString(),
    rsi: stock.rsi,
    macd: stock.macd,
    volume: stock.volume,
    change: stock.change
  };
}
