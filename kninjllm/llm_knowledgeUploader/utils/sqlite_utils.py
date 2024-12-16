import sqlite3
import json


class SQLiteHandler:
    def __init__(self, db_name):
        self.db_name = db_name

    def execute_sql(self, sql_statement):
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()

            if sql_statement.strip().lower().startswith("select"):
                cursor.execute(sql_statement)
                columns = [description[0] for description in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                response = results
            else:
                cursor.execute(sql_statement)
                conn.commit()
                response = cursor.rowcount

        except sqlite3.Error as err:
            response = str(err)
        
        finally:
            conn.close()
        
        return json.dumps(response, ensure_ascii=False)
