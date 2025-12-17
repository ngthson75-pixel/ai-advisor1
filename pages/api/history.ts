import type { NextApiRequest, NextApiResponse } from 'next';
import { execSync } from 'child_process';
import path from 'path';

interface HoldingStock {
  buyDate: string;
  code: string;
  signalType: string;
  score: number;
  buyPrice: number;
  sellDate?: string;
  sellPrice?: number;
  currentPrice?: number;
  profitPercent: number;  // Always required now
  holdDays?: number;
  status: 'holding' | 'closed';
}

// Mock current prices (sẽ fetch từ VNStock trong production)
const MOCK_CURRENT_PRICES: Record<string, number> = {
  'HAG': 18032,   // -2.0% từ 18400
  'BMP': 173250,  // +5.0% từ 165000
  'VNM': 63342,   // +3.5% từ 61200
};

async function fetchCurrentPrice(code: string): Promise<number | null> {
  try {
    // Try VNStock first
    const scriptPath = path.join(process.cwd(), 'scripts', 'fetch_vnstock.py');
    const result = execSync(`python3 ${scriptPath}`, {
      timeout: 5000,
      encoding: 'utf-8'
    });
    
    const data = JSON.parse(result);
    
    if (data.success && data.data) {
      const stock = data.data.find((s: any) => s.code === code);
      if (stock) {
        return stock.price;
      }
    }
    
    return null;
  } catch (error) {
    console.error(`Error fetching ${code}:`, error);
    return null;
  }
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    // Load history data
    const history: HoldingStock[] = [
      {
        buyDate: '01/12/2025',
        code: 'SAB',
        signalType: 'Swing T+',
        score: 70,
        buyPrice: 48700,
        sellDate: '10/12/2025',
        sellPrice: 51700,
        profitPercent: 6.16,
        holdDays: 10,
        status: 'closed'
      },
      {
        buyDate: '01/12/2025',
        code: 'GAS',
        signalType: 'Swing T+',
        score: 65,
        buyPrice: 64100,
        sellDate: '08/12/2025',
        sellPrice: 64700,
        profitPercent: 0.94,
        holdDays: 7,
        status: 'closed'
      },
      {
        buyDate: '04/12/2025',
        code: 'HAG',
        signalType: 'Swing T+',
        score: 60,
        buyPrice: 18400,
        profitPercent: -2.0,
        status: 'holding'
      },
      {
        buyDate: '11/12/2025',
        code: 'BMP',
        signalType: 'Trend Following',
        score: 68,
        buyPrice: 165000,
        profitPercent: 5.0,
        status: 'holding'
      },
      {
        buyDate: '15/12/2025',
        code: 'VNM',
        signalType: 'Trend Following',
        score: 72,
        buyPrice: 61200,
        profitPercent: 3.5,
        status: 'holding'
      }
    ];

    // Update current prices for holding stocks
    for (const stock of history) {
      if (stock.status === 'holding') {
        // Try to fetch real price from VNStock
        let currentPrice = await fetchCurrentPrice(stock.code);
        
        // Fallback to mock if VNStock fails
        if (!currentPrice) {
          currentPrice = MOCK_CURRENT_PRICES[stock.code] || stock.buyPrice;
        }
        
        stock.currentPrice = currentPrice;
        stock.profitPercent = Number(((currentPrice - stock.buyPrice) / stock.buyPrice * 100).toFixed(2));
      }
    }

    res.status(200).json({
      success: true,
      history: history,
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('API Error:', error);
    res.status(500).json({ 
      error: 'Internal server error',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
}
