#!/usr/bin/env python3
"""
Database Cleanup Tool
Remove invalid stock symbols and keep only real NASDAQ/AMEX stocks
"""

import sqlite3
from fast_stock_validator import FastStockValidator

def cleanup_database():
    """Clean the database by removing invalid stock symbols"""
    print("🧹 StockHark Database Cleanup")
    print("=" * 50)
    
    # Initialize fast validator
    validator = FastStockValidator()
    
    if len(validator.all_symbols) == 0:
        print("❌ No symbols loaded from JSON files")
        return False
    
    # Connect to database
    conn = sqlite3.connect('stocks.db')
    cursor = conn.cursor()
    
    # Get current database stats
    cursor.execute('SELECT COUNT(*) FROM stock_data')
    total_mentions = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT symbol) FROM stock_data')
    unique_symbols = cursor.fetchone()[0]
    
    print(f"📊 Current Database:")
    print(f"   Total mentions: {total_mentions:,}")
    print(f"   Unique symbols: {unique_symbols:,}")
    
    # Get all symbols and their counts
    cursor.execute('''
        SELECT symbol, COUNT(*) as mentions
        FROM stock_data 
        GROUP BY symbol 
        ORDER BY mentions DESC
    ''')
    
    all_symbols = cursor.fetchall()
    
    # Validate each symbol
    print(f"\n🔍 Validating symbols...")
    
    valid_symbols = []
    invalid_symbols = []
    
    for symbol, mentions in all_symbols:
        if validator.is_valid_symbol(symbol):
            valid_symbols.append((symbol, mentions))
        else:
            invalid_symbols.append((symbol, mentions))
    
    valid_mentions = sum(mentions for _, mentions in valid_symbols)
    invalid_mentions = sum(mentions for _, mentions in invalid_symbols)
    
    print(f"\n📈 Validation Results:")
    print(f"   ✅ Valid symbols: {len(valid_symbols)} ({len(valid_symbols)/len(all_symbols)*100:.1f}%)")
    print(f"   ❌ Invalid symbols: {len(invalid_symbols)} ({len(invalid_symbols)/len(all_symbols)*100:.1f}%)")
    print(f"   ✅ Valid mentions: {valid_mentions:,} ({valid_mentions/total_mentions*100:.1f}%)")
    print(f"   ❌ Invalid mentions: {invalid_mentions:,} ({invalid_mentions/total_mentions*100:.1f}%)")
    
    if len(invalid_symbols) == 0:
        print(f"\n🎉 Database is already clean! No cleanup needed.")
        conn.close()
        return True
    
    # Show what will be removed
    print(f"\n🗑️  Top 10 Invalid Symbols to Remove:")
    for i, (symbol, mentions) in enumerate(sorted(invalid_symbols, key=lambda x: x[1], reverse=True)[:10], 1):
        print(f"   {i:2}. {symbol:<8} - {mentions:,} mentions")
    
    # Ask for confirmation
    print(f"\n⚠️  This will permanently delete {invalid_mentions:,} mentions ({len(invalid_symbols)} symbols)")
    response = input("Continue with cleanup? (y/N): ").strip().lower()
    
    if response != 'y':
        print("❌ Cleanup cancelled")
        conn.close()
        return False
    
    # Perform cleanup
    print(f"\n🧹 Cleaning database...")
    
    # Delete invalid symbols
    invalid_symbol_list = [symbol for symbol, _ in invalid_symbols]
    
    # Use parameterized query for safety
    placeholders = ','.join('?' * len(invalid_symbol_list))
    delete_query = f'DELETE FROM stock_data WHERE symbol IN ({placeholders})'
    
    cursor.execute(delete_query, invalid_symbol_list)
    deleted_rows = cursor.rowcount
    
    conn.commit()
    
    # Get updated stats
    cursor.execute('SELECT COUNT(*) FROM stock_data')
    new_total_mentions = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT symbol) FROM stock_data')
    new_unique_symbols = cursor.fetchone()[0]
    
    print(f"\n✅ Cleanup Complete!")
    print(f"   Deleted mentions: {deleted_rows:,}")
    print(f"   Remaining mentions: {new_total_mentions:,}")
    print(f"   Remaining symbols: {new_unique_symbols:,}")
    print(f"   Database size reduced by: {(deleted_rows/total_mentions)*100:.1f}%")
    
    # Show top remaining stocks
    print(f"\n🔥 Top 10 Remaining Valid Stocks:")
    cursor.execute('''
        SELECT symbol, COUNT(*) as mentions,
               SUM(CASE WHEN sentiment_label = 'bullish' THEN 1 ELSE 0 END) as bullish,
               SUM(CASE WHEN sentiment_label = 'bearish' THEN 1 ELSE 0 END) as bearish
        FROM stock_data 
        GROUP BY symbol 
        ORDER BY mentions DESC
        LIMIT 10
    ''')
    
    top_stocks = cursor.fetchall()
    
    print(f"{'Rank':<4} {'Symbol':<8} {'Mentions':<8} {'Bullish':<7} {'Bearish':<7}")
    print("-" * 50)
    
    for i, (symbol, mentions, bullish, bearish) in enumerate(top_stocks, 1):
        print(f"{i:<4} ${symbol:<7} {mentions:<8} {bullish:<7} {bearish:<7}")
    
    conn.close()
    
    print(f"\n🎯 Next Steps:")
    print(f"   1. Your database now contains only valid NASDAQ/AMEX stocks")
    print(f"   2. Future data collection will use fast validation")
    print(f"   3. Run 'python app.py' to see clean results")
    print(f"   4. Visit http://localhost:5000 for updated dashboard")
    
    return True

def backup_database():
    """Create a backup before cleanup"""
    import shutil
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"stocks_backup_{timestamp}.db"
    
    try:
        shutil.copy2('stocks.db', backup_name)
        print(f"✅ Database backed up to: {backup_name}")
        return True
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return False

if __name__ == "__main__":
    print("🧹 StockHark Database Cleanup Tool")
    print("=" * 50)
    
    print("\nThis tool will:")
    print("✅ Validate all symbols against NASDAQ/AMEX data")
    print("🗑️  Remove invalid symbols (common words, fake tickers)")
    print("💾 Keep only real stock symbols")
    print("📊 Show before/after statistics")
    
    try:
        # Create backup first
        if backup_database():
            print()
            # Perform cleanup
            if cleanup_database():
                print(f"\n🎉 Database cleanup successful!")
            else:
                print(f"\n❌ Database cleanup failed or cancelled")
        else:
            print(f"❌ Cannot proceed without backup")
            
    except KeyboardInterrupt:
        print(f"\n\n⏹️  Cleanup cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()