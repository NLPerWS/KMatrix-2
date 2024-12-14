import json
from argparse import ArgumentParser
import os
import re
import gc
import sys
from vllm import LLM
from transformers import AutoTokenizer
import torch

from kninjllm.llm_retriever.RULE.rule_retrieval.vllm_inference import inference
from kninjllm.llm_retriever.RULE.rule_retrieval.index import DenseSearcher

def process_data_no_rule(data_path: str):
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    
    if 'clutrr' in data_path or 'theoremQA' in data_path:
        system_prompt = "Please answer the question. Just output the answer and do not ouptut anything else."
    elif 'ulogic' in data_path:
        system_prompt = "Please answer the question. This is a True or False question, please answer the option only and do not ouptut anything else."
    elif 'law' in data_path:
        system_prompt = "回答问题。只输出答案，不输出任何其他内容。"


    input_prompt = """Question: {question}\n\nAnswer:"""
    if 'law' in data_path:
        input_prompt = """问题: {question}\n\n答案:"""

    prompts = []
    answers = []

    for d in data:
        prompt = [{"role": "system", "content": system_prompt}]
        if 'instruction' in d and d['instruction'] != "":
            question = d['instruction'] + '\n\n' + d['input']
        else:
            question = d['input']
        prompt.append({"role": "user", "content": input_prompt.format(question=question)})
        prompts.append(prompt)
        if 'ulogic' in data_path:
            answers.append(str(d["positive_"]))
        else:
            answers.append(d["output"])
        
    return prompts, answers


def process_data_self_induction_rule(data_path: str):
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    
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

    for d in data:
        prompt = [{"role": "system", "content": system_prompt}]
        if 'instruction' in d and d['instruction'] != "":
            question = d['instruction'] + '\n\n' + d['input']
        else:
            question = d['input']
        prompt.append({"role": "user", "content": input_prompt.format(question=question, rule=d['self_induction'])})
        prompts.append(prompt)
        if 'ulogic' in data_path:
            answers.append(str(d["positive_"]))
        else:
            answers.append(d["output"])
        
    return prompts, answers

def process_data_golden_rule(data_path: str, rule_path: str):
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    with open(rule_path, 'r', encoding='utf-8') as f:
        rules = json.load(f)    
    
    
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

    for d in data:
        prompt = [{"role": "system", "content": system_prompt}]
        if 'instruction' in d and d['instruction'] != "":
            question = d['instruction'] + '\n\n' + d['input']
        else:
            question = d['input']
        prompt.append({"role": "user", "content": input_prompt.format(question=question, rule=rules[str(d["rule"][0])]['NL'])})
        prompts.append(prompt)
        if 'ulogic' in data_path:
            answers.append(str(d["positive_"]))
        else:
            answers.append(d["output"])
        
    return prompts, answers

def main_no_retrieval(tokenizer, llm, data_path, rule_path, output_path, setting):
    if setting == "no_rule":
        prompts, answers = process_data_no_rule(data_path)
    elif setting == "golden_rule":
        prompts, answers = process_data_golden_rule(data_path, rule_path)
    elif setting == "self-induction":
        prompts, answers = process_data_self_induction_rule(data_path)
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
    res = f"Accuracy: {num_true/len(answers)}"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(res)
        
        
def build_or_load_sparse_index(rule_path, index_dir, build_or_index):
    searcher = BM25Searcher(index_dir)

    if build_or_index == "build":

        searcher.build_index(index_dir, rule_path)
        searcher.load_index()
    else:
        searcher.load_index()
    
    return searcher

def build_or_load_dense_index(rule_path, index_dir, model_name, build_or_index):
    searcher = DenseSearcher(index_dir, model_name, rule_path)

    if build_or_index == "build":
        searcher.build_index()
        searcher.load_index()
    else:
        searcher.load_index()
    
    return searcher
        
