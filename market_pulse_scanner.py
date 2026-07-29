#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Market Pulse Scanner
Quét giá hiện tại của 172 mã, tính dòng tiền ngành, top movers.
Chạy mỗi giờ trong giờ giao dịch (9:30-15:00) qua GitHub Actions.

Output: Lưu vào bảng market_pulse trong PostgreSQL
"""

import os
import sys
import json
import time
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ── WATCHLIST 172 mã ─────────────────────────────────────────────────────────
WATCHLIST = [
    'ACB','ACG','AGG','AGR','ANV','APC','APH','BAB','BAF','BCG','BCM','BFC',
    'BID','BMI','BSI','BSR','BTP','BVH','BVS','BWE','CAV','CCL','CII','CMG',
    'CNG','CRC','CSM','CTD','CTG','CTR','CTS','DCM','DGC','DGW','DIG','DPG',
    'DPM','DRC','DXG','EIB','ELC','EVF','EVS','FMC','FPT','FRT','FTS','GAS',
    'GEG','GEX','GMD','GVR','HAG','HAH','HBC','HCM','HDB','HDG','HPG','HSG',
    'HT1','HUT','HVN','IDI','IMP','KBC','KDC','KDH','KOS','LCG','LPB','MBB',
    'MBS','MCH','MIG','MRC','MSB','MSN','MWG','NAB','NAF','NBB','NHA','NKG',
    'NLG','NRC','NVB','NVL','OCB','PAN','PC1','PGC','PGB','PGD','PLC','PLX',
    'PMG','POW','PSI','PTB','PVI','PVD','PVS','PVT','QCG','REE','SAB','SBT',
    'SCS','SHB','SHS','SJS','SKG','SMC','SSB','SSI','STB','SZC','TCB','TCH',
    'TDC','TGG','TLG','TNG','TPB','TVS','VCB','VCI','VCS','VGC','VHC','VHM',
    'VIB','VIC','VIX','VJC','VND','VNM','VPB','VRE','VSC','VTP','VFS','HUT',
    'GEG','DCM',
]
WATCHLIST = list(dict.fromkeys(WATCHLIST))  # deduplicate

# ── SECTOR MAP ────────────────────────────────────────────────────────────────
SECTOR_MAP = {
    'VCB':'Ngân hàng','BID':'Ngân hàng','CTG':'Ngân hàng','TCB':'Ngân hàng',
    'VPB':'Ngân hàng','MBB':'Ngân hàng','STB':'Ngân hàng','HDB':'Ngân hàng',
    'ACB':'Ngân hàng','VIB':'Ngân hàng','EIB':'Ngân hàng','SHB':'Ngân hàng',
    'LPB':'Ngân hàng','TPB':'Ngân hàng','OCB':'Ngân hàng','MSB':'Ngân hàng',
    'SSB':'Ngân hàng','BAB':'Ngân hàng','NVB':'Ngân hàng','PGB':'Ngân hàng',
    'NAB':'Ngân hàng',
    'SSI':'Chứng khoán','VCI':'Chứng khoán','HCM':'Chứng khoán','VND':'Chứng khoán',
    'BSI':'Chứng khoán','MBS':'Chứng khoán','SHS':'Chứng khoán','PSI':'Chứng khoán',
    'EVS':'Chứng khoán','TVS':'Chứng khoán','FTS':'Chứng khoán','CTS':'Chứng khoán',
    'VIX':'Chứng khoán',
    'VHM':'BĐS','VIC':'BĐS','VRE':'BĐS','NVL':'BĐS','KDH':'BĐS',
    'DIG':'BĐS','DXG':'BĐS','NLG':'BĐS','CII':'BĐS','NBB':'BĐS',
    'SJS':'BĐS','NHA':'BĐS','KBC':'BĐS','TDC':'BĐS','SZC':'BĐS',
    'NRC':'BĐS','HDG':'BĐS','CCL':'BĐS','BCG':'BĐS',
    'HPG':'Công nghiệp','HSG':'Công nghiệp','GEX':'Công nghiệp','REE':'Công nghiệp',
    'PC1':'Công nghiệp','CTD':'Công nghiệp','HBC':'Công nghiệp','CTR':'Công nghiệp',
    'HT1':'Công nghiệp','DPG':'Công nghiệp','LCG':'Công nghiệp','NKG':'Công nghiệp',
    'SMC':'Công nghiệp','CSM':'Công nghiệp','BWE':'Công nghiệp','VGC':'Công nghiệp',
    'GAS':'Năng lượng','PLX':'Năng lượng','BSR':'Năng lượng','POW':'Năng lượng',
    'PVD':'Năng lượng','PVT':'Năng lượng','PVS':'Năng lượng','GEG':'Năng lượng',
    'DCM':'Năng lượng','DPM':'Năng lượng','CNG':'Năng lượng','PLC':'Năng lượng',
    'MWG':'Tiêu dùng','VNM':'Tiêu dùng','SAB':'Tiêu dùng','MSN':'Tiêu dùng',
    'FRT':'Tiêu dùng','DGW':'Tiêu dùng','MCH':'Tiêu dùng','BAF':'Tiêu dùng',
    'ANV':'Tiêu dùng','VHC':'Tiêu dùng','FMC':'Tiêu dùng','KDC':'Tiêu dùng',
    'SBT':'Tiêu dùng','PAN':'Tiêu dùng','NAF':'Tiêu dùng','DRC':'Tiêu dùng',
    'FPT':'Công nghệ','CMG':'Công nghệ','ELC':'Công nghệ','VCS':'Công nghệ',
    'DGC':'Công nghệ',
    'HVN':'Vận tải','VJC':'Vận tải','GMD':'Vận tải','VSC':'Vận tải',
    'HAH':'Vận tải','SCS':'Vận tải','TCH':'Vận tải','HUT':'Vận tải','VTP':'Vận tải',
    'VFS':'Vận tải',
    'BVH':'Đa ngành','BCM':'Đa ngành','BMI':'Đa ngành','MIG':'Đa ngành',
    'PVI':'Đa ngành','AGR':'Đa ngành','AGG':'Đa ngành',
}

# ── DB ────────────────────────────────────────────────────────────────────────
def get_db():
    return psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        port=int(os.getenv('DB_PORT', '5432')),
        connect_timeout=10,
    )

def ensure_table(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS market_pulse (
                id SERIAL PRIMARY KEY,
                scan_time TIMESTAMP NOT NULL,
                advancing INTEGER DEFAULT 0,
                declining INTEGER DEFAULT 0,
                unchanged INTEGER DEFAULT 0,
                total_scanned INTEGER DEFAULT 0,
                top_gainers JSONB DEFAULT '[]',
                top_losers JSONB DEFAULT '[]',
                ceil_stocks JSONB DEFAULT '[]',
                floor_stocks JSONB DEFAULT '[]',
                sector_data JSONB DEFAULT '[]',
                summary_text TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        conn.commit()
    print("✅ Table market_pulse ready")

# ── Lấy giá hiện tại ─────────────────────────────────────────────────────────
def get_current_prices(tickers, batch_size=10, sleep_sec=2):
    """
    Lấy giá hiện tại từ vnstock intraday.
    Batch để tránh rate limit.
    """
    from vnstock import Vnstock
    prices = {}
    total = len(tickers)
    
    for i in range(0, total, batch_size):
        batch = tickers[i:i+batch_size]
        for ticker in batch:
            try:
                stock = Vnstock().stock(symbol=ticker, source='VCI')
                df = stock.quote.intraday(symbol=ticker, page_size=1)
                if df is not None and not df.empty:
                    price = float(df['close'].iloc[-1])
                    if price > 0:
                        prices[ticker] = price
            except Exception as e:
                pass  # silent fail per ticker
        
        if i + batch_size < total:
            time.sleep(sleep_sec)
        
        done = min(i + batch_size, total)
        print(f"  Scanned {done}/{total} tickers...")
    
    return prices

# ── Lấy prev_price từ DB ─────────────────────────────────────────────────────
def get_prev_prices(conn, tickers):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT ticker, prev_price, price FROM eod_prices WHERE ticker = ANY(%s) AND prev_price IS NOT NULL",
            (tickers,)
        )
        rows = cur.fetchall()
    return {r[0]: {'prev': r[1], 'eod': r[2]} for r in rows}

# ── Tính sector data ──────────────────────────────────────────────────────────
def calc_sector_data(ticker_changes):
    sector_agg = {}
    for ticker, data in ticker_changes.items():
        s = SECTOR_MAP.get(ticker, 'Khác')
        if s not in sector_agg:
            sector_agg[s] = []
        sector_agg[s].append(data['pct'])
    
    sector_list = []
    for sector, changes in sector_agg.items():
        avg = sum(changes) / len(changes)
        adv = sum(1 for c in changes if c > 0.5)
        dec = sum(1 for c in changes if c < -0.5)
        trend = 'up' if avg > 0.5 else 'down' if avg < -0.5 else 'flat'
        sector_list.append({
            'sector': sector,
            'avg_pct': round(avg, 2),
            'advancing': adv,
            'declining': dec,
            'count': len(changes),
            'trend': trend,
        })
    
    sector_list.sort(key=lambda x: x['avg_pct'], reverse=True)
    return sector_list

# ── Build summary text ────────────────────────────────────────────────────────
def build_summary(advancing, declining, unchanged, total,
                  top_gainers, top_losers, ceil_stocks, floor_stocks,
                  sector_data, scan_time):
    
    breadth = f"{advancing} mã tăng / {declining} mã giảm / {unchanged} mã đứng (/{total} mã theo dõi)"
    
    top_up_str = ', '.join([f"{g['ticker']}(+{g['pct']}%)" for g in top_gainers[:5]]) if top_gainers else 'Không có'
    top_dn_str = ', '.join([f"{l['ticker']}({l['pct']}%)" for l in top_losers[:5]]) if top_losers else 'Không có'
    ceil_str   = ', '.join([s['ticker'] for s in ceil_stocks[:5]]) if ceil_stocks else 'Không có'
    floor_str  = ', '.join([s['ticker'] for s in floor_stocks[:5]]) if floor_stocks else 'Không có'
    
    # Top sectors
    sector_up   = [s for s in sector_data if s['trend'] == 'up']
    sector_down = [s for s in sector_data if s['trend'] == 'down']
    sector_up_str   = ', '.join([f"{s['sector']}(+{s['avg_pct']}%)" for s in sector_up[:3]]) if sector_up else 'Không rõ'
    sector_down_str = ', '.join([f"{s['sector']}({s['avg_pct']}%)" for s in sector_down[:3]]) if sector_down else 'Không rõ'
    
    hour = scan_time.strftime('%H:%M')
    
    summary = f"""[MARKET PULSE {hour}]
