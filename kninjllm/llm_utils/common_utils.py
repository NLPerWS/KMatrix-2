import os
import json
import pickle
import subprocess
import sys

import numpy as np
import pandas as pd
import hashlib
from docx import Document  
import PyPDF2  
import traceback
import time
from root_config import RootConfig



from kninjllm.llm_retriever.contriever.generate_passage_embeddings import main_do_embedding as do_contriever_embedding
from kninjllm.llm_retriever.BGE.embedding import embedding as do_BGE_embedding
from kninjllm.llm_retriever.BGE_m3.embedding import embedding as do_BGEM3_embedding
from kninjllm.llm_retriever.DPR.embedding import embedding as do_DPR_embedding
from kninjllm.llm_retriever.E5.embedding import embedding as do_E5_embedding
from kninjllm.llm_retriever.BERT.embedding import embedding as do_BERT_embedding

# from kninjllm.llm_retriever.in_memory.bm25_retriever import do_BM25_embedding as do_BM25_embedding
from kninjllm.llm_utils.file_parser.deepdoc.parser.parser_main import parser_main,get_file_extension


import torch
from transformers import AutoTokenizer, AutoModel
from transformers import AutoModelForCausalLM, AutoTokenizer,LlamaForCausalLM
from transformers.generation.utils import GenerationConfig
from vllm import RequestOutput, SamplingParams,LLM
from refined.inference.processor import Refined

def set_proxy():
    if RootConfig.HTTP_PROXY != "":
        os.environ['HTTP_PROXY']=RootConfig.HTTP_PROXY
    if RootConfig.HTTPS_PROXY != "":
        os.environ['HTTPS_PROXY']=RootConfig.HTTPS_PROXY
    

def unset_proxy():
    if 'HTTP_PROXY' in os.environ:
        del os.environ['HTTP_PROXY']
        subprocess.call(['unset', 'HTTP_PROXY'], shell=True)
        
    if 'HTTPS_PROXY' in os.environ:
        del os.environ['HTTPS_PROXY']
        subprocess.call(['unset', 'HTTPS_PROXY'], shell=True)
    
    if 'HF_HOME' in os.environ:
        del os.environ['HF_HOME']
        subprocess.call(['unset', 'HF_HOME'], shell=True)
        
    if 'OPENBLAS_NUM_THREADS' in os.environ:
        del os.environ['OPENBLAS_NUM_THREADS']
        subprocess.call(['unset', 'OPENBLAS_NUM_THREADS'], shell=True)
        
    if 'HF_ENDPOINT' in os.environ:
        del os.environ['HF_ENDPOINT']
        subprocess.call(['unset', 'HF_ENDPOINT'], shell=True)
    
    
    
def _load_pickle_file(filename):
    with open(filename, "rb") as f:
        return pickle.load(f)

def _reverse_dict(ori_dict):
    reversed_dict = {v: k for k, v in ori_dict.items()}
    return reversed_dict

def RequestOutputToDict(pred):
    if not isinstance(pred,RequestOutput):
        return pred
    pred_dict = {
        "request_id":pred.request_id,
        "prompt":pred.prompt,
        "prompt_token_ids":pred.prompt_token_ids,
        "prompt_logprobs":pred.prompt_logprobs,
        "outputs":[{
            "index":pred.outputs[0].index,
            "text":pred.outputs[0].text,
            "token_ids":pred.outputs[0].token_ids,
            "cumulative_logprob":pred.outputs[0].cumulative_logprob,
            "logprobs":pred.outputs[0].logprobs,
            "finish_reason":pred.outputs[0].finish_reason,
            }],
        "finished":pred.finished
    }
    return pred_dict

def calculate_hash(str_array):
    combined_str = ''.join(str_array).encode('utf-8')
    hash_object = hashlib.sha256(combined_str)
    return str(hash_object.hexdigest())


class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, RequestOutput):
            return None  
        else:
            return super().default(obj)

