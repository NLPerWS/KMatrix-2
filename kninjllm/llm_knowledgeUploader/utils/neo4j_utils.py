import json
from neo4j import GraphDatabase, basic_auth

class Neo4jHandler:
    def __init__(self, uri,dbname, username, password):
        self.uri = uri
        self.dbname = dbname
        self.username = username
        self.password = password
        
    def do_query(self,cypher_query,cypher_json):
        self.driver = GraphDatabase.driver(self.uri,auth=basic_auth(self.username, self.password))
        # # cypher语句 + 参数
        # cypher_query = '''
        # MATCH (a:Officer {name:$name})-[r:officer_of|intermediary_of|registered_address*..10]-(b)
        # RETURN b.name as name LIMIT 20
        # '''
        # cypher_json = {
        #     "name":"Ross, Jr. - Wilbur Louis"
        # }
        # # 只使用cypher语句
        # cypher_query = '''
        # MATCH (a:Officer {name:"Ross, Jr. - Wilbur Louis"})-[r:officer_of|intermediary_of|registered_address*..10]-(b)
        # RETURN b.name as name LIMIT 20
        # '''
        # cypher_json = {}
        
        final_results = []
        with self.driver.session(database=self.dbname) as session:
            results = session.read_transaction(
                lambda tx: tx.run(cypher_query,cypher_json).data())
            for record in results:
                final_results.append(record)

        self.driver.close()
        return final_results


    # def close(self):
    #     self.driver.close()

    # def execute_query(self, query, parameters=None):

    #     if parameters is None:
    #         parameters = {}
        
    #     with self.driver.session() as session:
    #         result = session.run(query, parameters)
            
    #         if query.strip().upper().startswith("MATCH"):
    #             # 如果是查询语句，返回结果
    #             return [record.data() for record in result]
    #         else:
    #             # 如果是增删改，提交事务并返回成功标志
    #             return "Transaction successful"

    # # 根据实体属性,查询id
    # def get_node_ids(self, label, parameters):
    #     # 将字典转换为 Cypher 查询的属性格式
    #     param_str = ', '.join([f"{key}: ${key}" for key in parameters.keys()])
    #     query = f"MATCH (n:{label} {{{param_str}}}) RETURN n"
        
    #     result = self.execute_query(query, parameters)
        
        
    #     ids = []
    #     for res in result:
    #         ids.append(res['n']['id'])
    #     return ids


    # def create_node_if_not_exists(self, label, parameters):
    #     # 查询是否已存在该 id 的节点
    #     check_query = f"MATCH (p:{label} {{id: $id}}) RETURN p"
    #     existing = self.execute_query(check_query, {"id": parameters['id']})
        
    #     # 如果不存在，则创建节点
    #     if not existing:
    #         props = ", ".join([f"{key}: ${key}" for key in parameters.keys()])
    #         create_query = f"CREATE (p:{label} {{{props}}})"
    #         return self.execute_query(create_query, parameters)
    #     else:
    #         print("Node with this ID already exists.")
    #         return ""

    # def create_relationship(self, from_node_label,from_node_key, from_node_value, to_node_label, to_node_key, to_node_value,relationship_type):
    #     query = (
    #         f"MATCH (a:{from_node_label} {{{from_node_key}: $from_id}}), (b:{to_node_label} {{{to_node_key}: $to_id}}) "
    #         f"MERGE (a)-[r:{relationship_type}]->(b) "
    #         "RETURN r"
    #     )
    #     parameters = {"from_id": from_node_value, "to_id": to_node_value}
    #     return self.execute_query(query, parameters)

    # def delete_all_nodes(self):
    #     query = "MATCH (n) DETACH DELETE n"
    #     self.execute_query(query)
        
        
def testNode(neo4j_handler):

    # 删除所有节点 并创建新节点
    neo4j_handler.delete_all_nodes()
    neo4j_handler.create_node_if_not_exists('Person', {"name": "Alice", "age": 30,"id":"1"})
    neo4j_handler.create_node_if_not_exists('Person', {"name": "Bob", "age": 24,"id":"2"})
    
    query = f"MATCH (n:Person) RETURN n"
    res = neo4j_handler.execute_query(query=query)
    print(res)


