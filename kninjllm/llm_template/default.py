from typing import Any, Dict, List 
import numpy as np
from root_config import RootConfig
from kninjllm.llm_generator.base_generator.self_rag.retrieval_lm.utils import TASK_INST, PROMPT_DICT, load_special_tokens, load_jsonlines, postprocess, fix_spacing,control_tokens




class defaultTemplate:
    def __init__(self,info,generator,retriever):
        self.info = info
        self.retriever = retriever
        self.generator = generator
        try:
            self.tokenizer = self.generator.tokenizer
        except Exception as e: 
            self.tokenizer = None
            
        self.logSaver = RootConfig.logSaver

    def run(self,
            query:str="",
            query_list: List[str]=[]):
        
        if query != "" and len(query_list) == 0:
            query_list.append(query)
        
        # print("---------------query_list------------------\n",query_list)
        
        # 1. 检索
        querys_knowledgeList = self.retriever.run(query_list=query_list)['final_result']

        final_prompt_list = []
        for one_query,one_query_know_list in zip(query_list,querys_knowledgeList):
            knowledge = ""
            for k in one_query_know_list:
                knowledge = knowledge + k['content'] + "\n"
            temp_prompt = self.info['prompt'].replace("{knowledge}",knowledge).replace("{question}",one_query)
            
            print("---------------------------temp_prompt-------------------------------\n",temp_prompt)
            
            final_prompt_list.append(temp_prompt)
        
        # print('-------------------------final_prompt_list---------------------------\n',final_prompt_list)
        
        llm_res_list = self.generator.run(prompt_list=final_prompt_list)['final_result']
        
        final_list = []
        for llm_res,retrieverList in zip(llm_res_list,querys_knowledgeList):
            resObj = {
                "ctxs":retrieverList,
                "content":llm_res['content']
            }
            final_list.append(resObj)
        
        return {"final_result":final_list}