def changeExcelToJson(filePath:str,type:str):
    finalJsonObjList = []
    xl = pd.ExcelFile(filePath)
    sheet_names = xl.sheet_names
    file_name = os.path.basename(filePath)

    for sheet_name in sheet_names:
        finalJsonObj = {
            "id":file_name,
            "header":[], # [str]
            "rows":[],    # [str]
            # "data":[]           # [List[Any]]
        }
        if type == 'row_column':
            df = pd.read_excel(filePath, sheet_name=sheet_name)
            for index,row in df.iterrows():
                temp_data_list = []
                skip_first_column = True
                for column_name, cell_value in row.items():
                    if skip_first_column:
                        skip_first_column = False
                        continue
                    temp_data_list.append(cell_value)
                    if column_name not in finalJsonObj['header']:
                        finalJsonObj['header'].append(column_name)
                finalJsonObj['rows'].append(temp_data_list)
            # finalJsonObj['rows'] = df[df.columns[0]].to_list()

        elif type == 'column':
            df = pd.read_excel(filePath, sheet_name=sheet_name)
            for index,row in df.iterrows():
                temp_data_list = []
                for column_name, cell_value in row.items():
                    column_name = str(column_name).replace('\\','\\\\').replace('NaN',' ')
                    cell_value = str(cell_value).replace('\\','\\\\').replace('NaN',' ')
                    
                    temp_data_list.append(cell_value)
                    if column_name not in finalJsonObj['header']:
                        finalJsonObj['header'].append(column_name)
                finalJsonObj['rows'].append(temp_data_list)


        elif type == 'row':
            df = pd.read_excel(filePath, sheet_name=sheet_name,header=None)
            finalJsonObj['header'] = df[df.columns[0]].tolist()
            for column in df.columns[1:]:
                finalJsonObj['rows'].append(df[column].tolist())
        else:
            return []
        finalJsonObjList.append(finalJsonObj)
    # print("finalJsonObjList=>\n",finalJsonObjList)
    return finalJsonObjList

def loadKnowledgeByCatch(knowledge_path,info_type=""):
    
    catchData = []
    catch_flag = False
    
    if isinstance(knowledge_path, str):

        for catchDataObj in RootConfig.tempPipeLineKnowledgeCatch:
            if catchDataObj['path'] == knowledge_path:
                catch_flag = True
                catchData = catchDataObj['data']
                
        if catch_flag == False:
            catchData = read_server_files(knowledge_path,True,info_type)
            RootConfig.tempPipeLineKnowledgeCatch.append({"path":knowledge_path,"data":catchData})

        return catchData
    
    else:
        
        for catchDataObj in RootConfig.tempPipeLineKnowledgeCatch:
            if catchDataObj['path'] == "\t".join(knowledge_path):
                catch_flag = True
                catchData = catchDataObj['data']
                
        if catch_flag == False:
            catchData = []
            for one_db_path in knowledge_path:
                tempdata = read_server_files(RootConfig.knowledgeUploadDirPath + one_db_path,True,info_type)
                catchData.extend(tempdata)
            
            RootConfig.tempPipeLineKnowledgeCatch.append({"path":"\t".join(knowledge_path),"data":catchData})

        return catchData
    

