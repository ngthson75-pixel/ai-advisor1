#!/usr/bin/env python3
"""
Daily Signal Scanner - FILTERED VERSION
Auto dedup + quality filter + smart limits

Run daily at 6 PM to generate clean signal list
"""

import json
from datetime import datetime
from collections import defaultdict

# Quality gates
QUALITY_GATES = {
    'min_score': 80,              # Minimum score threshold
    'max_signals': 20,            # Max signals to output
    'min_signals': 5,             # Alert if too few
    'dedup_by': 'ticker',         # 1 signal per ticker
    'priority': 'score',          # Keep highest score
    'exclude_low_price': 10000,   # Exclude stocks < 10k
}


def load_raw_signals():
    """Load raw signals from scanner output"""
    try:
        with open('scripts/signals/signals_raw.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('signals', [])
    except Exception as e:
        print(f"Error loading raw signals: {e}")
        return []


def apply_quality_filter(signals):
    """Filter signals by score and price"""
    filtered = []
    
    for signal in signals:
        # Score check
        if signal.get('score', 0) < QUALITY_GATES['min_score']:
            print(f"  ⏭️  {signal['ticker']}: Low score ({signal.get('score')}%)")
            continue
        
        # Price check (exclude penny stocks)
        if signal.get('entry_price', 0) < QUALITY_GATES['exclude_low_price']:
            print(f"  ⏭️  {signal['ticker']}: Price too low ({signal.get('entry_price')})")
            continue
        
        filtered.append(signal)
    
    print(f"\n📊 Quality Filter: {len(signals)} → {len(filtered)} signals")
    return filtered


def deduplicate_signals(signals):
    """Keep only best signal per ticker (highest score)"""
    ticker_signals = {}
    
    for signal in signals:
        ticker = signal['ticker']
        
        if ticker not in ticker_signals:
            ticker_signals[ticker] = signal
        else:
            existing = ticker_signals[ticker]
            
            # Compare scores
            if signal['score'] > existing['score']:
                print(f"  ↪️  {ticker}: Replace score {existing['score']}% → {signal['score']}%")
                ticker_signals[ticker] = signal
            elif signal['score'] == existing['score']:
                # If same score, keep newer date
                if signal.get('date', '') > existing.get('date', ''):
                    print(f"  ↪️  {ticker}: Same score, keep newer")
                    ticker_signals[ticker] = signal
                else:
                    print(f"  ⏭️  {ticker}: Skip duplicate (score {signal['score']}%)")
            else:
                print(f"  ⏭️  {ticker}: Skip (lower score: {signal['score']}% vs {existing['score']}%)")
    
    deduplicated = list(ticker_signals.values())
    
    print(f"\n🔄 Deduplication: {len(signals)} → {len(deduplicated)} unique tickers")
    return deduplicated


def limit_signals(signals):
    """Limit to max signals, keep highest scores"""
    max_signals = QUALITY_GATES['max_signals']
    
    if len(signals) <= max_signals:
        return signals
    
    # Sort by score DESC, take top N
    sorted_signals = sorted(signals, key=lambda s: s.get('score', 0), reverse=True)
    limited = sorted_signals[:max_signals]
    
    print(f"\n✂️  Signal Limit: {len(signals)} → {max_signals} (kept top scores)")
    return limited


def check_quality_gates(signals):
    """Check if signals meet quality gates"""
    issues = []
    
    # Check minimum signals
    if len(signals) < QUALITY_GATES['min_signals']:
        issues.append(f"⚠️  Too few signals: {len(signals)} < {QUALITY_GATES['min_signals']}")
    
    # Check score distribution
    avg_score = sum(s.get('score', 0) for s in signals) / len(signals) if signals else 0
    if avg_score < 85:
        issues.append(f"⚠️  Low average score: {avg_score:.1f}%")
    
    return issues


def save_filtered_signals(signals):
    """Save filtered signals to output file"""
    output = {
        'scan_date': datetime.now().strftime('%Y-%m-%d'),
        'scan_time': datetime.now().strftime('%H:%M:%S'),
        'total_signals': len(signals),
        'quality_gates': QUALITY_GATES,
        'signals': signals
    }
    
    # Save to latest file
    with open('scripts/signals/signals_latest.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    # Also save dated backup
    dated_file = f"scripts/signals/signals_{datetime.now().strftime('%Y%m%d')}.json"
    with open(dated_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Saved: signals_latest.json ({len(signals)} signals)")


def print_summary(signals):
    """Print summary for manual review"""
    print("\n" + "="*70)
    print("📋 FILTERED SIGNALS SUMMARY")
    print("="*70)
    
    print(f"\nTotal signals: {len(signals)}")
    
    if not signals:
        print("\n⚠️  NO SIGNALS PASSED FILTERS!")
        return
    
    # Score distribution
    scores = [s.get('score', 0) for s in signals]
    print(f"\nScore range: {min(scores)}% - {max(scores)}%")
    print(f"Average score: {sum(scores)/len(scores):.1f}%")
    
    # Top signals
    print(f"\n⭐ TOP 5 SIGNALS:")
    top_5 = sorted(signals, key=lambda s: s.get('score', 0), reverse=True)[:5]
    for i, signal in enumerate(top_5, 1):
        print(f"  {i}. {signal['ticker']:6} @ {signal.get('entry_price'):>7,.0f} - {signal.get('score'):>3}% - {signal.get('strategy')}")
    
    # Strategy distribution
    strategy_count = defaultdict(int)
    for signal in signals:
        strategy_count[signal.get('strategy', 'UNKNOWN')] += 1
    
    print(f"\n📊 BY STRATEGY:")
    for strategy, count in sorted(strategy_count.items(), key=lambda x: x[1], reverse=True):
        print(f"  {strategy:20} : {count} signals")


def main():
    """Main filter workflow"""
    print("="*70)
    print("🔍 DAILY SIGNAL SCANNER - FILTERED VERSION")
    print("="*70)
    
    # Step 1: Load raw signals
    print("\n📡 Step 1: Loading raw signals...")
    raw_signals = load_raw_signals()
    print(f"  Loaded: {len(raw_signals)} raw signals")
    
    if not raw_signals:
        print("\n❌ No raw signals found! Run scanner first.")
        return
    
    # Step 2: Quality filter
    print("\n✅ Step 2: Applying quality filter...")
    filtered = apply_quality_filter(raw_signals)
    
    # Step 3: Deduplication
    print("\n🔄 Step 3: Deduplicating by ticker...")
    deduplicated = deduplicate_signals(filtered)
    
    # Step 4: Limit signals
    print("\n✂️  Step 4: Limiting to max signals...")
    limited = limit_signals(deduplicated)
    
    # Step 5: Quality gates check
    print("\n🚦 Step 5: Checking quality gates...")
    issues = check_quality_gates(limited)
    
    if issues:
        print("\n⚠️  QUALITY GATE WARNINGS:")
        for issue in issues:
            print(f"  {issue}")
        print("\n  ⚠️  Manual review recommended!")
    else:
        print("  ✅ All quality gates passed")
    
    # Step 6: Save output
    print("\n💾 Step 6: Saving filtered signals...")
    save_filtered_signals(limited)
    
    # Step 7: Print summary
    print_summary(limited)
    
    print("\n" + "="*70)
    print("✅ FILTERING COMPLETE")
    print("="*70)
    print(f"\nNext steps:")
    print(f"  1. Review: cat scripts/signals/signals_latest.json")
    print(f"  2. Test: Open frontend locally")
    print(f"  3. Deploy: git add . && git commit && git push origin staging")
    print("\n")


if __name__ == '__main__':
    main()
