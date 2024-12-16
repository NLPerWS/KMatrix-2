from typing import Any, Dict, List, Optional
from vllm import SamplingParams
from kninjllm.llm_utils.common_utils import RequestOutputToDict,loadModelByCatch
from root_config import RootConfig

class LLama2Generator:

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
        self.model = loadModelByCatch(model_name='llama2',model_path=model_path)
        
    def run(
        self,
        prompt: str = "",
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
        
        print("------------------------------  llama2  -------------------------")
        
        if prompt != "" and len(prompt_list) == 0:
            prompt_list = [prompt]
        
        # 外部知识与模型知识冲突检测与消解
        from kninjllm.llm_conflict_of_knowledge.External_Model_Knowledge_Conflicts import ExternalModelKnowledgeConflicts
        conflicts = ExternalModelKnowledgeConflicts()
        for index,p in enumerate(prompt_list):
            prompt_list[index] = conflicts.execute(prompt=p,function_str=self.knowledgeDiffFuntion)
        
        
        if self.logSaver is not None:
            self.logSaver.writeStrToLog("Function -> LLama2Generator -> run")
            self.logSaver.writeStrToLog("Given generator prompt_list -> : " + prompt_list)

        print("------------------------------  prompt_list  -------------------------\n",prompt_list)
        

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
        
        if self.logSaver is not None:
            self.logSaver.writeStrToLog("Returns generator reply : "+ content )
    
        return {"final_result":final_result}
    
        
    