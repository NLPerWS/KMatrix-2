import json
import sys
import time
from typing import Any, Dict, List
import pandas as pd

from kninjllm.llm_utils.common_utils import calculate_hash



def split_by_length(max_length, doc_list):
    from collections import defaultdict

    title_to_texts = defaultdict(list)
    for doc in doc_list:
        parts = doc['content'].split('\t')
        if len(parts) == 3:
            doc_id, text, title = parts
            title_to_texts[title].append((text, doc['source']))

    final_list = []
    for title, texts_and_sources in title_to_texts.items():
        current_text = ''
        current_source = ''
        current_space_count = 0  
        for text, source in texts_and_sources:
            text_space_count = text.count(' ')
            if current_space_count + text_space_count > max_length:
                if current_text:
                    id = calculate_hash(current_text)
                    final_list.append({"id":id,"content":current_text})
                current_text = text
                current_source = source
                current_space_count = text_space_count  
                current_text = current_text + " " + text if current_text else text
                current_source = source
                current_space_count += text_space_count
        if current_text:
            id = calculate_hash(current_text)
            final_list.append({"id":id,"content":current_text})

    return final_list


class LinearizerToText:

    def __init__(self,
                    knowledge_line_count,
                    max_length: int = 100,
                    valueList:List[Any] = [],
                    count = 0):
        self.max_length = max_length
        self.valueList = valueList
        self.count = count
        self.knowledge_line_count = knowledge_line_count
    
    def run(self, value:List[Any]):
        this_step_list = []
        print("-----------------------------LinearizerToText --------------------------------",len(value))
        if len(value) > 0:
            self.count += 1
            tempValue = value
            input_list = []
            if isinstance(tempValue,list) and isinstance(tempValue[0],dict) and 'content' in tempValue[0] and tempValue[0]['content'] != "" and tempValue[0]['content'] != None:
                self.valueList.extend(tempValue)
            
            if isinstance(tempValue,list) and isinstance(tempValue[0],dict) and "header" in tempValue[0] and "rows" in tempValue[0] \
                and tempValue[0]["header"] != None and tempValue[0]["rows"] != None:  
                for tempObj in tempValue:
                    for row_list in tempObj["rows"]:
                        if "id" in tempObj:
                            title = tempObj['id']
                        elif "doc_title" in tempObj:
                            title = tempObj['doc_title']
                        else:
                            raise ValueError("The table data format is incorrect and should contain id or doc_title fields. Please check...")
                        
                        pre_text = "<H> [title] <T> " + title + " "
                        for index,row_td in enumerate(row_list):
                            pre_text  = pre_text + "<H> " + tempObj["header"][index] + " <T> " + str(row_td) + " "
                        input_list.append({
                            "title":title,
                            "content":pre_text,
                        })

            if isinstance(tempValue,list) and isinstance(tempValue[0],dict) and "triples" in tempValue[0] \
                and tempValue[0]['triples'] != None:
                for obj in tempValue:
                    title = str(obj['triples'][0][0])
                    pre_text = "<H> [title] <T> " + title + " "
                    for triple_list in obj['triples']:
                        temp_triple_list = triple_list.copy()
                        first_element = temp_triple_list.pop(0)
                        last_element = temp_triple_list.pop()
                        pre_text = pre_text + "<H> " + " ".join(temp_triple_list) + " <T> " + str(last_element) + " "
                    input_list.append({
                        "title":title,
                        "content":pre_text,
                    })
            
            if input_list != []:
                input_text_list = list(map(lambda x:x['content'],input_list))
                from kninjllm.llm_linearizer.Verbalizer.verbalizer import verbalizer as liner
                result = liner(input_text_list)
                for index,res in enumerate(result):
                    title = input_list[index]['title']
                    id =  calculate_hash([res])
                    content = res
                    this_step_list.append({"id":id,"content":content})
        else:
            self.count += 1
        
        if self.count > self.knowledge_line_count:
            raise ValueError("Error in initial parameters of linearizer. Please check...")
        
        # new_this_step_list = split_by_length(max_length=self.max_length,doc_list=this_step_list)
        new_this_step_list = this_step_list
        
        self.valueList.extend(new_this_step_list)
        
        print("finally final_knowledge len:  \n",len(self.valueList))
        
        if self.knowledge_line_count != self.count:
            return {"final_result":{"flag":0,"knowledge":[]}}
        else:
            return {"final_result":{"flag":1,"knowledge":self.valueList}}
    