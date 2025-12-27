#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TELEGRAM NOTIFICATION SYSTEM FOR ADMIN

Owner: Nguyễn Thanh Sơn
Email: ngthson75@gmail.com  
Phone: +84938127666
Telegram: @your_telegram_username
"""

import os
import requests
from datetime import datetime
from typing import Optional, Dict, List


class TelegramNotifier:
    """
    Send notifications to admin via Telegram
    MUCH EASIER than email!
    """
    
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if not self.bot_token or not self.chat_id:
            print("⚠️ Telegram not configured!")
            print("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env")
    
    
    def send_message(self, text: str, parse_mode: str = 'HTML') -> bool:
        """
        Send text message to admin
        
        Args:
            text: Message content (supports HTML)
            parse_mode: 'HTML' or 'Markdown'
        
        Returns:
            True if sent successfully
        """
        
        if not self.bot_token or not self.chat_id:
            print("❌ Telegram not configured")
            return False
        
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        
        payload = {
            'chat_id': self.chat_id,
            'text': text,
            'parse_mode': parse_mode,
            'disable_web_page_preview': False
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ Telegram message sent")
                return True
            else:
                print(f"❌ Telegram error: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Telegram exception: {e}")
            return False
    
    
    def send_signal_notification(self, signal: Dict) -> bool:
        """
        Send beautiful signal notification
        
        Args:
            signal: Signal data dictionary
        """
        
        # Get validation info
        validation = signal.get('validation', {})
        errors = validation.get('errors', [])
        warnings = validation.get('warnings', [])
        quality_score = validation.get('quality_score', 0)
        
        # Determine emoji based on quality
        if errors:
            status_emoji = "🚨"
            status_text = "ERROR"
        elif quality_score >= 80:
            status_emoji = "✅"
            status_text = "EXCELLENT"
        elif quality_score >= 60:
            status_emoji = "⚠️"
            status_text = "GOOD"
        else:
            status_emoji = "⚠️"
            status_text = "FAIR"
        
        # Format price difference
        price_diff = signal.get('price_diff_pct', 0)
        if abs(price_diff) > 5:
            price_emoji = "🔴"
        elif abs(price_diff) > 2:
            price_emoji = "🟡"
        else:
            price_emoji = "🟢"
        
        # Build message
        message = f"""
{status_emoji} <b>NEW SIGNAL: {signal['code']}</b> {status_emoji}

<b>━━━━━━━━━━━━━━━━━━━━━</b>

📊 <b>Strategy:</b> {signal['strategy_type']}
🎯 <b>Quality:</b> {quality_score}/100 ({status_text})

<b>━━━━━━━━━━━━━━━━━━━━━</b>

💰 <b>PRICES:</b>
  • Current: {signal['current_price']:,.0f} VND
  • Entry: {signal['entry_price']:,.0f} VND {price_emoji}
  • Stop Loss: {signal['stop_loss']:,.0f} VND (-{signal.get('risk_pct', 0):.1f}%)
  • Take Profit: {signal['take_profit']:,.0f} VND (+{signal.get('reward_pct', 0):.1f}%)
  
📈 <b>R/R Ratio:</b> {signal.get('rr_ratio', 0):.2f}x
📊 <b>RSI:</b> {signal.get('rsi', 50):.0f}
📦 <b>Volume:</b> {signal.get('volume_ratio', 1):.2f}x

<b>━━━━━━━━━━━━━━━━━━━━━</b>
"""
        
        # Add price difference warning
        if abs(price_diff) > 2:
            message += f"\n{price_emoji} <b>Price Diff:</b> {price_diff:+.1f}%"
            if abs(price_diff) > 5:
                message += " ⚠️ <b>CRITICAL!</b>"
            message += "\n"
        
        # Add errors
        if errors:
            message += "\n❌ <b>ERRORS:</b>\n"
            for err in errors[:3]:  # Max 3 errors
                message += f"  • {err}\n"
        
        # Add warnings
        if warnings:
            message += "\n⚠️ <b>WARNINGS:</b>\n"
            for warn in warnings[:3]:  # Max 3 warnings
                message += f"  • {warn}\n"
        
        message += f"""
<b>━━━━━━━━━━━━━━━━━━━━━</b>

⏰ <b>Detected:</b> {datetime.now().strftime('%H:%M:%S')}

🔗 <a href="https://ai-advisor1.netlify.app/admin/signals">Review Dashboard</a>

<i>Signal ID: {signal.get('id', 'N/A')}</i>
"""
        
        return self.send_message(message)
    
    
    def send_approval_notification(self, signal: Dict) -> bool:
        """
        Send notification when signal is approved
        """
        
        message = f"""
✅ <b>SIGNAL APPROVED</b>

<b>{signal['code']}</b> has been approved and published to users.

📊 <b>Details:</b>
  • Entry: {signal['entry_price']:,.0f} VND
  • SL: {signal['stop_loss']:,.0f} VND
  • TP: {signal['take_profit']:,.0f} VND

