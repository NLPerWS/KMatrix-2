import shutil
import json
import os
from typing import Any, Dict, List, Optional
from vllm import SamplingParams
from root_config import RootConfig
from kninjllm.llm_utils.common_utils import RequestOutputToDict,loadModelByCatch


class RagGenerator:

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
            
        loadModel = loadModelByCatch(model_name='selfrag',model_path=model_path)
        self.model = loadModel['model']
        self.tokenizer = loadModel['tokenizer']
            
    def run(
        self,
        prompt: str = "",
        prompt_list: List[str] = [],
        sampling_params: Any=None,
        saveLogFlag = True
    ):
        if sampling_params is None:
            sampling_params = SamplingParams()
            for k in self.generation_kwargs:
                sampling_params.__setattr__(k, self.generation_kwargs[k])
        else:
            sampling_params = sampling_params
            
        if self.model==None:
            raise ValueError("The model is empty.")
        
        if prompt != "" and len(prompt_list) == 0:
            prompt_list = [prompt]
        
        if self.logSaver is not None and saveLogFlag == True:
            self.logSaver.writeStrToLog("Function -> RagGenerator -> run")
            self.logSaver.writeStrToLog("Given generator prompt_list -> : "+prompt_list)
        
        final_result = []
        preds = self.model.generate(prompt_list, sampling_params)
        for one_prompt,pred in zip(prompt_list, preds):
            pred_dict =  RequestOutputToDict(pred)
            content = pred_dict['outputs'][0]['text']
            final_result.append({
                "prompt":one_prompt,
                "content":content,
                "meta":{"pred":pred_dict},    
            })    
        
        if self.logSaver is not None and saveLogFlag == True:
            self.logSaver.writeStrToLog("Returns generator reply : "+content)

        return {"final_result":final_result}

