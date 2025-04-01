import json
from kninjllm.llm_generator.close_generator.openai_generator import OpenAIGenerator
from root_config import RootConfig
import re

class ExternalKnowledgeConflicts:
    def __init__(self,llm=None):
        if llm != None:
            self.llm = llm
        else:
            self.llm = OpenAIGenerator(api_key=RootConfig.openai_api_key,generation_kwargs={"temperature":0},do_log=False)
      
    def execute(self, query_obj_list,method="prompt_project"):
        
        if method == "none":
            
            for index,query in enumerate(query_obj_list):
                query_obj_list[index]['filter_ctxs_list'] = query_obj_list[index]['ctxs_content_list']
            
            return query_obj_list
        
        
        elif method == "prompt_project":
        
            prompt_list = []
            for query_obj in query_obj_list:
            
                ctxs_content_list = query_obj['ctxs_content_list']
                
                knowledge_ctxs_content_list = []
                for index,c in enumerate(ctxs_content_list):
                    ctxs_content_list[index] = str(index+1) + ".  " + c
                    
                    c_list = c.split("\t")
                    if len(c_list) == 3 and "wiki" in c_list[0]:
                        c = c_list[1]
                    
                    s = str(index+1) + ".  " + c
                    knowledge_ctxs_content_list.append(s)

                # # old_prompt
                filter_prompt = """
                    我会给出一个问题和一个知识列表,你要判断知识列表中的知识是否正确,以及该知识是否可以支持回答我的问题,最后把可以回答我的问题的正确知识的id组成新知识id列表,以数组的格式返回给我。
                    只返回新知识id列表数组,不要返回任何其他信息。如果知识列表中没有能够支持回答我的问题的知识,就返回: []。

                    示例1:
                    问题:
                    特朗普总统的出生国家是?

                    知识列表:
                    1.  特朗普击败了拜登当选了美国总统。
                    2.  唐纳德·特朗普，1946年6月14日出生于美国。
                    3.  特朗普出生于纽约。
                    4.  如果一个人出生在城市A,城市A属于国家B,则这个人的出生国家是国家B。
                    5.  泽连斯基，出生于乌克兰。
                    6.  特朗普，美国纽约人

                    新知识列表:
                    [1,2,3,4,6]



                    示例2:
                    问题:
                    RAF Lakenheath is situated in which English county?

                    知识列表:
                    1.  RAF Lakenheath Royal Air Force Lakenheath or RAF Lakenheath is a Royal Air Force station near the town of Lakenheath in Suffolk, England, north-east of Mildenhall and west of Thetford.
                    2.  joan hamburg is the mother of michael kors. michael kors is owner of versace.
                    3.  RAF Lakenheath is primarily used for air force purposes，Suffolk, England.
                    4.  If Facility X provides service in Region Y, then Facility X operates in Region Y.
                    5.  If Vehicle X is built in Region Y, then Vehicle X is manufactured in Region Y.
                    6.  If Alcohol X is produced in Region Y, then Alcohol X is brewed in Region Y.
                    新知识列表:
                    [1,3,4]


                    示例3:
                    问题:
                    [Natasha] went with her mother [Cindy] to pick out a gift for [Cindy]'s mother, [Frances]. [Natasha] and her uncle [Hugh] went to the pet shop. [Natasha] saw a puppy that she loved, so [Hugh] bought it for her.\nWho is Hugh to Frances?

                    知识列表:
                    1.  the Stanley Cup to Camp Lejeune, to the beach, and to his church for his day with the Cup.
                    2.  We family lived on a 160-acre dairy farm that was also used to grow crops such as hay and tobacco. 
                    3.  Alice married secondly Eric Siepmann and with him had a third son, William Siepmann. 
                    4.  daughter(A, B) ∧ daughter(B, C) ∧ uncle(C, D) ∧ female(A) ∧ male(D) => son(A, D).
                    5.  mother(A, B) ∧ daughter(B, C) ∧ brother(C, D) ∧ aunt(D, E) ∧ son(E, F) ∧ sister(F, G) ∧ sister(G, H) ∧ aunt(H, I) ∧ brother(I, J) ∧ female(A) ∧ male(J) => uncle(A, J).
                    6.  mother(A, B) ∧ daughter(B, C) ∧ father(C, D) ∧ daughter(D, E) ∧ brother(E, F) ∧ brother(F, G) ∧ uncle(G, H) ∧ sister(H, I) ∧ female(A) ∧ female(I) => aunt(A, I).
                    新知识列表:
                    [4]


                    请回答:
                    问题:
                    """ + query_obj['question'] + """

                    知识列表:
                    """ + "\n".join(knowledge_ctxs_content_list) + """

                    新知识列表:

                """
                
                
                # print("----------------------filter_prompt--------------------------\n",filter_prompt,type(filter_prompt))
                prompt_list.append(filter_prompt)
                
            
            llm_res_list = self.llm.run(prompt_list=prompt_list)['final_result']
            llm_res_content_list = list(map(lambda x:x['content'],llm_res_list))
            
            final_result = []
            for query_obj,res_content in zip(query_obj_list,llm_res_content_list):
                ctxs_content_list = query_obj['ctxs_content_list']
            
                matches = re.findall(r'\[(.*?)\]', res_content, re.DOTALL)
                try:
                    matches = matches[0]
                    matches = '[' + matches + ']'
                except:
                    matches = '[]'

                print('--------------------------matches------------------------------\n',matches,type(matches))
                matches_list = json.loads(matches)

                print('--------------------------matches_list------------------------------\n',matches_list,type(matches_list))
                
                final_ctxs_list = []
                for index,ctx in enumerate(ctxs_content_list):
                    current = index + 1
                    if current in matches_list:
                        final_ctxs_list.append(ctx)
                
                query_obj['filter_ctxs_list'] = final_ctxs_list
                final_result.append(query_obj)
                
            return final_result
        
        
        else:
            raise ValueError('knowledgeDiffFuntion is not supported')