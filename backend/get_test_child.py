"""获取或创建测试用的child_id"""
import sqlite3
import sys

db_path = "storage/app/database.sqlite"

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查是否有现有的children记录
    cursor.execute("SELECT id, name FROM children LIMIT 5;")
    children = cursor.fetchall()
    
    if children:
        print("现有的children记录:")
        for child_id, name in children:
            print(f"  ID: {child_id}, 姓名: {name}")
        print(f"\n推荐使用 child_id: {children[0][0]}")
        print(f"child_id={children[0][0]}")
    else:
        print("数据库中没有children记录")
        print("需要先创建一个child记录")
        # 创建一个测试child
        cursor.execute("""
            INSERT INTO children (name, gender, birth_date, avatar_url, created_at, updated_at)
            VALUES ('测试小朋友', '男', '2015-01-01', NULL, datetime('now'), datetime('now'))
        """)
        conn.commit()
        child_id = cursor.lastrowid
        print(f"已创建测试child记录, ID: {child_id}")
        print(f"child_id={child_id}")
    
    conn.close()
    
except Exception as e:
    print(f"错误: {e}")
    sys.exit(1)