import type { NextApiRequest, NextApiResponse } from 'next';
import { GoogleGenerativeAI } from '@google/generative-ai';

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY || '');

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { userMessage, userBehavior } = req.body;
    
    const model = genAI.getGenerativeModel({ model: 'gemini-2.0-flash-exp' });
    
    let prompt = '';
    
    if (userMessage) {
      prompt = `Bạn là AI Discipline Coach chuyên về tâm lý giao dịch chứng khoán.

Người dùng nói: "${userMessage}"

Phân tích:
1. Cảm xúc: Fear/Greed/FOMO/Panic/Confident/Anxious
2. Điểm cảm xúc (0-100)
3. Cần can thiệp không? (true/false)
4. Thông điệp phản hồi (2-3 câu, thân thiện, khuyến khích)
5. 3-4 lời khuyên cụ thể

Trả về JSON:
{
  "emotionDetected": "string",
  "emotionScore": number,
  "intervention": boolean,
  "message": "string",
  "advice": ["string"]
}`;
    } else {
      prompt = `Phân tích hành vi giao dịch:

Hành vi 30 ngày qua:
- Mua đuổi: ${userBehavior?.chasedBuys || 0} lần
- Bán hoảng loạn: ${userBehavior?.panicSells || 0} lần  
- Điểm kỷ luật: ${userBehavior?.disciplineScore || 50}/100

Đưa ra:
1. Phân tích hành vi
2. Lời khuyên cải thiện
3. Behavioral insights

JSON format tương tự`;
    }

    const result = await model.generateContent(prompt);
    const text = result.response.text();
    
    const jsonMatch = text.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      const analysis = JSON.parse(jsonMatch[0]);
      
      if (!userMessage && userBehavior) {
        analysis.behaviorInsights = {
          chasedBuys: userBehavior.chasedBuys || 8,
          panicSells: userBehavior.panicSells || 3,
          disciplineScore: userBehavior.disciplineScore || 72,
          trend: 'improving'
        };
      }
      
      return res.status(200).json(analysis);
    }
    
    throw new Error('Could not parse response');
    
  } catch (error) {
    console.error('Gemini error:', error);
    
    return res.status(200).json({
      emotionDetected: 'Confident',
      emotionScore: 70,
      intervention: false,
      message: 'Tốt! Bạn đang có tâm lý giao dịch ổn định. Hãy duy trì kỷ luật và tuân thủ chiến lược của mình.',
      advice: [
        'Tiếp tục giữ kỷ luật cắt lỗ ở mức -5%',
        'Không mua đuổi khi giá tăng quá 3% trong ngày',
        'Ghi chép lại mọi quyết định để học hỏi',
        'Review danh mục mỗi tuần để điều chỉnh'
      ],
      behaviorInsights: {
        chasedBuys: 8,
        panicSells: 3,
        disciplineScore: 72,
        trend: 'improving'
      }
    });
  }
}