# 读取服务器数据
def read_server_files(path,do_liner=True,know_flag=""):
    
    # print("read_server_files_dirpath\n",path)
    def read_one_file(file_path):
        
        # print("read_one_file\n",file_path)
        
        from kninjllm.llm_linearizer.LinearizerToText import LinearizerToText
        data = []
        # json 
        if file_path.endswith(".json"):
            with open(file_path, 'r',encoding='utf-8') as file:
                tempData = json.load(file)
            if isinstance(tempData,list) and len(tempData) > 0:
                # 普通json文件
                if "triples" in tempData[0] and  do_liner == True:
                    print("json文件有triples字段，triple线性化器")
                    # liner_data_list = tempData
                    lt = LinearizerToText(knowledge_line_count=1,max_length=100,valueList=[],count=0)
                    liner_data_list = lt.run(value=tempData)['final_result']['knowledge']
                    data.extend(liner_data_list)
                # triple 线性化器
                else:
                    print("json文件没有triples字段，普通json文件")
                    data.extend(tempData) 
            else:
                data.append(tempData)
                    
        # 表格 线性化器
        elif file_path.endswith(".xlsx") or file_path.endswith(".xls"):
            
            # deepdoc
            string_list = parser_main(file_path=file_path, file_type='xlsx') 
            string_list = [line.strip() for line in string_list if line.strip()]
            data = list(map(lambda x: {"id": get_random_id_from_string(x), "content": x}, string_list))
            
            # 线性化器            
            # table_list = changeExcelToJson(file_path,'column')
            # # print("table_list\n",table_list)
            # if do_liner == True:
            #     lt = LinearizerToText(knowledge_line_count=1,max_length=100,valueList=[],count=0)
            #     liner_data_list = lt.run(value=table_list)['final_result']['knowledge']
            #     data.extend(liner_data_list)
            # else:
            #     data.extend(table_list) 
            
                
        elif file_path.endswith(".jsonl"):
            with open(file_path, 'r',encoding='utf-8') as file:
                for line in file:
                    data.append(json.loads(line))
        
        elif file_path.endswith(".pkl") or file_path.endswith(".pickle"):
            with open(file_path, 'rb') as file:
                try:
                    while True:
                        dict_obj = pickle.load(file)
                        data.append(dict_obj)
                except EOFError:
                    pass    
                  
        elif file_path.endswith(".csv") or file_path.endswith(".tsv"):
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = [line for line in file]
            data = list(map(lambda x: {"id": get_random_id_from_string(x), "content": x[1]}, lines))
            
        # 文本
        elif file_path.endswith(".txt") :
            split_list = ['。','！','？','.','!','?']
            split_max_length = 200
            file_name, file_extension = os.path.splitext(file_path)
            
            # print('----------------------know_flag-------------------\n',know_flag)
            if file_extension == '.txt' and know_flag == "Rule_NL":
                
                with open(file_path, 'r', encoding='utf-8') as file:
                    strings = file.readlines()
                
                if do_liner == True:
                    data = []
                    for s in strings:
                        id = s.split("\t")[0]
                        content = s.replace(id,'',1)
                        data.append({
                            "id":id,
                            "content":content
                        })
                    return data
                else:
                    return strings
            
            else:
                with open(file_path, 'r', encoding='utf-8') as file:
                    string_list = file.readlines()
                string_list = [line.strip() for line in string_list if line.strip()]
                data = list(map(lambda x: {"id": get_random_id_from_string(x), "content": x}, string_list))
                
        elif file_path.endswith(".md") or file_path.endswith(".markdown"):
            # 使用 deepdoc_parser
            string_list = parser_main(file_path=file_path, file_type='md') 
            string_list = [line.strip() for line in string_list if line.strip()]
            data = list(map(lambda x: {"id": get_random_id_from_string(x), "content": x}, string_list))
        
            # # 处理文本文件
            # with open(file_path, 'r', encoding='utf-8') as file:
            #     string = file.read()
            # string_list = split_string(string,split_list,split_max_length)
            
        elif file_path.endswith(".doc") or file_path.endswith(".docx"):
            # 使用 deepdoc_parser
            string_list = parser_main(file_path=file_path, file_type='doc') 
            string_list = [line.strip() for line in string_list if line.strip()]
            data = list(map(lambda x: {"id": get_random_id_from_string(x), "content": x}, string_list))
            
            # # 处理 .docx 文件
            # string = ""
            # doc = Document(file_path)
            # for para in doc.paragraphs:
            #     string += para.text + "\n"  # 添加段落文本并换行
            # string_list = split_string(string,split_list,split_max_length)
            
        elif file_path.endswith(".pdf"):
            # 使用 deepdoc_parser
            string_list = parser_main(file_path=file_path, file_type='pdf') 
            string_list = [line.strip() for line in string_list if line.strip()]
            data = list(map(lambda x: {"id": get_random_id_from_string(x), "content": x}, string_list))
        
            # # 处理 .pdf 文件
            # string = ""
            # with open(file_path, 'rb') as file:
            #     reader = PyPDF2.PdfReader(file)
            #     for page in reader.pages:
            #         string += page.extract_text() + "\n"  # 添加页面文本并换行
            #     string_list = split_string(string,split_list,split_max_length)
            
        elif file_path.endswith(".html"):
            # 使用 deepdoc_parser
            string_list = parser_main(file_path=file_path, file_type='html') 
            string_list = [line.strip() for line in string_list if line.strip()]
            data = list(map(lambda x: {"id": get_random_id_from_string(x), "content": x}, string_list))
            
        elif file_path.endswith(".ppt") or file_path.endswith(".pptx"):
            # 使用 deepdoc_parser
            string_list = parser_main(file_path=file_path, file_type='ppt') 
            string_list = [line.strip() for line in string_list if line.strip()]
            data = list(map(lambda x: {"id": get_random_id_from_string(x), "content": x}, string_list))
        
        # 其他格式暂不支持
        else:
            data = []
            print(f"Unsupported file type: {file_path}")
            
        return data
    
    final_data_list = []
    # is dir
    if os.path.isdir(path):  
        
        for file_name in os.listdir(path):
            file_path = os.path.join(path, file_name)
            data = read_one_file(file_path)
            final_data_list.extend(data)
    
    # is file
    elif os.path.isfile(path):  
        data = read_one_file(path)
        final_data_list.extend(data)
        # print("final_data_list\n",final_data_list)
        
    else:
        raise ValueError(f"Path is not a folder or file or path does not exist: {path}")

    # 过滤 不符合格式的数据 
    if do_liner:
        final_data_list = [item for item in final_data_list if 'content' in item]
    return final_data_list

