#!/usr/bin/env python3
"""
Signal Editor - Interactive tool to edit signals before deploy
"""

import json
from datetime import datetime

SIGNALS_FILE = 'scripts/signals/signals_latest.json'

def load_signals():
    """Load current signals"""
    try:
        with open(SIGNALS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading signals: {e}")
        return None


def save_signals(data):
    """Save edited signals"""
    try:
        # Backup first
        backup_file = f"scripts/signals/signals_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ Backup saved: {backup_file}")
        
        # Save edited version
        with open(SIGNALS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ Saved: {SIGNALS_FILE}")
        
    except Exception as e:
        print(f"❌ Error saving: {e}")


def display_signals(data):
    """Display signals list"""
    signals = data.get('signals', [])
    
    print("\n" + "="*70)
    print(f"📊 CURRENT SIGNALS ({len(signals)} total)")
    print("="*70)
    
    for i, signal in enumerate(signals, 1):
        print(f"{i:2}. {signal['ticker']:6} @ {signal.get('entry_price', 0):>8,.0f} - {signal.get('score', 0):>3}% - {signal.get('strategy', 'N/A')}")
    
    print("="*70)


def remove_signal(data):
    """Remove a signal by index"""
    display_signals(data)
    
    try:
        index = int(input("\nEnter signal number to remove (0 to cancel): ")) - 1
        
        if index < 0:
            print("❌ Cancelled")
            return data
        
        signals = data['signals']
        
        if 0 <= index < len(signals):
            removed = signals.pop(index)
            data['total_signals'] = len(signals)
            print(f"✅ Removed: {removed['ticker']} @ {removed.get('entry_price', 0):,.0f}")
        else:
            print("❌ Invalid index")
            
    except (ValueError, KeyError) as e:
        print(f"❌ Error: {e}")
    
    return data


def edit_price(data):
    """Edit signal price"""
    display_signals(data)
    
    try:
        index = int(input("\nEnter signal number to edit (0 to cancel): ")) - 1
        
        if index < 0:
            print("❌ Cancelled")
            return data
        
        signals = data['signals']
        
        if 0 <= index < len(signals):
            signal = signals[index]
            
            print(f"\nEditing: {signal['ticker']}")
            print(f"  Current entry: {signal.get('entry_price', 0):,.0f}")
            print(f"  Current SL:    {signal.get('stop_loss', 0):,.0f}")
            print(f"  Current TP:    {signal.get('take_profit', 0):,.0f}")
            
            # Edit entry price
            new_entry = input(f"\nNew entry price (or Enter to keep {signal.get('entry_price', 0):,.0f}): ").strip()
            if new_entry:
                signal['entry_price'] = float(new_entry.replace(',', ''))
                print(f"  ✅ Entry updated: {signal['entry_price']:,.0f}")
            
            # Edit stop loss
            new_sl = input(f"New stop loss (or Enter to keep {signal.get('stop_loss', 0):,.0f}): ").strip()
            if new_sl:
                signal['stop_loss'] = float(new_sl.replace(',', ''))
                print(f"  ✅ SL updated: {signal['stop_loss']:,.0f}")
            
            # Edit take profit
            new_tp = input(f"New take profit (or Enter to keep {signal.get('take_profit', 0):,.0f}): ").strip()
            if new_tp:
                signal['take_profit'] = float(new_tp.replace(',', ''))
                print(f"  ✅ TP updated: {signal['take_profit']:,.0f}")
            
        else:
            print("❌ Invalid index")
            
    except (ValueError, KeyError) as e:
        print(f"❌ Error: {e}")
    
    return data


def edit_score(data):
    """Edit signal score"""
    display_signals(data)
    
    try:
        index = int(input("\nEnter signal number to edit score (0 to cancel): ")) - 1
        
        if index < 0:
            print("❌ Cancelled")
            return data
        
        signals = data['signals']
        
        if 0 <= index < len(signals):
            signal = signals[index]
            
            print(f"\nEditing: {signal['ticker']}")
            print(f"  Current score: {signal.get('score', 0)}%")
            
            new_score = input(f"\nNew score (0-100, or Enter to keep {signal.get('score', 0)}): ").strip()
            
            if new_score:
                score = int(new_score)
                if 0 <= score <= 100:
                    signal['score'] = score
                    print(f"  ✅ Score updated: {signal['score']}%")
                else:
                    print("❌ Score must be 0-100")
        else:
            print("❌ Invalid index")
            
    except (ValueError, KeyError) as e:
        print(f"❌ Error: {e}")
    
    return data


def add_signal(data):
    """Manually add a signal"""
    print("\n📝 Add New Signal")
    
    try:
        ticker = input("Ticker (e.g., VCB): ").strip().upper()
        entry = float(input("Entry price: ").replace(',', ''))
        sl = float(input("Stop loss: ").replace(',', ''))
        tp = float(input("Take profit: ").replace(',', ''))
        score = int(input("Score (0-100): "))
        strategy = input("Strategy (PULLBACK/BREAKOUT/EMA_CROSS): ").strip().upper()
        
        new_signal = {
            "ticker": ticker,
            "entry_price": entry,
            "stop_loss": sl,
            "take_profit": tp,
            "score": score,
            "strategy": strategy,
            "date": datetime.now().strftime('%Y-%m-%d')
        }
        
        data['signals'].append(new_signal)
        data['total_signals'] = len(data['signals'])
        
        print(f"\n✅ Added: {ticker} @ {entry:,.0f} (score: {score}%)")
        
    except (ValueError, KeyError) as e:
        print(f"❌ Error: {e}")
    
    return data


def main():
    """Main interactive menu"""
    print("="*70)
    print("🔧 SIGNAL EDITOR")
    print("="*70)
    
    # Load signals
    data = load_signals()
    
    if not data:
        print("❌ Cannot load signals file")
        return
    
    while True:
        print("\n" + "="*70)
        print("MENU:")
        print("  1. View signals")
        print("  2. Remove signal")
        print("  3. Edit prices (Entry/SL/TP)")
        print("  4. Edit score")
        print("  5. Add signal manually")
        print("  6. Save & Exit")
        print("  0. Exit without saving")
        print("="*70)
        
        choice = input("\nChoice: ").strip()
        
        if choice == '1':
            display_signals(data)
            
        elif choice == '2':
            data = remove_signal(data)
            
        elif choice == '3':
            data = edit_price(data)
            
        elif choice == '4':
            data = edit_score(data)
            
        elif choice == '5':
            data = add_signal(data)
            
        elif choice == '6':
            save_signals(data)
            print("\n✅ Changes saved! Ready to deploy.")
            break
            
        elif choice == '0':
            print("\n❌ Exiting without saving")
            break
            
        else:
            print("❌ Invalid choice")


if __name__ == '__main__':
    main()
