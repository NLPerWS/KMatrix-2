from torch import Tensor
import torch
import torch.nn.functional as F
import os, tqdm
import json, time
import numpy as np
import argparse
from transformers import AutoModel, AutoTokenizer, T5EncoderModel, T5Config, AutoConfig
from transformers.modeling_outputs import BaseModelOutput
from typing import List
from kninjllm.llm_retriever.BERT.utils_test import logger, pool, move_to_cuda, create_batch_dict


class DenseEncoder(torch.nn.Module):
    def __init__(self, args):
        super().__init__()
        kwargs = {
            "pretrained_model_name_or_path": args.model_path,
        }
        if args.llm:
            kwargs['attn_implementation'] = 'flash_attention_2'
            kwargs['use_cache'] = False
            kwargs['trust_remote_code'] = False

        if args.dtype == 'bf16':
            kwargs['torch_dtype'] = torch.bfloat16
        elif args.dtype == 'fp16':
            kwargs['torch_dtype'] = torch.float16
        
        print(f"Model kwargs: {kwargs}")
        if not args.T5:
            self.encoder = AutoModel.from_pretrained(**kwargs)
        else:
            print(f"Only use encoder for T5 Model")
            self.encoder = T5EncoderModel.from_pretrained(**kwargs)
        self.tokenizer = AutoTokenizer.from_pretrained(args.model_path)
        
        if args.sentence_pooling_method == 'eos':
            self.pool_type = 'eos'
            self.tokenizer.pad_token = self.tokenizer.eos_token
            self.tokenizer.padding_side = "left"
        elif args.sentence_pooling_method == 'cls':
            self.pool_type = 'cls'
        elif args.sentence_pooling_method == 'mean':
            self.pool_type = 'mean'

        self.normalize = False
        self.prompt = ''
            
        self.max_query_length = args.max_query_length
        self.max_passage_length = args.max_passage_length
        
        self.gpu_count = torch.cuda.device_count()
        
        self.encoder.eval()
        if self.gpu_count > 1:
            self.encoder = torch.nn.DataParallel(self.encoder)
        self.device = torch.device("cuda")
        self.encoder.cuda()
        self.print_flag = 0

    
    def encode_queries(self, queries, batch_size=32,**kwargs) -> np.ndarray:
        """Used for encoding the queries of retrieval or reranking tasks"""
        
        input_texts = [self.prompt + q for q in queries]

        return self.encode(queries, batch_size, max_length=self.max_query_length)

    def encode_corpus(self, corpus, batch_size=32,**kwargs) -> np.ndarray:
        """Used for encoding the corpus of retrieval tasks"""
        if type(corpus) is dict:
            sentences = [
                (corpus["title"][i] + " " + corpus["text"][i]).strip()
                if "title" in corpus
                else corpus["text"][i].strip()
                for i in range(len(corpus["text"]))
            ]
        else:
            if type(corpus[0]) is str:
                sentences = corpus
            elif type(corpus[0]) is dict:
                sentences = [
                    (doc["title"] + " " + doc["text"]).strip() if "title" in doc else doc["text"].strip()
                    for doc in corpus
                ]
            
        return self.encode(sentences, batch_size, max_length=self.max_passage_length)
    
    @torch.no_grad()
    def encode(self, sentences, batch_size=32, **kwargs) -> np.ndarray:
        """ Returns a list of embeddings for the given sentences.
        Args:
            sentences (`List[str]`): List of sentences to encode
            batch_size (`int`): Batch size for the encoding

        Returns:
            `List[np.ndarray]` or `List[tensor]`: List of embeddings for the given sentences
        """
        
        if 'max_length' in kwargs:
            input_texts: List[str] = sentences
            max_length = kwargs['max_length']   
        
        else:
            input_texts: List[str] = [self.prompt + sen for sen in sentences]
            max_length = self.max_query_length
        
        encoded_embeds = []
        batch_size = int(batch_size) * self.gpu_count
        for start_idx in tqdm.tqdm(range(0, len(input_texts), batch_size), desc='encoding', mininterval=10):
            batch_input_texts: List[str] = input_texts[start_idx: start_idx + batch_size]
            
            batch_dict = create_batch_dict(self.tokenizer, batch_input_texts, pool_type=self.pool_type, max_length=max_length)
            
            batch_dict = move_to_cuda(batch_dict)
            with torch.cuda.amp.autocast():
                outputs: BaseModelOutput = self.encoder(**batch_dict)
                embeds = pool(outputs.last_hidden_state, batch_dict['attention_mask'], self.pool_type)
                
                if self.normalize:
                    embeds = F.normalize(embeds, p=2, dim=-1)
                encoded_embeds.append(embeds.cpu().numpy())

        return np.concatenate(encoded_embeds, axis=0)

def get_model(args):
    return DenseEncoder(args)