# 根据字符串获取随机id(str)
def get_random_id_from_string(input_string):
    # 使用MD5哈希算法
    hash_object = hashlib.md5(input_string.encode())
    return str(hash_object.hexdigest())

# 拆分一个字符串为字符串数组
# 1. 根据分割词列表[]拆分,并且拆分的句子不能超过最大长度
# 2. 拆分的句子在最大长度的范围内必须以分割词结尾,并且句子长度尽量最长(不能超过最大长度)
def split_string(input_string, delimiters, max_length):
    import re
    
    # Create a regex pattern to split by the delimiters
    pattern = '|'.join(map(re.escape, delimiters))
    
    # Split the input string by the delimiters, keeping the delimiters
    parts = re.split(f'({pattern})', input_string)
    
    result = []
    current_sentence = ''
    
    for part in parts:
        if part in delimiters:
            # Check if adding this part exceeds the max length
            if len(current_sentence) + len(part) <= max_length:
                current_sentence += part
            else:
                # If it exceeds, add the current sentence to result and start a new one
                if current_sentence:
                    result.append(current_sentence)
                current_sentence = part
        else:
            # Check if adding this part exceeds the max length
            if len(current_sentence) + len(part) <= max_length:
                current_sentence += part
            else:
                # If it exceeds, add the current sentence to result and start a new one
                if current_sentence:
                    result.append(current_sentence)
                current_sentence = part
    
    # Add the last sentence if it's not empty
    if current_sentence:
        result.append(current_sentence)
    
    return result

