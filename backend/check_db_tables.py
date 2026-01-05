"""检查数据库中的表"""
import sqlite3
import sys

db_path = "storage/app/database.sqlite"

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 获取所有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("数据库中的表:")
    for table in tables:
        print(f"  - {table[0]}")
    
    # 检查钱包相关的表
    wallet_tables = ['savings_boxes', 'pocket_money', 'wallet_transactions']
    existing_wallet_tables = [t[0] for t in tables if t[0] in wallet_tables]
    
    if existing_wallet_tables:
        print(f"\n发现钱包表: {existing_wallet_tables}")
        print("\n由于表已存在,需要标记迁移为已完成或删除表后重新迁移")
        
        # 检查表结构
        for table_name in existing_wallet_tables:
            print(f"\n{table_name} 表结构:")
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  {col[1]} {col[2]}")
    
    conn.close()
    
except Exception as e:
    print(f"错误: {e}")
    sys.exit(1)