def process_data_sparse_retrieval_rule(topk,data_path: str, rule_dir: str, index_dir: str, build_or_index: str, retrieval_query: str):   
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)  
    with open(f"{rule_dir}/test_rule.json", 'r', encoding='utf-8') as f:
        rules = json.load(f)
    rules = {r["id"]: r["content"] for r in rules}
    searcher = build_or_load_sparse_index(rule_dir, index_dir, build_or_index)
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
        if retrieval_query == "input_and_self_induction_rule":
            doc_ids, scores = searcher.search(d["input"] + ' ' + d["self_induction"], topk)
        else:
            doc_ids, scores = searcher.search(d[retrieval_query], topk)
        
        if len(doc_ids) == 0:
            import random
            doc_ids = random.sample(list(rules.keys()), topk)

        rule = rules[doc_ids[0]]
        retrieved_rules.append(doc_ids[:topk])
        if "rule" in d and len(d["rule"]) > 0:
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
    
        
    return prompts, answers, retrieved_rules, recall_5, recall_10, recall_1

def process_data_dense_retrieval_rule(topk,data_path: str, rule_dir: str, index_dir: str, model_name: str, build_or_index: str, retrieval_query: str):   
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)  
    with open(f"{rule_dir}/test_rule.json", 'r', encoding='utf-8') as f:
        rules = json.load(f)
    rules = {r["id"]: r["content"] for r in rules}
    searcher = build_or_load_dense_index(f"{rule_dir}/test_rule.json", index_dir, model_name, build_or_index)
    if 'clutrr' in data_path or 'theoremQA' in data_path:
        system_prompt = "Please answer the question according to the given rule. Just output the answer and do not ouptut anything else."
    elif 'ulogic' in data_path:
        system_prompt = "Please answer the question according to the given rule. This is a True or False question, please answer the option only and do not ouptut anything else."
    elif 'law' in data_path:
        system_prompt = "请按照给定的规则回答问题。只输出答案，不输出任何其他内容。"
    else:
        system_prompt = "请按照给定的规则回答问题。只输出答案，不输出任何其他内容。"
    
    
    input_prompt = """Question: {question}\n\nRule: {rule}\n\nAnswer:"""
    if 'law' in data_path:
        input_prompt = """问题: {question}\n\n规则: {rule}\n\n答案:"""

    retrieved_rules = []
    prompts = []
    answers = []
    recall_5 = 0
    recall_10 = 0
    recall_1 = 0
    for d in data:
        if retrieval_query == "input_and_self_induction_rule":
            doc_ids, scores = searcher.search(d["input"] + ' ' + d["self_induction"], topk)
        else:
            doc_ids, scores = searcher.search(d[retrieval_query], topk)
        
        if len(doc_ids) == 0:
            import random
            doc_ids = random.sample(list(rules.keys()), topk)

        rule = rules[doc_ids[0]]

        retrieved_rules.append(doc_ids[:topk])
        if "rule" in d and len(d["rule"]) > 0:
            if str(d["rule"][0]) in doc_ids[:10]:
                recall_10 += 1
            if str(d["rule"][0]) == doc_ids[0]:
                recall_1 += 1
            if str(d["rule"][0]) in doc_ids[:5]:
                recall_5 += 1
        
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

    # 这一步不做规则增强生成，只做规则检索，并完成生成步骤完整提示构建
        
    return prompts, answers, retrieved_rules, recall_5, recall_10, recall_1


    
