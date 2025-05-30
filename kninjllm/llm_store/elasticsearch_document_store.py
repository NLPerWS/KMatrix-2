# SPDX-FileCopyrightText: 2023-present deepset GmbH <info@deepset.ai>
#
# SPDX-License-Identifier: Apache-2.0
import logging
from typing import Any, Dict, List, Literal, Mapping, Optional, Union
import numpy as np

# There are no import stubs for elastic_transport and elasticsearch so mypy fails
from elastic_transport import NodeConfig  # type: ignore[import-not-found]
from kninjllm.llm_common.serialization import default_from_dict, default_to_dict
from kninjllm.llm_common.document import Document
from kninjllm.llm_common.errors import DocumentStoreError, DuplicateDocumentError
from kninjllm.llm_common.types import DuplicatePolicy
from kninjllm.llm_store.utils.filter_utils_conver import convert
from kninjllm.llm_common.version import __version__ as kninjllm_version

from elasticsearch import Elasticsearch, helpers  # type: ignore[import-not-found]

from kninjllm.llm_store.utils.filter_utils_calculate import _normalize_filters

logger = logging.getLogger(__name__)

Hosts = Union[str, List[Union[str, Mapping[str, Union[str, int]], NodeConfig]]]

# document scores are essentially unbounded and will be scaled to values between 0 and 1 if scale_score is set to
# True. Scaling uses the expit function (inverse of the logit function) after applying a scaling factor
# (e.g., BM25_SCALING_FACTOR for the bm25_retrieval method).
# Larger scaling factor decreases scaled scores. For example, an input of 10 is scaled to 0.99 with
# BM25_SCALING_FACTOR=2 but to 0.78 with BM25_SCALING_FACTOR=8 (default). The defaults were chosen empirically.
# Increase the default if most unscaled scores are larger than expected (>30) and otherwise would incorrectly
# all be mapped to scores ~1.
BM25_SCALING_FACTOR = 8


