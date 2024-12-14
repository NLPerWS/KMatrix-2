from typing import Any, Dict, List, Optional
from kninjllm.llm_generator.base_generator.RESDSQL.compont_RESDSQL import do_text_to_sql
from root_config import RootConfig

# 保存当前工作目录
import os
cwd = os.getcwd()
print("--------------------当前工作目录-----------------\n",cwd)

class Sql_language_generator:

    def __init__(
        self,
        db_info:dict,
        tables:dict,
        device:str,
    ):
        self.db_info = db_info
        self.tables = tables
        self.device = device
    
    def run(
        self,
        query: str
    ):
        
        query_list = [query]
        # 切换工作目录
        os.chdir(RootConfig.root_path + "kninjllm/llm_generator/base_generator/RESDSQL")
        data_list = do_text_to_sql(query_list=query_list,tables=self.tables,root_path=RootConfig.root_path,
                                   db_info=self.db_info,device=self.device,model_path=RootConfig.root_path + "dir_model")
        os.chdir(cwd)
        
        # 调用
        res_query = data_list[0]
        return {"final_result":res_query}