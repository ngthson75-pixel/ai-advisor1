#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UNIVERSAL SIGNAL CLEANUP - AUTO-DETECTS SCHEMA

Owner: Nguyễn Thanh Sơn
Email: ngthson75@gmail.com

Works with ANY signals database schema!
"""

import sqlite3
from datetime import datetime, timedelta
import sys


class UniversalSignalCleanup:
    """
    Auto-detects database schema and performs cleanup
    """
    
    def __init__(self, db_path='signals.db', dry_run=False):
        self.db_path = db_path
        self.dry_run = dry_run
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        
        # Detect schema
        self.schema = self._detect_schema()
        
    def _detect_schema(self):
        """Auto-detect database schema"""
        try:
            self.cursor.execute("PRAGMA table_info(signals)")
            columns = {row[1]: row[2] for row in self.cursor.fetchall()}
            
            if not columns:
                print("❌ ERROR: 'signals' table not found!")
                sys.exit(1)
            
            # Detect column names
            schema = {
                'id_col': 'id',
                'date_col': None,
                'ticker_col': None,
                'state_col': None,
                'score_col': None,
                'created_col': None
            }
            
            # Find date column
            date_candidates = ['date', 'detected_at', 'created_at', 'timestamp']
            for col in date_candidates:
                if col in columns:
                    schema['date_col'] = col
                    break
            
            # Find ticker/code column
            ticker_candidates = ['ticker', 'code', 'symbol', 'stock']
            for col in ticker_candidates:
                if col in columns:
                    schema['ticker_col'] = col
                    break
            
            # Find state column
            state_candidates = ['state', 'status', 'action']
            for col in state_candidates:
                if col in columns:
                    schema['state_col'] = col
                    break
            
            # Find score column
            score_candidates = ['quality_score', 'score', 'strength', 'confidence']
            for col in score_candidates:
                if col in columns:
                    schema['score_col'] = col
                    break
            
            schema['all_columns'] = list(columns.keys())
            
            return schema
            
        except Exception as e:
            print(f"❌ ERROR detecting schema: {e}")
            sys.exit(1)
    
    def get_stats(self):
        """Get database statistics"""
        stats = {}
        
        # Total count
        self.cursor.execute("SELECT COUNT(*) FROM signals")
        stats['total'] = self.cursor.fetchone()[0]
        
        # By date (if date column exists)
        if self.schema['date_col']:
            query = f"""
                SELECT {self.schema['date_col']}, COUNT(*) 
                FROM signals 
                GROUP BY {self.schema['date_col']} 
                ORDER BY {self.schema['date_col']} DESC
            """
            self.cursor.execute(query)
            stats['by_date'] = self.cursor.fetchall()
        else:
            stats['by_date'] = []
        
        # By state (if state column exists)
        if self.schema['state_col']:
            query = f"""
                SELECT {self.schema['state_col']}, COUNT(*) 
                FROM signals 
                GROUP BY {self.schema['state_col']}
            """
            self.cursor.execute(query)
            stats['by_state'] = dict(self.cursor.fetchall())
        else:
            stats['by_state'] = {}
        
        return stats
    
    def cleanup_old_signals(self, days_old=7):
        """Delete signals older than X days"""
        
        if not self.schema['date_col']:
            print("⚠️  No date column found - skipping age-based cleanup")
            return 0
        
        cutoff_date = (datetime.now() - timedelta(days=days_old)).strftime('%Y-%m-%d')
        
        # Count query
        count_query = f"""
            SELECT COUNT(*) FROM signals 
            WHERE {self.schema['date_col']} < ?
        """
        self.cursor.execute(count_query, (cutoff_date,))
        count = self.cursor.fetchone()[0]
        
        if count == 0:
            print(f"✅ No signals older than {days_old} days")
            return 0
        
        if self.dry_run:
            print(f"🔍 DRY RUN: Would delete {count} signals older than {cutoff_date}")
            
            # Show samples
            sample_query = f"""
                SELECT {self.schema['ticker_col'] or 'id'}, {self.schema['date_col']}
                FROM signals 
                WHERE {self.schema['date_col']} < ?
                ORDER BY {self.schema['date_col']} ASC
                LIMIT 5
            """
            self.cursor.execute(sample_query, (cutoff_date,))
            samples = self.cursor.fetchall()
            
            for row in samples:
                print(f"   → {row[0]} from {row[1]}")
            
            if count > 5:
                print(f"   ... and {count - 5} more")
        else:
            print(f"🗑️  Deleting {count} signals older than {cutoff_date}...")
            
            delete_query = f"""
                DELETE FROM signals 
                WHERE {self.schema['date_col']} < ?
            """
            self.cursor.execute(delete_query, (cutoff_date,))
            self.conn.commit()
            
            print(f"✅ Deleted {count} old signals")
        
        return count
    
    def cleanup_low_quality(self, min_score=30, days_old=1):
        """Delete low-quality signals"""
        
        if not self.schema['score_col']:
            print("⚠️  No score column found - skipping quality-based cleanup")
            return 0
        
        cutoff_date = (datetime.now() - timedelta(days=days_old)).strftime('%Y-%m-%d')
        
        # Build query
        conditions = [f"{self.schema['score_col']} < ?"]
        params = [min_score]
        
        if self.schema['date_col']:
            conditions.append(f"{self.schema['date_col']} < ?")
            params.append(cutoff_date)
        
        where_clause = " AND ".join(conditions)
        
        # Count query
        count_query = f"SELECT COUNT(*) FROM signals WHERE {where_clause}"
        self.cursor.execute(count_query, params)
        count = self.cursor.fetchone()[0]
        
        if count == 0:
            print(f"✅ No low-quality signals (score < {min_score})")
            return 0
        
        if self.dry_run:
            print(f"🔍 DRY RUN: Would delete {count} low-quality signals")
        else:
            print(f"🗑️  Deleting {count} low-quality signals...")
            
            delete_query = f"DELETE FROM signals WHERE {where_clause}"
            self.cursor.execute(delete_query, params)
            self.conn.commit()
            
            print(f"✅ Deleted {count} low-quality signals")
        
        return count
    
    def keep_only_latest_n(self, n=100):
        """Keep only the latest N signals"""
        
        if not self.schema['date_col']:
            print("⚠️  No date column found - cannot determine latest signals")
            return 0
        
        total = self.get_stats()['total']
        
        if total <= n:
            print(f"✅ Only {total} signals, keeping all (target: {n})")
            return 0
        
        # Get the Nth latest date
        query = f"""
            SELECT {self.schema['date_col']} 
            FROM signals 
            ORDER BY {self.schema['date_col']} DESC 
            LIMIT 1 OFFSET ?
        """
        self.cursor.execute(query, (n-1,))
        result = self.cursor.fetchone()
        
        if not result:
            return 0
        
        cutoff_date = result[0]
        
        # Count how many will be deleted
        count_query = f"""
            SELECT COUNT(*) FROM signals 
            WHERE {self.schema['date_col']} < ?
        """
        self.cursor.execute(count_query, (cutoff_date,))
        count = self.cursor.fetchone()[0]
        
        if self.dry_run:
            print(f"🔍 DRY RUN: Would delete {count} signals (keeping latest {n})")
        else:
            print(f"🗑️  Deleting {count} signals (keeping latest {n})...")
            
            delete_query = f"""
                DELETE FROM signals 
                WHERE {self.schema['date_col']} < ?
            """
            self.cursor.execute(delete_query, (cutoff_date,))
            self.conn.commit()
            
            print(f"✅ Deleted {count} signals, kept {n} latest")
        
        return count
    
    def full_cleanup(self, days_old=7, min_score=30, max_signals=200):
        """Run full cleanup"""
        
        print("=" * 70)
        print("🧹 UNIVERSAL SIGNAL CLEANUP")
        print("=" * 70)
        
        # Show schema
        print(f"\n📋 Detected Schema:")
        print(f"   Date column: {self.schema['date_col'] or 'NOT FOUND'}")
        print(f"   Ticker column: {self.schema['ticker_col'] or 'NOT FOUND'}")
        print(f"   Score column: {self.schema['score_col'] or 'NOT FOUND'}")
        print(f"   State column: {self.schema['state_col'] or 'NOT FOUND'}")
        
        # Show current stats
        stats = self.get_stats()
        print(f"\n📊 Current State:")
        print(f"   Total signals: {stats['total']}")
        
        if stats['by_state']:
            print(f"   By state: {stats['by_state']}")
        
        if stats['by_date']:
            print(f"   Date range: {stats['by_date'][-1][0]} to {stats['by_date'][0][0]}")
            print(f"   Dates with signals: {len(stats['by_date'])}")
        
        print("\n" + "-" * 70)
        
        total_deleted = 0
        
        # Cleanup 1: Old signals
        print(f"\n1️⃣  Cleanup: Signals older than {days_old} days")
        total_deleted += self.cleanup_old_signals(days_old=days_old)
        
        # Cleanup 2: Low quality
        print(f"\n2️⃣  Cleanup: Low-quality signals (score < {min_score})")
        total_deleted += self.cleanup_low_quality(min_score=min_score)
        
        # Cleanup 3: Keep only latest N
        current_total = self.get_stats()['total']
        if current_total > max_signals:
            print(f"\n3️⃣  Cleanup: Keep only latest {max_signals} signals")
            total_deleted += self.keep_only_latest_n(n=max_signals)
        
        # Final stats
        print("\n" + "-" * 70)
        final_stats = self.get_stats()
        print(f"\n📊 Final State:")
        print(f"   Remaining: {final_stats['total']} signals")
        print(f"   Deleted: {total_deleted} signals")
        
        print("\n" + "=" * 70)
        if self.dry_run:
            print("🔍 DRY RUN COMPLETE - No changes made")
        else:
            print("✅ CLEANUP COMPLETE")
        print("=" * 70)
        
        return total_deleted
    
    def close(self):
        """Close database connection"""
        self.conn.close()


def main():
    """CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Universal Signal Cleanup - Works with any schema!',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--db', default='signals.db', help='Database file path')
    parser.add_argument('--dry-run', action='store_true', help='Preview without deleting')
    parser.add_argument('--days', type=int, default=7, help='Delete signals older than X days')
    parser.add_argument('--min-score', type=int, default=30, help='Delete signals below this score')
    parser.add_argument('--keep-latest', type=int, default=200, help='Keep only N latest signals')
    parser.add_argument('--stats-only', action='store_true', help='Show stats only')
    parser.add_argument('--aggressive', action='store_true', help='Use 3 days instead of 7')
    
    args = parser.parse_args()
    
    # Adjust days for aggressive mode
    days_old = 3 if args.aggressive else args.days
    
    try:
        cleanup = UniversalSignalCleanup(
            db_path=args.db,
            dry_run=args.dry_run or args.stats_only
        )
        
        if args.stats_only:
            # Just show stats
            print("=" * 70)
            print("📊 DATABASE STATISTICS")
            print("=" * 70)
            
            stats = cleanup.get_stats()
            print(f"\nTotal signals: {stats['total']}")
            
            if stats['by_state']:
                print(f"\nBy state:")
                for state, count in stats['by_state'].items():
                    print(f"  {state}: {count}")
            
            if stats['by_date']:
                print(f"\nBy date (last 10):")
                for date, count in stats['by_date'][:10]:
                    print(f"  {date}: {count} signals")
            
            print("=" * 70)
        else:
            # Full cleanup
            cleanup.full_cleanup(
                days_old=days_old,
                min_score=args.min_score,
                max_signals=args.keep_latest
            )
        
        cleanup.close()
        
    except FileNotFoundError:
        print(f"❌ ERROR: Database file '{args.db}' not found!")
        sys.exit(1)
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
