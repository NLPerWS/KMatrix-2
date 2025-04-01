import json
import os
import requests
from elasticsearch import Elasticsearch
from elasticsearch.helpers import scan
from kninjllm.llm_common.version import __version__ as kninjllm_version
from vllm import SamplingParams
from kninjllm.llm_utils.common_utils import unset_proxy,loadModelByCatch
from root_config import RootConfig

from uuid import uuid4

# 与 ES 解耦
# 全局变量存储ES模拟数据和文件路径
_es_data = {}
_es_file_path = RootConfig.wikidata_emnlp23_db_path

def get_es_client():
    """模拟ES客户端，加载JSON文件数据到内存"""
    global _es_data, _es_file_path
    # 初始化或加载JSON文件
    if os.path.exists(_es_file_path):
        with open(_es_file_path, 'r') as f:
            _es_data = json.load(f)
    else:
        _es_data = {}
        with open(_es_file_path, 'w') as f:
            json.dump(_es_data, f)
    return None  # 保持接口兼容，但返回None

def insert_one_to_es(client, index, data):
    """向指定索引插入一条数据"""
    global _es_data, _es_file_path
    
    if index not in _es_data:
        _es_data[index] = []
    
    # 生成唯一ID并插入数据
    doc_id = str(uuid4())
    _es_data[index].append({'_id': doc_id, '_source': data})
    
    # 立即写入文件
    with open(_es_file_path, 'w') as f:
        json.dump(_es_data, f)
    return "ok"

def delete_many_by_es(client, index, data):
    """删除所有匹配条件的文档"""
    global _es_data, _es_file_path
    
    if index not in _es_data:
        return "ok"
    
    # 过滤出不需要删除的文档
    remaining = []
    for doc in _es_data[index]:
        match = all(doc['_source'].get(k) == v for k, v in data.items())
        if not match:
            remaining.append(doc)
    
    _es_data[index] = remaining
    
    # 立即写入文件
    with open(_es_file_path, 'w') as f:
        json.dump(_es_data, f)
    return "ok"

def find_one_by_es(client, index, data):
    """查找第一个匹配条件的文档"""
    global _es_data
    
    if index not in _es_data:
        return None
    
    for doc in _es_data[index]:
        if all(doc['_source'].get(k) == v for k, v in data.items()):
            return doc['_source']
    return None

def find_by_es(client, index):
    """获取索引下的所有文档"""
    global _es_data
    return [doc['_source'] for doc in _es_data.get(index, [])]



def get_query_sparql(url,headers=None,params=None):
    unset_proxy()
    try:
        res = requests.get(url=url, params=params,headers=headers,timeout=5)
    except:
        try:
            res = requests.post(url="http://ave0lv6oah9g.guyubao.com/do_request_sparql",headers = {'Content-Type': 'application/json'},json={
                "url":url,
                "headers":headers,
                "params":params
            })
        except:
            res = None
        
    return res


def proxy_query_wiki(query):
    unset_proxy()
    res = requests.post(url="http://ave0lv6oah9g.guyubao.com/do_query_wiki",headers = {'Content-Type': 'application/json'},json={'query':query}).json()['data']
    return res
    

def natural_to_sparql(prompt):
    sampling_params = SamplingParams(temperature=0, top_p=1,max_tokens=200,stop=["</s>", "\n"])
    loadModel = loadModelByCatch(model_name='wikisp',model_path=RootConfig.WikiSP_model_path)
    model = loadModel['model']
    pred = model.generate(prompt, sampling_params)[0]
    content = pred.outputs[0].text
    return content
