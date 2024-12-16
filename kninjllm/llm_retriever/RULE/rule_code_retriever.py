from argparse import ArgumentParser
import json
import os
import sys
from typing import Any, Dict, List, Optional
from transformers import AutoTokenizer

from root_config import RootConfig
from kninjllm.llm_retriever.RULE.rule_retrieval.query2rule import do_main as query2rule
from kninjllm.llm_retriever.RULE.rule_retrieval.main_rule import do_main as main_rule
from kninjllm.llm_utils.common_utils import loadModelByCatch,do_initCatch
from kninjllm.llm_utils.common_utils import knowledge_conflict_check

# 获取当前工作目录
current_working_directory = os.getcwd()

class RULE_Code_Retriever:

    def __init__(
        self,
        searchDataList,
        top_k = 10,
        model_path:str="",
        ExternalKnowledgeConflictsFlag:bool=False
    ):
        self.top_k = top_k
        self.logSaver = RootConfig.logSaver
        self.searchDataList = searchDataList
        self.model_path = RootConfig.Qwen25_14B_model_path
        self.retriever_path = "/mnt/publiccache/huggingface/bge-base-en-v1.5"
        self.ExternalKnowledgeConflictsFlag = ExternalKnowledgeConflictsFlag
        # self.retriever_path = "BAAI/bge-base-zh-v1.5"
    def run(
        self,
        query:str = "",
        query_list: List[str] = []
    ):
        
        print("RULE_Code_Retriever infer ...")
        
        if query != "" and len(query_list) == 0:
            query_list = [query]
        
        if len(self.searchDataList) == 0:
            return {"final_result": []}
        
        if self.logSaver is not None:
            self.logSaver.writeStrToLog("Function -> RULE_Code_Retriever -> run | Given the search text, return the search content ")
            self.logSaver.writeStrToLog("search input -> : query_list: "+str(query_list))
            
        do_initCatch(clean_knowledge=False,clean_model=True)
        
        # 将工作目录切换至当前文件夹
        work_path = RootConfig.root_path + "kninjllm/llm_retriever/RULE/rule_retrieval"
        print(work_path)
        print("当前工作目录:\n",os.getcwd())
        print("切换至:\n",work_path)
        os.chdir(work_path)
        sys.path.append(work_path)
        print("当前工作目录:\n",os.getcwd())
            
        dataset = "code"
        # step1
        parser = ArgumentParser()
        args = parser.parse_args()
        args.model_path = self.model_path
        
        args.model = loadModelByCatch(model_name=self.model_path,model_path=self.model_path)
        args.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        # args.model = None
        # args.tokenizer = None
        # args.data_path = f"{work_path}/dataset/{dataset}/test_data.json"
        
        args.query_list = list(map(lambda x:{"instruction": "","input": x,"output": "","rule": []},query_list))

        args.output_path = f"{work_path}/dataset/{dataset}/test_data_with_self_induction_rule.json"
        # args.batch_size = ""
        args.n = 1
        query2rule(args)
        
        do_initCatch(clean_knowledge=False,clean_model=True)
        # step2
        parser = ArgumentParser()
        parser.add_argument("--rule_path", type=str)
        args = parser.parse_args()
        args.setting = "retrieval"
        args.dataset = dataset
        args.data_path = f"{work_path}/dataset/{dataset}/test_data_with_self_induction_rule.json"
        args.rule_dir = f"{work_path}/dataset/{dataset}/test_rule_json"
        with open(args.rule_dir + "/test_rule.json",'w',encoding='utf-8') as f:
            json.dump(self.searchDataList,f,ensure_ascii=False)
        
        args.retriever_path = self.retriever_path
        args.model_path = self.model_path
        args.model = None
        args.tokenizer = None
        
        args.index_dir = f"{work_path}/index/{dataset}"
        if os.path.exists(args.index_dir + "_dense"):
            os.remove(args.index_dir + "_dense")
        
        args.topk = self.top_k
        retrieved_rules,outputs = main_rule(args)
        
        final_result = []
        for retrieved_rule in retrieved_rules:
            one_query_rules = []
            for one_rule in retrieved_rule:
                one_rule_obj = {
                    "id": one_rule,
                    "content":list(filter(lambda x: x['id']==one_rule, self.searchDataList))[0]['content']
                }
                one_query_rules.append(one_rule_obj)
            final_result.append(one_query_rules)
        
        do_initCatch(clean_knowledge=False,clean_model=True)
        
        final_result = knowledge_conflict_check(query_list=query_list,final_result=final_result,ExternalKnowledgeConflictsFlag=self.ExternalKnowledgeConflictsFlag)
        
        if self.logSaver is not None:
            self.logSaver.writeStrToLog("search returned -> : final_result: "+str(final_result))
            
        return {"final_result": final_result}
        
    