class ElasticsearchDocumentStore:

    def __init__(
        self,
        *,
        hosts: Optional[Hosts] = None,
        index: str = "default",
        embedding_similarity_function: Literal["cosine", "dot_product", "l2_norm", "max_inner_product"] = "cosine",
        **kwargs,
    ):
        """
        Creates a new ElasticsearchDocumentStore instance.
        When no index is explicitly specified, it will use the default index "default".
        It will also try to create that index if it doesn't exist yet. Otherwise it will use the existing one.

        One can also set the similarity function used to compare Documents embeddings. This is mostly useful
        when using the `ElasticsearchDocumentStore` in a Pipeline with an `ElasticsearchEmbeddingRetriever`.

        For more information on connection parameters, see the official Elasticsearch documentation:
        https://www.elastic.co/guide/en/elasticsearch/client/python-api/current/connecting.html

        For the full list of supported kwargs, see the official Elasticsearch reference:
        https://elasticsearch-py.readthedocs.io/en/stable/api.html#module-elasticsearch

        :param hosts: List of hosts running the Elasticsearch client. Defaults to None
        :param index: Name of index in Elasticsearch, if it doesn't exist it will be created. Defaults to "default"
        :param embedding_similarity_function: The similarity function used to compare Documents embeddings.
            Defaults to "cosine". This parameter only takes effect if the index does not yet exist and is created.
            To choose the most appropriate function, look for information about your embedding model.
            To understand how document scores are computed, see the Elasticsearch documentation:
            https://www.elastic.co/guide/en/elasticsearch/reference/current/dense-vector.html#dense-vector-params
        :param **kwargs: Optional arguments that ``Elasticsearch`` takes.
        """
        self._hosts = hosts
        self._client = Elasticsearch(
            hosts,
            headers={"user-agent": f"kninjllm-py-ds/{kninjllm_version}"},
            **kwargs,
        )
        self._index = index
        self._embedding_similarity_function = embedding_similarity_function
        self._kwargs = kwargs

        # Check client connection, this will raise if not connected
        self._client.info()

        # configure mapping for the embedding field
        mappings = {
            "properties": {
                "embedding": {"type": "dense_vector", "index": True, "similarity": embedding_similarity_function}
            }
        }

        # Create the index if it doesn't exist
        if not self._client.indices.exists(index=index):
            self._client.indices.create(index=index, mappings=mappings)

    def to_dict(self) -> Dict[str, Any]:
        # This is not the best solution to serialise this class but is the fastest to implement.
        # Not all kwargs types can be serialised to text so this can fail. We must serialise each
        # type explicitly to handle this properly.
        return default_to_dict(
            self,
            hosts=self._hosts,
            index=self._index,
            embedding_similarity_function=self._embedding_similarity_function,
            **self._kwargs,
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ElasticsearchDocumentStore":
        return default_from_dict(cls, data)

    def count_documents(self) -> int:
        """
        Returns how many documents are present in the document store.
        """
        return self._client.count(index=self._index)["count"]

    # filter get data
    def _search_documents(self, **kwargs) -> List[Document]:
        """
        Calls the Elasticsearch client's search method and handles pagination.
        """

        top_k = kwargs.get("size")
        if top_k is None and "knn" in kwargs and "k" in kwargs["knn"]:
            top_k = kwargs["knn"]["k"]

        documents: List[Document] = []
        from_ = 0
        # Handle pagination
        while True:
            res = self._client.search(
                index=self._index,
                from_=from_,
                **kwargs,
            )

            documents.extend(self._deserialize_document(hit) for hit in res["hits"]["hits"])
            from_ = len(documents)

            if top_k is not None and from_ >= top_k:
                break
            if from_ >= res["hits"]["total"]["value"]:
                break
        return documents

    def _search_all_documents(self) -> List[Document]:
        documents: List[Document] = []
        
        scroll = '5m'  
        query = {"query": {"match_all": {}}}  

        response = self._client.search(
            index=self._index,
            scroll=scroll,
            size=10000,  
            body=query
        )

        while True:
            if len(response['hits']['hits']) == 0:
                break

            documents.extend(self._deserialize_document(hit) for hit in response["hits"]["hits"])

            response = self._client.scroll(scroll_id=response['_scroll_id'], scroll=scroll)

        return documents
    
    def _search_all_documents_to_dict(self) -> List[Document]:
        documents_dict = []
        
        scroll = '5m'  
        query = {"query": {"match_all": {}}}  

        response = self._client.search(
            index=self._index,
            scroll=scroll,
            size=10000,  
            body=query
        )

        while True:
            if len(response['hits']['hits']) == 0:
                break

            documents_dict.extend(hit['_source'] for hit in response["hits"]["hits"])

            response = self._client.scroll(scroll_id=response['_scroll_id'], scroll=scroll)

        return documents_dict
    
    
    def filter_documents(self, filters: Optional[Dict[str, Any]] = None) -> List[Document]:
        if filters and "operator" not in filters and "conditions" not in filters:
            filters = convert(filters)

        query = {"bool": {"filter": _normalize_filters(filters)}} if filters else None
        documents = self._search_documents(query=query)
        return documents

    def write_documents(self, documents: List[Document], policy: DuplicatePolicy = DuplicatePolicy.NONE) -> int:
        """
        Writes Documents to Elasticsearch.
        If policy is not specified or set to DuplicatePolicy.NONE, it will raise an exception if a document with the
        same ID already exists in the document store.
        """
        if len(documents) > 0:
            if not isinstance(documents[0], Document):
                msg = "param 'documents' must contain a list of objects of type Document"
                raise ValueError(msg)

        if policy == DuplicatePolicy.NONE:
            policy = DuplicatePolicy.FAIL

        action = "index" if policy == DuplicatePolicy.OVERWRITE else "create"
        documents_written, errors = helpers.bulk(
            client=self._client,
            actions=(
                {
                    "_op_type": action,
                    "_id": doc.id,
                    "_source": doc.to_dict(),
                }
                for doc in documents
            ),
            refresh="wait_for",
            index=self._index,
            raise_on_error=False,
        )

        if errors:
            duplicate_errors_ids = []
            other_errors = []
            for e in errors:
                error_type = e["create"]["error"]["type"]
                if policy == DuplicatePolicy.FAIL and error_type == "version_conflict_engine_exception":
                    duplicate_errors_ids.append(e["create"]["_id"])
                elif policy == DuplicatePolicy.SKIP and error_type == "version_conflict_engine_exception":
                    # when the policy is skip, duplication errors are OK and we should not raise an exception
                    continue
                else:
                    other_errors.append(e)

            if len(duplicate_errors_ids) > 0:
                msg = f"IDs '{', '.join(duplicate_errors_ids)}' already exist in the document store."
                raise DuplicateDocumentError(msg)

            if len(other_errors) > 0:
                msg = f"Failed to write documents to Elasticsearch. Errors:\n{other_errors}"
                raise DocumentStoreError(msg)

        return documents_written

    def _deserialize_document(self, hit: Dict[str, Any]) -> Document:
        """
        Creates a Document from the search hit provided.
        This is mostly useful in self.filter_documents().
        """
        data = hit["_source"]

        if "highlight" in hit:
            data["metadata"]["highlighted"] = hit["highlight"]
        data["score"] = hit["_score"]

        return Document.from_dict(data)

    def delete_documents(self, document_ids: List[str]) -> None:
        """
        Deletes all documents with a matching document_ids from the document store.

        :param object_ids: the object_ids to delete
        """

        #
        helpers.bulk(
            client=self._client,
            actions=({"_op_type": "delete", "_id": id_} for id_ in document_ids),
            refresh="wait_for",
            index=self._index,
            raise_on_error=False,
        )

    def _bm25_retrieval(
        self,
        query: str,
        *,
        filters: Optional[Dict[str, Any]] = None,
        fuzziness: str = "AUTO",
        top_k: int = 10,
        scale_score: bool = False,
    ) -> List[Document]:

        if not query:
            return []

        body: Dict[str, Any] = {
            "size": top_k,
            "query": {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": query,
                                "fuzziness": fuzziness,
                                "type": "most_fields",
                                "operator": "OR",
                            }
                        }
                    ]
                }
            },
        }

        if filters:
            body["query"]["bool"]["filter"] = _normalize_filters(filters)

        documents = self._search_documents(**body)

        if scale_score:
            for doc in documents:
                doc.score = float(1 / (1 + np.exp(-np.asarray(doc.score / BM25_SCALING_FACTOR))))

        return documents

    def _embedding_retrieval(
        self,
        query_embedding: List[float],
        *,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 10,
        num_candidates: Optional[int] = None,
        field:str = "field"
    ) -> List[Document]:
        """
        Retrieves documents that are most similar to the query embedding using a vector similarity metric.
        It uses the Elasticsearch's Approximate k-Nearest Neighbors search algorithm.

        This method is not mean to be part of the public interface of
        `ElasticsearchDocumentStore` nor called directly.
        `ElasticsearchEmbeddingRetriever` uses this method directly and is the public interface for it.

        :param query_embedding: Embedding of the query.
        :param filters: Filters applied to the retrieved Documents. Defaults to None.
            Filters are applied during the approximate kNN search to ensure that top_k matching documents are returned.
        :param top_k: Maximum number of Documents to return, defaults to 10
        :param num_candidates: Number of approximate nearest neighbor candidates on each shard. Defaults to top_k * 10.
            Increasing this value will improve search accuracy at the cost of slower search speeds.
            You can read more about it in the Elasticsearch documentation:
            https://www.elastic.co/guide/en/elasticsearch/reference/current/knn-search.html#tune-approximate-knn-for-speed-accuracy
        :raises ValueError: If `query_embedding` is an empty list
        :return: List of Document that are most similar to `query_embedding`
        """

        if not query_embedding:
            msg = "query_embedding must be a non-empty list of floats"
            raise ValueError(msg)

        if not num_candidates:
            num_candidates = top_k * 10

        body: Dict[str, Any] = {
            "knn": {
                "field": field,
                "query_vector": query_embedding,
                "k": top_k,
                "num_candidates": num_candidates,
            },
        }

        if filters:
            body["knn"]["filter"] = _normalize_filters(filters)

        docs = self._search_documents(**body)
        return docs