👥 <b>Users notified:</b> {signal.get('user_count', 'N/A')}
⏰ <b>Time:</b> {datetime.now().strftime('%H:%M:%S')}

🔗 <a href="https://ai-advisor1.netlify.app/admin/signals">Dashboard</a>
"""
        
        return self.send_message(message)
    
    
    def send_rejection_notification(self, signal: Dict, reason: str) -> bool:
        """
        Send notification when signal is rejected
        """
        
        message = f"""
❌ <b>SIGNAL REJECTED</b>

<b>{signal['code']}</b> has been rejected.

📝 <b>Reason:</b> {reason}

⏰ <b>Time:</b> {datetime.now().strftime('%H:%M:%S')}
"""
        
        return self.send_message(message)
    
    
    def send_test_message(self) -> bool:
        """
        Send test message to verify setup
        """
        
        message = f"""
🎉 <b>TELEGRAM SETUP SUCCESSFUL!</b>

Admin notification system is working!

Owner: <b>Nguyễn Thanh Sơn</b>
Email: ngthson75@gmail.com
Phone: +84938127666

⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

You will now receive:
✅ New signal notifications
✅ Approval confirmations  
✅ Error alerts
✅ System updates

🔗 <a href="https://ai-advisor1.netlify.app/admin/signals">Admin Dashboard</a>
"""
        
        return self.send_message(message)


# ============================================================================
# INTEGRATION WITH EXISTING ADMIN API
# ============================================================================

def integrate_telegram_notifications():
    """
    Example: How to use in admin_api.py
    """
    
    # Initialize notifier
    telegram = TelegramNotifier()
    
    # Example 1: Send test message
    telegram.send_test_message()
    
    # Example 2: Send signal notification
    signal_data = {
        'id': 123,
        'code': 'MBB',
        'strategy_type': 'SWING_T+',
        'entry_price': 26500,
        'stop_loss': 25175,
        'take_profit': 28620,
        'current_price': 26500,
        'price_diff_pct': 0.0,
        'risk_pct': 5.0,
        'reward_pct': 8.0,
        'rr_ratio': 1.6,
        'rsi': 65,
        'volume_ratio': 1.8,
        'validation': {
            'errors': [],
            'warnings': ['High RSI'],
            'quality_score': 75
        }
    }
    
    telegram.send_signal_notification(signal_data)
    
    # Example 3: Approval notification
    telegram.send_approval_notification({
        'code': 'MBB',
        'entry_price': 26500,
        'stop_loss': 25175,
        'take_profit': 28620,
        'user_count': 150
    })


# ============================================================================
# TEST SCRIPT
# ============================================================================

if __name__ == '__main__':
    """
    Test Telegram notifications
    """
    
    print("=" * 70)
    print("🤖 TELEGRAM NOTIFIER TEST")
    print("=" * 70)
    
    # Load environment
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check config
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not bot_token or not chat_id:
        print("\n❌ Missing configuration!")
        print("\nPlease set in .env:")
        print("TELEGRAM_BOT_TOKEN=your_bot_token")
        print("TELEGRAM_CHAT_ID=your_chat_id")
        print("\nSee TELEGRAM_SETUP_GUIDE.md for instructions")
        exit(1)
    
    print(f"\n✅ Bot Token: {bot_token[:20]}...")
    print(f"✅ Chat ID: {chat_id}")
    
    # Initialize
    notifier = TelegramNotifier()
    
    # Test 1: Simple message
    print("\n📨 Test 1: Sending simple message...")
    result = notifier.send_message("🎉 <b>Test message</b> from AI Advisor Admin System!")
    
    if result:
        print("✅ Simple message sent successfully!")
    else:
        print("❌ Failed to send simple message")
        exit(1)
    
    # Test 2: Test message
    print("\n📨 Test 2: Sending test notification...")
    result = notifier.send_test_message()
    
    if result:
        print("✅ Test notification sent!")
    else:
        print("❌ Failed to send test notification")
    
    # Test 3: Signal notification
    print("\n📨 Test 3: Sending signal notification...")
    
    test_signal = {
        'id': 1,
        'code': 'MBB',
        'strategy_type': 'SWING_T+',
        'entry_price': 26500,
        'stop_loss': 25175,
        'take_profit': 28620,
        'current_price': 26500,
        'price_diff_pct': 0.0,
        'risk_pct': 5.0,
        'reward_pct': 8.0,
        'rr_ratio': 1.6,
        'rsi': 65,
        'volume_ratio': 1.8,
        'validation': {
            'errors': [],
            'warnings': ['High RSI value'],
            'quality_score': 75
        }
    }
    
    result = notifier.send_signal_notification(test_signal)
    
    if result:
        print("✅ Signal notification sent!")
    else:
        print("❌ Failed to send signal notification")
    
    print("\n" + "=" * 70)
    print("✅ ALL TESTS COMPLETE!")
    print("=" * 70)
    print("\nCheck your Telegram for messages!")