def main_retrieval(topk,tokenizer, llm, data_path, rule_dir, index_dir, retriever_path, output_path, build_or_index, sparse_or_dense, retrieval_query):
    
    # 规则检索第二步
    if sparse_or_dense == "sparse":
        index_dir = index_dir + "_sparse"
        prompts, answers, retrieved_rules, recall_5, recall_10, recall_1 = process_data_sparse_retrieval_rule(topk,data_path, rule_dir, index_dir, build_or_index, retrieval_query)
    else:
        index_dir = index_dir + "_dense"
        # 这个里面返回的prompts已经自动拼接好了各种提示语（检索到的规则知识+prompt+query）
        prompts, answers, retrieved_rules, recall_5, recall_10, recall_1 = process_data_dense_retrieval_rule(topk,data_path, rule_dir, index_dir, retriever_path, build_or_index, retrieval_query)
    
    outputs=""
    # 从这个地方开始，利用检索到的规则知识+prompt+query 进行生成
    
    # outputs = inference(tokenizer, llm, prompts)
    # del llm
    # gc.collect()
    # torch.cuda.empty_cache()
    # torch.distributed.destroy_process_group()

    # num_true = 0

    # if 'law' in data_path:
    #     for output, answer in zip(outputs, answers):
    #         if answer.strip() in output.strip():
    #             num_true += 1
    # else:
    #     for output, answer in zip(outputs, answers):
    #         if answer.strip().lower() in output.strip().lower():
    #             num_true += 1
            
            
    # print(f"Accuracy: {num_true/len(answers)}")

     # 这个地方结束，利用检索到的规则知识+prompt+query 进行生成


    # num_true=0
    # answers=12
    # print(f"Recall@1: {recall_1}")
    # print(f"Recall@5: {recall_5}")
    # print(f"Recall@10: {recall_10}") 
    # res = f"Accuracy: {num_true/len(answers)}\nRecall@1: {recall_1}\nRecall@5: {recall_5}\nRecall@10: {recall_10}"
    # with open(output_path, 'w', encoding='utf-8') as f:
        # f.write(res)
    
    # print("predict answer list:",outputs)
        
    return retrieved_rules,outputs
        
        
