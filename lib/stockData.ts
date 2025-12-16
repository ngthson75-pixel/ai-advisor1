// Utility to fetch real stock data from Vietnamese market
// Using SSI iBoard public API (no authentication needed)

interface StockQuote {
  code: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  high: number;
  low: number;
  open: number;
}

interface TechnicalIndicators {
  rsi: number;
  macd: number;
  macdSignal: number;
  ema20: number;
  ema50: number;
}

export async function fetchStockQuote(stockCode: string): Promise<StockQuote | null> {
  try {
    // SSI iBoard API endpoint for stock quotes
    const response = await fetch(
      `https://iboard-query.ssi.com.vn/stock/${stockCode}`,
      {
        headers: {
          'Accept': 'application/json',
        },
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();

    return {
      code: stockCode,
      price: data.lastPrice || data.price || 0,
      change: data.change || 0,
      changePercent: data.changePc || 0,
      volume: data.totalVol || 0,
      high: data.highest || 0,
      low: data.lowest || 0,
      open: data.open || 0,
    };
  } catch (error) {
    console.error(`Error fetching ${stockCode}:`, error);
    return null;
  }
}

export async function fetchMultipleStocks(stockCodes: string[]): Promise<StockQuote[]> {
  const promises = stockCodes.map(code => fetchStockQuote(code));
  const results = await Promise.allSettled(promises);
  
  return results
    .filter((result): result is PromiseFulfilledResult<StockQuote> => 
      result.status === 'fulfilled' && result.value !== null
    )
    .map(result => result.value);
}

export function calculateRSI(prices: number[], period: number = 14): number {
  if (prices.length < period + 1) return 50;

  let gains = 0;
  let losses = 0;

  for (let i = 1; i <= period; i++) {
    const difference = prices[i] - prices[i - 1];
    if (difference >= 0) {
      gains += difference;
    } else {
      losses -= difference;
    }
  }

  const avgGain = gains / period;
  const avgLoss = losses / period;

  if (avgLoss === 0) return 100;

  const rs = avgGain / avgLoss;
  const rsi = 100 - (100 / (1 + rs));

  return Math.round(rsi * 100) / 100;
}

export function calculateSimpleMACD(prices: number[]): { macd: number; signal: number } {
  if (prices.length < 26) {
    return { macd: 0, signal: 0 };
  }

  // Simple EMA calculation
  const ema12 = calculateEMA(prices, 12);
  const ema26 = calculateEMA(prices, 26);
  const macd = ema12 - ema26;

  // Signal line (9-period EMA of MACD)
  const macdLine = [macd];
  const signal = calculateEMA(macdLine, 9);

  return {
    macd: Math.round(macd * 100) / 100,
    signal: Math.round(signal * 100) / 100,
  };
}

function calculateEMA(prices: number[], period: number): number {
  if (prices.length === 0) return 0;
  if (prices.length < period) return prices[prices.length - 1];

  const k = 2 / (period + 1);
  let ema = prices[0];

  for (let i = 1; i < prices.length; i++) {
    ema = prices[i] * k + ema * (1 - k);
  }

  return ema;
}

// Fallback: Generate mock historical data for technical indicators
export function generateMockHistoricalData(currentPrice: number, days: number = 30): number[] {
  const prices: number[] = [];
  let price = currentPrice;

  for (let i = 0; i < days; i++) {
    const change = (Math.random() - 0.5) * 0.04 * price; // +/- 2% daily
    price = Math.max(price + change, price * 0.9); // Không giảm quá 10%
    prices.unshift(price);
  }

  return prices;
}

export async function getStockWithIndicators(stockCode: string): Promise<{
  quote: StockQuote;
  indicators: TechnicalIndicators;
} | null> {
  const quote = await fetchStockQuote(stockCode);
  
  if (!quote) return null;

  // Generate historical data for indicators (in production, fetch real historical data)
  const historicalPrices = generateMockHistoricalData(quote.price);
  
  const rsi = calculateRSI(historicalPrices);
  const { macd, signal } = calculateSimpleMACD(historicalPrices);

  return {
    quote,
    indicators: {
      rsi,
      macd,
      macdSignal: signal,
      ema20: calculateEMA(historicalPrices, 20),
      ema50: calculateEMA(historicalPrices, 50),
    },
  };
}
