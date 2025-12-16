import Anthropic from '@anthropic-ai/sdk';
import type { NextApiRequest, NextApiResponse } from 'next';

const anthropic = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY,
});

interface DisciplineRequest {
  userMessage?: string;
  userBehavior?: {
    chasedBuys: number;
    panicSells: number;
    disciplineScore: number;
  };
}

interface DisciplineResponse {
  emotionDetected: string;
  emotionScore: number;
  intervention: boolean;
  message: string;
  advice: string[];
  behaviorInsights?: {
    chasedBuys: number;
    panicSells: number;
    disciplineScore: number;
    trend: string;
  };
  timestamp: string;
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<DisciplineResponse | { error: string }>
) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { userMessage, userBehavior } = req.body as DisciplineRequest;

    if (userMessage) {
      // Emotion detection and coaching
      const prompt = `Bạn là AI Discipline Coach giúp nhà đầu tư duy trì kỷ luật. Phân tích câu hỏi/tâm trạng của user:

"${userMessage}"

Hãy:
1. NHẬN DIỆN CẢM XÚC: (Calm/Excited/FOMO/Fear/Panic)
2. ĐIỂM CẢM XÚC: 0-100 (0=rất bình tĩnh, 100=hoảng loạn)
3. CẦN CAN THIỆP: true/false (nếu user đang định làm điều sai)
4. PHẢN HỒI: Câu trả lời empathetic nhưng firm (2-3 câu)
5. LỜI KHUYÊN: 3-4 bullet points cụ thể

Trả lời JSON:
{
  "emotionDetected": "Panic",
  "emotionScore": 85,
  "intervention": true,
  "message": "Tôi hiểu bạn đang lo lắng...",
  "advice": [
    "Không nên bán trong tâm trạng hoảng loạn",
    "Hãy đợi 24h trước khi quyết định"
  ]
}`;

      const message = await anthropic.messages.create({
        model: 'claude-sonnet-4-20250514',
        max_tokens: 1000,
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
            behaviorInsights: userBehavior,
            timestamp: new Date().toISOString()
          });
        }
      }
    }

    // Default behavior analysis response
    if (userBehavior) {
      return res.status(200).json(generateBehaviorAnalysis(userBehavior));
    }

    // Fallback
    res.status(200).json({
      emotionDetected: 'Calm',
      emotionScore: 30,
      intervention: false,
      message: 'Hãy cho tôi biết bạn đang cảm thấy như thế nào hoặc có câu hỏi gì về đầu tư.',
      advice: [
        'Duy trì kỷ luật giao dịch',
        'Tuân thủ stop-loss',
        'Không giao dịch khi cảm xúc'
      ],
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('Discipline Coach Error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
}

function generateBehaviorAnalysis(behavior: any): DisciplineResponse {
  const { chasedBuys, panicSells, disciplineScore } = behavior;

  let intervention = false;
  let message = '';
  let advice = [];
  let trend = 'Ổn định';

  if (chasedBuys > 5) {
    intervention = true;
    trend = 'Cần cải thiện';
    message = `Bạn đã mua đuổi ${chasedBuys} lần trong tháng qua. Đây là hành vi phổ biến dẫn đến thua lỗ. Hãy kiên nhẫn chờ giá pullback trước khi vào lệnh.`;
    advice = [
      '❌ Không mua khi cổ phiếu đã tăng >5% trong ngày',
      '⏰ Chờ giá về vùng hỗ trợ hoặc pullback',
      '📊 Chỉ mua khi có breakout xác nhận với volume lớn',
      '🎯 Set price alert thay vì monitor liên tục (giảm FOMO)'
    ];
  } else if (panicSells > 3) {
    intervention = true;
    trend = 'Cần cải thiện';
    message = `Bạn đã bán hoảng loạn ${panicSells} lần. Điều này cho thấy bạn giao dịch dựa trên cảm xúc chứ không phải chiến lược. Hãy set stop-loss tự động để tránh quyết định cảm xúc.`;
    advice = [
      '🤖 Set stop-loss tự động NGAY sau khi mua',
      '⏸️ Không check portfolio quá thường xuyên (1-2 lần/ngày là đủ)',
      '🧘 Nếu cảm thấy hoảng loạn, tạm dừng 24h trước khi quyết định',
      '📝 Viết lý do MUA và cam kết tuân thủ stop-loss'
    ];
  } else if (disciplineScore >= 80) {
    trend = 'Xuất sắc';
    message = `Chúc mừng! Điểm kỷ luật ${disciplineScore}/100 là rất tốt. Bạn đang giao dịch một cách có hệ thống. Hãy tiếp tục duy trì!`;
    advice = [
      '✅ Tiếp tục tuân thủ kế hoạch giao dịch',
      '📈 Consider tăng position size nhẹ khi có setup A+',
      '📚 Document các trade tốt để replicate',
      '🎓 Có thể thử các strategy nâng cao'
    ];
  } else {
    message = `Điểm kỷ luật ${disciplineScore}/100 đang ở mức trung bình. Bạn có đủ nền tảng, chỉ cần cải thiện thêm tính kiên nhẫn và tuân thủ.`;
    advice = [
      '📝 Viết rõ kế hoạch TRƯỚC KHI mua/bán',
      '⏰ Đặt rule: Không được trade trong 1h đầu phiên',
      '💰 Limit số lượng giao dịch: max 3 trades/tuần',
      '🔍 Review lại mọi trade cuối tuần'
    ];
  }

  return {
    emotionDetected: 'Analyzed',
    emotionScore: 50,
    intervention,
    message,
    advice,
    behaviorInsights: {
      chasedBuys,
      panicSells,
      disciplineScore,
      trend
    },
    timestamp: new Date().toISOString()
  };
}
