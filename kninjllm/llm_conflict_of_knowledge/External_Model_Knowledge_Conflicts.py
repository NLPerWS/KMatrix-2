import json
from kninjllm.llm_generator.close_generator.openai_generator import OpenAIGenerator
from root_config import RootConfig

class ExternalModelKnowledgeConflicts:
    def __init__(self):
      self.open_ai = OpenAIGenerator(api_key=RootConfig.openai_api_key,do_log=False)
      
      
    def execute(self,prompt,function_str):
        
        # 外部知识优先
        if function_str == "Faithful to context":
            
            # pre_prompt = '请注意,我所提供的知识优先级最高,如果我提供的知识与你本身的知识冲突,则必须以我提供的知识为准!'
            
            pre_prompt = 'Please note that the information I provide takes highest priority. If there is any conflict between my information and your own, you must prioritize the information I provide!'
            
            new_prompt = pre_prompt + "\n\n" + prompt
        
        # 联合知识优先
        elif function_str == "Factuality improvement":
            new_prompt = prompt
        
        # default
        else:
            new_prompt = prompt
        
        return new_prompt
    