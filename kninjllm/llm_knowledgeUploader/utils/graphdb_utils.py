from SPARQLWrapper import SPARQLWrapper, JSON

class GraphHandler:
    def __init__(self, uri,dbname, username, password):
        # 创建SPARQLWrapper对象
        if not str(uri).endswith("/"):
            uri = uri + "/"
        uri = uri + "repositories/" + dbname
        self.sparql = SPARQLWrapper(uri)
        # 设置身份验证信息
        self.sparql.setCredentials(username, password)
        
    def execute_query(self, query):
        self.sparql.setQuery(query)
        # 设置返回格式
        self.sparql.setReturnFormat(JSON)
        # 执行查询并获取结果
        results = self.sparql.query().convert()
        # print('-------------------------results-----------------------')
        # print(results)
        res_list = []
        # 处理结果
        for result in results["results"]["bindings"]:
            # print(result["subject"]["value"], result["predicate"]["value"], result["object"]["value"])
            res_list.append(result)
        return res_list
