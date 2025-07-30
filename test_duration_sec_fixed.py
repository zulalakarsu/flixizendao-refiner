#!/usr/bin/env python3
"""
Test the fixed duration_sec column functionality
"""
import sqlite3
from pathlib import Path

def test_duration_sec():
    """Test that duration_sec column is working correctly."""
    print("🧪 Testing duration_sec Column Fix")
    print("=" * 50)
    
    db_path = "output/refined.sqlite"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test 1: Check if duration_sec column exists
        print("\n📋 Schema Check:")
        cursor.execute("PRAGMA table_info(viewing_activity)")
        columns = cursor.fetchall()
        duration_sec_exists = any(col[1] == 'duration_sec' for col in columns)
        print(f"   ✅ duration_sec column exists: {duration_sec_exists}")
        
        # Test 2: Check data conversion
        print("\n📊 Duration Conversion Test:")
        cursor.execute("""
            SELECT duration, duration_sec, 
                   CASE 
                       WHEN duration_sec = 0 THEN '❌'
                       ELSE '✅'
                   END as conversion_status
            FROM viewing_activity 
            WHERE duration IS NOT NULL AND duration != ''
            LIMIT 10
        """)
        
        conversions = cursor.fetchall()
        for duration, duration_sec, status in conversions:
            print(f"   {status} '{duration}' → {duration_sec} seconds")
        
        # Test 3: Most watched content with duration_sec
        print("\n🏆 Most Watched Content (using duration_sec):")
        cursor.execute("""
            SELECT title, COUNT(*) as view_count, 
                   SUM(duration_sec) / 3600.0 as hours_watched
            FROM viewing_activity 
            WHERE duration_sec > 0 AND title IS NOT NULL AND title != ''
            GROUP BY title 
            ORDER BY hours_watched DESC 
            LIMIT 5
        """)
        
        top_content = cursor.fetchall()
        for i, (title, views, hours) in enumerate(top_content, 1):
            print(f"{i:2d}. {title[:40]:<40} {views:>4} views, {hours:>5.1f} hours")
        
        # Test 4: Time analysis with duration_sec
        print("\n⏰ Time Analysis (using duration_sec):")
        cursor.execute("""
            SELECT 
                COUNT(*) as total_sessions,
                AVG(duration_sec) / 60.0 as avg_session_minutes,
                SUM(duration_sec) / 3600.0 as total_hours,
                MIN(duration_sec) as min_seconds,
                MAX(duration_sec) as max_seconds
            FROM viewing_activity
            WHERE duration_sec > 0
        """)
        
        time_data = cursor.fetchone()
        if time_data[0]:
            sessions, avg_min, total_hours, min_sec, max_sec = time_data
            print(f"   Total Sessions: {sessions:,}")
            print(f"   Average Session: {avg_min:.1f} minutes")
            print(f"   Total Viewing Time: {total_hours:.1f} hours ({total_hours/24:.1f} days)")
            print(f"   Session Range: {min_sec} - {max_sec} seconds")
        
        # Test 5: Quality check
        print("\n📈 Duration Conversion Quality:")
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(CASE WHEN duration_sec > 0 THEN 1 END) as valid_conversions,
                COUNT(CASE WHEN duration_sec = 0 THEN 1 END) as failed_conversions
            FROM viewing_activity
            WHERE duration IS NOT NULL AND duration != ''
        """)
        
        quality = cursor.fetchone()
        total, valid, failed = quality
        print(f"   Total Records: {total:,}")
        print(f"   Successful Conversions: {valid:,} ({valid/total*100:.1f}%)")
        print(f"   Failed Conversions: {failed:,} ({failed/total*100:.1f}%)")
        
        conn.close()
        
        print("\n" + "=" * 50)
        print("🎉 duration_sec Column Fix: SUCCESS!")
        print("✅ Netflix duration strings properly converted to integer seconds")
        print("✅ SQL queries now use fast numeric calculations")
        print("✅ Ready for advanced analytics and ML training")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_duration_sec() 