from typing import Any, Dict, List, Optional


from kninjllm.llm_common.errors import DeserializationError
from kninjllm.llm_common.document import Document
from kninjllm.llm_common.component import component
from kninjllm.llm_common.serialization import default_from_dict, default_to_dict
from kninjllm.llm_store.in_memory_store import InMemoryDocumentStore
from kninjllm.llm_utils.common_utils import knowledge_conflict_check

@component
class InMemoryEmbeddingRetriever:
    def __init__(
        self,
        document_store: InMemoryDocumentStore,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 10,
        scale_score: bool = False,
        return_embedding: bool = False,
    ):
        """
        Create the InMemoryEmbeddingRetriever component.

        :param document_store:
            An instance of InMemoryDocumentStore.
        :param filters:
            A dictionary with filters to narrow down the search space.
        :param top_k:
            The maximum number of documents to retrieve.
        :param scale_score:
            Scales the BM25 score to a unit interval in the range of 0 to 1, where 1 means extremely relevant. If set to `False`, uses raw similarity scores.
        :param return_embedding:
            Whether to return the embedding of the retrieved Documents.

        :raises ValueError:
            If the specified top_k is not > 0.
        """
        if not isinstance(document_store, InMemoryDocumentStore):
            raise ValueError("document_store must be an instance of InMemoryDocumentStore")

        self.document_store = document_store

        if top_k <= 0:
            raise ValueError(f"top_k must be greater than 0. Currently, top_k is {top_k}")

        self.filters = filters
        self.top_k = top_k
        self.scale_score = scale_score
        self.return_embedding = return_embedding

    def _get_telemetry_data(self) -> Dict[str, Any]:
        """
        Data that is sent to Posthog for usage analytics.
        """
        return {"document_store": type(self.document_store).__name__}

    def to_dict(self) -> Dict[str, Any]:
        """
        Serializes the component to a dictionary.

        :returns:
            Dictionary with serialized data.
        """
        docstore = self.document_store.to_dict()
        return default_to_dict(
            self,
            document_store=docstore,
            filters=self.filters,
            top_k=self.top_k,
            scale_score=self.scale_score,
            return_embedding=self.return_embedding,
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InMemoryEmbeddingRetriever":
        """
        Deserializes the component from a dictionary.

        :param data:
            The dictionary to deserialize from.
        :returns:
            The deserialized component.
        """
        init_params = data.get("init_parameters", {})
        if "document_store" not in init_params:
            raise DeserializationError("Missing 'document_store' in serialization data")
        if "type" not in init_params["document_store"]:
            raise DeserializationError("Missing 'type' in document store's serialization data")
        data["init_parameters"]["document_store"] = InMemoryDocumentStore.from_dict(
            data["init_parameters"]["document_store"]
        )
        return default_from_dict(cls, data)

    @component.output_types(documents=List[Document])
    def run(
        self,
        query_embedding: List[float],
        filters: Optional[Dict[str, Any]] = None,
        top_k: Optional[int] = None,
        scale_score: Optional[bool] = None,
        return_embedding: Optional[bool] = None,
    ):
        """
        Run the InMemoryEmbeddingRetriever on the given input data.

        :param query_embedding:
            Embedding of the query.
        :param filters:
            A dictionary with filters to narrow down the search space.
        :param top_k:
            The maximum number of documents to return.
        :param scale_score:
            Scales the similarity score to a unit interval in the range of 0 to 1, where 1 means extremely relevant. If set to `False`, uses raw similarity scores.
            If not specified, the value provided at initialization is used.
        :param return_embedding:
            Whether to return the embedding of the retrieved Documents.
        :returns:
            The retrieved documents.

        :raises ValueError:
            If the specified DocumentStore is not found or is not an InMemoryDocumentStore instance.
        """
        if filters is None:
            filters = self.filters
        if top_k is None:
            top_k = self.top_k
        if scale_score is None:
            scale_score = self.scale_score
        if return_embedding is None:
            return_embedding = self.return_embedding

        docs = self.document_store.embedding_retrieval(
            query_embedding=query_embedding,
            filters=filters,
            top_k=top_k,
            scale_score=scale_score,
            return_embedding=return_embedding,
        )

        return {"documents": docs}