def testRelationship(neo4j_handler):
    
    # # # 删除所有节点 并创建新节点
    # neo4j_handler.delete_all_nodes()
    
    # insert_list = [
    #     {"name": "Alice", "age": 1, "id": "1"},
    #     {"name": "Bob", "age": 2, "id": "2"},
    #     {"name": "Charlie", "age": 3, "id": "3"},
    #     {"name": "David", "age": 4, "id": "4"},
    #     {"name": "Eva", "age": 5, "id": "5"},
    #     {"name": "Frank", "age": 6, "id": "6"},
    #     {"name": "Grace", "age": 7, "id": "7"},
    #     {"name": "Henry", "age": 8, "id": "8"},
    #     {"name": "Ivy", "age": 9, "id": "9"},
    #     {"name": "Jack", "age": 10, "id": "10"},
    #     {"name": "Kathy", "age": 11, "id": "11"},
    #     {"name": "Leo", "age": 12, "id": "12"},
    #     {"name": "Mona", "age": 13, "id": "13"},
    #     {"name": "Nora", "age": 14, "id": "14"},
    #     {"name": "Oscar", "age": 15, "id": "15"},
    #     {"name": "Paul", "age": 16, "id": "16"},
    #     {"name": "Quincy", "age": 17, "id": "17"},
    #     {"name": "Rita", "age": 18, "id": "18"},
    #     {"name": "Sam", "age": 19, "id": "19"},
    #     {"name": "Tina", "age": 20, "id": "20"},
    #     {"name": "Uma", "age": 21, "id": "21"},
    #     {"name": "Victor", "age": 22, "id": "22"},
    #     {"name": "Wendy", "age": 23, "id": "23"},
    #     {"name": "Xander", "age": 24, "id": "24"},
    #     {"name": "Yvonne", "age": 25, "id": "25"},
    #     {"name": "Zack", "age": 26, "id": "26"},
    # ]
    # for insert in insert_list:
    #     neo4j_handler.create_node_if_not_exists('Person', insert)
    
    # # 创建关系
    # print("Creating relationship...")
    # neo4j_handler.create_relationship("Person", "id", "1", "Person", "id", "2", "FRIEND")
    # neo4j_handler.create_relationship("Person", "id", "1", "Person", "id", "4", "FAMILY")
    # neo4j_handler.create_relationship("Person", "id", "1", "Person", "id", "9", "FRIEND")
    # neo4j_handler.create_relationship("Person", "id", "3", "Person", "id", "4", "COLLEAGUE")
    # neo4j_handler.create_relationship("Person", "id", "5", "Person", "id", "6", "FAMILY")
    # neo4j_handler.create_relationship("Person", "id", "7", "Person", "id", "8", "FRIEND")
    # neo4j_handler.create_relationship("Person", "id", "9", "Person", "id", "10", "NEIGHBOR")
    # neo4j_handler.create_relationship("Person", "id", "11", "Person", "id", "12", "FRIEND")
    # neo4j_handler.create_relationship("Person", "id", "13", "Person", "id", "14", "COLLEAGUE")
    # neo4j_handler.create_relationship("Person", "id", "15", "Person", "id", "16", "FAMILY")
    # neo4j_handler.create_relationship("Person", "id", "17", "Person", "id", "18", "FRIEND")
    # neo4j_handler.create_relationship("Person", "id", "19", "Person", "id", "20", "NEIGHBOR")
    # neo4j_handler.create_relationship("Person", "id", "21", "Person", "id", "22", "FRIEND")
    # neo4j_handler.create_relationship("Person", "id", "23", "Person", "id", "24", "COLLEAGUE")
    # neo4j_handler.create_relationship("Person", "id", "25", "Person", "id", "26", "FAMILY")
    # neo4j_handler.create_relationship("Person", "id", "11", "Person", "id", "1", "FRIEND")
    # neo4j_handler.create_relationship("Person", "id", "15", "Person", "id", "1", "ARMY")

    # 读取关系
    print("Reading relationships...")
    
    # id = neo4j_handler.get_node_ids('Entity',{})[0]
    # # 与 实体 有关系的
    # query = f"MATCH (a:Person {{id: '{id}'}})-[r]->(b) RETURN type(r) AS relationship, b AS related_node"
    # # 与 实体关系为 FRIEND 的
    # # query = f"MATCH (a:Person {{id: '{id}'}})-[r:FRIEND]->(b) RETURN type(r) AS relationship, b AS related_node"
    
    query = '''
        MATCH (a:Officer {name:$name})-[r:officer_of|intermediary_of|registered_address*..10]-(b)
        RETURN b.name as name LIMIT 20
    '''
    relationships = neo4j_handler.execute_query(query=query)
    print(relationships)

