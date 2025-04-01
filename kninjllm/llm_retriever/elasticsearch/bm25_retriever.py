from typing import Any, Dict, List, Optional
from kninjllm.llm_common.component import component
from kninjllm.llm_common.serialization import default_from_dict, default_to_dict
from kninjllm.llm_store.elasticsearch_document_store import ElasticsearchDocumentStore
from root_config import RootConfig
from kninjllm.llm_utils.common_utils import knowledge_conflict_check

@component
class ElasticsearchBM25Retriever:


    def __init__(
        self,
        top_k = 10,
        model_path:str="",
        filters: Optional[Dict[str, Any]] = None,
        fuzziness: str = "AUTO",
        scale_score: bool = False,
    ):

        self._document_store = None
        self._filters = filters or {}
        self._fuzziness = fuzziness
        self.top_k = top_k
        self._scale_score = scale_score
        self.logSaver = RootConfig.logSaver

    def to_dict(self) -> Dict[str, Any]:
        return default_to_dict(
            self,
            filters=self._filters,
            fuzziness=self._fuzziness,
            top_k=self.top_k,
            scale_score=self._scale_score,
            document_store=self._document_store.to_dict(),
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ElasticsearchBM25Retriever":
        data["init_parameters"]["document_store"] = ElasticsearchDocumentStore.from_dict(
            data["init_parameters"]["document_store"]
        )
        return default_from_dict(cls, data)

    def setKnowledge(self,searchDataList,knowledge_path):
        if self._document_store == None:
            raise Exception("document_store is None")
    @component.output_types(final_result=List[List[Dict[str,Any]]])
    def run(
        self,
        query_obj: Dict[str,Any] = {},
    ):
        print("-------------------------------BM25_Retriever-----------------------------------")

        if query_obj == {}:
            return {"final_result": [[]]}
        
        if self._document_store == None:
            return {"final_result": [[]]}
        
        if self.logSaver is not None:
            self.logSaver.writeStrToLog("Function -> ElasticsearchBM25Retriever -> run | Given the search text, return the search content ")
            self.logSaver.writeStrToLog("search input -> :querys: "+str(query_obj))

        final_docs_dicts_list = []
        docs = self._document_store._bm25_retrieval(query=query_obj['question'], top_k=self.top_k)
        selected_keys = ['id', 'content', 'source','score']
        docs_dicts_list = list(map(lambda x: {k: x.__dict__[k] for k in selected_keys if k in x.__dict__}, docs))
        final_docs_dicts_list.append(docs_dicts_list)

        if self.logSaver is not None:
            self.logSaver.writeStrToLog("search returned -> : final_result: "+str(final_docs_dicts_list))
        return {"final_result": final_docs_dicts_list}