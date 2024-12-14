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


class RULE_NL_Retriever:

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
        self.retriever_path = "BAAI/bge-base-zh-v1.5"
        self.ExternalKnowledgeConflictsFlag = ExternalKnowledgeConflictsFlag
        print("------------self.searchDataList len------------------\n",len(self.searchDataList))

    def run(
        self,
        query:str = "",
        query_list: List[str] = []
    ):

        print("RULE_NL_Retriever infer ...")
        
        if query != "" and len(query_list) == 0:
            query_list = [query]
            
        if len(self.searchDataList) == 0:
            return {"final_result": []}
        
        if self.logSaver is not None:
            self.logSaver.writeStrToLog("Function -> RULE_NL_Retriever -> run | Given the search text, return the search content ")
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
        
        dataset = "law"
        instruction = "已知以下指控['保险诈骗', '制造、贩卖、传播淫秽物品', '非法获取公民个人信息', '冒充军人招摇撞骗', '强制猥亵、侮辱妇女', '敲诈勒索', '串通投标', '故意伤害', '招摇撞骗', '非法组织卖血', '破坏监管秩序', '倒卖文物', '倒卖车票、船票', '传播性病', '脱逃', '破坏生产经营', '侵犯著作权', '非国家工作人员受贿', '危险驾驶', '虚开增值税专用发票、用于骗取出口退税、抵扣税款发票', '破坏广播电视设施、公用电信设施', '招收公务员、学生徇私舞弊', '非法买卖、运输、携带、持有毒品原植物种子、幼苗', '打击报复证人', '破坏交通设施', '盗窃、侮辱尸体', '假冒注册商标', '行贿', '生产、销售假药', '非法生产、买卖警用装备', '职务侵占', '赌博', '贪污', '挪用特定款物', '非法转让、倒卖土地使用权', '生产、销售伪劣产品', '伪造、变造金融票证', '抢劫', '劫持船只、汽车', '遗弃', '非法吸收公众存款', '出售、购买、运输假币', '非法占用农用地', '侮辱', '挪用公款', '伪造、变造、买卖武装部队公文、证件、印章', '传授犯罪方法', '扰乱无线电通讯管理秩序', '利用影响力受贿', '盗窃', '虐待被监管人', '挪用资金', '污染环境', '重婚', '非法持有、私藏枪支、弹药', '非法生产、销售间谍专用器材', '伪证', '破坏电力设备', '私分国有资产', '非法制造、买卖、运输、邮寄、储存枪支、弹药、爆炸物', '骗取贷款、票据承兑、金融票证', '非法处置查封、扣押、冻结的财产', '违法发放贷款', '拐卖妇女、儿童', '聚众哄抢', '虚报注册资本', '隐匿、故意销毁会计凭证、会计帐簿、财务会计报告', '掩饰、隐瞒犯罪所得、犯罪所得收益', '诈骗', '过失损坏武器装备、军事设施、军事通信', '徇私枉法', '非法行医', '重大责任事故', '虐待', '生产、销售有毒、有害食品', '非法采矿', '徇私舞弊不征、少征税款', '破坏计算机信息系统', '集资诈骗', '绑架', '强迫劳动', '对非国家工作人员行贿', '强奸', '非法种植毒品原植物', '非法携带枪支、弹药、管制刀具、危险物品危及公共安全', '走私武器、弹药', '洗钱', '侵占', '拐骗儿童', '金融凭证诈骗', '提供侵入、非法控制计算机信息系统程序、工具', '故意毁坏财物', '诬告陷害', '销售假冒注册商标的商品', '非法采伐、毁坏国家重点保护植物', '逃税', '生产、销售伪劣农药、兽药、化肥、种子', '玩忽职守', '组织、强迫、引诱、容留、介绍卖淫', '贷款诈骗', '引诱、教唆、欺骗他人吸毒', '破坏交通工具', '过失致人死亡', '危险物品肇事', '妨害公务', '走私、贩卖、运输、制造毒品', '非法拘禁', '走私普通货物、物品', '对单位行贿', '信用卡诈骗', '非法经营', '持有、使用假币', '收买被拐卖的妇女、儿童', '单位受贿', '帮助犯罪分子逃避处罚', '徇私舞弊不移交刑事案件', '非法侵入住宅', '介绍贿赂', '重大劳动安全事故', '受贿', '聚众斗殴', '合同诈骗', '滥用职权', '盗窃、抢夺枪支、弹药、爆炸物', '生产、销售不符合安全标准的食品', '拒不执行判决、裁定', '盗掘古文化遗址、古墓葬', '伪造货币', '过失致人重伤', '非法猎捕、杀害珍贵、濒危野生动物', '滥伐林木', '窝藏、包庇', '动植物检疫徇私舞弊', '强迫交易', '非法获取国家秘密', '非法买卖制毒物品']，xx应是哪项指控？"
        
        # step1
        parser = ArgumentParser()
        args = parser.parse_args()
        args.model_path = self.model_path
        
        args.model = loadModelByCatch(model_name=self.model_path,model_path=self.model_path)
        
        args.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        
        # args.data_path = f"{work_path}/dataset/{dataset}/test_data.json"
        
        args.query_list = list(map(lambda x:{"instruction": instruction,"input": x,"output": "","rule": []},query_list))
        
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
        
        
        os.chdir(current_working_directory)
        print("执行完成,当前工作目录:\n",os.getcwd())
        
        do_initCatch(clean_knowledge=False,clean_model=True)
        
        final_result = knowledge_conflict_check(query_list=query_list,final_result=final_result,ExternalKnowledgeConflictsFlag=self.ExternalKnowledgeConflictsFlag)
        
        if self.logSaver is not None:
            self.logSaver.writeStrToLog("search returned -> : final_result: "+str(final_result))
            
        return {"final_result": final_result}