def do_initCatch(clean_knowledge=True,clean_model=True):

    def get_gpu_memory_usage(gpu_index):
        """Helper function to query GPU memory usage for a specific GPU."""
        try:
            # Execute 'nvidia-smi' command and parse the output
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=memory.used', '--format=csv,nounits,noheader'],
                stdout=subprocess.PIPE,
                check=True
            )
            # Decode the byte string, strip extra whitespace, and split by line
            usage_lines = result.stdout.decode('utf-8').strip().split('\n')
            # Parse the desired GPU's usage line to get the memory usage as integer
            if gpu_index < len(usage_lines):
                return int(usage_lines[gpu_index].strip())
            else:
                raise ValueError(f"GPU index {gpu_index} out of range, found {len(usage_lines)} GPUs")
        except Exception as e:
            print(f"Error querying GPU memory usage: {e}")
            return None

    if clean_knowledge:
        # 清空和删除配置变量
        del RootConfig.tempPipeLineKnowledgeCatch
        RootConfig.tempPipeLineKnowledgeCatch = []


    if clean_model:
        del RootConfig.tempModelCatch
        RootConfig.tempModelCatch = []
        
        import gc
        import ray
        import torch
        from vllm.model_executor.parallel_utils.parallel_state import destroy_model_parallel

        # 终止模型并行进程
        destroy_model_parallel()
        # 判断并终止分布式进程组
        try:
            torch.distributed.destroy_process_group()
        except Exception as e:
            pass
        # 清除CUDA缓存和同步设备
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
        torch.cuda.empty_cache()
        # 关闭Ray进程
        ray.shutdown()
        # 进行垃圾收集
        gc.collect()
        
        # # Wait for GPU memory to be released
        # initial_memory_usage = get_gpu_memory_usage(gpu_index=int(RootConfig.CUDA_VISIBLE_DEVICES))
        # print("-----------initial_memory_usage--------\n",initial_memory_usage)
        
        # timeout = 60  # set a timeout in seconds
        # elapsed_time = 0
        
        # while elapsed_time < timeout:
        #     time.sleep(5)  # check every second
        #     current_memory_usage = get_gpu_memory_usage(gpu_index=int(RootConfig.CUDA_VISIBLE_DEVICES))
        #     print("-----------current_memory_usage--------\n",current_memory_usage)
        #     if current_memory_usage is not None and current_memory_usage <= initial_memory_usage - 30000: 
        #         break
        #     elapsed_time += 1

    return True

# 知识冲突消解 调用及后处理
def knowledge_conflict_check(query_list,final_result,ExternalKnowledgeConflictsFlag):
    
    if ExternalKnowledgeConflictsFlag == True:
        
        print("-----------------------执行外部知识冲突消解--------------------------------")
        from kninjllm.llm_conflict_of_knowledge.External_Knowledge_Conflicts import ExternalKnowledgeConflicts
        conflict = ExternalKnowledgeConflicts()
        query_obj_list = []
        for query,res in zip(query_list,final_result):
            if isinstance(query,dict):
                query = query['question']
            
            ctxs_content_list = [x['content'] for x in res]
            query_obj_list.append({
                "question":query,
                "ctxs_content_list":ctxs_content_list
            })
        filter_res_list = conflict.execute(query_obj_list = query_obj_list)
        for index,(filter_res,res) in enumerate(zip(filter_res_list,final_result)):
            # 如果冲突返回为空,就拼top1
            if len(filter_res['filter_ctxs_list']) == 0:
                filter_res['filter_ctxs_list'] = [x['content'] for x in final_result[index][0:1]]
            final_result[index] = [{"content":x} for x in filter_res['filter_ctxs_list']]
        
        return final_result
    # print('-------------------------final_result---------------------------------\n',final_result)
    else:
        return final_result
        

