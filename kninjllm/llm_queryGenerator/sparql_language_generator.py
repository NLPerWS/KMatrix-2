from typing import Any, Dict, List, Optional

from kninjllm.llm_generator.base_generator.wikidata_emnlp23.infer import e2esparql_generate_flask

class Sparql_language_generator:

    def __init__(
        self,
        tables
    ):
        self.tables = tables
    def run(
        self,
        query: str
    ):
        print("-----------self.tables---------------\n",self.tables)
        res_query = e2esparql_generate_flask(query)
        
        return {"final_result":res_query}