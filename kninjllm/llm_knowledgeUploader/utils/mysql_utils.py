import json
import mysql.connector
from mysql.connector import Error,pooling
import traceback

class MySQLUtils:
    def __init__(self, host, user, password, database):
        """初始化数据库连接"""
        self.host = host.split(":")[0]
        self.port = host.split(":")[1]
        self.user = user
        self.password = password
        self.database = database
        
        pool = mysql.connector.pooling.MySQLConnectionPool(
            pool_name="mypool",
            pool_size=5,
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database
        )
        self.connection = pool.get_connection()
        # self.cursor = self.connection.cursor()

    def disconnect(self):
        """断开数据库连接"""
        if self.connection.is_connected():
            self.connection.close()
            print("Database connection closed")
    def execute_query(self, query, params=None):
        """执行插入、更新、删除操作"""
        if not self.connection.is_connected():
            self.connect()
            
        cursor = self.connection.cursor(dictionary=True)  # 设置 cursor 为字典游标
        cursor.execute(query, params)
        
        results = cursor.fetchall()

        cursor.close()

        # 将结果转换为 JSON 格式
        json_results = json.dumps(results, ensure_ascii=False)

        return json_results
    
    def fetch_query(self, query, params=None):
        """执行选择操作并获取结果"""
        if not self.connection.is_connected():
            self.connect()
        
        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute(query, params)
            result = cursor.fetchall()
            return result
        except Error as e:
            print(f"Error: {e}")
            return None
        finally:
            cursor.close()

# 使用该类的示例
if __name__ == "__main__":
    pass