def loadRetriever(searchDataList,retrieverName,topk,ExternalKnowledgeConflictsFlag):
    from kninjllm.llm_retriever.BGE.BGE_retriever import BGE_Retriever
    from kninjllm.llm_retriever.BGE_m3.BGE_retriever import BGEM3_Retriever
    from kninjllm.llm_retriever.BERT.BERT_retriever import BERT_Retriever
    from kninjllm.llm_retriever.contriever.Contriever_retriever import Contriever_Retriever
    from kninjllm.llm_retriever.DPR.DPR_retriever import DPR_Retriever
    from kninjllm.llm_retriever.E5.E5_retriever import E5_Retriever
    from kninjllm.llm_retriever.in_memory.bm25_retriever import InMemoryBM25Retriever
    from kninjllm.llm_retriever.RULE.rule_code_retriever import RULE_Code_Retriever
    from kninjllm.llm_retriever.RULE.rule_nl_retriever import RULE_NL_Retriever

    
    # from kninjllm.llm_retriever.elasticsearch.bm25_retriever import ElasticsearchBM25Retriever
    # from kninjllm.llm_retriever.elasticsearch.embedding_retriever import ElasticsearchEmbeddingRetriever
    # from kninjllm.llm_retriever.in_memory.embedding_retriever import InMemoryEmbeddingRetriever
    
    if retrieverName == "BGE":
        model_path = RootConfig.BGE_model_path
        retriever = BGE_Retriever(searchDataList=searchDataList,top_k=topk,model_path=model_path,ExternalKnowledgeConflictsFlag=ExternalKnowledgeConflictsFlag)
        
    elif retrieverName == "BGEM3":
        model_path = RootConfig.BGEm3_model_path
        retriever = BGEM3_Retriever(searchDataList=searchDataList,top_k=topk,model_path=model_path,ExternalKnowledgeConflictsFlag=ExternalKnowledgeConflictsFlag)
        
    elif retrieverName == "contriever":
        model_path = RootConfig.contriever_model_path
        retriever = Contriever_Retriever(searchDataList=searchDataList,top_k=topk,model_path=model_path,ExternalKnowledgeConflictsFlag=ExternalKnowledgeConflictsFlag)
        
    elif retrieverName == "DPR":
        model_path = RootConfig.DPR_model_path
        retriever = DPR_Retriever(searchDataList=searchDataList,top_k=topk,model_path=model_path,ExternalKnowledgeConflictsFlag=ExternalKnowledgeConflictsFlag)
        
    elif retrieverName == "BERT":
        model_path = RootConfig.BERT_model_path
        retriever = BERT_Retriever(searchDataList=searchDataList,top_k=topk,model_path=model_path,ExternalKnowledgeConflictsFlag=ExternalKnowledgeConflictsFlag)
        
    elif retrieverName == "E5":
        model_path = RootConfig.E5_model_path
        retriever = E5_Retriever(searchDataList=searchDataList,top_k=topk,model_path=model_path,ExternalKnowledgeConflictsFlag=ExternalKnowledgeConflictsFlag)
    
    elif retrieverName == "BM25":
        model_path = ""
        retriever = InMemoryBM25Retriever(searchDataList=searchDataList,top_k=topk,model_path=model_path,ExternalKnowledgeConflictsFlag=ExternalKnowledgeConflictsFlag)
    
    # 规则 语言检索
    elif retrieverName == "RuleNL":
        model_path = ""
        retriever = RULE_NL_Retriever(searchDataList=searchDataList,top_k=topk,model_path=model_path,ExternalKnowledgeConflictsFlag=ExternalKnowledgeConflictsFlag)
    
    # 规则 代码检索
    elif retrieverName == "RuleCode":
        model_path = ""
        retriever = RULE_Code_Retriever(searchDataList=searchDataList,top_k=topk,model_path=model_path,ExternalKnowledgeConflictsFlag=ExternalKnowledgeConflictsFlag)
    
    
    # elif retrieverName == "ES_BM25":
    #     model_path = ""
    #     retriever = ElasticsearchBM25Retriever(top_k=topk,model_path=model_path)
    
    # elif retrieverName == "ES_Embedding":
    #     model_path = ""
    #     retriever = ElasticsearchEmbeddingRetriever(top_k=topk)
        

    # elif retrieverName == "memory_Embedding":
    #     model_path = ""
    #     retriever = InMemoryEmbeddingRetriever(top_k=topk)
        
    else:
        raise ValueError(f"Unsupported model types...")

    return retriever

def loadGenerator(generatorName,generation_kwargs,knowledgeDiffFuntion):
    from kninjllm.llm_generator.close_generator.openai_generator import OpenAIGenerator
    from kninjllm.llm_generator.base_generator.baichuan2.component_generator_baichuan2 import Baichuan2Generator
    from kninjllm.llm_generator.base_generator.llama2.component_generator_llama2 import LLama2Generator
    from kninjllm.llm_generator.base_generator.self_rag.self_rag_generator import RagGenerator
    from kninjllm.llm_generator.base_generator.qwq.component_generator_qwq32b import QWQGenerator
    
    if generatorName == "ChatGPT":
        generator = OpenAIGenerator(api_key=RootConfig.openai_api_key,generation_kwargs=generation_kwargs,knowledgeDiffFuntion=knowledgeDiffFuntion)
    
    elif generatorName == "Baichuan2":
        model_path = RootConfig.baichuan2_model_path
        generator = Baichuan2Generator(model_path=model_path,generation_kwargs=generation_kwargs,knowledgeDiffFuntion=knowledgeDiffFuntion)
    
    elif generatorName == "QWQ":
        model_path = RootConfig.QWQ_model_path
        generator = QWQGenerator(model_path=model_path,generation_kwargs=generation_kwargs,knowledgeDiffFuntion=knowledgeDiffFuntion)
    
    elif generatorName == "LLama2":
        model_path = RootConfig.llama2_model_path
        generator = LLama2Generator(model_path=model_path,generation_kwargs=generation_kwargs,knowledgeDiffFuntion=knowledgeDiffFuntion)
    
    elif generatorName == "selfRag":
        model_path = RootConfig.selfRAG_model_path
        generator = RagGenerator(model_path=model_path,generation_kwargs=generation_kwargs,knowledgeDiffFuntion=knowledgeDiffFuntion)
         
    else:
        raise ValueError(f"Unsupported model types...")
    
    return generator    


