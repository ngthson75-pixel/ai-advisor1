#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Momentum Score Calculator
Yêu cầu: pip install ta  (thay thế pandas-ta, tương thích mọi Python version)
"""
import os, sys, time, logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from vnstock import Quote

try:
    import ta, ta.momentum, ta.trend, ta.volatility, ta.volume
except ImportError:
    print("❌ pip install ta")
    sys.exit(1)

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///signals.db')
if DATABASE_URL.startswith('postgresql://'):
    DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+psycopg://', 1)
try:
    engine = create_engine(DATABASE_URL)
except Exception as e:
    logger.error(f"DB failed: {e}"); engine = None

try:
    from daily_signal_scanner_eod import TOP_343_STOCKS, get_stock_type
    STOCK_LIST = TOP_343_STOCKS
    logger.info(f"✓ {len(STOCK_LIST)} mã từ scanner gốc")
except ImportError:
    STOCK_LIST = [
        'VCB','VHM','VIC','VNM','HPG','TCB','VPB','MBB','STB','MSN',
        'FPT','VRE','SSI','BID','CTG','PLX','GAS','MWG','VJC','HDB',
        'DGC','REE','TPB','ACB','GVR','PNJ','DPM','GMD','SHB','LPB',
        'BVH','HVN','DXG','GEX','VIB','EIB','BCM','KDH','BSR','POW',
        'SAB','NVL','VCI','MSB','OCB','HAH','DPG','VND','HCM','CTD',
    ]
    logger.warning(f"⚠️  Fallback {len(STOCK_LIST)} blue chips")
    def get_stock_type(t):
        return 'Blue Chip' if t in ['VCB','VHM','VIC','VNM','HPG','TCB','BID','CTG','GAS','FPT'] else 'Mid Cap'

STRONG_BUY_THRESHOLD = 75
BUY_THRESHOLD        = 55
MAX_SIGNALS_PER_DAY  = 20
MIN_ADV_VND          = 2_000_000_000
MIN_DATA_DAYS        = 80

def get_last_trading_day():
    d = datetime.now()
    if d.weekday() == 5: d -= timedelta(days=1)
    elif d.weekday() == 6: d -= timedelta(days=2)
    return d.strftime('%Y-%m-%d')

def fetch_stock_data(ticker, days=120, max_retries=5):
    for attempt in range(max_retries):
        try:
            end_date   = get_last_trading_day()
            start_date = (datetime.strptime(end_date,'%Y-%m-%d') - timedelta(days=days*2)).strftime('%Y-%m-%d')
            df = Quote(symbol=ticker, source='VCI').history(start=start_date, end=end_date)
            if df is None or len(df) == 0: return None
            col_map = {'open':'Open','high':'High','low':'Low','close':'Close','volume':'Volume'}
            df = df.rename(columns={k:v for k,v in col_map.items() if k in df.columns})
            for col in ['Open','High','Low','Close']:
                if col in df.columns: df[col] = df[col] * 1000
            if any(c not in df.columns for c in ['Close','High','Low','Volume']): return None
            df = df.sort_index().dropna()
            return df if len(df) >= MIN_DATA_DAYS else None
        except Exception as e:
            err = str(e)
            err_lower = err.lower()
            is_rate_limit = any(w in err_lower for w in
                                ['quá nhiều','rate limit','too many','thử lại','vui lòng'])
            if is_rate_limit:
                # Đọc số giây VCI yêu cầu chờ từ thông báo lỗi (vd: "thử lại sau 9 giây")
                import re
                m = re.search(r'(\d+)\s*giây', err)
                suggested = int(m.group(1)) if m else 15
                # Chờ thêm buffer để chắc chắn
                wait = suggested + 5 + (attempt * 10)
                logger.warning(f"⏳ Rate limit {ticker} (attempt {attempt+1}/{max_retries}), chờ {wait}s...")
                time.sleep(wait)
                # Sau khi chờ, tiếp tục retry
                continue
            else:
                logger.debug(f"Lỗi {ticker}: {e}")
                return None
    logger.warning(f"⚠️  {ticker}: hết retry sau {max_retries} lần")
    return None

def _safe(series, default=0.0):
    if series is None or len(series)==0: return float(default)
    val = series.iloc[-1]
    return float(val) if not pd.isna(val) else float(default)

def calc_indicators(df):
    close, high, low, volume = df['Close'], df['High'], df['Low'], df['Volume']
    ema20 = ta.trend.EMAIndicator(close, window=20).ema_indicator()
    ema50 = ta.trend.EMAIndicator(close, window=50).ema_indicator()
    roc20 = close.pct_change(20) * 100
    roc60 = close.pct_change(60) * 100
    rsi   = ta.momentum.RSIIndicator(close, window=14).rsi()
    macd_hist = ta.trend.MACD(close, window_slow=26, window_fast=12, window_sign=9).macd_diff()
    stoch_k   = ta.momentum.StochasticOscillator(high, low, close, window=14, smooth_window=3).stoch()
    bb_pband  = ta.volatility.BollingerBands(close, window=20, window_dev=2).bollinger_pband()
    atr_val   = _safe(ta.volatility.AverageTrueRange(high, low, close, window=14).average_true_range())
    obv_s     = ta.volume.OnBalanceVolumeIndicator(close, volume).on_balance_volume()
    avg5, avg20 = volume.tail(5).mean(), volume.tail(20).mean()
    vol_ratio = float(avg5/avg20) if avg20>0 else 1.0
    obv_w = obv_s.tail(30).values
    obv_slope = float(np.polyfit(np.arange(len(obv_w)), obv_w, 1)[0]) if len(obv_w)>=10 else 0.0
    recent = df.tail(30)
    adv_vnd = float(recent['Volume'].mean() * recent['Close'].mean())
    close_val = _safe(close)
    atr_pct = float(atr_val/close_val*100) if close_val>0 else 0.0
    return {
        'close':_safe(close), 'ema20':_safe(ema20), 'ema50':_safe(ema50),
        'rsi':_safe(rsi,50), 'macd_hist':_safe(macd_hist), 'stoch_k':_safe(stoch_k,50),
        'bb_pband':_safe(bb_pband,0.5), 'roc20':_safe(roc20), 'roc60':_safe(roc60),
        'vol_ratio':vol_ratio, 'obv_slope':obv_slope, 'adv_vnd':adv_vnd, 'atr_pct':atr_pct,
    }

def score_trend(i):
    s = 0
    s += 10 if i['roc20']>5 else (5 if i['roc20']>2 else 0)
    s += 10 if i['roc60']>12 else (5 if i['roc60']>4 else 0)
    if i['ema20']>i['ema50']: s+=8
    if i['close']>i['ema50']: s+=7
    return s

def score_volume(i):
    s = 0
    s += 10 if i['vol_ratio']>1.5 else (6 if i['vol_ratio']>1.2 else 0)
    if i['obv_slope']>0: s+=8
    if i['adv_vnd']>=MIN_ADV_VND: s+=7
    return s

def score_oscillator(i):
    s = 0
    r = i['rsi']
    s += 10 if 45<=r<=70 else (5 if 40<=r<45 else 0)
    if i['macd_hist']>0: s+=8
    k = i['stoch_k']
    s += 7 if 50<=k<=80 else (3 if 40<=k<50 else 0)
    return s

def score_volatility(i):
    s = 0
    a = i['atr_pct']
    s += 8 if 2<=a<=7 else (4 if (1.5<=a<2 or 7<a<=9) else 0)
    b = i['bb_pband']
    s += 7 if 0.4<=b<=0.85 else (3 if (0.3<=b<0.4 or 0.85<b<=0.95) else 0)
    return s

def compute_ai_score(df):
    try:
        ind = calc_indicators(df)
        g1,g2,g3,g4 = score_trend(ind), score_volume(ind), score_oscillator(ind), score_volatility(ind)
        return {
            'ai_score':g1+g2+g3+g4, 'score_trend':g1, 'score_volume':g2,
            'score_oscillator':g3, 'score_volatility':g4,
            'close':ind['close'], 'rsi':round(ind['rsi'],1),
            'ema20':round(ind['ema20'],0), 'ema50':round(ind['ema50'],0),
            'roc20':round(ind['roc20'],1), 'roc60':round(ind['roc60'],1),
            'vol_ratio':round(ind['vol_ratio'],2), 'adv_vnd':ind['adv_vnd'],
            'atr_pct':round(ind['atr_pct'],1),
        }
    except Exception as e:
        logger.debug(f"score error: {e}"); return None

def build_signal(ticker, sd, rank):
    close, ema50, score = sd['close'], sd['ema50'], sd['ai_score']
    sl  = float(ema50*0.97) if ema50>0 else float(close*0.92)
    risk = close - sl
    tp  = float(close + risk*2.5) if risk>0 else float(close*1.12)
    rr  = float((tp-close)/risk) if risk>0 else 2.5
    return {
        'ticker':ticker, 'strategy':'MOMENTUM_AI', 'action':'BUY',
        'entry_price':float(close), 'stop_loss':round(sl,0), 'take_profit':round(tp,0),
        'risk_reward':round(rr,2), 'strength':int(score),
        'is_priority':int(score>=STRONG_BUY_THRESHOLD),
        'stock_type':get_stock_type(ticker), 'rsi':float(sd['rsi']),
        'date':get_last_trading_day(), 'ai_score':score, 'rank':rank,
        'score_breakdown':{'trend':sd['score_trend'],'volume':sd['score_volume'],
                           'oscillator':sd['score_oscillator'],'volatility':sd['score_volatility']},
        'roc20':sd['roc20'], 'roc60':sd['roc60'], 'vol_ratio':sd['vol_ratio'], 'atr_pct':sd['atr_pct'],
    }

def get_market_regime_score():
    try:
        df = fetch_stock_data('VNINDEX', days=60)
        if df is None: return 50.0
        ema20 = _safe(ta.trend.EMAIndicator(df['Close'],window=20).ema_indicator())
        ema50 = _safe(ta.trend.EMAIndicator(df['Close'],window=50).ema_indicator())
        rsi   = _safe(ta.momentum.RSIIndicator(df['Close'],window=14).rsi(), 50)
        score = 50.0 + (20 if ema20>ema50 else -20) + (15 if df['Close'].iloc[-1]>ema50 else -15)
        score += 10 if 40<=rsi<=70 else (-20 if rsi<30 else 0)
        result = max(0.0, min(100.0, score))
        logger.info(f"Market Regime: {result:.0f}/100")
        return result
    except Exception as e:
        logger.warning(f"Regime error: {e}"); return 50.0

def _save_momentum_signals(signals):
    try:
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM signals WHERE strategy = 'MOMENTUM_AI'"))
            for s in signals:
                conn.execute(text('''INSERT INTO signals
                    (ticker,strategy,entry_price,stop_loss,take_profit,risk_reward,
                     strength,is_priority,stock_type,rsi,date,action)
                    VALUES (:ticker,:strategy,:entry_price,:stop_loss,:take_profit,:risk_reward,
                     :strength,:is_priority,:stock_type,:rsi,:date,:action)'''),
                    {k:s[k] for k in ['ticker','strategy','entry_price','stop_loss','take_profit',
                     'risk_reward','strength','is_priority','stock_type','rsi','date','action']})
            conn.commit()
        logger.info(f"✅ Saved {len(signals)} MOMENTUM_AI signals")
    except Exception as e:
        logger.error(f"❌ DB error: {e}")

def scan_momentum_signals(tickers=None, regime_threshold=40.0, max_signals=MAX_SIGNALS_PER_DAY, save_to_db=False):
    if tickers is None: tickers = STOCK_LIST
    t0 = datetime.now()
    logger.info("="*60)
    logger.info(f"🚀 AI Momentum Scanner | {len(tickers)} mã | {get_last_trading_day()}")
    logger.info("="*60)

    regime = get_market_regime_score()
    if regime < regime_threshold:
        logger.warning(f"⚠️  Regime {regime:.0f} < {regime_threshold} → TẮT signals")
        return []

    all_scores = []; success=skip=error=0
    for i, ticker in enumerate(tickers):
        if (i+1)%50==0:
            logger.info(f"   [{i+1}/{len(tickers)}] Đủ score: {len(all_scores)} | {(datetime.now()-t0).seconds}s")
        df = fetch_stock_data(ticker, days=120)
        if df is None: skip+=1; continue
        adv = float(df.tail(30)['Volume'].mean() * df.tail(30)['Close'].mean())
        if adv < MIN_ADV_VND: skip+=1; continue
        sd = compute_ai_score(df)
        if sd is None: error+=1; continue
        success+=1
        if sd['ai_score'] >= BUY_THRESHOLD:
            all_scores.append({'ticker':ticker,'score_data':sd})
            logger.info(f"  ✓ {ticker}: {sd['ai_score']}/100 "
                       f"[T{sd['score_trend']}|V{sd['score_volume']}|O{sd['score_oscillator']}|Vol{sd['score_volatility']}] "
                       f"RSI={sd['rsi']:.0f} ROC20={sd['roc20']:+.1f}%")
        time.sleep(1.5)   # 1.5s giữa các request — tránh rate limit VCI

    all_scores.sort(key=lambda x: x['score_data']['ai_score'], reverse=True)
    signals = [build_signal(x['ticker'], x['score_data'], r) for r, x in enumerate(all_scores[:max_signals], 1)]

    elapsed = (datetime.now()-t0).seconds
    logger.info(f"\n📊 Quét:{len(tickers)} OK:{success} Skip:{skip} Lỗi:{error} | Score:{len(all_scores)} | Signals:{len(signals)} | {elapsed}s")

    if signals:
        logger.info(f"\n🏆 TOP SIGNALS:")
        logger.info(f"  {'#':<3} {'Mã':<6} {'Score':<7} {'Tier':<11} {'RSI':<5} {'ROC20':>6} {'Giá vào':>10}  R/R")
        logger.info("  "+"-"*60)
        for s in signals[:10]:
            tier = "STRONG BUY" if s['ai_score']>=STRONG_BUY_THRESHOLD else "BUY"
            logger.info(f"  #{s['rank']:<2} {s['ticker']:<6} {s['ai_score']:<7} {tier:<11} "
                       f"{s['rsi']:<5.0f} {s['roc20']:>+5.1f}% {s['entry_price']:>10,.0f}  {s['risk_reward']:.1f}x")

    if save_to_db and signals and engine: _save_momentum_signals(signals)
    return signals

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description='AI Momentum Score Calculator')
    p.add_argument('--tickers', nargs='+')
    p.add_argument('--top', type=int, default=30)
    p.add_argument('--full', action='store_true')
    p.add_argument('--save', action='store_true')
    p.add_argument('--no-regime', action='store_true', dest='no_regime')
    args = p.parse_args()

    if args.tickers:    test_list = args.tickers
    elif args.full:     test_list = STOCK_LIST
    else:               test_list = STOCK_LIST[:args.top]

    signals = scan_momentum_signals(
        tickers=test_list,
        regime_threshold=0.0 if args.no_regime else 40.0,
        save_to_db=args.save,
    )

    print()
    if signals:
        print(f"✅ {len(signals)} tín hiệu MOMENTUM_AI\n")
        print(f"{'#':<4} {'Mã':<7} {'Score':>5} {'Tier':<12} {'Entry':>12} {'SL':>12} {'TP':>12} {'R/R':<5} {'RSI':<5} {'ROC20':>6}")
        print("-"*85)
        for s in signals:
            tier = "STRONG BUY" if s['ai_score']>=STRONG_BUY_THRESHOLD else "BUY"
            print(f"#{s['rank']:<3} {s['ticker']:<7} {s['ai_score']:>5} {tier:<12} "
                  f"{s['entry_price']:>12,.0f} {s['stop_loss']:>12,.0f} {s['take_profit']:>12,.0f} "
                  f"{s['risk_reward']:<5.1f} {s['rsi']:<5.0f} {s['roc20']:>+5.1f}%")
        strong = sum(1 for s in signals if s['ai_score']>=STRONG_BUY_THRESHOLD)
        print(f"\n  STRONG BUY (≥{STRONG_BUY_THRESHOLD}): {strong}  |  BUY: {len(signals)-strong}")
    else:
        print("⚠️  Không có tín hiệu. Thêm --no-regime để test.")
