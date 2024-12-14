from argparse import Namespace
from typing import Any, Dict, List, Optional
from kninjllm.llm_retriever.contriever.passage_retrieval import main_infer
from root_config import RootConfig
from kninjllm.llm_utils.common_utils import knowledge_conflict_check

class Contriever_Retriever:

    def __init__(
        self,
        searchDataList,
        top_k = 10,
        model_path:str="",
        search_path="",
        ExternalKnowledgeConflictsFlag:bool=False
    ):
        self.top_k = top_k
        self.logSaver = RootConfig.logSaver
        self.model_path = model_path
        self.searchDataList = searchDataList
        self.search_path = search_path
        self.ExternalKnowledgeConflictsFlag = ExternalKnowledgeConflictsFlag
        
    def run(
        self,
        query:str = "",
        query_list: List[str] = []
    ):
        if query != "" and len(query_list) == 0:
            query_list = [query]
        
        # if len(self.searchDataList) == 0:
        #     return {"final_result": []}
        
        if self.logSaver is not None:
            self.logSaver.writeStrToLog("Function -> Contriever_Retriever -> run | Given the search text, return the search content ")
            self.logSaver.writeStrToLog("search input -> :query_list: "+str(query_list))

        query_list = list(map(lambda x:{"question":x},query_list))
        args = Namespace(dataSetList=query_list,
                            passages=self.searchDataList, 
                            passages_path=self.search_path, 
                            n_docs=self.top_k,
                            validation_workers=32,
                            per_gpu_batch_size=64,
                            save_or_load_index=False,
                            model_name_or_path=self.model_path,
                            no_fp16=False,
                            question_maxlength=512,
                            indexing_batch_size=1000000,
                            projection_size=768,
                            n_subquantizers=0,
                            n_bits=8,
                            lang=None,
                            dataset="none",
                            lowercase=False,
                            normalize_text=False,
                            )
        
        final_result = main_infer(args)
        
        final_result = knowledge_conflict_check(query_list=query_list,final_result=final_result,ExternalKnowledgeConflictsFlag=self.ExternalKnowledgeConflictsFlag)
        
        if self.logSaver is not None:
            self.logSaver.writeStrToLog("search returned -> : final_result: "+str(final_result))
            
        return {"final_result": final_result}
    
    