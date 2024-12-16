import traceback
from root_config import RootConfig
from kninjllm.llm_utils.common_utils import set_proxy,unset_proxy
import time
import json
import requests
import os
import time
import traceback
import re
from SPARQLWrapper import SPARQLExceptions,SPARQLWrapper, JSON
from kninjllm.llm_generator.base_generator.wikidata_emnlp23.utils import get_query_sparql,proxy_query_wiki

from kninjllm.llm_knowledgeUploader.utils.sqlite_utils import SQLiteHandler
from kninjllm.llm_knowledgeUploader.utils.mysql_utils import MySQLUtils

from kninjllm.llm_knowledgeUploader.utils.neo4j_utils import Neo4jHandler
from kninjllm.llm_knowledgeUploader.utils.graphdb_utils import GraphHandler


from kninjllm.llm_retriever.contriever.Contriever_retriever import Contriever_Retriever
from kninjllm.llm_queryGenerator.sparql_language_generator import Sparql_language_generator
from kninjllm.llm_queryGenerator.natural_language_generator import Natural_language_generator
from kninjllm.llm_queryGenerator.sql_language_generator import Sql_language_generator
from kninjllm.llm_queryGenerator.cql_language_generator import Cql_language_generator



class InterfaceExecute:
    def __init__(self,domain, type, url,parser,tables):
        self.domain = domain
        self.type = type
        self.url = url
        self.parser = parser
        self.tables = tables

        if self.parser == "SPARQLParser/Parser":

            self.language_generator_parser = Sparql_language_generator(tables=self.tables)
            
        elif self.parser == "NLParser/Parser":
            self.language_generator_parser = Natural_language_generator()

        elif self.parser == "SqlParser/Parser":
            info = self.getInfoByUrl(self.url)
            db_info = {
                "host":info['base_url'],
                "user":info['username'],
                "password":info['password'],
                "database":info['dbname']
            }
            self.language_generator_parser = Sql_language_generator(db_info=db_info, tables=self.tables, device=RootConfig.CUDA_VISIBLE_DEVICES)
            
        elif self.parser == "CQLParser/Parser":
            self.language_generator_parser = Cql_language_generator()

        else:
            raise ValueError("parser type error")

        if type == "local":
            if not self.url.startswith("/"):
                read_path = os.path.join(RootConfig.root_path,self.url)
            else:
                read_path = self.url
            if os.path.isfile(read_path) and read_path.endswith(".jsonl"):
                try:
                    with open(read_path,'r',encoding='utf-8') as f:
                        self.data_list = [json.loads(line) for line in f.readlines()]
                except:
                    raise ValueError(f"this file not exist {read_path}")
            else:
                self.data_list = []

            self.contriever = Contriever_Retriever(searchDataList=[],top_k=1,model_path=RootConfig.contriever_model_path)
        else:
            self.contriever = None
            
      
    def execute_by_google(self,input):
        
        print("-----------------execute_by_google-------------------------")

        def execute_google_query(query,search_char):
            if "wikipedia" in search_char:
                search_char = "https://en.wikipedia.org/wiki"
            
            unset_proxy()
            time.sleep(1)
            url = "https://google.serper.dev/search"
            payload = json.dumps({
            "q": query
            })
            headers = {
            'X-API-KEY': RootConfig.google_search_key,
            'Content-Type': 'application/json'
            }
            response = requests.request("POST", url, headers=headers, data=payload)
            # if response.COD
            if response.status_code==200:
                results=response.json()
            else:
                raise Exception("google key error!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            knowl = ""
            if "answer_box" in results:
                if "snippet" in results["answer_box"]:
                    knowl += results["answer_box"]["snippet"]
                    knowl += " "
            # organic answers
            if "organic" in results:
                organic_result=results["organic"]
                organic_result_sort=[]
                for single_organic_result in organic_result:
                    if search_char in single_organic_result["link"]:
                        organic_result_sort.append(single_organic_result)
                # yield maximun 3 snippets
                if len(knowl) == 0:
                    # if no answer box, yield maximun 3 snippets
                    num_snippets = min(5, len(organic_result_sort))
                else:
                    num_snippets = min(0, len(organic_result_sort))
                
                organic_result_sort = sorted(organic_result_sort,key = lambda i:len(i),reverse=True)
                    
                for i in range(num_snippets):
                    if "snippet" in organic_result_sort[i]:
                        knowl += organic_result_sort[i]["snippet"]
                        knowl += "\n"
            return knowl

        print("Generate query...")
        # 注释：查询query生成器
        query = self.language_generator_parser.run(query=input)['final_result']
        # query = input
        # 注释：查询query生成器
        # print(query)
        print("Retrieve  knowledge...")
        # 注释：查询接口
        knowl = execute_google_query(query+" "+self.url,self.url.replace("@",""))
        # 注释：查询接口
        # print(knowl)
        return input,input+" "+self.url,knowl

    def execute_by_wiki(self,input):
        
        print("-----------------execute_by_wiki-------------------------")

        def query_wiki(query):
            unset_proxy()
            while True:
                try:
                    # # 直接访问
                    sparql = SPARQLWrapper(self.url)
                    sparql.setQuery(query)
                    sparql.setTimeout(1)
                    sparql.setReturnFormat(JSON)
                    results = sparql.query().convert()
                    item_labels = []
                    if "results" in results:
                        for result in results["results"]["bindings"][:10]:
                            item_labels.append(result)
                    return item_labels
                except:
                    # traceback.print_exc()
                    try:
                        res = proxy_query_wiki(query)
                        return res
                    except:
                        traceback.print_exc()
                        time.sleep(65)
                        print("query wiki error sleep 65 minutes")
                        # return []

        def get_entity_name(entity_id):
            
            url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&format=json&ids={entity_id}"
            # response = requests.get(url)
            response = get_query_sparql(url=url)
            
            data = response.json()

            # Extract the entity name
            entity = data["entities"][entity_id]
            # print("entity = data[entities][entity_id]:",entity)
            try:
                entity_name = entity["labels"]["en"]["value"]  # Assuming you want the English name
            except:
                entity_name=""
                print("entity has no label")

            return entity_name

        def get_wiki_info(list_of_info):
            
            info_list = []
            print("get_wiki_info(list_of_info):\n",list_of_info)
            for i in range(len(list_of_info)):
                tmp_info = list_of_info[i]
                
                if len(tmp_info) == 1:
                    try:
                        tmp_value=tmp_info["x"]['value']
                        if 'http://www.wikidata.org/' in tmp_value:
                            info_list.append(get_entity_name(tmp_value.split('/')[-1]))
                        else:
                            info_list.append(tmp_value)
                    except:
                        pass
                else:
                    # ans_1 ans_2
                    try:
                        tmp_info=list(tmp_info.values())
                        # print("tmp_info=list(tmp_info.values()):",tmp_info)
                        
                        info_list.append(get_entity_name(tmp_info[0]['value'].split('/')[-1]))
                        info_list.append(get_entity_name(tmp_info[1]['value'].split('/')[-1]))
                    except:
                        print("tmp_info is []")
                        pass
                    
            
            # convert list to string
            opt = ''
            for i in info_list:
                opt += i
                opt += ', '
                
            return opt[:-2]+'.'

        def execute_wiki_query(query, processed_query):
            knowl = ""
            info = query_wiki(processed_query)
                
            if len(info) != 0:
                tmp_answer = get_wiki_info(info)
                knowl += processed_query.strip()
                knowl += "\n Answer: "
                knowl += tmp_answer.strip()
            return knowl


        # endpoint_url = "https://query.wikidata.org/sparql"
        print("Generate query...")
        query = input
        processed_query = self.language_generator_parser.run(query=query)['final_result']
        # processed_query = query
        # 注释：查询query生成器
        print("Generate query result:",processed_query)
        print("Retrieve knowledge...")
        time.sleep(1)
        knowl = execute_wiki_query(query, processed_query)
        return input,processed_query,knowl
        
    # 不用 
    def execute_by_local(self,input):
        self.contriever.searchDataList = self.data_list
        res = self.contriever.run(query = input)['final_result'][0]
        knowl = ""
        for ctx in res['ctxs']:
            knowl += ctx['content'] + "\n"
            
        return input,input,knowl
    
    # 关系型数据库接口 (mysql)
    def execute_by_RDBMS(self,input):

        try:
            # 调用sql生成器 生成sql语句
            query = self.language_generator_parser.run(query=input)['final_result']
            print("----------------mysql query--------------------\n",query)
            
            info = self.getInfoByUrl(self.url)
            db_handler = MySQLUtils(host=info['base_url'], user=info['username'], password=info['password'], database=info['dbname'])
            results = db_handler.execute_query(query)
            knowl = input + "\nAnswer: " + str(results)
            
        except:
            traceback.print_exc()
            query = ""
            knowl = ""
            
        if isinstance(knowl,list):
            knowl = str(knowl)
        return input,query,knowl 
        
    # 图数据库接口 neo4j
    def execute_by_GDBMS(self,input):
        
        # 动态获取用户输入的url,username,password 如果用户没有输入,就使用默认配置
        if self.url != "":
            info = self.getInfoByUrl(self.url)
            if info['username'] != "" and info['password'] != "" and info['dbname'] != "" and info['base_url'] != "":
                NEO4J_HOST = info['base_url']
                NEO4J_DEFAULT_DB =  info['dbname']
                NEO4J_USERNAME = info['username']
                NEO4J_PASSWORD =  info['password']
                    
        try:
            # 调用cql生成器 生成cql语句 需要先生成 sparql语句
            sparql_parser = Sparql_language_generator(tables=self.tables)
            sparql_query = sparql_parser.run(query=input)['final_result']
            
            # sparql_query = 'SELECT DISTINCT ?e WHERE { ?e <pred:instance_of> ?c . ?c <pred:name> "human" }'
            
            query = self.language_generator_parser.run(query=sparql_query)['final_result']
            cypher_json = {}            
            neo4j_handler = Neo4jHandler(NEO4J_HOST,NEO4J_DEFAULT_DB,  NEO4J_USERNAME,  NEO4J_PASSWORD)
            results = neo4j_handler.do_query(query,cypher_json)
            knowl = input + "\nAnswer: " + str(results)
            
        except:
            traceback.print_exc()
            query = ""
            knowl = ""
        if isinstance(knowl,list):
            knowl = str(knowl)
        return input,query,knowl 
            
    # 图数据库接口 graphdb
    def execute_by_graphdb(self,input): 
        
        # 动态获取用户输入的url,username,password 如果用户没有输入,就使用默认配置
        if self.url != "":
            info = self.getInfoByUrl(self.url)
            if info['username'] != "" and info['password'] != "" and info['dbname'] != "" and info['base_url'] != "":
                GRAPH_DB_URL = info['base_url']
                GRAPH_DB_NAME =  info['dbname']
                GRAPH_DB_USERNAME = info['username']
                GRAPH_DB_PASSWORD =  info['password']
          
        try:
            # 调用 sparql 生成器 生成 sparql 语句
            query = self.language_generator_parser.run(query=input)['final_result']
            
            # query = """
            #     SELECT ?subject ?predicate ?object
            #     WHERE {
            #         ?subject ?predicate ?object
            #     }
            #     LIMIT 10
            # """
            graphHandler = GraphHandler(GRAPH_DB_URL,GRAPH_DB_NAME, GRAPH_DB_USERNAME, GRAPH_DB_PASSWORD)
            results = graphHandler.execute_query(query=query)
            knowl = input + "\nAnswer: " + str(results)
            
        except:
            traceback.print_exc()
            query = ""
            knowl = ""
            
        if isinstance(knowl,list):
            knowl = str(knowl)
            
        return input,query,knowl 

    # 获取数据库连接的 数据库名称,账号,密码
    def getInfoByUrl(self,url):
        # 提取 ? 之前的 URL 部分
        try:
            base_url = url.split('?')[0]
        except:
            base_url = ""
        pattern = r"db=([^&]+)&u=([^&]+)&p=([^&]+)"
        match = re.search(pattern, url)
        if match:
            p_db = match.group(1)
            u_value = match.group(2)
            p_value = match.group(3)
        else:
            p_db = ""
            u_value = ""
            p_value = ""
        
        return {
            "base_url":base_url,
            "dbname":p_db,
            "username":u_value,
            "password":p_value
        }
                        
    def execute(self,input):
        if self.type == "google":
            self.url = self.getInfoByUrl(self.url)['base_url']
            input,processed_query,knowl = self.execute_by_google(input)
        elif self.type == "local":
            input,processed_query,knowl = self.execute_by_local(input)
        elif self.type == "sqlite":
            input,processed_query,knowl = self.execute_by_RDBMS(input)
        elif self.type == "neo4j":
            input,processed_query,knowl = self.execute_by_GDBMS(input)    
        elif self.type == "graphdb":
            if "query.wikidata.org" in self.url:
                self.url = self.getInfoByUrl(self.url)['base_url']
                input,processed_query,knowl = self.execute_by_wiki(input)
            else:
                input,processed_query,knowl = self.execute_by_graphdb(input)      
        else:
            input = input
            processed_query = input
            knowl = ""
            raise ValueError("Invalid Interface type")
            
        # print("interface retriever know :\n",knowl)
        
        return {"final_result":{"input":input,"processed_query":processed_query,"knowl":knowl}}
    