def do_main(args):
    
    print(torch.cuda.device_count())

    llm = args.model
    tokenizer = args.tokenizer
    
    output_dir = f"results/{args.dataset}"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    if args.setting == 'no_retrieval':
        llm = LLM(model=args.model_path, tensor_parallel_size=torch.cuda.device_count())
        print("No retrieval")
        print(f"run no_rule with {args.data_path} and {args.model_path}")
        output_path = f"{output_dir}/{args.model_path.split('/')[-1]}_no_rule.txt"
        main_no_retrieval(tokenizer, llm, args.data_path, args.rule_path, output_path, "no_rule")
        print(f"done") 
        print(f"run golden_rule with {args.data_path} and {args.rule_path}")
        output_path = f"{output_dir}/{args.model_path.split('/')[-1]}_golden_rule.txt"
        main_no_retrieval(tokenizer, llm, args.data_path, args.rule_path, output_path, "golden_rule")
        print(f"done")
        print(f"run self-induction with {args.data_path} and {args.rule_path}")
        output_path = f"{output_dir}/{args.model_path.split('/')[-1]}_self_induction.txt"
        main_no_retrieval(tokenizer, llm, args.data_path, args.rule_path, output_path, "self-induction")
        print(f"done")
    elif args.setting == "retrieval":
        print("With retrieval")
        
        # print(f"run sparse retrieval_input with {args.data_path} and {args.rule_path}")
        # output_path = f"{output_dir}/{args.model_path.split('/')[-1]}_sparse_input.txt"
        # retrieved_rules = main_retrieval(tokenizer, args.model_path, args.data_path, args.rule_dir, args.index_dir, args.retriever_path, output_path, "build", "sparse", "input")
        # print(f"done")

        
        # print(f"run sparse retrieval_self_induction_rule with {args.data_path} and {args.rule_path}")
        # output_path = f"{output_dir}/{args.model_path.split('/')[-1]}_sparse_self_induction_rule.txt"
        # retrieved_rules = main_retrieval(tokenizer, args.model_path, args.data_path, args.rule_dir, args.index_dir, args.retriever_path, output_path, "load", "sparse", "self_induction")
        # print(f"done")
        # data = json.load(open(args.data_path, 'r', encoding='utf-8'))
        # for d, r in zip(data, retrieved_rules):
        #     d['retrieved_rules'] = r
        # output_retrieved_rules_path = f"dataset/{args.dataset}/test_data_with_sparse_self_induction_retrieved_rules.json"
        # with open(output_retrieved_rules_path, 'w', encoding='utf-8') as f:
        #     json.dump(data, f, indent=2, ensure_ascii=False)



        # print(f"run sparse retrieval_input_and_self_induction_rule with {args.data_path} and {args.rule_path}")
        # output_path = f"{output_dir}/{args.model_path.split('/')[-1]}_sparse_input_and_self_induction_rule.txt"
        # retrieved_rules = main_retrieval(tokenizer, args.model_path, args.data_path, args.rule_dir, args.index_dir, args.retriever_path, output_path, "load", "sparse", "input_and_self_induction_rule")
        # print(f"done")
        # data = json.load(open(args.data_path, 'r', encoding='utf-8'))
        # for d, r in zip(data, retrieved_rules):
        #     d['retrieved_rules'] = r
        # output_retrieved_rules_path = f"dataset/{args.dataset}/test_data_with_sparse_input_and_self_induction_retrieved_rules.json"
        # with open(output_retrieved_rules_path, 'w', encoding='utf-8') as f:
        #     json.dump(data, f, indent=2, ensure_ascii=False)


        # print(f"run dense retrieval_input with {args.data_path} and {args.rule_path}")
        # output_path = f"{output_dir}/{args.model_path.split('/')[-1]}_dense_input.txt"
        # retrieved_rules = main_retrieval(tokenizer, args.model_path, args.data_path, args.rule_dir, args.index_dir, args.retriever_path, output_path, "build", "dense", "input")
        # print(f"done")

        # print(f"run dense retrieval_self_induction_rule with {args.data_path} and {args.rule_path}")
        # output_path = f"{output_dir}/{args.model_path.split('/')[-1]}_dense_self_induction_rule.txt"
        # retrieved_rules = main_retrieval(tokenizer, args.model_path, args.data_path, args.rule_dir, args.index_dir, args.retriever_path, output_path, "load", "dense", "self_induction")
        # print(f"done")
        # data = json.load(open(args.data_path, 'r', encoding='utf-8'))
        # for d, r in zip(data, retrieved_rules):
        #     d['retrieved_rules'] = r
        # output_retrieved_rules_path = f"dataset/{args.dataset}/test_data_with_dense_self_induction_retrieved_rules.json"
        # with open(output_retrieved_rules_path, 'w', encoding='utf-8') as f:
        #     json.dump(data, f, indent=2, ensure_ascii=False)
        
        # print(f"run dense retrieval_input_and_self_induction_rule with {args.data_path} and {args.rule_path}")
        # output_path = f"{output_dir}/{args.model_path.split('/')[-1]}_dense_input_and_self_induction_rule.txt"
        output_path = ""

        # 规则检索第二步+规则增强生成
        retrieved_rules,outputs = main_retrieval(args.topk,tokenizer, llm, args.data_path, args.rule_dir, args.index_dir, args.retriever_path, output_path, "build", "dense", "input_and_self_induction_rule")
        
        print(f"done")
        
        # data = json.load(open(args.data_path, 'r', encoding='utf-8'))
        # for d, r in zip(data, retrieved_rules):
            # d['retrieved_rules'] = r
        # output_retrieved_rules_path = f"dataset/{args.dataset}/test_data_with_dense_input_and_self_induction_retrieved_rules.json"
        # with open(output_retrieved_rules_path, 'w', encoding='utf-8') as f:
            # json.dump(data, f, indent=2, ensure_ascii=False)
        
        return retrieved_rules,outputs

if __name__ == "__main__":
    # parser = ArgumentParser()
    # parser.add_argument("--setting", type=str, choices=['no_retrieval', 'retrieval'])
    # parser.add_argument("--model_path", type=str)
    # parser.add_argument("--dataset", type=str)
    # parser.add_argument("--data_path", type=str)
    # parser.add_argument("--rule_path", type=str)
    # parser.add_argument("--rule_dir", type=str)
    # parser.add_argument("--index_dir", type=str)
    # parser.add_argument("--retriever_path", type=str)
    # parser.add_argument("--build_or_index", type=str)
    # parser.add_argument("--sparse_or_dense", type=str)
    # args = parser.parse_args()
    
    # do_main(args)
    
    pass