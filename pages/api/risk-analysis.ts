import Anthropic from '@anthropic-ai/sdk';
import type { NextApiRequest, NextApiResponse } from 'next';

const anthropic = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY,
});

interface RiskAnalysisResponse {
  marketSentiment: string;
  fearIndex: number;
  stopTradingMode: boolean;
  alerts: Array<{
    type: 'warning' | 'danger' | 'info';
    title: string;
    message: string;
  }>;
  explanation: string;
  recommendations: string[];
  timestamp: string;
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<RiskAnalysisResponse | { error: string }>
) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    // Mock market data (trong production lấy từ real API)
    const marketData = {
      vnIndex: 1250.5,
      vnIndexChange: -2.8,
      foreignFlow: -580, // billion VND
      volumeChange: 45, // % increase
      volatilityIndex: 24,
    };

    const prompt = `Bạn là chuyên gia rủi ro thị trường chứng khoán Việt Nam. Phân tích tình hình thị trường:

VN-Index: ${marketData.vnIndex} (${marketData.vnIndexChange}%)
Khối ngoại: ${marketData.foreignFlow} tỷ VND
Volume thay đổi: +${marketData.volumeChange}%
Volatility Index: ${marketData.volatilityIndex}

Hãy đánh giá:
1. TÂM LÝ THỊ TRƯỜNG: (Euphoric/Optimistic/Neutral/Fearful/Panic)
2. FEAR INDEX: 0-100 (0=cực kỳ lạc quan, 100=hoảng loạn)
3. CÓ NÊN STOP TRADING: true/false
4. CẢNH BÁO: Các rủi ro cần lưu ý
5. GIẢI THÍCH: Tại sao thị trường như vậy (3-4 câu)
6. KHUYẾN NGHỊ: 3-4 hành động cụ thể

Trả lời JSON format:
{
  "marketSentiment": "Panic",
  "fearIndex": 72,
  "stopTradingMode": true,
  "alerts": [
    {
      "type": "danger",
      "title": "Thị trường rơi mạnh",
      "message": "VN-Index giảm 2.8%..."
    }
  ],
  "explanation": "Giải thích chi tiết...",
  "recommendations": ["Khuyến nghị 1", "Khuyến nghị 2"]
}`;

    const message = await anthropic.messages.create({
      model: 'claude-sonnet-4-20250514',
      max_tokens: 1500,
      messages: [{
        role: 'user',
        content: prompt
      }]
    });

    const content = message.content[0];
    if (content.type === 'text') {
      const jsonMatch = content.text.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        const aiResponse = JSON.parse(jsonMatch[0]);
        
        return res.status(200).json({
          ...aiResponse,
          timestamp: new Date().toISOString()
        });
      }
    }

    // Fallback response
    res.status(200).json(generateFallbackRiskAnalysis(marketData));

  } catch (error) {
    console.error('Risk Analysis Error:', error);
    
    // Return fallback on error
    res.status(200).json(generateFallbackRiskAnalysis({
      vnIndex: 1250.5,
      vnIndexChange: -2.8,
      foreignFlow: -580,
      volumeChange: 45,
      volatilityIndex: 24,
    }));
  }
}

function generateFallbackRiskAnalysis(marketData: any): RiskAnalysisResponse {
  const isMarketDown = marketData.vnIndexChange < -2;
  const isForeignSelling = marketData.foreignFlow < -400;
  const isHighVolatility = marketData.volatilityIndex > 20;

  let fearIndex = 50;
  let marketSentiment = 'Neutral';
  let stopTradingMode = false;

  if (isMarketDown && isForeignSelling) {
    fearIndex = 75;
    marketSentiment = 'Panic';
    stopTradingMode = true;
  } else if (isMarketDown) {
    fearIndex = 60;
    marketSentiment = 'Fearful';
  }

  const alerts = [];
  
  if (isMarketDown) {
    alerts.push({
      type: 'danger' as const,
      title: '🚨 Thị trường rơi mạnh',
      message: `VN-Index giảm ${Math.abs(marketData.vnIndexChange)}% trong phiên. Volume tăng ${marketData.volumeChange}% cho thấy áp lực bán mạnh.`
    });
  }

  if (isForeignSelling) {
    alerts.push({
      type: 'warning' as const,
      title: '⚠️ Khối ngoại bán ròng',
      message: `Khối ngoại bán ròng ${Math.abs(marketData.foreignFlow)} tỷ VND. Áp lực từ dòng tiền institutional.`
    });
  }

  if (isHighVolatility) {
    alerts.push({
      type: 'info' as const,
      title: '📊 Volatility cao',
      message: `Volatility Index ở mức ${marketData.volatilityIndex}, cao hơn mức trung bình. Thị trường không ổn định.`
    });
  }

  const explanation = stopTradingMode
    ? `Thị trường đang trong giai đoạn panic selling với VN-Index giảm ${Math.abs(marketData.vnIndexChange)}% và khối ngoại bán mạnh. Volume tăng đột biến ${marketData.volumeChange}% cho thấy nhiều nhà đầu tư đang tháo chạy. Đây là lúc dễ đưa ra quyết định sai lầm nhất do cảm xúc chi phối.`
    : `Thị trường có biến động nhưng chưa ở mức báo động. Cần theo dõi thêm tín hiệu trong 1-2 phiên tới để đánh giá xu hướng rõ hơn.`;

  const recommendations = stopTradingMode
    ? [
        '❌ KHÔNG mua thêm cổ phiếu trong 1-2 phiên tới',
        '💰 Giữ cash position cao (>30%) để đợi cơ hội tốt hơn',
        '🛡️ Review lại stop-loss cho các vị thế hiện tại',
        '🧘 Tránh ra quyết định dựa trên cảm xúc hoảng loạn'
      ]
    : [
        '👀 Theo dõi sát diễn biến trong 1-2 phiên',
        '📊 Chỉ trade các setup có xác suất cao',
        '⚖️ Giảm position size xuống 50% bình thường',
        '✅ Đảm bảo mọi vị thế đều có stop-loss'
      ];

  return {
    marketSentiment,
    fearIndex,
    stopTradingMode,
    alerts,
    explanation,
    recommendations,
    timestamp: new Date().toISOString()
  };
}
