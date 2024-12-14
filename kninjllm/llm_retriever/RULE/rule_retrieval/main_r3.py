from argparse import ArgumentParser
import os
import random
import json

from vllm import LLM,SamplingParams
from transformers import AutoTokenizer
import torch

from kninjllm.llm_retriever.RULE.rule_retrieval.vllm_inference import inference
from kninjllm.llm_retriever.RULE.rule_retrieval.index import BM25Searcher, DenseSearcher

random.seed(42)

class R3:
    def __init__(self,
                model_name=None, 
                max_new_tokens=1024, 
                max_doc_len=100,
                max_length=None,
                ):
        self.name = model_name + "vllm_rerank_llm"
        self.model_name = model_name
        self.quantization = None
        self.max_length = max_length
        self.max_doc_len = max_doc_len
        self.max_new_tokens = max_new_tokens
        self.num = 20


        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.tokenizer.pad_token = self.tokenizer.bos_token

        self.model = LLM(model=self.model_name, tensor_parallel_size=torch.cuda.device_count())
        self.sampling_params =  SamplingParams(n=1, temperature=0, max_tokens=512)
        
    def get_prompt(self, query, docs):
        num = len(docs)
        self.num = num
        msg = [
            {'role': 'system',
             'content': "You are RankLLM, an intelligent assistant that can rank rules based on their relevancy to the query. If a rule can be applied to or help solve a query, that rule is more relevant."},
        ]
        
        prompt = f"I will provide you with {num} rules, each indicated by a numerical identifier []. Rank the rules based on their relevance to the query: {query}.\n\n"
        rank = 0
        for doc in docs:
            rank += 1
            prompt += f"[{rank}] {doc}\n"
        prompt += f"Query: {query}.\nRank the {num} rules above based on their relevance to the query. All the rules should be included and listed using identifiers, in descending order of relevance. The output format should be [] > [], e.g., [2] > [1], Only respond with the ranking results, do not say any word or explain."
            
        msg.append({'role': 'user', 'content': prompt})

        return msg
        
    def __call__(self, query_list, doc_list):
        msgs = [self.get_prompt(q, d) for q, d in zip(query_list, doc_list)]
        prompts = [self.tokenizer.apply_chat_template(m, tokenize=False, add_generation_prompt=True) for m in msgs]
        outputs = self.model.generate(prompts, self.sampling_params)
        rankings = [self.post_process(output.outputs[0].text) for output in outputs]
        return rankings
        
    def post_process(self, res):
        res = res.split('####')[-1]
        
        def clean_response(response: str):
            new_response = ''
            for c in response:
                if not c.isdigit():
                    new_response += ' '
                else:
                    try:
                        d = int(c)
                        new_response += c
                    except:
                        new_response += ' '
                        continue
                    
            new_response = new_response.strip()
            return new_response

        def remove_duplicate(response):
            new_response = []
            for c in response:
                if c not in new_response:
                    new_response.append(c)
            return new_response
        
        ranking = clean_response(res)
        ranking = [int(x) - 1 for x in ranking.split()]
        ranking = remove_duplicate(ranking)
        doc_set = set(list(range(self.num)))
        ranking = [x for x in ranking if x in doc_set]
        diff = set(doc_set) - set(ranking)
        ranking = ranking + sorted(list(diff))
        
        return ranking
    

        
def main_r3(llm_path, data_path, rule_dir):
    r3_model = R3(model_name=llm_path)
    data = json.load(open(data_path, 'r', encoding='utf-8'))
    rules = json.load(open(f"{rule_dir}/test_rule.json", 'r', encoding='utf-8'))
    rules = {r["id"]: r["content"] for r in rules}
    query_list = [d['input'] for d in data]
    rule_ids_list = [d['retrieved_rules'] for d in data]
    rule_list = [[rules[str(r)] for r in rule_ids] for rule_ids in rule_ids_list]
    rankings = r3_model(query_list, rule_list)
    rule_ids = [[rule_ids[min(r, len(rule_ids) - 1)] for r in ranking] for ranking, rule_ids in zip(rankings, rule_ids_list)]

    for d, rule_id in zip(data, rule_ids):
        d['r3_rule_ids'] = rule_id
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
        