def loadModelByCatch(model_name,model_path=""):

    print(f"-------LOAD : {model_name} ---- {model_path}  --------")

    # 自动获取model_path
    if model_name == "selfrag":
        model_path = RootConfig.selfRAG_model_path
        
    elif model_name == "llama2":
        model_path = RootConfig.llama2_model_path
    
    elif model_name == "baichuan2":
        model_path = RootConfig.baichuan2_model_path
        
    elif model_name == "qwq":
        model_path = RootConfig.QWQ_model_path
        
    elif model_name == "NED":
        model_path = RootConfig.NED_model_path
    
    elif model_name == "wikisp":
        model_path = RootConfig.WikiSP_model_path
        
    elif "Qwen2.5-14B-Instruct" in model_name:
        model_path = RootConfig.Qwen25_14B_model_path
        
    else:
        pass

    catchData = None
    catch_flag = False
    for catchDataObj in RootConfig.tempModelCatch:
        if catchDataObj['path'] == model_path:
            print("找到模型缓存...\n",model_path)
            catch_flag = True
            break
    
    if catch_flag == True:
        pass
    else:
        print("------------load model path :----,\n",model_path)
        set_proxy()
        try:
            if model_name == "selfrag":
                model = LLM(model=model_path,dtype="half",
                            tensor_parallel_size=torch.cuda.device_count(),
                            max_logprobs=35000,
                            trust_remote_code=True)
                # model = LLM(model=model_path,dtype="half", tensor_parallel_size=1)
                tokenizer = AutoTokenizer.from_pretrained(model_path, padding_side="left")
                catchData = {
                    "model":model,
                    "tokenizer":tokenizer
                }
                RootConfig.tempModelCatch.append({"path":model_path,"data":catchData})
                model = None
                tokenizer = None
                catchData = None
                
            elif model_name == "llama2":
                model = LLM(model_path,
                            dtype="half",
                            trust_remote_code=True,
                            tensor_parallel_size=torch.cuda.device_count())
                tokenizer = AutoTokenizer.from_pretrained(model_path, padding_side="left")
                
                # model = LlamaForCausalLM.from_pretrained(self.model_path, device_map="auto", low_cpu_mem_usage=True, torch_dtype=torch.float32)
                # tokenizer = AutoTokenizer.from_pretrained(self.model_path,trust_remote_code=True)
                
                catchData = {
                    "model":model,
                    "tokenizer":tokenizer
                }
                RootConfig.tempModelCatch.append({"path":model_path,"data":catchData})
                model = None
                catchData = None
            
            elif model_name == "baichuan2":
                model = LLM(model=model_path,
                            trust_remote_code=True,
                            tensor_parallel_size=torch.cuda.device_count()) 
                tokenizer = AutoTokenizer.from_pretrained(model_path, padding_side="left",trust_remote_code=True)
                catchData = {
                    "model":model,
                    "tokenizer":tokenizer
                }
                RootConfig.tempModelCatch.append({"path":model_path,"data":catchData})
                model = None
                tokenizer = None
                catchData = None
                
            elif model_name == "qwq":
                # # vllm
                model = LLM(model=model_path,
                                dtype="half",
                                trust_remote_code=True,
                                tensor_parallel_size=torch.cuda.device_count(),
                                # worker_use_ray=False,  # 启用Ray支持
                                # enforce_eager=False,
                                # gpu_memory_utilization=0.8, # 根据显存情况调整,
                                )
                tokenizer = AutoTokenizer.from_pretrained(model_path, padding_side="left",trust_remote_code=True)
                catchData = {
                    "model":model,
                    "tokenizer":tokenizer
                }
                RootConfig.tempModelCatch.append({"path":model_path,"data":catchData})
                model = None
                tokenizer = None
                catchData = None
                
            elif "Qwen" in model_name:
                model = LLM(model=model_path,tensor_parallel_size=torch.cuda.device_count(),dtype="half")
                tokenizer = AutoTokenizer.from_pretrained(model_path, padding_side="left")
                
                catchData = {
                    "model":model,
                    "tokenizer":tokenizer
                }
                RootConfig.tempModelCatch.append({"path":model_path,"data":catchData})
                model = None
                catchData = None
        
            elif "bge" in model_name:
                model = AutoModel.from_pretrained(model_name, torch_dtype=torch.float16, trust_remote_code=True)
                catchData = {
                    "model":model,
                    "tokenizer":None
                }
                
                RootConfig.tempModelCatch.append({"path":model_path,"data":catchData})
                model = None
                catchData = None
                
            elif model_name == "NED":
                model = Refined.from_pretrained(model_name=model_path,
                                        entity_set="wikidata",
                                        download_files=True,
                                        use_precomputed_descriptions=True)
                catchData = {
                    "model":model,
                    "tokenizer":None
                }
                
                RootConfig.tempModelCatch.append({"path":model_path,"data":catchData})
                model = None
                catchData = None
            
            elif model_name == "wikisp":
                wikisp_model = LLM(model_path, dtype="half",tensor_parallel_size=torch.cuda.device_count())
                catchData = {
                    "model":wikisp_model,
                    "tokenizer":None
                }
                RootConfig.tempModelCatch.append({"path":model_path,"data":catchData})
                wikisp_model = None
                catchData = None


            else:
                pass

        except torch.cuda.OutOfMemoryError as e:
            traceback.print_exc()

    unset_proxy()
    result_list = list(filter(lambda x:x['path'] == model_path,RootConfig.tempModelCatch))
    
    if len(result_list) <= 0:
        print("load model error ...")
        return None
    
    return result_list[0]['data']


