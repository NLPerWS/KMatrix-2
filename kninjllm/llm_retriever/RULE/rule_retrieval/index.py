
from typing import List
import json

from transformers import AutoTokenizer, AutoModel
import torch
from torch.utils.data import Dataset, DataLoader    
from kninjllm.llm_utils.common_utils import loadModelByCatch

# class BM25Searcher:
#     def __init__(self, index_dir: str):
#         if not os.path.exists(index_dir):
#             os.makedirs(index_dir)
#         self.index_dir = index_dir
#         self.searcher = None
    
#     def build_index(self, out_folder, json_folder, num_threads=10):
#         command = [
#             'python3', '-m', 'pyserini.index.lucene',
#             '--collection', 'JsonCollection',
#             '--input', json_folder,
#             '--index', out_folder,
#             '--generator', 'DefaultLuceneDocumentGenerator',
#             '--threads', str(num_threads)
#             # '--storePositions', '--storeDocvectors', '--storeRaw'
#         ]
#         try:
#             subprocess.run(command, check=True)
#         except subprocess.CalledProcessError as e:
#             print(f"Error: {e}")
    
#     def load_index(self):
#         self.searcher = LuceneSearcher(self.index_dir)
        
#     def search(self, query: str, k: int):
#         hits = self.searcher.search(query, k)
#         doc_ids = [hit.docid for hit in hits]
#         scores = [hit.score for hit in hits]
#         return doc_ids, scores
    
class CosineSim:

    @staticmethod
    def sim(query_embds, doc_embds):
        query_embds = query_embds / (torch.norm(query_embds, dim=-1, keepdim=True) + 1e-9)
        doc_embds = doc_embds / (torch.norm(doc_embds, dim=-1, keepdim=True) + 1e-9)
        return torch.mm(query_embds, doc_embds.t())
    
class ClsPooler:

    @staticmethod
    def pool(outputs, *args):
        return outputs[:,0]
    
    
class DenseSearcher:
    def __init__(self, index_dir, model_name, doc_path, max_len=512):
        self.max_len = max_len
        self.model_name = model_name
        
        print("------------self.model_name-------------\n",self.model_name)
        # self.model = AutoModel.from_pretrained(self.model_name, torch_dtype=torch.float16, trust_remote_code=True)
        self.model = loadModelByCatch(model_name=self.model_name,model_path=self.model_name)
        
        self.index_dir = index_dir   
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = self.model.to(self.device)
        self.model.eval()
        self.similarity = CosineSim()
        self.pooler = ClsPooler()
        self.embeddings = None
        data = json.load(open(doc_path, 'r'))
        self.data = data


    def build_index(self):
        docs = [d['content'] for d in self.data]
        dataloader = DataLoader(docs, batch_size=64, collate_fn=self.collate_fn)
        embeddings = []
        print(f"build index ...")
        for batch in dataloader:
            with torch.no_grad():
                batch = {k: v.to(self.device) for k, v in batch.items()}
                outputs = self.model(**batch)
                emb = self.pooler.pool(outputs[0], batch['attention_mask'])
                embeddings.append(emb)
        print(f"index built ~")
        embeddings = torch.cat(embeddings, dim=0)
        torch.save(embeddings, self.index_dir)
        self.embeddings = embeddings    
        
    def load_index(self):
        self.embeddings = torch.load(self.index_dir)
        

    def search(self, query, k):
        query_dict = self.tokenizer(query, padding="longest", truncation="longest_first", max_length=self.max_len, return_tensors='pt')
        query_dict = {k: v.to(self.device) for k, v in query_dict.items()}
        query_embds = self.model(**query_dict)[0]
        query_embds = self.pooler.pool(query_embds, query_dict['attention_mask'])
        sim = self.similarity_fn(query_embds, self.embeddings)
        scores, doc_ids = torch.topk(sim[0], k)
        doc_ids = doc_ids.cpu().numpy().tolist()
        doc_ids = [self.data[i]['id'] for i in doc_ids]
        return doc_ids, scores
        

    def collate_fn(self, docs):
        # content is a list of strings
        content = docs
        return_dict = self.tokenizer(content, padding="longest", truncation="longest_first", max_length=self.max_len, return_tensors='pt')
        return return_dict
    

    def similarity_fn(self, query_embds, doc_embds):
        return self.similarity.sim(query_embds, doc_embds)