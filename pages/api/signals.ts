import type { NextApiRequest, NextApiResponse } from 'next';
import { GoogleGenerativeAI } from '@google/generative-ai';

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY || '');

interface StockData {
  code: string;
  price: number;
  rsi: number;
  macd: number;
  volume: number;
}

const MOCK_STOCKS: StockData[] = [
  { code: 'MBB', price: 28500, rsi: 42, macd: 1.2, volume: 8500000 },
  { code: 'VNM', price: 85200, rsi: 32, macd: -0.8, volume: 1200000 },
  { code: 'HPG', price: 24500, rsi: 55, macd: 2.3, volume: 18900000 },
  { code: 'FPT', price: 132000, rsi: 68, macd: 3.5, volume: 2100000 },
  { code: 'VCB', price: 108500, rsi: 38, macd: -1.2, volume: 3200000 },
  { code: 'VIC', price: 42300, rsi: 48, macd: 0.7, volume: 8700000 }
];

async function analyzeWithGemini(stock: StockData): Promise<any> {
  try {
    const model = genAI.getGenerativeModel({ model: 'gemini-2.0-flash-exp' });
    
    const prompt = `Bạn là chuyên gia phân tích chứng khoán Việt Nam. Phân tích cổ phiếu sau:

Mã: ${stock.code}
Giá hiện tại: ${stock.price.toLocaleString()} VND
RSI: ${stock.rsi}
MACD: ${stock.macd}
Khối lượng: ${stock.volume.toLocaleString()}

Hãy đưa ra:
1. Tín hiệu: MUA hoặc BÁN
2. Loại tín hiệu: SWING T+ (giữ 3-5 ngày) hoặc INTRADAY (trong ngày)
3. Score từ 0-100
4. Xác suất thành công (%)
5. Giá vào lệnh đề xuất
6. Stop loss
7. Take profit
8. Tỷ lệ vốn nên đặt (%)
9. Max drawdown dự kiến (%)
10. Phân tích ngắn gọn (2-3 câu)

Trả về JSON format:
{
  "signal": "MUA" hoặc "BÁN",
  "signalType": "SWING T+" hoặc "INTRADAY",
  "score": number,
  "probability": number,
  "entryPrice": number,
  "stopLoss": number,
  "takeProfit": number,
  "positionSize": number,
  "maxDrawdown": number,
  "analysis": "string"
}`;

    const result = await model.generateContent(prompt);
    const response = result.response;
    const text = response.text();
    
    const jsonMatch = text.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      const analysis = JSON.parse(jsonMatch[0]);
      return {
        stockCode: stock.code,
        currentPrice: stock.price,
        signal: analysis.signal,
        signalType: analysis.signalType,
        score: analysis.score,
        probability: analysis.probability,
        analysis: analysis.analysis,
        entryPrice: analysis.entryPrice,
        stopLoss: analysis.stopLoss,
        takeProfit: analysis.takeProfit,
        positionSize: analysis.positionSize,
        maxDrawdown: analysis.maxDrawdown,
        timestamp: new Date().toISOString()
      };
    }
    
    throw new Error('Could not parse AI response');
    
  } catch (error) {
    console.error('Gemini API error:', error);
    return getRuleBasedSignal(stock);
  }
}

function getRuleBasedSignal(stock: StockData) {
  const isBuy = stock.rsi < 45 && stock.macd > 0;
  const isSell = stock.rsi > 65 || stock.macd < -1;
  
  const signal = isBuy ? 'MUA' : isSell ? 'BÁN' : 'GIỮ';
  const score = isBuy ? 72 : isSell ? 68 : 50;
  const probability = isBuy ? 68 : isSell ? 65 : 50;
  
  let analysis = '';
  if (isBuy) {
    analysis = `${stock.code} đang có tín hiệu hồn hợp nhưng nghiêng về tích cực với RSI ${stock.rsi} cho thấy cổ phiếu đã oversold và có khả năng phục hồi. MACD bullish xác nhận động lực tăng đang hình thành.`;
  } else {
    analysis = `${stock.code} cho tín hiệu tích cực với MACD bullish và RSI ${stock.rsi} ở vùng trung tính. Volume ${(stock.volume / 1000000).toFixed(1)} triệu cho thấy thanh khoản tốt.`;
  }
  
  return {
    stockCode: stock.code,
    currentPrice: stock.price,
    signal: signal,
    signalType: 'SWING T+',
    score: score,
    probability: probability,
    analysis: analysis,
    entryPrice: Math.round(stock.price * (isBuy ? 1.01 : 0.99)),
    stopLoss: Math.round(stock.price * (isBuy ? 0.95 : 1.05)),
    takeProfit: Math.round(stock.price * (isBuy ? 1.08 : 0.92)),
    positionSize: 15,
    maxDrawdown: isBuy ? 5 : 8,
    timestamp: new Date().toISOString()
  };
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const signals = await Promise.all(
      MOCK_STOCKS.map(stock => analyzeWithGemini(stock))
    );

    res.status(200).json({
      success: true,
      signals: signals,
      aiProvider: 'Google Gemini 2.0 Flash',
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('API Error:', error);
    res.status(500).json({ 
      error: 'Internal server error'
    });
  }
}
