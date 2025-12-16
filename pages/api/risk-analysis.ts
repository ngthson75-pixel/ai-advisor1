import type { NextApiRequest, NextApiResponse } from 'next';
import { GoogleGenerativeAI } from '@google/generative-ai';

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY || '');

const MOCK_MARKET_DATA = {
  vnIndex: 1265.42,
  change: -12.35,
  changePercent: -0.97,
  foreignNetValue: -850000000,
  volatility: 1.8,
  advanceDecline: { advance: 145, decline: 298, unchanged: 89 }
};

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  try {
    const model = genAI.getGenerativeModel({ model: 'gemini-2.0-flash-exp' });
    
    const prompt = `Bạn là chuyên gia phân tích rủi ro thị trường chứng khoán Việt Nam.

Dữ liệu thị trường hiện tại:
- VN-Index: ${MOCK_MARKET_DATA.vnIndex} (${MOCK_MARKET_DATA.changePercent}%)
- Khối ngoại bán ròng: ${(MOCK_MARKET_DATA.foreignNetValue / 1000000).toFixed(0)} triệu VND
- Volatility: ${MOCK_MARKET_DATA.volatility}%
- Tăng/Giảm: ${MOCK_MARKET_DATA.advanceDecline.advance}/${MOCK_MARKET_DATA.advanceDecline.decline}

Phân tích:
1. Tâm lý thị trường: Panic/Fear/Neutral/Optimistic/Euphoric
2. Fear Index (0-100)
3. Có nên kích hoạt STOP TRADING MODE không? (true/false)
4. 2-3 cảnh báo quan trọng
5. Giải thích chi tiết (3-4 câu)
6. 3-4 khuyến nghị hành động

Trả về JSON:
{
  "marketSentiment": "string",
  "fearIndex": number,
  "stopTradingMode": boolean,
  "alerts": [{"type": "danger/warning", "title": "string", "message": "string"}],
  "explanation": "string",
  "recommendations": ["string"]
}`;

    const result = await model.generateContent(prompt);
    const text = result.response.text();
    
    const jsonMatch = text.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      const analysis = JSON.parse(jsonMatch[0]);
      return res.status(200).json(analysis);
    }
    
    throw new Error('Could not parse response');
    
  } catch (error) {
    console.error('Gemini error:', error);
    
    // Fallback
    return res.status(200).json({
      marketSentiment: 'Fear',
      fearIndex: 68,
      stopTradingMode: false,
      alerts: [
        {
          type: 'warning',
          title: 'Khối ngoại bán ròng mạnh',
          message: 'Khối ngoại đã bán ròng 850 tỷ VND trong phiên, cho thấy tâm lý thận trọng.'
        },
        {
          type: 'warning',
          title: 'Áp lực bán tăng',
          message: '298 mã giảm so với 145 mã tăng, thị trường đang trong xu hướng giảm điểm.'
        }
      ],
      explanation: 'Thị trường đang trong giai đoạn điều chỉnh với VN-Index giảm 0.97%. Tỷ lệ cổ phiếu giảm/tăng là 298/145 cho thấy áp lực bán đang cao. Khối ngoại tiếp tục bán ròng 850 tỷ là dấu hiệu cần thận trọng.',
      recommendations: [
        'Giảm tỷ trọng cổ phiếu xuống 60-70% danh mục',
        'Tập trung vào cổ phiếu bluechip có thanh khoản tốt',
        'Đặt lệnh stop loss chặt chẽ ở mức -3% đến -5%',
        'Tránh mua đuổi, chờ tín hiệu phục hồi rõ ràng hơn'
      ]
    });
  }
}
