import os
import time
import uuid
from root_config import RootConfig
os.environ["CUDA_VISIBLE_DEVICES"] = RootConfig.CUDA_VISIBLE_DEVICES
import sys
import json
import traceback
from flask import Flask, jsonify, request
from flask_cors import *
import shutil
from typing import Any, Dict, List, Optional
import gc
import ray
import torch
import pyarrow.parquet as pq
import pandas as pd
from kninjllm.llm_utils.common_utils import loadRetriever,loadGenerator,loadKnowledgeByCatch,read_server_files,EmbeddingByRetriever,do_initCatch

class Kninjllm_Flask:
    
    def __init__(self,flask_name,
                 initJsonConfigDataPath:str,
                 dbinitJsonConfigDataPath:str,
                 taskinitJsonConfigDataPath:str,
                 datasetDataPath:str
                ):
        
        # init flask_app
        self.app = Flask(flask_name)
        self.app = Flask(__name__, static_url_path='')
        self.app.config['JSON_AS_ASCII'] = False
        
        CORS(self.app, resources={r"/*": {"origins": "*"}}, send_wildcard=True)

        # init dir
        self.initJsonConfigDataPath = initJsonConfigDataPath
        self.dbinitJsonConfigDataPath = dbinitJsonConfigDataPath
        self.taskinitJsonConfigDataPath = taskinitJsonConfigDataPath
        self.datasetDataPath = datasetDataPath
        
        if not os.path.exists("dir_dataset_upload/"):
            os.mkdir("dir_dataset_upload/")
            
        if not os.path.exists("dir_init_config/"):
            os.mkdir("dir_init_config/")
                
        if not os.path.exists("dir_knowledge_upload/"):
            os.mkdir("dir_knowledge_upload/")
        
        if not os.path.exists("dir_model/"):
            os.mkdir("dir_model/")
        
        if not os.path.exists("dir_task_reult_data/"):
            os.mkdir("dir_task_reult_data/")
        
        
        if not os.path.exists(self.initJsonConfigDataPath):
            with open(self.initJsonConfigDataPath,'w',encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False)
        
        if not os.path.exists(self.dbinitJsonConfigDataPath):
            with open(self.dbinitJsonConfigDataPath,'w',encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False)
        
        if not os.path.exists(self.taskinitJsonConfigDataPath):
            with open(self.taskinitJsonConfigDataPath,'w',encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False)
        
        if not os.path.exists(self.datasetDataPath):
            with open(self.datasetDataPath,'w',encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False)

        
        # self.current_template_name = ""
        # 清空缓存
        @self.app.get('/initCatch')
        def initCatch():
            do_initCatch(clean_knowledge=True,clean_model=True)
            return jsonify({"data": "ok", "code": 200})   
            
            
        # 获取初始数据集列表
        @self.app.get('/getDataSetList')
        def getDataSetList():
            try:
                with open(self.datasetDataPath,'r',encoding='utf-8') as f:
                    data = json.load(f)
                return jsonify({"data": data, "code": 200})
            except Exception as e:
                traceback.print_exc()
                return jsonify({"data": str(e), "code": 500})
            
        # 更新 数据集列表
        @self.app.post('/updateDataSetList')
        def updateDataSetList():
            jsondata = request.get_json()
            data = jsondata["data"]
            try:
                with open(self.datasetDataPath,'w',encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False)
                    
                # 删除对应文件
                for fileName in os.listdir(RootConfig.datasetUploadDirPath):
                    del_flag = True
                    for d in data:
                        if fileName == d['fileName']:
                            del_flag = False
                    
                    if del_flag:
                        path = RootConfig.datasetUploadDirPath + fileName
                        os.remove(path)
                    
                return jsonify({"data": data, "code": 200})
            except Exception as e:
                traceback.print_exc()
                return jsonify({"data": str(e), "code": 500})
            
            
        # 获取模板类型列表
        @self.app.get('/getTemplateTypeList')
        def getTemplateTypeList():
            # data = ['default','selfRagShort','selfRagLong','COK']
            data = ['Naive','Loop','Adaptive','Iterative']
            
            return jsonify({"data": data, "code": 200})
            
        # 获取初始模板配置
        @self.app.get('/getInitConfig')
        def getInitConfig():
            try:
                with open(self.initJsonConfigDataPath,'r',encoding='utf-8') as f:
                    data = json.load(f)
                return jsonify({"data": data, "code": 200})
            except Exception as e:
                traceback.print_exc()
                return jsonify({"data": str(e), "code": 500})
            
        # 更新 模板配置
        @self.app.post('/updateInitConfig')
        def updateInitConfig():
            jsondata = request.get_json()
            order = jsondata["order"]
            data = jsondata["data"]
            try:
                origin_template_name = jsondata["origin_template_name"]
            except:
                origin_template_name = ""
            
            if origin_template_name == "":
                origin_template_name = data['name']
            
            # print('---------------------order------------------------\n',order)
            # print('---------------------data------------------------\n',data)
            # print('---------------------origin_template_name------------------------\n',origin_template_name)

            if order == 'delete':
                with open(initJsonConfigDataPath, 'r', encoding='utf-8') as f:
                        dataList = json.load(f)
                    # 使用列表推导式来过滤掉不需要的元素
                dataList = [one_con for one_con in dataList if one_con['name'] != data['name']]
                with open(initJsonConfigDataPath, 'w', encoding='utf-8') as f:
                    json.dump(dataList, f, ensure_ascii=False)
                return jsonify({"data": dataList, "code": 200})
                    
            # 存在就更新 
            elif order == 'update':
                with open(initJsonConfigDataPath, 'r', encoding='utf-8') as f:
                        dataList = json.load(f)
                for index,one_con in enumerate(dataList):
                    if one_con['name'] == origin_template_name:
                        dataList[index] = data
                        break

                with open(initJsonConfigDataPath, 'w', encoding='utf-8') as f:
                    json.dump(dataList, f, ensure_ascii=False)
                
                return jsonify({"data": dataList, "code": 200})
            
            elif order == 'add':
                with open(initJsonConfigDataPath, 'r', encoding='utf-8') as f:
                        dataList = json.load(f)
                        
                # 校验 重复name
                if data['name'] in [one_con['name'] for one_con in dataList]:
                    return jsonify({"data": "name repeat", "code": 500})
                
                dataList.append(data)
                with open(initJsonConfigDataPath, 'w', encoding='utf-8') as f:
                    json.dump(dataList, f, ensure_ascii=False)
                
                return jsonify({"data": dataList, "code": 200})
            
                        
            else:
                return jsonify({"data": "order error", "code": 500})
            
            
        # 获取数据库类型
        @self.app.get('/getDataBaseType')
        def getDataBaseType():
            
            data = [
                {
                    "value":"Text",
                    "label":"Text",
                    "children":[
                        {
                            "value":"TextFile",
                            "label":"TextFile",
                            "acceptType":".txt,.md,.markdown,.doc,.docx,.pdf,.json,.jsonl"
                        },
                        {
                            "value":"onlineDB",
                            "label":"onlineDB",
                            "acceptType":""
                        }
                    ]
                },
                {
                    "value":"Table",
                    "label":"Table",
                    "children":[
                        {
                            "value":"MysqlDB",
                            "label":"MysqlDB",
                            "acceptType":""
                        },
                        {
                            "value":"Excel",
                            "label":"Excel",
                            "acceptType":".xls,.xlsx"
                        } 
                    ]
                },
                {
                    "value":"Graph",
                    "label":"Knowledge Graph",
                    "children":[
                        {
                            "value":"GraphDB",
                            "label":"GraphDB",
                            "acceptType":""
                        },
                        {
                            "value":"Neo4jDB",
                            "label":"Neo4jDB",
                            "acceptType":""
                        },
                        {
                            "value":"Triple",
                            "label":"Triple",
                            "acceptType":".csv,.json,.tsv,.txt"
                        }
                        
                    ]
                },
                {
                    "value":"Rule",
                    "label":"Rule",
                    "children":[
                        {
                            "value":"Rule_NL",
                            "label":"Rule_NL",
                            "acceptType":".json,.txt"
                        },
                        {
                            "value":"Rule_FOL",
                            "label":"Rule_FOL",
                            "acceptType":".json"
                        }
                    ]
                },
                {
                    "value":"Code",
                    "label":"Code",
                    "children":[
                        {
                            "value":"Rule_Code",
                            "label":"Rule_Code",
                            "acceptType":".json"
                        }
                    ]
                }
                
            ]
            
            return jsonify({"data": data, "code": 200})
            
        # 获取数据库配置数据
        @self.app.get('/getDataBaseData')
        def getDataBaseData():
            try:
                with open(self.dbinitJsonConfigDataPath,'r',encoding='utf-8') as f:
                    data = json.load(f)
                return jsonify({"data": data, "code": 200})
            except Exception as e:
                traceback.print_exc()
                return jsonify({"data": str(e), "code": 500})
            
            

        # 获取知识冲突处理方法
        @self.app.get('/getknowledgeDiffFunction')
        def getknowledgeDiffFunction():
            
            data = [
                {
                    "value":"Faithful to context",
                    "label":"Faithful to context",
                },
                {
                    "value":"Factuality improvement",
                    "label":"Factuality improvement",
                }
            ]
            
            return jsonify({"data": data, "code": 200})
            
            
        # 更新 数据库数据
        @self.app.post('/updateDbConfig')
        def updateDbConfig():
            jsondata = request.get_json()
            order = jsondata["order"]
            data = jsondata["data"]
            origin_Db_name = jsondata["origin_Db_name"]
            if origin_Db_name == "":
                origin_Db_name = data['name']
            
            print('---------------------order------------------------\n',order)
            print('---------------------data------------------------\n',data)
            print('---------------------origin_Db_name------------------------\n',origin_Db_name)

            if order == 'delete':
                with open(dbinitJsonConfigDataPath, 'r', encoding='utf-8') as f:
                        dataList = json.load(f)
                    # 使用列表推导式来过滤掉不需要的元素
                dataList = [one_con for one_con in dataList if one_con['infoName'] != data['infoName']]
                with open(dbinitJsonConfigDataPath, 'w', encoding='utf-8') as f:
                    json.dump(dataList, f, ensure_ascii=False)
                    
                # 删除本地文件夹
                if os.path.exists(RootConfig.knowledgeUploadDirPath+data['infoPath']):
                    shutil.rmtree(RootConfig.knowledgeUploadDirPath+data['infoPath'])
                
                # 删除知识缓存
                db_dir_path = RootConfig.knowledgeUploadDirPath+data['infoName']
                for index,catchDataObj in enumerate(RootConfig.tempPipeLineKnowledgeCatch):
                    if catchDataObj['path'] == db_dir_path:
                        del RootConfig.tempPipeLineKnowledgeCatch[index] 
                
                return jsonify({"data": dataList, "code": 200})
                    
            # 存在就更新 
            elif order == 'update':
                with open(dbinitJsonConfigDataPath, 'r', encoding='utf-8') as f:
                        dataList = json.load(f)
                for index,one_con in enumerate(dataList):
                    if one_con['infoName'] == origin_Db_name:
                        dataList[index] = data
                        break

                with open(dbinitJsonConfigDataPath, 'w', encoding='utf-8') as f:
                    json.dump(dataList, f, ensure_ascii=False)
                
                # 重命名文件夹
                origin_Db_path = origin_Db_name.replace("/","_")
                if os.path.exists(RootConfig.knowledgeUploadDirPath+origin_Db_path):
                    os.rename(RootConfig.knowledgeUploadDirPath+origin_Db_path,RootConfig.knowledgeUploadDirPath+data['infoPath'])
                
                return jsonify({"data": dataList, "code": 200})
            
            elif order == 'add':
                with open(dbinitJsonConfigDataPath, 'r', encoding='utf-8') as f:
                        dataList = json.load(f)
                        
                # 校验 重复name
                if data['infoName'] in [one_con['infoName'] for one_con in dataList]:
                    return jsonify({"data": "infoName repeat", "code": 500})
                
                dataList.append(data)
                with open(dbinitJsonConfigDataPath, 'w', encoding='utf-8') as f:
                    json.dump(dataList, f, ensure_ascii=False)
                
                return jsonify({"data": dataList, "code": 200})
                        
            else:
                return jsonify({"data": "order error", "code": 500})
            
            
        # 获取数据库知识数据
        @self.app.post('/getDataBaseKnowledgeData')
        def getDataBaseKnowledgeData():
            jsondata = request.get_json()
            infoName = jsondata["infoName"]
            infoType = jsondata["infoType"]
            infoPath = jsondata["infoName"].replace("/","_")
            root_type = infoType[0]
            xld_type = infoType[1]
            
            if not os.path.exists(RootConfig.knowledgeUploadDirPath + infoPath + "/"):
                return jsonify({"data": [], "code": 200})
            final_list = []
            sample_len = 10
            for index,fileName in enumerate(os.listdir(RootConfig.knowledgeUploadDirPath + infoPath + "/")):
                filePath = os.path.join(RootConfig.knowledgeUploadDirPath + infoPath + "/",fileName)
                sampleDataList = read_server_files(filePath,False,xld_type)[0:sample_len]
                one_file_obj = {
                    "id": index,
                    "label":fileName,
                    "value":fileName,
                    "children":sampleDataList
                }
                final_list.append(one_file_obj)
            
            return jsonify({"data": final_list, "code": 200})

        # 删除数据库知识数据
        @self.app.post('/delDataBaseKnoeledgeData')            
        def delDataBaseKnoeledgeData():
            jsondata = request.get_json()
            infoName = jsondata["infoName"]
            infoType = jsondata["infoType"]
            infoPath = jsondata["infoName"].replace("/","_")
            
            delFileName = jsondata["delFileName"]
            
            for index,fileName in enumerate(os.listdir(RootConfig.knowledgeUploadDirPath + infoPath + "/")):
                if fileName == delFileName:
                    filePath = os.path.join(RootConfig.knowledgeUploadDirPath + infoPath + "/",fileName)
                    os.remove(filePath)
            
            #  调用 getDataBaseKnowledgeData 重新获取文件列表
            response = getDataBaseKnowledgeData()
            final_list = response.get_json()["data"]
            
            # 删除知识缓存
            db_dir_path = RootConfig.knowledgeUploadDirPath + infoName
            for index,catchDataObj in enumerate(RootConfig.tempPipeLineKnowledgeCatch):
                if catchDataObj['path'] == db_dir_path:
                    del RootConfig.tempPipeLineKnowledgeCatch[index] 
        
            return jsonify({"data": final_list, "code": 200})
            
        # 获取检索器列表
        @self.app.post('/getRetrieverDataListByDB')
        def getRetrieverDataListByDB():
            jsondata = request.get_json()
            dbInfoList = jsondata["dbInfoList"]
            print("------------dbInfoList-----------------------\n",dbInfoList)
            
            # 默认只选一个数据库
            dbInfoList = dbInfoList
            
            if len(dbInfoList) == 0:
                return jsonify({"data": [], "code": 200})
            
            data = []
            for dbInfo in dbInfoList:
                # 如果是链接型知识库, 返回查询接口
                if dbInfo[1].endswith("DB"):
                    if dbInfo[1] == "onlineDB":
                        data.append({
                            "label":"NLParser/Parser",
                            "value":"NLParser/Parser"
                        })
                    elif dbInfo[1] == "GraphDB":
                        data.append({
                            "label":"SPARQLParser/Parser",
                            "value":"SPARQLParser/Parser"
                        })
                    elif dbInfo[1] == "MysqlDB":
                        data.append({
                            "label":"SqlParser/Parser",
                            "value":"SqlParser/Parser"
                        })    
                    elif dbInfo[1] == "Neo4jDB":
                        data.append({
                            "label":"CQLParser/Parser",
                            "value":"CQLParser/Parser"
                        })   
                    else:
                        pass
                    
                elif "Rule" in dbInfo[0] or "Code" in dbInfo[0]:
                    if dbInfo[1] == "Rule_Code":
                        data.append({
                            "label":"Rule_Code/RuleCode",
                            "value":"Rule_Code/RuleCode"
                        })
                    else:
                        data.append({
                            "label":"Rule_NL/RuleNL",
                            "value":"Rule_NL/RuleNL"
                        })
                else:
                    data.append({
                        "label":"contriever/TEXT",
                        "value":"contriever/TEXT"
                    })
                    data.append({
                        "label":"DPR/TEXT",
                        "value":"DPR/TEXT"
                    })
                    data.append({
                        "label":"BGE/TEXT",
                        "value":"BGE/TEXT"
                    })
                    data.append({
                        "label":"E5/TEXT",
                        "value":"E5/TEXT"
                    })
                    data.append({
                        "label":"BERT/TEXT",
                        "value":"BERT/TEXT"
                    })
                    data.append({
                        "label":"BM25/TEXT",
                        "value":"BM25/TEXT"
                    })
            
            # 去重
            data = self.remove_duplicates(data)
            
            return jsonify({"data": data, "code": 200})

        # 获取生成器列表
        @self.app.get('/getLlmDataList')
        def getLlmDataList():
            data = ['ChatGPT','Baichuan2','LLama2','selfRag']
            return jsonify({"data": data, "code": 200})
            
        # 获取任务数据
        @self.app.get('/getTaskDataList')
        def getTaskDataList():
            try:
                with open(self.taskinitJsonConfigDataPath,'r',encoding='utf-8') as f:
                    data = json.load(f)
                return jsonify({"data": data, "code": 200})
            except Exception as e:
                traceback.print_exc()
                return jsonify({"data": str(e), "code": 500})
            
        # 更新 任务数据
        @self.app.post('/updateTaskData')
        def updateTaskData():
            jsondata = request.get_json()
            data = jsondata["data"]
            try:
                # 删除任务对应的结果
                with open(self.taskinitJsonConfigDataPath,'r',encoding='utf-8') as f:
                    origin_list = json.load(f)
                origin_name_list = [x['name'] for x in origin_list]
                new_name_list = [x['name'] for x in data]
                del_name_list = []
                for o_name in origin_name_list:
                    if o_name not in new_name_list:
                        del_name_list.append(o_name)
                
                if len(del_name_list) > 0:
                    for del_name in del_name_list:
                        del_path = RootConfig.dir_task_reult_data_path + del_name + ".json"
                        if os.path.exists(del_path):
                            os.remove(del_path)
                # update
                with open(self.taskinitJsonConfigDataPath,'w',encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False)
                    
                return jsonify({"data": data, "code": 200})
            except Exception as e:
                traceback.print_exc()
                return jsonify({"data": str(e), "code": 500})
            
        # 开始运行任务
        @self.app.post('/runTaskData')
        def runTaskData():
            jsondata = request.get_json()
            run_data = jsondata["run_data"]
            
            with open(self.taskinitJsonConfigDataPath,'r',encoding='utf-8') as f:
                origin_taskDataList = json.load(f)
            # 查找模板信息
            with open(self.initJsonConfigDataPath,'r',encoding='utf-8') as f:
                templateDataList = json.load(f)
            templateInfo = list(filter(lambda x:x['name'] == run_data['template'],templateDataList))[0]
            
            # 查找数据集信息
            datasetPath = RootConfig.datasetUploadDirPath + run_data['datasets']
            if os.path.exists(datasetPath):
                with open(datasetPath, 'r', encoding='utf-8') as f:
                    datasetList = json.load(f)
            else:
                return jsonify({"data": "数据集不存在", "code": 500})
            
            # 测试
            # datasetList = datasetList[0:3]
            
            for index,one_con in enumerate(origin_taskDataList):
                try:
                    if one_con['name'] == run_data['name']:
                        origin_taskDataList[index]['taskFlag'] = 'running'
                        with open(self.taskinitJsonConfigDataPath,'w',encoding='utf-8') as f:
                            json.dump(origin_taskDataList, f, ensure_ascii=False)
                        print("----------------running--------------------")
                            
                        # 根据模板,数据集,跑结果
                        input_list = []
                        for data in datasetList:
                            # km2
                            if "instruction" in data and "input" in data:
                                input_list.append(data['input'])
                            else:
                                input_list.append(data['question'])
                        
                        res_list = self.do_chat(input_list,templateInfo)
                        
                        # 计算准确率
                        if len(datasetList) == len(res_list):
                            num_true = 0
                            
                            recall_1 = 0
                            recall_5 = 0
                            recall_10 = 0
                            
                            for i in range(len(datasetList)):
                                datasetList[i]['predict_output'] = res_list[i]['content']
                                datasetList[i]['ctxs'] = res_list[i]['ctxs']
                                
                                if "golden_answers" not in datasetList[i] and "output" in datasetList[i]:
                                    datasetList[i]['golden_answers'] = [datasetList[i]['output']]
                                # check true answer
                                for gold_answer in datasetList[i]['golden_answers']:
                                    # 回答是 golden_answers 中的某个元素 的 子串
                                    if gold_answer.strip().lower() in res_list[i]['content'].strip().lower():
                                        num_true += 1
                                        break
                                # check true ctx
                                if "rule" in datasetList[i]:
                                    ctxs_id_list = list(map(lambda x:str(x['id']),res_list[i]['ctxs']))
                                    if str(datasetList[i]['rule'][0]) in ctxs_id_list[0:1]:
                                        recall_1 += 1
                                    if str(datasetList[i]['rule'][0]) in ctxs_id_list[0:5]:
                                        recall_5 += 1
                                    if str(datasetList[i]['rule'][0]) in ctxs_id_list[0:10]:
                                        recall_10 += 1
                                        
                            AccuracyRate = (num_true / len(datasetList)) * 100
                            recall_1 = (recall_1 / len(datasetList)) * 100
                            recall_5 = (recall_5 / len(datasetList)) * 100
                            recall_10 = (recall_10 / len(datasetList)) * 100
                            
                            origin_taskDataList[index]['result'] = {
                                "AccuracyRate":f"{AccuracyRate}%",
                                "recall_1":f"{recall_1}%",
                                "recall_5":f"{recall_5}%",
                                "recall_10":f"{recall_10}%",
                            }
                        
                            origin_taskDataList[index]['taskFlag'] = 'finished'
                            print("----------------finished--------------------")
                        
                            with open(RootConfig.dir_task_reult_data_path + run_data['name'] + ".json",'w',encoding='utf-8') as f:
                                json.dump(datasetList, f, ensure_ascii=False)
                                
                            with open(self.taskinitJsonConfigDataPath,'w',encoding='utf-8') as f:
                                json.dump(origin_taskDataList, f, ensure_ascii=False)
                            
                            return jsonify({"data": 'ok', "code": 200})
                        
                        else:
                            origin_taskDataList[index]['taskFlag'] = 'failed'
                            with open(self.taskinitJsonConfigDataPath,'w',encoding='utf-8') as f:
                                json.dump(origin_taskDataList, f, ensure_ascii=False)
                            return jsonify({"data": "server error ...", "code": 500})
                
                except Exception as e:
                    traceback.print_exc()
                    origin_taskDataList[index]['taskFlag'] = 'failed'
                    with open(self.taskinitJsonConfigDataPath,'w',encoding='utf-8') as f:
                        json.dump(origin_taskDataList, f, ensure_ascii=False)
                    return jsonify({"data": str(e), "code": 500})
        # chat接口
        @self.app.post('/do_chat')
        def do_chat():
            # time.sleep(3)
            jsondata = request.get_json()
            templateInfo = jsondata["templateInfo"]
            input = jsondata["input"]
            
            res_list = self.do_chat([input],templateInfo)
            
            if len(res_list) > 0:
                return jsonify({"data": res_list[0], "code": 200})
            else:
                return jsonify({"data": "server error ...", "code": 500})
        
        # 上传 - 知识库的知识
        @self.app.route('/uploadKnowledge', methods=['POST'])
        def uploadKnowledge():
            
            savePath = request.form.get("savePath")
            savePath = savePath.replace("/","_")
            print('-------------------savePath1-------------------\n',savePath)
            if savePath == "":
                raise ValueError("Upload path is empty")
            if not savePath.endswith("/"):
                savePath = savePath + "/"
            savePath = RootConfig.knowledgeUploadDirPath + savePath
            print('-------------------savePath2-------------------\n',savePath)
            if not os.path.exists(savePath):
                os.makedirs(savePath, exist_ok=True)
                        
            if 'file' not in request.files:
                raise ValueError('No file part')
            file = request.files['file']
            print('-------------------file-------------------\n',file)

            # 删除之前先删除旧文件            
            # if os.path.exists(savePath):
            #     for filename in os.listdir(savePath):
            #         file_path = os.path.join(savePath, filename)
            #         try:
            #             if os.path.isfile(file_path):
            #                 os.unlink(file_path) 
            #             elif os.path.isdir(file_path):
            #                 shutil.rmtree(file_path)
            #         except Exception as e:
            #             print(f'Failed to delete {file_path}. Reason: {e}')
            
            filename = file.filename 
            file.save(savePath+filename)  
            
            # 删除知识缓存
            db_dir_path = savePath
            for index,catchDataObj in enumerate(RootConfig.tempPipeLineKnowledgeCatch):
                if catchDataObj['path'] == db_dir_path:
                    del RootConfig.tempPipeLineKnowledgeCatch[index] 
            
            return jsonify({"data": "upload success", "code": 200})
        
        # 上传 - 任务的数据集
        @self.app.route('/uploadDataset', methods=['POST'])
        def uploadDataset():
            
            uploadTime = request.form.get("uploadTime")
            print(uploadTime)
            
            if 'file' not in request.files:
                return jsonify({'error': 'No file part','code':500}) 

            files = request.files.getlist('file')
            if not files:
                return jsonify({'error': 'No file uploaded','code':500})

            with open(self.datasetDataPath,'r',encoding='utf-8') as f:
                origin_datasetDataList = json.load(f)

            for file in files:
                filename = file.filename 
                
                has_flag = False
                # 如果存在就更新上传时间 不存在就添加
                for index,d in enumerate(origin_datasetDataList):
                    if d['fileName'] == filename:
                        has_flag = True
                        origin_datasetDataList[index]['uploadTime'] = uploadTime
                if has_flag == False:
                    print("添加",filename)
                    origin_datasetDataList.append({
                        'fileName':filename,
                        'uploadTime':uploadTime
                    })

                # 保存文件到服务器
                print(filename)
                savePath = RootConfig.datasetUploadDirPath + filename
                file.save(savePath)  
            with open(self.datasetDataPath,'w',encoding='utf-8') as f:
                json.dump(origin_datasetDataList, f, ensure_ascii=False)

            return jsonify({'message': 'Files successfully uploaded','code':200})
        
        
    # chat方法
    def do_chat(self,inputStrList,templateInfo):
        
        from kninjllm.llm_retriever.interface.root_retriever import RootRetriever
        from kninjllm.llm_retriever.interface.retriever_interface import InterfaceRetriever

        if len(inputStrList) == 1 and inputStrList[0] == "INITKNOWLEDGEANDMODELANDDEPLOY":
            print("do_initCatch and deploy ... ")
            do_initCatch(clean_knowledge=True,clean_model=True)
        
        # 根据不同的模板类型,调用不同的类
        from kninjllm.llm_template.default import defaultTemplate
        from kninjllm.llm_template.selfRagShort import selfRagShortTemplate
        from kninjllm.llm_template.selfRagLong import selfRagLongTemplate
        from kninjllm.llm_template.cok import cokTemplate
        from kninjllm.llm_template.Iterative import IterativeTemaplte
        
        # Naive','Loop','Adaptive','Iterative
        
        templateConfig = {
            "Naive":defaultTemplate,
            "Loop":cokTemplate,
            "Adaptive":selfRagLongTemplate,
            "Iterative":IterativeTemaplte,
        }
        
        # print("------------------------------templateInfo-------------------------\n",templateInfo)
        
        try:
            retriever_list = []
            
            # 如果 含有DB类型知识库 就添加接口查询器(作为检索器)
            if any(d['infoType'][1].endswith("DB") for d in templateInfo['dbInfoList']):
                from kninjllm.llm_knowledgeUploader.utils.interface_execute import InterfaceExecute
                this_interface_config = {}
                parser_list = templateInfo['retrieverModelInfo']['modelNameList']
                parser_list = list(filter(lambda x:x.endswith('/Parser'),parser_list))
                
                for info in templateInfo['dbInfoList']:
                    domain_list = info['infoName'].split('/')
                    if len(domain_list) != 2 or not info['infoType'][1].endswith("DB"):
                        continue
                    # db=([^&]+)&u=([^&]+)&p=([^&]+)
                    add_url = info['dbHost'] + "?" + "db=" + info['dbName'] + "&u=" + info['dbUsername'] + "&p=" + info['dbPassword']
                    print('----------------add_url----------------\n',add_url)
                    
                    tables = []
                    table_path = RootConfig.root_path + "dir_knowledge_upload/" + info['infoPath']
                    print('----------------table_path----------------\n',table_path)
                    if os.path.exists(table_path):
                        for file in os.listdir(table_path):
                            if file.endswith(".json"):
                                with open(table_path + "/" + file, 'r',encoding='utf-8') as f:
                                    table = json.load(f)
                                tables.append(table)
                                break
                    
                    if info['infoType'][1] == "onlineDB":
                        if "NLParser/Parser" in parser_list:
                            parser = "NLParser/Parser"
                        interface = InterfaceExecute(domain=info['infoName'],type='google',url=add_url,parser=parser,tables=tables)
                        
                    elif info['infoType'][1] == "GraphDB":
                        if "SPARQLParser/Parser" in parser_list:
                            parser = "SPARQLParser/Parser"
                        interface = InterfaceExecute(domain=info['infoName'],type='graphdb',url=add_url,parser=parser,tables=tables)
                        
                    elif info['infoType'][1] == "Neo4jDB":
                        if "CQLParser/Parser" in parser_list:
                            parser = "CQLParser/Parser"
                        interface = InterfaceExecute(domain=info['infoName'],type='neo4j',url=add_url,parser=parser,tables=tables)
                        
                    elif info['infoType'][1] == "MysqlDB":
                        if "SqlParser/Parser" in parser_list:
                            parser = "SqlParser/Parser"
                        if len(tables) == 0:
                            raise ValueError("缺少mysql数据库本体描述文件...")
                        interface = InterfaceExecute(domain=info['infoName'],type='sqlite',url=add_url,parser=parser,tables=tables)
                        
                    else:
                        print('不支持的接口类型',info['infoType'][1])

                    domain_0 = domain_list[0]
                    domain_1 = domain_list[1]
                    if domain_0 in this_interface_config:
                        this_interface_config[domain_0][domain_1] = interface
                    else:
                        this_interface_config[domain_0] = {}
                        this_interface_config[domain_0][domain_1] = interface
                        
                print('-----------------------------------this_interface_config---------------------------------------\n',this_interface_config)
                retriever = InterfaceRetriever(searchDataList=this_interface_config,top_k=templateInfo['retrieverModelInfo']['topk'],ExternalKnowledgeConflictsFlag=templateInfo['knowledgeDiffSwitch'])
                retriever_list.append(retriever)
            
            print('parser完成 -----------retriever_list-------------\n',retriever_list)
            
            # 规则NL 检索器
            if any(d['infoType'][1] == "Rule_NL" for d in templateInfo['dbInfoList']) or any(d['infoType'][1] == "Rule_FOL" for d in templateInfo['dbInfoList']):
                data_list = []
                for info in templateInfo['dbInfoList']:
                    if info['infoType'][1] == "Rule_NL" or info['infoType'][1] == "Rule_FOL":
                        temp_data_list = loadKnowledgeByCatch([info['infoPath']],info['infoType'][1])
                        data_list.extend(temp_data_list)
                retriever = loadRetriever(searchDataList=data_list,retrieverName="RuleNL",topk=templateInfo['retrieverModelInfo']['topk'],ExternalKnowledgeConflictsFlag=templateInfo['knowledgeDiffSwitch'])
                retriever.top_k = templateInfo['retrieverModelInfo']['topk']
                retriever_list.append(retriever)
                
            print('rule nl 完成 -----------retriever_list-------------\n',retriever_list)

            # 规则CODE 检索器
            if any(d['infoType'][1] == "Rule_Code" for d in templateInfo['dbInfoList']):
                data_list = []
                for info in templateInfo['dbInfoList']:
                    if info['infoType'][1] == "Rule_Code":
                        temp_data_list = loadKnowledgeByCatch([info['infoPath']],info['infoType'][1])
                        data_list.extend(temp_data_list)
                retriever = loadRetriever(searchDataList=data_list,retrieverName="RuleCode",topk=templateInfo['retrieverModelInfo']['topk'],ExternalKnowledgeConflictsFlag=templateInfo['knowledgeDiffSwitch'])
                retriever.top_k = templateInfo['retrieverModelInfo']['topk']
                retriever_list.append(retriever)
            print('rule code 完成 -----------retriever_list-------------\n',retriever_list)
                
            # 文本检索器
            if any(d['infoType'][1] == "TextFile" or d['infoType'][1] == "Excel" or d['infoType'][1] == "Triple" for d in templateInfo['dbInfoList']):
                # 加载知识
                data_list = []
                for info in templateInfo['dbInfoList']:
                    if info['infoType'][1] == "TextFile" or info['infoType'][1] == "Excel" or info['infoType'][1] == "Triple":
                        print("----info----\n",info)
                        temp_data_list = loadKnowledgeByCatch([info['infoPath']],info['infoType'][1])
                        data_list.extend(temp_data_list)
                # embedding
                this_retrieverName = list(filter(lambda x:"/TEXT" in x,templateInfo['retrieverModelInfo']['modelNameList']))[0].split("/")[0]
                if this_retrieverName != "BM25":
                    embedding_catch_flag = False
                    for index,catchDataObj in enumerate(RootConfig.tempPipeLineKnowledgeCatch):
                        if catchDataObj['path'] == templateInfo['name']+"_embedding":
                            data_list = catchDataObj['data']
                            embedding_catch_flag = True
                    if embedding_catch_flag == False:
                        data_list = EmbeddingByRetriever(data_list,[this_retrieverName])
                        RootConfig.tempPipeLineKnowledgeCatch.append({
                            "path":templateInfo['name']+"_embedding",
                            "data":data_list
                        })
                    
                retriever = loadRetriever(searchDataList=data_list,retrieverName=this_retrieverName,topk=templateInfo['retrieverModelInfo']['topk'],ExternalKnowledgeConflictsFlag=templateInfo['knowledgeDiffSwitch'])
                retriever.top_k = templateInfo['retrieverModelInfo']['topk']
                retriever_list.append(retriever)
            print('文本检索器 完成 -----------retriever_list-------------\n',retriever_list)
                
            retriever = RootRetriever(searchDataList=retriever_list,top_k=templateInfo['retrieverModelInfo']['topk'])
                        
            # ---------------------
            # 生成器不受知识库影响 
            generator = loadGenerator(generatorName=templateInfo['llmModelInfo']['modelName'],generation_kwargs={"max_tokens":templateInfo['llmModelInfo']['maxToken'],"temperature":templateInfo['llmModelInfo']['temperature'],'top_p':templateInfo['llmModelInfo']['topp']},knowledgeDiffFuntion=templateInfo['knowledgeDiffFunction'])
            
            generator.generation_kwargs = {"max_tokens":templateInfo['llmModelInfo']['maxToken'],"temperature":templateInfo['llmModelInfo']['temperature'],'top_p':templateInfo['llmModelInfo']['topp']}

            # print("-----------------------外部知识之间的冲突消解 flag----------------------\n",templateInfo['knowledgeDiffSwitch'])
            # print("-----------------------外部知识与模型之间的冲突消解 Function-----------------------\n",templateInfo['knowledgeDiffFunction'])

            template = templateConfig[templateInfo['type']](info=templateInfo,generator=generator,retriever=retriever)
            resObj_list = template.run(query_list=inputStrList)['final_result']
            
            return resObj_list

        except Exception as e:
            traceback.print_exc()
            return []
    

    # 去重字典数组
    def remove_duplicates(self,dict_list):
        seen = set()
        unique_dicts = []
        for d in dict_list:
            items = tuple(d.items())
            if items not in seen:
                seen.add(items)
                unique_dicts.append(d)
        return unique_dicts

    # run 
    def run(self, host, port):
        self.app.run(host=host, port=port,threaded=True)

if __name__ == "__main__":
    
    my_flask_app = Kninjllm_Flask(flask_name='my_flask_app',
                                  initJsonConfigDataPath=RootConfig.dir_init_config_path +"init_template.json",
                                  dbinitJsonConfigDataPath=RootConfig.dir_init_config_path + "init_database.json",
                                  taskinitJsonConfigDataPath=RootConfig.dir_init_config_path + "init_task.json",
                                  datasetDataPath=RootConfig.dir_init_config_path + "init_dataset.json",
                                  )
    my_flask_app.run(host='0.0.0.0', port=int(RootConfig.SERVER_PORT))
    