from typing import List
import jieba
from rank_bm25 import BM25Okapi
from tqdm import tqdm
from kninjllm.llm_utils.common_utils import knowledge_conflict_check


def do_BM25_embedding(input_List):
        
    return [
                list(filter(lambda x: x.replace(" ", "") != "", list(jieba.cut(doc['content'].lower(), cut_all=False))))
                for doc in tqdm(input_List, desc="Tokenizing corpus")
            ]
        


class InMemoryBM25Retriever:
    def __init__(self,searchDataList, top_k=10, model_path:str="",ExternalKnowledgeConflictsFlag:bool=False):

        self.top_k = top_k
        self.model_path = model_path
        self.searchDataList = searchDataList
        self.ExternalKnowledgeConflictsFlag = ExternalKnowledgeConflictsFlag
        self.tokenized_corpus = self._tokenize_corpus()
        self.bm25 = BM25Okapi(self.tokenized_corpus)
        

    def _tokenize_corpus(self):
        """
        对文档集合进行分词。

        :return: 分词后的文档集合。
        """
        return [
            list(filter(lambda x: x.replace(" ", "") != "", list(jieba.cut(doc['content'].lower(), cut_all=False))))
            for doc in tqdm(self.searchDataList, desc="Tokenizing corpus")
        ]

    def run(self,
            query:str = "",
            query_list: List[str] = []):
        
        if query != "" and len(query_list) == 0:
            query_list = [query]
        
        final_result = []
        for query in query_list:
            tokenized_query = list(jieba.cut(query.lower(), cut_all=False))
            scores = self.bm25.get_scores(tokenized_query)
            top_n_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:self.top_k]

            results = []
            for idx in top_n_indices:
                doc = self.searchDataList[idx]
                results.append({
                    'id': doc['id'],
                    'content': doc['content'],
                    'score': scores[idx]
                })
            final_result.append(results)

        final_result = knowledge_conflict_check(query_list=query_list,final_result=final_result,ExternalKnowledgeConflictsFlag=self.ExternalKnowledgeConflictsFlag)
        
        return {"final_result":final_result}