import json
import time
import traceback
from typing import Any, Dict, List 
import numpy as np
from root_config import RootConfig

class IterativeTemaplte():
    def __init__(self,info,generator,retriever, iter_num = 2):
        self.iter_num = iter_num
        self.info = info
        self.generator = generator
        self.retriever = retriever

    # 1. query 先检索一次,将query和检索结果拼接,用于下一次生成
    # 2. query + 生成的回复 再次检索 , 将query和检索结果拼接,用于下一次生成 (重复n次)
    def run(self,
            query:str="",
            query_list: List[str]=[]):
        
        if query != "" and len(query_list) == 0:
            query_list.append(query)
        
        dataset_list = list(map(lambda x:{"question":x,'content':""},query_list))
        count = 0
        final_result_list = []
        for data in dataset_list:
            count += 1
            question = data['question']
            
            past_generation_result = [] # list of N items
            for iter_idx in range(self.iter_num):
                # generation-augmented retrieval
                if iter_idx == 0:
                    input_query = question
                else:
                    input_query = f"{question} {past_generation_result[iter_idx-1]}"

                data[f'retriever_prompt_{iter_idx+1}'] = input_query

                print(f"第{count}条数据,第{iter_idx} 次,开始检索...")
                retrieval_results = self.retriever.run(query_list = [question])['final_result'][0]
                print(f"第{count}条数据,第{iter_idx} 次,检索完成 ...")
                data[f'retriever_result_{iter_idx+1}'] = retrieval_results

                ctxs_str = "\n".join(list(map(lambda x:x['content'],retrieval_results)))
                prompt = f"""
                Given the following document information：
    				{ctxs_str}

    				Please refer to the above document information to provide answer to the following question.Only give me the answer and do not output any other words.If the document contains incorrect information or if the document information is irrelevant to the question, please ignore the document and generate the answer independently.

    				Question:{question}
    				Answer:
                """

                data[f'gen_prompt_{iter_idx+1}'] = prompt
                
                gen_result = ""
                for _ in range(3):
                    try:
                        gen_result = self.generator.run(prompt_list=[prompt])['final_result'][0]['content']
                        break
                    except Exception as e:
                        traceback.print_exc()
                        time.sleep(20)
                    
                past_generation_result.append(gen_result)
                data[f'gen_result_{iter_idx+1}'] = gen_result
                
                # 最后一次  更新 final_data_list 的 pred
                if iter_idx == self.iter_num-1 :
                    data['content'] = gen_result
                    data['ctxs'] = retrieval_results
        
            final_result_list.append(data)
            
            print(f"====================================== {count} 处理完成 ... ======================================")
            
        return {"final_result":final_result_list}