from typing import Any, Dict, List, Optional
from root_config import RootConfig
from kninjllm.llm_retriever.BGE.infer import infer
from kninjllm.llm_utils.common_utils import knowledge_conflict_check

class BGE_Retriever:

    def __init__(
        self,
        searchDataList,
        top_k = 10,
        model_path:str="",
        ExternalKnowledgeConflictsFlag:bool=False
    ):
        self.top_k = top_k
        self.logSaver = RootConfig.logSaver
        self.model_path = model_path
        self.searchDataList = searchDataList
        self.ExternalKnowledgeConflictsFlag = ExternalKnowledgeConflictsFlag
    def run(
        self,
        query:str = "",
        query_list: List[str] = []
        
    ):
        
        print("BGE infer ...")
        
        if query != "" and len(query_list) == 0:
            query_list = [query]
        
        if len(self.searchDataList) == 0:
            return {"final_result": []}
        
        if self.logSaver is not None:
            self.logSaver.writeStrToLog("Function -> BGE_Retriever -> run | Given the search text, return the search content ")
            self.logSaver.writeStrToLog("search input -> : query_list: "+str(query_list))
            
        print("------------self.model_path---------")
        print(self.model_path)
        
        final_result = infer(
            model=self.model_path,
            input_query=query_list,
            passage=self.searchDataList,
            top_k=self.top_k,
        )
        
        final_result = knowledge_conflict_check(query_list=query_list,final_result=final_result,ExternalKnowledgeConflictsFlag=self.ExternalKnowledgeConflictsFlag)
        
        if self.logSaver is not None:
            self.logSaver.writeStrToLog("search returned -> : final_result: "+str(final_result))
            
        return {"final_result": final_result}
