from vllm import  SamplingParams

from typing import List

def process_data(data, tokenizer):
    data = [tokenizer.apply_chat_template(d, tokenize=False, add_generation_prompt=True) for d in data]
    return data
    


def inference(tokenizer, llm, prompts) -> List[str]:
    sampling_params = SamplingParams(n=1, temperature=0, max_tokens=256)
    prompts = process_data(prompts, tokenizer)
    outputs = llm.generate(prompts, sampling_params)
    outputs = [output.outputs[0].text for output in outputs]
    return outputs

def inference_n(tokenizer, llm, n, prompts) -> List[str]:
    sampling_params = SamplingParams(n=n, temperature=0.7, max_tokens=256)
    prompts = process_data(prompts, tokenizer)
    outputs = llm.generate(prompts, sampling_params)
    outputs = [[output.outputs[i].text for i in range(n)] for output in outputs]
    return outputs