def EmbeddingByRetriever(dataList,retrieverNameList):
    print("utils -> EmbeddingByRetriever ....",retrieverNameList)
    
    for retrieverName in retrieverNameList:
        id_data_config = {}
        
        if "contriever" == retrieverName:
            embedding_name = "contriever_embedding"
            allids_list,allembeddings_list = do_contriever_embedding(passages=dataList)
        elif "BGE" == retrieverName:
            embedding_name = "BGE_embedding"
            allids_list,allembeddings_list = do_BGE_embedding(passages=dataList)
        elif "BGEM3" == retrieverName:
            embedding_name = "BGEM3_embedding"
            allids_list,allembeddings_list = do_BGEM3_embedding(passages=dataList)
        elif "DPR" == retrieverName:
            embedding_name = "DPR_embedding"
            allids_list,allembeddings_list = do_DPR_embedding(passages=dataList)
        elif "E5" == retrieverName:
            embedding_name = "E5_embedding"
            allids_list,allembeddings_list = do_E5_embedding(passages=dataList)
        elif "BERT" == retrieverName:
            embedding_name = "BERT_embedding"
            allids_list,allembeddings_list = do_BERT_embedding(passages=dataList)
        # elif "BM25" == retrieverName:
            # embedding_name = "BM25_embedding"
            # allids_list,allembeddings_list = do_BM25_embedding(input_List=dataList)
        else:
            continue
            # raise ValueError("Unsupported retriever embedding types")
            
        for id,emb in zip(allids_list,allembeddings_list):
            id_data_config[id] = emb.tolist()
            
        for data in dataList:
            if len(allids_list) == len(allembeddings_list) == len(dataList):
                data[embedding_name] = id_data_config[data['id']]
            else:
                continue
                # raise ValueError("embedding incorrect length ...")
            
    return dataList