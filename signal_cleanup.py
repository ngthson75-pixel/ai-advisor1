#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUTOMATED SIGNAL CLEANUP SYSTEM

Owner: Nguyễn Thanh Sơn
Email: ngthson75@gmail.com
Phone: +84938127666

Purpose:
- Remove old/expired signals automatically
- Keep database clean and performant
- Maintain only relevant signals for users
"""

import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class Signal(Base):
    """Signal model matching admin_api.py"""
    __tablename__ = 'signals'
    
    id = Column(Integer, primary_key=True)
    code = Column(String(10), nullable=False)
    strategy_type = Column(String(50), nullable=False)
    entry_price = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=False)
    take_profit = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    price_diff_pct = Column(Float, default=0)
    risk_pct = Column(Float, default=0)
    reward_pct = Column(Float, default=0)
    rr_ratio = Column(Float, default=0)
    rsi = Column(Float, default=0)
    volume_ratio = Column(Float, default=0)
    validation_errors = Column(Text, default='[]')
    validation_warnings = Column(Text, default='[]')
    quality_score = Column(Integer, default=0)
    state = Column(String(20), default='pending_review')
    detected_at = Column(DateTime, default=datetime.now)
    reviewed_at = Column(DateTime, nullable=True)
    published_at = Column(DateTime, nullable=True)
    reviewed_by = Column(String(100), nullable=True)
    admin_notes = Column(Text, nullable=True)
    reject_reason = Column(Text, nullable=True)


class SignalCleanupManager:
    """
    Manage signal cleanup with multiple strategies
    """
    
    def __init__(self, database_url='sqlite:///signals.db', dry_run=False):
        """
        Args:
            database_url: Database connection string
            dry_run: If True, only show what would be deleted
        """
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        self.dry_run = dry_run
        
    def get_stats(self):
        """Get current database stats"""
        total = self.session.query(Signal).count()
        
        by_state = self.session.query(
            Signal.state,
            func.count(Signal.id)
        ).group_by(Signal.state).all()
        
        by_date = self.session.query(
            func.date(Signal.detected_at),
            func.count(Signal.id)
        ).group_by(func.date(Signal.detected_at)).order_by(func.date(Signal.detected_at).desc()).all()
        
        return {
            'total': total,
            'by_state': dict(by_state),
            'by_date': by_date
        }
    
    def cleanup_old_signals(self, days_old=7):
        """
        Strategy 1: Delete signals older than X days
        
        Args:
            days_old: Signals older than this are deleted
            
        Returns:
            Number of signals deleted
        """
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        query = self.session.query(Signal).filter(
            Signal.detected_at < cutoff_date
        )
        
        count = query.count()
        
        if count == 0:
            print(f"✅ No signals older than {days_old} days")
            return 0
        
        if self.dry_run:
            print(f"🔍 DRY RUN: Would delete {count} signals older than {cutoff_date.date()}")
            signals = query.limit(5).all()
            for sig in signals:
                print(f"   → {sig.code} (ID:{sig.id}) from {sig.detected_at.date()}")
            if count > 5:
                print(f"   ... and {count - 5} more")
        else:
            print(f"🗑️  Deleting {count} signals older than {cutoff_date.date()}...")
            query.delete()
            self.session.commit()
            print(f"✅ Deleted {count} old signals")
        
        return count
    
    def cleanup_rejected_signals(self, days_old=3):
        """
        Strategy 2: Delete rejected signals older than X days
        
        Args:
            days_old: Rejected signals older than this are deleted
            
        Returns:
            Number of signals deleted
        """
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        query = self.session.query(Signal).filter(
            Signal.state == 'rejected',
            Signal.reviewed_at < cutoff_date
        )
        
        count = query.count()
        
        if count == 0:
            print(f"✅ No rejected signals older than {days_old} days")
            return 0
        
        if self.dry_run:
            print(f"🔍 DRY RUN: Would delete {count} rejected signals")
            signals = query.limit(5).all()
            for sig in signals:
                print(f"   → {sig.code} (ID:{sig.id}) rejected on {sig.reviewed_at.date()}")
            if count > 5:
                print(f"   ... and {count - 5} more")
        else:
            print(f"🗑️  Deleting {count} rejected signals...")
            query.delete()
            self.session.commit()
            print(f"✅ Deleted {count} rejected signals")
        
        return count
    
    def cleanup_pending_signals(self, days_old=2):
        """
        Strategy 3: Delete pending signals that weren't reviewed
        
        Args:
            days_old: Pending signals older than this are deleted
            
        Returns:
            Number of signals deleted
        """
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        query = self.session.query(Signal).filter(
            Signal.state == 'pending_review',
            Signal.detected_at < cutoff_date
        )
        
        count = query.count()
        
        if count == 0:
            print(f"✅ No stale pending signals")
            return 0
        
        if self.dry_run:
            print(f"🔍 DRY RUN: Would delete {count} stale pending signals")
            signals = query.limit(5).all()
            for sig in signals:
                print(f"   → {sig.code} (ID:{sig.id}) pending since {sig.detected_at.date()}")
            if count > 5:
                print(f"   ... and {count - 5} more")
        else:
            print(f"🗑️  Deleting {count} stale pending signals...")
            query.delete()
            self.session.commit()
            print(f"✅ Deleted {count} stale pending signals")
        
        return count
    
    def cleanup_low_quality_signals(self, min_score=30, days_old=1):
        """
        Strategy 4: Delete low-quality signals
        
        Args:
            min_score: Signals below this score are deleted
            days_old: Only delete if older than this
            
        Returns:
            Number of signals deleted
        """
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        query = self.session.query(Signal).filter(
            Signal.quality_score < min_score,
            Signal.detected_at < cutoff_date,
            Signal.state != 'approved'  # Don't delete approved signals
        )
        
        count = query.count()
        
        if count == 0:
            print(f"✅ No low-quality signals to remove")
            return 0
        
        if self.dry_run:
            print(f"🔍 DRY RUN: Would delete {count} low-quality signals (score < {min_score})")
            signals = query.limit(5).all()
            for sig in signals:
                print(f"   → {sig.code} (ID:{sig.id}) score={sig.quality_score}, state={sig.state}")
            if count > 5:
                print(f"   ... and {count - 5} more")
        else:
            print(f"🗑️  Deleting {count} low-quality signals...")
            query.delete()
            self.session.commit()
            print(f"✅ Deleted {count} low-quality signals")
        
        return count
    
    def keep_only_latest_n_signals(self, n=100):
        """
        Strategy 5: Keep only the latest N signals
        
        Args:
            n: Number of latest signals to keep
            
        Returns:
            Number of signals deleted
        """
        total = self.session.query(Signal).count()
        
        if total <= n:
            print(f"✅ Only {total} signals, keeping all (target: {n})")
            return 0
        
        # Get IDs of signals to keep (latest N)
        keep_ids = [
            row[0] for row in self.session.query(Signal.id)
            .order_by(Signal.detected_at.desc())
            .limit(n)
            .all()
        ]
        
        # Delete signals not in keep list
        query = self.session.query(Signal).filter(
            Signal.id.notin_(keep_ids)
        )
        
        count = query.count()
        
        if self.dry_run:
            print(f"🔍 DRY RUN: Would delete {count} signals (keeping latest {n})")
            signals = query.order_by(Signal.detected_at.asc()).limit(5).all()
            for sig in signals:
                print(f"   → {sig.code} (ID:{sig.id}) from {sig.detected_at.date()}")
            if count > 5:
                print(f"   ... and {count - 5} more")
        else:
            print(f"🗑️  Deleting {count} signals (keeping latest {n})...")
            query.delete(synchronize_session=False)
            self.session.commit()
            print(f"✅ Deleted {count} signals, kept {n} latest")
        
        return count
    
    def full_cleanup(self, aggressive=False):
        """
        Run all cleanup strategies in order
        
        Args:
            aggressive: If True, use shorter retention periods
        """
        print("=" * 70)
        print("🧹 SIGNAL DATABASE CLEANUP")
        print("=" * 70)
        
        # Show current stats
        stats = self.get_stats()
        print(f"\n📊 Current state:")
        print(f"   Total signals: {stats['total']}")
        print(f"   By state: {stats['by_state']}")
        print(f"   By date (last 7 days): {len([d for d in stats['by_date'] if d[0]])}")
        
        print("\n" + "-" * 70)
        
        total_deleted = 0
        
        # Strategy 1: Delete very old signals
        if aggressive:
            print("\n1️⃣  Cleanup: Signals older than 3 days")
            total_deleted += self.cleanup_old_signals(days_old=3)
        else:
            print("\n1️⃣  Cleanup: Signals older than 7 days")
            total_deleted += self.cleanup_old_signals(days_old=7)
        
        # Strategy 2: Delete rejected signals
        print("\n2️⃣  Cleanup: Rejected signals")
        if aggressive:
            total_deleted += self.cleanup_rejected_signals(days_old=1)
        else:
            total_deleted += self.cleanup_rejected_signals(days_old=3)
        
        # Strategy 3: Delete stale pending signals
        print("\n3️⃣  Cleanup: Stale pending signals")
        if aggressive:
            total_deleted += self.cleanup_pending_signals(days_old=1)
        else:
            total_deleted += self.cleanup_pending_signals(days_old=2)
        
        # Strategy 4: Delete low-quality signals
        print("\n4️⃣  Cleanup: Low-quality signals")
        total_deleted += self.cleanup_low_quality_signals(min_score=30, days_old=1)
        
        # Strategy 5: Keep only latest N (optional, only if too many)
        if stats['total'] > 500:
            print("\n5️⃣  Cleanup: Keep only latest 200 signals")
            total_deleted += self.keep_only_latest_n_signals(n=200)
        
        # Final stats
        print("\n" + "-" * 70)
        final_stats = self.get_stats()
        print(f"\n📊 Final state:")
        print(f"   Total signals: {final_stats['total']}")
        print(f"   Deleted: {total_deleted} signals")
        print(f"   Remaining: {final_stats['total']}")
        
        print("\n" + "=" * 70)
        if self.dry_run:
            print("🔍 DRY RUN COMPLETE - No changes made")
        else:
            print("✅ CLEANUP COMPLETE")
        print("=" * 70)
        
        return total_deleted
    
    def close(self):
        """Close database connection"""
        self.session.close()


# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    """Main CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='AI Advisor Signal Cleanup Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (preview what would be deleted)
  python signal_cleanup.py --dry-run
  
  # Full cleanup (default: 7 days retention)
  python signal_cleanup.py
  
  # Aggressive cleanup (3 days retention)
  python signal_cleanup.py --aggressive
  
  # Delete only old signals (14 days)
  python signal_cleanup.py --old-only --days 14
  
  # Keep only latest 50 signals
  python signal_cleanup.py --keep-latest 50
  
  # Just show stats
  python signal_cleanup.py --stats-only
        """
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview what would be deleted without actually deleting'
    )
    
    parser.add_argument(
        '--aggressive',
        action='store_true',
        help='Use shorter retention periods (3 days instead of 7)'
    )
    
    parser.add_argument(
        '--old-only',
        action='store_true',
        help='Only delete old signals, skip other cleanup strategies'
    )
    
    parser.add_argument(
        '--days',
        type=int,
        default=7,
        help='Number of days to keep (for --old-only)'
    )
    
    parser.add_argument(
        '--keep-latest',
        type=int,
        help='Keep only this many latest signals'
    )
    
    parser.add_argument(
        '--stats-only',
        action='store_true',
        help='Only show statistics, do not delete anything'
    )
    
    parser.add_argument(
        '--db',
        default='sqlite:///signals.db',
        help='Database URL (default: sqlite:///signals.db)'
    )
    
    args = parser.parse_args()
    
    # Create cleanup manager
    manager = SignalCleanupManager(
        database_url=args.db,
        dry_run=args.dry_run or args.stats_only
    )
    
    try:
        if args.stats_only:
            # Just show stats
            print("=" * 70)
            print("📊 DATABASE STATISTICS")
            print("=" * 70)
            stats = manager.get_stats()
            print(f"\nTotal signals: {stats['total']}")
            print(f"\nBy state:")
            for state, count in stats['by_state'].items():
                print(f"  {state}: {count}")
            print(f"\nBy date (last 14 days):")
            for date, count in stats['by_date'][:14]:
                print(f"  {date}: {count} signals")
            print("=" * 70)
            
        elif args.keep_latest:
            # Keep only latest N
            manager.keep_only_latest_n_signals(n=args.keep_latest)
            
        elif args.old_only:
            # Delete only old signals
            manager.cleanup_old_signals(days_old=args.days)
            
        else:
            # Full cleanup
            manager.full_cleanup(aggressive=args.aggressive)
        
    finally:
        manager.close()


if __name__ == '__main__':
    main()
