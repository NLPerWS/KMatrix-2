from typing import List
from kninjllm.llm_utils.common_utils import calculate_hash

class RootRetriever:
    def __init__(self,searchDataList, top_k=10, model_path:str=""):
        self.retriever_list = searchDataList
    def run(self,
            query:str = "",
            query_list: List[str] = []):
        
        if query != "" and len(query_list) == 0:
            query_list = [query]
        
        # 检索
        querys_knowledgeList = []
        for retriever in self.retriever_list:
            print("使用一个检索器 检索一次: ",retriever)
            temp_retriever_list = retriever.run(query_list=query_list)['final_result']
            querys_knowledgeList.append(temp_retriever_list)
            # print("------------------querys_knowledgeList------------------------\n",querys_knowledgeList)
        
        change_querys_knowledgeList = [[] for _ in range(len(querys_knowledgeList[0]))]
        # Iterate through each top-level sub-list
        for sublist in querys_knowledgeList:
            # Iterate through each pair of corresponding sub-lists
            for i, inner_list in enumerate(sublist):
                change_querys_knowledgeList[i].extend(inner_list)

        return {"final_result":change_querys_knowledgeList}