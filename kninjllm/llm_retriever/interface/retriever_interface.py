from typing import List
from kninjllm.llm_utils.common_utils import calculate_hash
from kninjllm.llm_utils.common_utils import knowledge_conflict_check

class InterfaceRetriever:
    def __init__(self,searchDataList, top_k=10, model_path:str="",ExternalKnowledgeConflictsFlag=False):

        self.searchDataList = searchDataList
        self.ExternalKnowledgeConflictsFlag = ExternalKnowledgeConflictsFlag

    def one_retriever(self,query):
        res_data_list = []
        for domain in self.searchDataList:
            domain_obj = self.searchDataList[domain]
            for domain_obj_xld in domain_obj:
                interface = domain_obj[domain_obj_xld]
                # print('====================================================================================')
                # print('-------------domain_obj_xld------------------\n',domain_obj_xld)
                res_obj = interface.execute(query)['final_result']
                knowl = res_obj['knowl']
                if interface.type == "graphdb" and "Answer:" in knowl: 
                    knowl = "Answer:" + knowl.split("Answer:")[1].strip()
                # print('--------------------------knowl-------------------------------------\n',knowl)
                # print('====================================================================================')
                res_data_list.append({
                    "id":calculate_hash([knowl]),
                    "content":knowl
                })
            
        return res_data_list

    def run(self,
            query:str = "",
            query_list: List[str] = []):
        
        if query != "" and len(query_list) == 0:
            query_list = [query]
        
        final_result = []
        for query in query_list:
            query_res_list = self.one_retriever(query=query)
            final_result.append(query_res_list)

        final_result = knowledge_conflict_check(query_list=query_list,final_result=final_result,ExternalKnowledgeConflictsFlag=self.ExternalKnowledgeConflictsFlag)
        
        return {"final_result":final_result}