Breadth: {breadth}
Tăng mạnh nhất: {top_up_str}
Giảm mạnh nhất: {top_dn_str}
Cổ phiếu trần: {ceil_str}
Cổ phiếu sàn: {floor_str}
Ngành dẫn dắt tăng: {sector_up_str}
Ngành bị rút tiền: {sector_down_str}"""
    
    return summary

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    print(f"\n{'='*60}")
    print(f"🔍 Market Pulse Scanner — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}")
    
    conn = get_db()
    ensure_table(conn)
    
    # Lấy prev_price từ DB
    print("\n📊 Loading prev prices from DB...")
    prev_data = get_prev_prices(conn, WATCHLIST)
    print(f"  Found prev_price for {len(prev_data)} tickers")
    
    if len(prev_data) < 10:
        print("⚠️  Không đủ prev_price data. Chạy update_eod_prices.py trước.")
    
    # Lấy giá hiện tại
    print(f"\n🔄 Fetching current prices for {len(WATCHLIST)} tickers...")
    current_prices = get_current_prices(WATCHLIST, batch_size=8, sleep_sec=3)
    print(f"  Got prices for {len(current_prices)} tickers")
    
    # Tính % change
    ticker_changes = {}
    for ticker, curr in current_prices.items():
        if ticker in prev_data and prev_data[ticker]['prev'] and prev_data[ticker]['prev'] > 0:
            prev = prev_data[ticker]['prev']
            pct = (curr - prev) / prev * 100
            ticker_changes[ticker] = {'price': curr, 'prev': prev, 'pct': round(pct, 2)}
        elif ticker in prev_data and prev_data[ticker]['eod'] > 0:
            # Dùng EOD price hôm qua làm prev nếu chưa có prev_price
            eod = prev_data[ticker]['eod']
            pct = (curr - eod) / eod * 100
            ticker_changes[ticker] = {'price': curr, 'prev': eod, 'pct': round(pct, 2)}
    
    print(f"  Calculated % change for {len(ticker_changes)} tickers")
    
    # Phân loại
    advancing = [t for t, d in ticker_changes.items() if d['pct'] >  0.5]
    declining = [t for t, d in ticker_changes.items() if d['pct'] < -0.5]
    unchanged = [t for t, d in ticker_changes.items() if -0.5 <= d['pct'] <= 0.5]
    
    ceil_stocks  = [{'ticker': t, 'pct': d['pct'], 'price': d['price']}
                    for t, d in ticker_changes.items() if d['pct'] >= 6.5]
    floor_stocks = [{'ticker': t, 'pct': d['pct'], 'price': d['price']}
                    for t, d in ticker_changes.items() if d['pct'] <= -6.5]
    
    sorted_changes = sorted(ticker_changes.items(), key=lambda x: x[1]['pct'], reverse=True)
    top_gainers = [{'ticker': t, 'pct': d['pct'], 'price': d['price']} for t, d in sorted_changes[:10]]
    top_losers  = [{'ticker': t, 'pct': d['pct'], 'price': d['price']} for t, d in sorted_changes[-10:]]
    
    # Sector data
    sector_data = calc_sector_data(ticker_changes)
    
    scan_time = datetime.now()
    summary   = build_summary(
        len(advancing), len(declining), len(unchanged), len(ticker_changes),
        top_gainers, top_losers, ceil_stocks, floor_stocks,
        sector_data, scan_time
    )
    
    print(f"\n{summary}")
    
    # Lưu vào DB
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO market_pulse
              (scan_time, advancing, declining, unchanged, total_scanned,
               top_gainers, top_losers, ceil_stocks, floor_stocks,
               sector_data, summary_text)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            scan_time,
            len(advancing), len(declining), len(unchanged), len(ticker_changes),
            json.dumps(top_gainers, ensure_ascii=False),
            json.dumps(top_losers,  ensure_ascii=False),
            json.dumps(ceil_stocks, ensure_ascii=False),
            json.dumps(floor_stocks,ensure_ascii=False),
            json.dumps(sector_data, ensure_ascii=False),
            summary,
        ))
        conn.commit()
    
    print(f"\n✅ Saved to market_pulse table")
    print(f"   Advancing: {len(advancing)}, Declining: {len(declining)}, Unchanged: {len(unchanged)}")
    print(f"   Ceil: {len(ceil_stocks)}, Floor: {len(floor_stocks)}")
    conn.close()

if __name__ == '__main__':
    main()