def main_r3_gen(model_path: str, data_path: str, rule_dir: str, output_path: str):   
    with open(data_path) as f:
        data = json.load(f)  
    with open(f"{rule_dir}/test_rule.json", 'r') as f:
        rules = json.load(f)
    rules = {r["id"]: r["content"] for r in rules}
    if 'clutrr' in data_path or 'theoremQA' in data_path:
        system_prompt = "Please answer the question according to the given rule. Just output the answer and do not ouptut anything else."
    elif 'ulogic' in data_path:
        system_prompt = "Please answer the question according to the given rule. This is a True or False question, please answer the option only and do not ouptut anything else."
    elif 'law' in data_path:
        system_prompt = "请按照给定的规则回答问题。只输出答案，不输出任何其他内容。"
    input_prompt = """Question: {question}\n\nRule: {rule}\n\nAnswer:"""
    if 'law' in data_path:
        input_prompt = """问题: {question}\n\n规则: {rule}\n\n答案:"""

    prompts = []
    answers = []
    retrieved_rules = []
    recall_5 = 0
    recall_10 = 0
    recall_1 = 0
    for d in data:
        doc_ids = d['r3_rule_ids']
        rule = rules[doc_ids[0]]
        if str(d["rule"][0]) in doc_ids[:10]:
            recall_10 += 1
        if str(d["rule"][0]) in doc_ids[:5]:
            recall_5 += 1
        if str(d["rule"][0]) == doc_ids[0]:
            recall_1 += 1
        
        prompt = [{"role": "system", "content": system_prompt}]
        if 'instruction' in d and d['instruction'] != "":
            question = d['instruction'] + '\n\n' + d['input']
        else:
            question = d['input']
        prompt.append({"role": "user", "content": input_prompt.format(question=question, rule=rule)})
        prompts.append(prompt)
        if 'ulogic' in data_path:
            answers.append(str(d["positive_"]))
        else:
            answers.append(d["output"])
    recall_5 = recall_5/len(data)
    recall_10 = recall_10/len(data)
    recall_1 = recall_1/len(data)
    
    llm = LLM(model=model_path, tensor_parallel_size=torch.cuda.device_count())
    outputs = inference(tokenizer, llm, prompts)
    num_true = 0
    if 'law' in data_path:
        for output, answer in zip(outputs, answers):
            if answer.strip() in output.strip():
                num_true += 1
    else:
        for output, answer in zip(outputs, answers):
            if answer.strip().lower() in output.strip().lower():
                num_true += 1
        
    print(f"Accuracy: {num_true/len(answers)}")
    print(f"Recall@1: {recall_1}")
    print(f"Recall@5: {recall_5}")
    print(f"Recall@10: {recall_10}")
    res = f"Accuracy: {num_true/len(answers)}\nRecall@1: {recall_1}\nRecall@5: {recall_5}\nRecall@10: {recall_10}"
    with open(output_path, 'w') as f:
        f.write(res)

        
if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--model_path", type=str)
    parser.add_argument("--dataset", type=str)
    parser.add_argument("--data_path", type=str)
    parser.add_argument("--rule_path", type=str)
    parser.add_argument("--rule_dir", type=str)
    parser.add_argument("--index_dir", type=str)
    parser.add_argument("--retriever_path", type=str)
    parser.add_argument("--build_or_index", type=str)
    parser.add_argument("--sparse_or_dense", type=str)
    parser.add_argument("--rerank_or_generation", type=str)
    parser.add_argument("--output_path", type=str)
    args = parser.parse_args()
    

    tokenizer = AutoTokenizer.from_pretrained(args.model_path)
    output_dir = f"results/{args.dataset}"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    
    if args.rerank_or_generation == "rerank":
        print(f"run r3 with {args.data_path} and {args.rule_path}")
        main_r3(args.model_path, args.data_path, args.rule_dir)
        print(f"done")
    elif args.rerank_or_generation == "generation":
        print(f"run r3 with {args.data_path} and {args.rule_path}")
        main_r3_gen(args.model_path, args.data_path, args.rule_dir, args.output_path)
        print(f"done")
    
     
