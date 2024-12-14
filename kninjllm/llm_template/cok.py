import argparse
import importlib
import json
from pathlib import Path
from typing import Any, Dict, List
from root_config import RootConfig
from kninjllm.llm_knowledgeUploader.utils.other_prompts import domain_selection_demonstration
from kninjllm.llm_knowledgeUploader.utils.final_parser import Parser

from root_config import RootConfig
from kninjllm.llm_utils.common_utils import loadRetriever,loadGenerator,loadModelByCatch
from kninjllm.llm_generator.close_generator.openai_generator import OpenAIGenerator

import kninjllm.llm_knowledgeUploader.utils.globalvar
kninjllm.llm_knowledgeUploader.utils.globalvar.init()

class cokTemplate:
    def __init__(self,info,generator,retriever):
        # self.generator = OpenAIGenerator(api_key=RootConfig.openai_api_key,model=RootConfig.openai_model_version,generation_kwargs={"max_tokens":1024,"temperature":0,"n":1},do_log=False)
        self.generator = generator
        self.generator.generation_kwargs['n'] = 1
        
        self.retriever = retriever

        self.logSaver = RootConfig.logSaver
        self.log_str_list = []
        
        try:
            mapping = self.retriever.retriever_list[0].searchDataList
            if isinstance(mapping, dict):
                self.domain_mapping = mapping
            else:
                print("------------------------- not domain mapping ------------------\n")
        except:
            do_import = importlib.import_module('kninjllm.llm_knowledgeUploader.utils.interface_config')
            importlib.reload(do_import)
            self.domain_mapping = do_import.domain_mapping
        
    def run(
        self,
        query: str = "",
        query_list: List[str]=[]
    ):
        
        parser = argparse.ArgumentParser()
        args = parser.parse_args()
        args.step = True
        args.threshold = 0.8
        
        if query != "" and len(query_list) == 0:
            query_list = [query]
        query_list = list(map(lambda x:{"question":x},query_list))
        dataset = Parser(data_list = query_list,domain_mapping=self.domain_mapping)
        # load data
        data = dataset.get_dataset()
        print('original data length:', len(data))
        print('original data :', data)
        
        # 多条
        final_result_list = []
        for index,d in enumerate(data):
            print("run_once....",index)
            temp_result = self.run_once(index,dataset,data,args)[0]
            # final_result_str = "cot_response: " + final_result['cot_response'] + "\n\n" + "cok_response: " + "First，"+final_result['edited_rationale_1']+" Second,"+final_result['edited_rationale_2']+" The answer is "+final_result['final_answer']+"\n"
            final_result_str = "First，"+temp_result['edited_rationale_1']+" Second,"+temp_result['edited_rationale_2']+" The answer is "+temp_result['final_answer']+"\n"
            final_result_list.append({"content":final_result_str,'ctxs':self.log_str_list})
                
            
        print('---------------------------ALL DONE!! final_result_list----------------------------')
        
        return {"final_result":final_result_list}
    
    def s1_reasoning_preparation(self,dataset, data_point, generator):
        print("****************** Start stage 1: reasoning preparation ...")
        question = dataset.get_question(data_point)
        print("****** Question:", question)
        question_input=data_point['question']
            
        prompt_question_input=domain_selection_demonstration+"Q: "+question_input+"\nRelevant domains: "
        s1_domains=self.generator.run(prompt=prompt_question_input)['final_result'][0]['content'].strip()
        s1_domains=s1_domains.strip().split(", ")
        data_point["s1_domains"]=s1_domains
            
        # 加一个日志
        if self.logSaver is not None:
            # 判断问题所属领域:s1_domains
            # self.logSaver.writeStrToLog("判断问题所属领域:" + json.dumps(s1_domains,ensure_ascii=False))
            self.logSaver.writeStrToLog("Domain Identify: " + json.dumps(s1_domains,ensure_ascii=False))
        self.log_str_list.append("Domain Identify: " + json.dumps(s1_domains,ensure_ascii=False))
        
        
        # 加一个日志
        # 获得检索信息源类型:
        type_list = []
        for domain in s1_domains:
            if domain in self.domain_mapping:
                type_list.extend(list(self.domain_mapping[domain].keys())) 
        if self.logSaver is not None:
            # self.logSaver.writeStrToLog("获得检索信息源类型:" + json.dumps(type_list,ensure_ascii=False))
            self.logSaver.writeStrToLog("Knowledge Base Select:" + json.dumps(type_list,ensure_ascii=False))
        self.log_str_list.append("Knowledge Base Select:" + json.dumps(type_list,ensure_ascii=False))
            
            
        data_point["question_input"]=question
        
        ### CoT generation
        
        cot_prompt = dataset.get_s1_prompt(question)
        
        data_point["cot_prompt"]=cot_prompt
        
        data_point = dataset.get_cot_sc_results(data_point,generator, cot_prompt)
        print("****** CoT answer:", data_point["cot_response"])
        print("****** CoT SC score:", data_point["cot_sc_score"])
        print("****** CoT SC answer:", data_point["cot_sc_response"])
        # print("data_point:",data_point)

        return data_point


    def s2_knowledge_adapting(self,dataset, data_point, generator, step):
        print("****************** Start stage 2: knowledge adapting ...")
        if step:
            print("****** Edit mode: Step by step")
            # Edit the rationales step by step
            data_point = dataset.update_rationales_step_by_step(generator, data_point)

        else:
            # Edit the rationales all at once
            print("****** Edit mode: At once")
            # Edit the rationales step by step
            data_point = dataset.update_rationales_at_once(generator, data_point)

        return data_point

    def s3_answer_consolidation(self,dataset, data_point, generator):
        print("****************** Start stage 3: answer consolidation ...")
        data_point = dataset.get_final_answer(generator, data_point)
        return data_point

    def run_once(self,i,dataset,data,args):
        self.log_str_list = []
        
        print("####################################", i, "####################################")
        data_point = data[i]
        data_point["id"] = i
        
        if 'cot_sc_score' not in data_point or 's1_domains' not in data_point:
            data_point = self.s1_reasoning_preparation(dataset, data_point, self.generator)
            # update the datapoint
            data[i] = data_point
        # Self-consistency threshold
        if 'final_answer' not in data_point:
            ##### run stage 2: Edit the rationales
            data_point = self.s2_knowledge_adapting(dataset, data_point, self.generator, args.step)
            # update the datapoint
            data[i] = data_point
            ##### run stage 3: answer consolidation
            data_point = self.s3_answer_consolidation(dataset, data_point, self.generator)
            # update the datapoint
            data[i] = data_point
            
            self.log_str_list.extend(dataset.log_str_list)
            # print(self.log_str_list)
            
            self.log_str_list = list(map(lambda x: {"content":x},self.log_str_list))
            
            return data
        else:
            return data
