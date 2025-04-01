from typing import Any, Dict, List, Optional

from tqdm import tqdm
from vllm import SamplingParams
from kninjllm.llm_utils.common_utils import RequestOutputToDict,loadModelByCatch
from root_config import RootConfig


class QWQGenerator:

    def __init__(
        self,
        model_path : str = "",
        generation_kwargs: Dict[str, Any] = {},
        knowledgeDiffFuntion:str = "",
        do_log: bool = True,
    ):
        if do_log:
            self.logSaver = RootConfig.logSaver
        else:
            self.logSaver = None
        
        self.generation_kwargs = generation_kwargs
        self.knowledgeDiffFuntion = knowledgeDiffFuntion
        self.saveFlag = False
        loadModel = loadModelByCatch(model_name='qwq',model_path=model_path)
        self.model = loadModel['model']
        self.tokenizer = loadModel['tokenizer']
        
        self.model_name = self.generation_kwargs.get("","")
        self.max_tokens = self.generation_kwargs.get("max_tokens",500)
        self.max_new_tokens = self.generation_kwargs.get("max_new_tokens",500)
        self.temperature = self.generation_kwargs.get("temperature",0)
        self.top_p = self.generation_kwargs.get("top_p",1)
        print("QWQ ... ")
    
    # vllm 优化
    def chat(self,prompt,sampling_params=None):

        messages = [{"role": "user", "content": prompt}]
        # 生成符合模型要求的对话格式
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        # 创建采样参数
        if sampling_params is None:
            sampling_params = SamplingParams(
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
            )
        else:
            # 如果传入自定义参数，转换为SamplingParams对象
            # sampling_params = SamplingParams(**sampling_params)
            sampling_params = sampling_params
        
        # 使用vLLM进行生成
        outputs = self.model.generate([text], sampling_params)
        
        # 提取并返回生成的文本
        return outputs[0].outputs[0].text

    
    def run(
        self,
        prompt: str ="",
        prompt_list: List[str] = [],
        sampling_params: Any = None
    ):
        
        if sampling_params is None:
            sampling_params = SamplingParams()
            for k in self.generation_kwargs:
                sampling_params.__setattr__(k, self.generation_kwargs[k])
        else:
            sampling_params = sampling_params
        
        if self.model==None:
            raise ValueError("The model is empty.")
        
        # print("------------------------------  baichuan2  -------------------------")
        
        if prompt != "" and len(prompt_list) == 0:
            prompt_list = [prompt]
        
        if self.logSaver is not None:
            self.logSaver.writeStrToLog("Function -> QWQGenerator -> run")
            self.logSaver.writeStrToLog("Given generator prompt_list -> : "+prompt_list)
        
        final_result = []
        
        for one_prompt in prompt_list:
            content = self.chat(prompt=one_prompt,sampling_params=sampling_params)
            final_result.append({
                "prompt":one_prompt,
                "content":content,
                "meta":{},    
            })    
            
        if self.logSaver is not None:
            self.logSaver.writeStrToLog("Returns generator reply : "+ content )
        
        return {"final_result":final_result}
    
        