import json
from argparse import ArgumentParser
import os
import sys
from vllm import LLM
from transformers import AutoTokenizer

from kninjllm.llm_retriever.RULE.rule_retrieval.vllm_inference import inference_n, inference

class ClutrrPrompt:
    system_prompt = "You are given a Query, which incorporates a short story descripting the relationship between some people and a question about the relationship. The relationship hops vary from 2 to 10 and are related to the number of different people. The Please write the inferential rule may help answer the question. The rule is only about relationship and the hops should be the same like in the Query. Please note the gender and do not use words like child or grandchild. The rule should in this format: 'If (premise), then (conclusion)'. The premise in the rule should be the abstraction of facts in the story and the conclusion in the rule should be aboue the question in the end. I will give three examples. Just output the rule and do not ouptut anything else."
    input1 = "Query: [Ashley]'s daughter, [Lillian], asked her mom to read her a story. [Nicholas]'s sister [Lillian] asked him for some help planting her garden.\nWho is Nicholas to Ashley?"
    output1 = "Rule: if A has a daughter B, B has a brother C, and A is female, C is male, then C is the grandson of A."
    input2 = "Query: [Beverly] is taking her nephew [Aaron] out for dinner. [Bobby] wanted his father, [Antonio], to have a great birthday party. He asked for advice from [Bobby]'s father, [Tracy], and his son, [Aaron].\nWho is Beverly to Tracy?"
    output2 = "Rule: if A has a son B, B has a father C, C has a son D, D has a aunt E, and A is female, E is female, then E is the sister of A."
    input3 = "Query: [Dan] went to his mother [Patrice]'s house to play cards. [Eric], [Patrice]'s other son, was there too. [Cesar] showed up later and asked his son [Dan] to deal him in too. [Don] took his favorite son [Steve] to a baseball game where he caught a foul ball as a souvenir. [Constance] and her brother [William] were making tea in the kitchen when [Rita], her son, came in to show her the painting he had made. [Don] and [Rita] asked their mother, if they could go play in the pool. [Monica] and her mother [William] made breakfast together. [Margaret] and her brother [Cesar] were making tea in the kitchen when [Monica], her son, came in to show her the painting he had made.\nWho is Eric to Steve?"
    output3 = "Rule: if A has a son B, B has a sister C, C has a mother D, D has a brother E, E has a daughter F, F has a mother G, G has a brother H, H has a son I, I has a mother J, J has a son K, and A is male, K is male, then K is the nephew of A."

class ClutrrFOLPrompt:
    system_prompt = "You are given a Query, which incorporates a short story descripting the relationship between some people and a question about the relationship. The relationship hops vary from 2 to 10 and are related to the number of different people. The Please write the inferential rule may help answer the question. The rule is only about relationship and the hops should be the same like in the Query. Please note the gender and do not use words like child or grandchild. The rule should be in FOL (first order language) format. The premise in the rule should be the abstraction of facts in the story and the conclusion in the rule should be aboue the question in the end. I will give three examples. Just output the rule and do not ouptut anything else."
    input1 = "Query: [Ashley]'s daughter, [Lillian], asked her mom to read her a story. [Nicholas]'s sister [Lillian] asked him for some help planting her garden.\nWho is Nicholas to Ashley?"
    output1 = "Rule: daughter(A, B) ^ brother(B, C) ^ female(A) ^ male(C) => son(A, C)"
    input2 = "Query: [Beverly] is taking her nephew [Aaron] out for dinner. [Bobby] wanted his father, [Antonio], to have a great birthday party. He asked for advice from [Bobby]'s father, [Tracy], and his son, [Aaron].\nWho is Beverly to Tracy?"
    output2 = "Rule: son(A, B) ^ father(B, C) ^ son(C, D) ^ aunt(D, E) ^ female(A) ^ female(E) => sister(A, E)"
    input3 = "Query: [Dan] went to his mother [Patrice]'s house to play cards. [Eric], [Patrice]'s other son, was there too. [Cesar] showed up later and asked his son [Dan] to deal him in too. [Don] took his favorite son [Steve] to a baseball game where he caught a foul ball as a souvenir. [Constance] and her brother [William] were making tea in the kitchen when [Rita], her son, came in to show her the painting he had made. [Don] and [Rita] asked their mother, if they could go play in the pool. [Monica] and her mother [William] made breakfast together. [Margaret] and her brother [Cesar] were making tea in the kitchen when [Monica], her son, came in to show her the painting he had made.\nWho is Eric to Steve?"
    output3 = "Rule: son(A, B) \u2227 sister(B, C) \u2227 mother(C, D) \u2227 brother(D, E) \u2227 daughter(E, F) \u2227 mother(F, G) \u2227 brother(G, H) \u2227 son(H, I) \u2227 mother(I, J) \u2227 son(J, K) \u2227 male(A) \u2227 male(K) => nephew(A, K)"


class DeerPrompt:
    system_prompt = "You are given a Question. Please write the inferential rule may help answer the question. I will give three examples. Just output the rule and do not ouptut anything else."
    input1 = \
"""
Question: Which of the following mushroom is most likely to be toxic?
A. Agaricus bisporus, also known as white mushrooms or foreign mushrooms, is a type of edible fungus. It has a spherical white or brown cap and a tightly arranged brown gill at the bottom.
B. Rubroboletus satanas, commonly known as Satan's bolete or the Devil's bolete, is a basidiomycete fungus of the bolete family (Boletaceae) and one of its most infamous members. It has striking appearance and at times putrid smell.
C. Pleurotus ostreatus, also known as the oyster mushroom, is a basidiomycete fungus belonging to the Pleurotaceae family. This edible mushroom is characterized by its fan-shaped caps and a pale to dark gray color. Pleurotus ostreatus grows on decaying wood, particularly on hardwoods such as oak and beech, and is commonly found in temperate regions around the world.
D. Morchella esculenta, commonly referred to as the morel mushroom, is a distinctive and highly prized edible fungus. Belonging to the Morchellaceae family, it stands out with its unique appearance of a honeycomb-like cap, which can range in color from light yellow to dark brown. Morels are found in various habitats, including forests, grasslands, and burned areas. 
"""
    output1 = "Rule: If a mushroom contains red colour and has unpleasant smell, then it probably is toxic."
    input2 = \
"""
Question: Which animal is most likely to have a big size?
A. Kangaroos are commonly found in Australia. They feed on the leaves, bark, and tender buds of plants
B. Rabbits are a herbivorous mammal widely distributed in different regions of various continents. They mainly feed on the tender leaves of grass, vegetables, and trees.
C. Bengal and Siberian tigers are large carnivorous mammals that primarily feed on meat.
D. Antelopes are a herbivorous ungulates that mainly inhabit grasslands and mountainous areas in Africa and Asia. They feed on grass, leaves, and tender buds.
"""
    output2 = "Rule: If an animal eats meat, then it probably has a big size."
    input3 = \
"""
Question: Which place is most likely to have rice that can be harvested more times?
A. Canada is a country located in North America. It has a diverse climate, ranging from temperate to subarctic, and is known for its production of wheat and canola.
B. Thailand is a Southeast Asian country known for its tropical climate and fertile plains. It is one of the world's largest exporters of rice and is renowned for its rice cultivation.
C. Norway is a country situated in Northern Europe. It has a cold and temperate climate, with limited agricultural land suitable for rice cultivation.
D. The North China Plain is a vast lowland region in northern China known for its fertile soil and favorable climate for rice cultivation.   
"""
    output3 = "Rule: If a place is closer to the equator, then the rice grown in that place probably can be harvested with more times."

class LawPrompt:
    options = """已知以下指控['保险诈骗', '制造、贩卖、传播淫秽物品', '非法获取公民个人信息', '冒充军人招摇撞骗', '强制猥亵、侮辱妇女', '敲诈勒索', '串通投标', '故意伤害', '招摇撞骗', '非法组织卖血', '破坏监管秩序', '倒卖文物', '倒卖车票、船票', '传播性病', '脱逃', '破坏生产经营', '侵犯著作权', '非国家工作人员受贿', '危险驾驶', '虚开增值税专用发票、用于骗取出口退税、抵扣税款发票', '破坏广播电视设施、公用电信设施', '招收公务员、学生徇私舞弊', '非法买卖、运输、携带、持有毒品原植物种子、幼苗', '打击报复证人', '破坏交通设施', '盗窃、侮辱尸体', '假冒注册商标', '行贿', '生产、销售假药', '非法生产、买卖警用装备', '职务侵占', '赌博', '贪污', '挪用特定款物', '非法转让、倒卖土地使用权', '生产、销售伪劣产品', '伪造、变造金融票证', '抢劫', '劫持船只、汽车', '遗弃', '非法吸收公众存款', '出售、购买、运输假币', '非法占用农用地', '侮辱', '挪用公款', '伪造、变造、买卖武装部队公文、证件、印章', '传授犯罪方法', '扰乱无线电通讯管理秩序', '利用影响力受贿', '盗窃', '虐待被监管人', '挪用资金', '污染环境', '重婚', '非法持有、私藏枪支、弹药', '非法生产、销售间谍专用器材', '伪证', '破坏电力设备', '私分国有资产', '非法制造、买卖、运输、邮寄、储存枪支、弹药、爆炸物', '骗取贷款、票据承兑、金融票证', '非法处置查封、扣押、冻结的财产', '违法发放贷款', '拐卖妇女、儿童', '聚众哄抢', '虚报注册资本', '隐匿、故意销毁会计凭证、会计帐簿、财务会计报告', '掩饰、隐瞒犯罪所得、犯罪所得收益', '诈骗', '过失损坏武器装备、军事设施、军事通信', '徇私枉法', '非法行医', '重大责任事故', '虐待', '生产、销售有毒、有害食品', '非法采矿', '徇私舞弊不征、少征税款', '破坏计算机信息系统', '集资诈骗', '绑架', '强迫劳动', '对非国家工作人员行贿', '强奸', '非法种植毒品原植物', '非法携带枪支、弹药、管制刀具、危险物品危及公共安全', '走私武器、弹药', '洗钱', '侵占', '拐骗儿童', '金融凭证诈骗', '提供侵入、非法控制计算机信息系统程序、工具', '故意毁坏财物', '诬告陷害', '销售假冒注册商标的商品', '非法采伐、毁坏国家重点保护植物', '逃税', '生产、销售伪劣农药、兽药、化肥、种子', '玩忽职守', '组织、强迫、引诱、容留、介绍卖淫', '贷款诈骗', '引诱、教唆、欺骗他人吸毒', '破坏交通工具', '过失致人死亡', '危险物品肇事', '妨害公务', '走私、贩卖、运输、制造毒品', '非法拘禁', '走私普通货物、物品', '对单位行贿', '信用卡诈骗', '非法经营', '持有、使用假币', '收买被拐卖的妇女、儿童', '单位受贿', '帮助犯罪分子逃避处罚', '徇私舞弊不移交刑事案件', '非法侵入住宅', '介绍贿赂', '重大劳动安全事故', '受贿', '聚众斗殴', '合同诈骗', '滥用职权', '盗窃、抢夺枪支、弹药、爆炸物', '生产、销售不符合安全标准的食品', '拒不执行判决、裁定', '盗掘古文化遗址、古墓葬', '伪造货币', '过失致人重伤', '非法猎捕、杀害珍贵、濒危野生动物', '滥伐林木', '窝藏、包庇', '动植物检疫徇私舞弊', '强迫交易', '非法获取国家秘密', '非法买卖制毒物品']"""
    system_prompt = f"给定一个问题，请写出可能有助于判断相关指控的推理规则（法条）。\n\n{options}\n\n我将给出三个例子。只输出规则，不要输出其他内容。"
    input1 = "上海市宝山区人民检察院指控：被告人吴某某在明知其未取得医生执业资格及医疗许可的情况下非法行医，且于2010年10月、2016年4月被卫生部门予以两次行政处罚，仍于2016年10月27日13时许再次在本区江杨北路XXX弄XXX号XXX室为前来就诊的瞿某某开具罗红霉素胶囊等药物并收取诊疗费用后，被民警当场查获。被告人吴某某到案后如实供述了上述犯罪事实。\r\n"
    output1 = """如果叙述内容符合:第三百三十六条 未取得医生执业资格的人非法行医，情节严重的，处三年以下有期徒刑、拘役或者管制，并处或者单处罚金；严重损害就诊人身体健康的，处三年以上十年以下有期徒刑，并处罚金；造成就诊人死亡的，处十年以上有期徒刑，并处罚金。未取得医生执业资格的人擅自为他人进行节育复通手术、假节育手术、终止妊娠手术或者摘取宫内节育器，情节严重的，处三年以下有期徒刑、拘役或者管制，并处或者单处罚金；严重损害就诊人身体健康的，处三年以上十年以下有期徒刑，并处罚金；造成就诊人死亡的，处十年以上有期徒刑，并处罚金。则指控:非法行医"""
    input2 = "经审理查明，2014年10月，被告人刘某某委托其岳父章某某帮其办理了3立方米的林木采伐许可证，采伐地点规定在城关镇三岔河村三岔河组陈家对门林山。2014年12月19日，被告人刘某某擅自改变采伐地点，在本组庙堂沟口河西自己的林山内采伐林木231株，经商南县林业局工程师现场测量鉴定，被告人刘某某采伐林木材积为9.6447立方米，折合活立木蓄积量为12.8596立方米。2014年12月26日被告人刘某某在其岳父的陪同下到商南县公安局森林分局投案，并如实交代了其犯罪事实。\r\n上述事实，被告人刘某某在开庭审理过程中亦无异议，且有受案登记表，证人章某某、刘某甲、张某某、宋某某的证言，现场勘查笔录及照片，勘验鉴定意见，林木采伐许可证，林权证，被告人刘某某到案说明书等证据证实，足以认定。\r\n"
    output2 = "如果叙述内容符合:第三百四十五条 盗伐森林或者其他林木，数量较大的，处三年以下有期徒刑、拘役或者管制，并处或者单处罚金；数量巨大的，处三年以上七年以下有期徒刑，并处罚金；数量特别巨大的，处七年以上有期徒刑，并处罚金。违反森林法的规定，滥伐森林或者其他林木，数量较大的，处三年以下有期徒刑、拘役或者管制，并处或者单处罚金；数量巨大的，处三年以上七年以下有期徒刑，并处罚金。非法收购、运输明知是盗伐、滥伐的林木，情节严重的，处三年以下有期徒刑、拘役或者管制，并处或者单处罚金；情节特别严重的，处三年以上七年以下有期徒刑，并处罚金。盗伐、滥伐国家级自然保护区内的森林或者其他林木的，从重处罚。则指控:滥伐林木"
    input3 = "商洛市商州区人民检察院指控，2010年3月至2012年2月，被告人秦某某通过各种途径取得佘某某、杨某、张某甲、唐某某、王某甲、赵某甲、刘某、王某乙、王某丙、赵某乙的身份证件，在上述人员不知情的情况下，冒用其居民身份证进行贷款，并在贷款担保书中提供虚假担保信息，从商州区城关信用社先后骗取贷款10笔，每笔4万元，共计40万元；同时被告人秦某某在周某、张某乙、赵某丙、熊某某知晓其借用本人身份证用途，周某、张某乙、赵某丙到场，熊某某未到场情况下，利用上述人员提供的身份证进行贷款，并在贷款担保书中提供虚假担保信息，从商州区城关信用社先后骗取贷款4笔，每笔4万元，共计16万元。综上，秦某某骗取贷款14笔56万元，除以佘某某名义贷款4万元被李某甲使用外，剩余52万元被告人秦某某个人私用。为证明上述事实，公诉机关当庭出示了被告人供述，证人证言，贷款清册，贷款契约等证据证明。故依据《中华人民共和国刑法》××××、××××之规定，指控被告人秦某某犯骗取贷款罪，并能如实供述犯罪事实，建议对其从轻处罚。\r\n"
    output3 = "如果叙述内容符合:第一百七十五条 以转贷牟利为目的，套取金融机构信贷资金高利转贷他人，违法所得数额较大的，处三年以下有期徒刑或者拘役，并处违法所得一倍以上五倍以下罚金；数额巨大的，处三年以上七年以下有期徒刑，并处违法所得一倍以上五倍以下罚金。单位犯前款罪的，对单位判处罚金，并对其直接负责的主管人员和其他直接责任人员，处三年以下有期徒刑或者拘役。则指控:骗取贷款、票据承兑、金融票证"

class LawFOLPrompt:
    options = """已知以下指控['保险诈骗', '制造、贩卖、传播淫秽物品', '非法获取公民个人信息', '冒充军人招摇撞骗', '强制猥亵、侮辱妇女', '敲诈勒索', '串通投标', '故意伤害', '招摇撞骗', '非法组织卖血', '破坏监管秩序', '倒卖文物', '倒卖车票、船票', '传播性病', '脱逃', '破坏生产经营', '侵犯著作权', '非国家工作人员受贿', '危险驾驶', '虚开增值税专用发票、用于骗取出口退税、抵扣税款发票', '破坏广播电视设施、公用电信设施', '招收公务员、学生徇私舞弊', '非法买卖、运输、携带、持有毒品原植物种子、幼苗', '打击报复证人', '破坏交通设施', '盗窃、侮辱尸体', '假冒注册商标', '行贿', '生产、销售假药', '非法生产、买卖警用装备', '职务侵占', '赌博', '贪污', '挪用特定款物', '非法转让、倒卖土地使用权', '生产、销售伪劣产品', '伪造、变造金融票证', '抢劫', '劫持船只、汽车', '遗弃', '非法吸收公众存款', '出售、购买、运输假币', '非法占用农用地', '侮辱', '挪用公款', '伪造、变造、买卖武装部队公文、证件、印章', '传授犯罪方法', '扰乱无线电通讯管理秩序', '利用影响力受贿', '盗窃', '虐待被监管人', '挪用资金', '污染环境', '重婚', '非法持有、私藏枪支、弹药', '非法生产、销售间谍专用器材', '伪证', '破坏电力设备', '私分国有资产', '非法制造、买卖、运输、邮寄、储存枪支、弹药、爆炸物', '骗取贷款、票据承兑、金融票证', '非法处置查封、扣押、冻结的财产', '违法发放贷款', '拐卖妇女、儿童', '聚众哄抢', '虚报注册资本', '隐匿、故意销毁会计凭证、会计帐簿、财务会计报告', '掩饰、隐瞒犯罪所得、犯罪所得收益', '诈骗', '过失损坏武器装备、军事设施、军事通信', '徇私枉法', '非法行医', '重大责任事故', '虐待', '生产、销售有毒、有害食品', '非法采矿', '徇私舞弊不征、少征税款', '破坏计算机信息系统', '集资诈骗', '绑架', '强迫劳动', '对非国家工作人员行贿', '强奸', '非法种植毒品原植物', '非法携带枪支、弹药、管制刀具、危险物品危及公共安全', '走私武器、弹药', '洗钱', '侵占', '拐骗儿童', '金融凭证诈骗', '提供侵入、非法控制计算机信息系统程序、工具', '故意毁坏财物', '诬告陷害', '销售假冒注册商标的商品', '非法采伐、毁坏国家重点保护植物', '逃税', '生产、销售伪劣农药、兽药、化肥、种子', '玩忽职守', '组织、强迫、引诱、容留、介绍卖淫', '贷款诈骗', '引诱、教唆、欺骗他人吸毒', '破坏交通工具', '过失致人死亡', '危险物品肇事', '妨害公务', '走私、贩卖、运输、制造毒品', '非法拘禁', '走私普通货物、物品', '对单位行贿', '信用卡诈骗', '非法经营', '持有、使用假币', '收买被拐卖的妇女、儿童', '单位受贿', '帮助犯罪分子逃避处罚', '徇私舞弊不移交刑事案件', '非法侵入住宅', '介绍贿赂', '重大劳动安全事故', '受贿', '聚众斗殴', '合同诈骗', '滥用职权', '盗窃、抢夺枪支、弹药、爆炸物', '生产、销售不符合安全标准的食品', '拒不执行判决、裁定', '盗掘古文化遗址、古墓葬', '伪造货币', '过失致人重伤', '非法猎捕、杀害珍贵、濒危野生动物', '滥伐林木', '窝藏、包庇', '动植物检疫徇私舞弊', '强迫交易', '非法获取国家秘密', '非法买卖制毒物品']"""
    system_prompt = f"给定一个问题，请写出可能有助于判断相关指控的推理规则（法条）。 请以一节逻辑语言的形式给出。\n\n{options}\n\n我将给出三个例子。只输出规则，不要输出其他内容。"
    input1 = "上海市宝山区人民检察院指控：被告人吴某某在明知其未取得医生执业资格及医疗许可的情况下非法行医，且于2010年10月、2016年4月被卫生部门予以两次行政处罚，仍于2016年10月27日13时许再次在本区江杨北路XXX弄XXX号XXX室为前来就诊的瞿某某开具罗红霉素胶囊等药物并收取诊疗费用后，被民警当场查获。被告人吴某某到案后如实供述了上述犯罪事实。\r\n"
    output1 = """∃x ((未取得医生执业资格(x) ∧ 非法行医(x)) ∧ 情节严重(x)) → ∃y 指控(x, y) ∧ y = “非法行医”。"""
    input2 = "经审理查明，2014年10月，被告人刘某某委托其岳父章某某帮其办理了3立方米的林木采伐许可证，采伐地点规定在城关镇三岔河村三岔河组陈家对门林山。2014年12月19日，被告人刘某某擅自改变采伐地点，在本组庙堂沟口河西自己的林山内采伐林木231株，经商南县林业局工程师现场测量鉴定，被告人刘某某采伐林木材积为9.6447立方米，折合活立木蓄积量为12.8596立方米。2014年12月26日被告人刘某某在其岳父的陪同下到商南县公安局森林分局投案，并如实交代了其犯罪事实。\r\n上述事实，被告人刘某某在开庭审理过程中亦无异议，且有受案登记表，证人章某某、刘某甲、张某某、宋某某的证言，现场勘查笔录及照片，勘验鉴定意见，林木采伐许可证，林权证，被告人刘某某到案说明书等证据证实，足以认定。\r\n"
    output2 = "∃x ((盗伐(x) ∨ 滥伐(x)) ∧ 数量较大(x) ∧ 违反森林法规定(x)) → ∃y 指控(x, y) ∧ y = “滥伐林木” )。"
    input3 = "商洛市商州区人民检察院指控，2010年3月至2012年2月，被告人秦某某通过各种途径取得佘某某、杨某、张某甲、唐某某、王某甲、赵某甲、刘某、王某乙、王某丙、赵某乙的身份证件，在上述人员不知情的情况下，冒用其居民身份证进行贷款，并在贷款担保书中提供虚假担保信息，从商州区城关信用社先后骗取贷款10笔，每笔4万元，共计40万元；同时被告人秦某某在周某、张某乙、赵某丙、熊某某知晓其借用本人身份证用途，周某、张某乙、赵某丙到场，熊某某未到场情况下，利用上述人员提供的身份证进行贷款，并在贷款担保书中提供虚假担保信息，从商州区城关信用社先后骗取贷款4笔，每笔4万元，共计16万元。综上，秦某某骗取贷款14笔56万元，除以佘某某名义贷款4万元被李某甲使用外，剩余52万元被告人秦某某个人私用。为证明上述事实，公诉机关当庭出示了被告人供述，证人证言，贷款清册，贷款契约等证据证明。故依据《中华人民共和国刑法》××××、××××之规定，指控被告人秦某某犯骗取贷款罪，并能如实供述犯罪事实，建议对其从轻处罚。\r\n"
    output3 = "∃x ((以转贷牟利为目的(x) ∧ 套取(金融机构, 信贷资金, x) ∧ 高利转贷(他人, x)) ∧ 违法所得数额较大(x)) → ∃y 指控(x, y) ∧ y = “骗取贷款、票据承兑、金融票证” )。"

class UlogicPrompt:
    system_prompt = "You are given a Context and a Question. Please write the inferential rule may help answer the question. The rule should in this format: 'If (premise), then (conclusion)'. The premise in the rule should be the abstraction of facts in the Context and the conclusion in the rule should be aboue the Question. I will give three examples. Just output the rule and do not ouptut anything else."
    input1 = "Context:\nJohn works at Google where he earns $100,000 per year, and the Tesla Model S is manufactured by Tesla Inc. which has set the price at $80,000, and if $100,000 is bigger than $80,000,\nQuestion:\nCan John own a Tesla Model S?"
    output1 = "Rule: If Person X works at Job A which pays Money Z1, and Vehicle Y is manufactured by Organization C which has set the price as Money Z2, and if Money Z1 is bigger than Money Z2, then Person X can own Vehicle Y."
    input2 = "Context:\nThe annual tech conference TechGalaxy 2023 booked the main convention hall at the Downtown Convention Center.\nQuestion:\nCan TechGalaxy 2023 access the main convention hall at the Downtown Convention Center?"
    output2 = "Rule: If Event X booked Facility Y, then Event X can access Facility Y."
    input3 = "Context:\nThe smartphone model X137 is made of a special polymer Zortex, which is known to react aggressively with isopropyl alcohol, causing the material to weaken and crack.\nQuestion:\nCan the smartphone model X137 be cleaned with isopropyl alcohol?"
    output3 = "Rule: If Electronic Device X is made of Material Z1, and Material Z1 reacts with Alcohol Y, then Electronic Device X cannot be cleaned with Alcohol Y."
    input4 = "Context:\nAuthorization for mining operations is granted by Environmental Protection Agency, and the Environmental Protection Agency operates in the Yellowstone National Park, and Yellowstone National Park is included in the State of Wyoming, and the State of Wyoming is a territory of the United States.\nQuestion:\nIs the authorization for mining operations legal in the United States?"
    output4 = "Rule: If Authorization X is granted by Facility A, and Facility A operates in Natural Place C, and Natural Place C is included in Region Z, and Region Z is a territory of Region Y, then Authorization X is legal in Region Y."
    input5 = "Context:\nArtist Alice is commissioned for a large mural titled 'Sunset Dreams' in the city center, involving vibrant colors and abstract shapes to represent the diversity of the community.\nQuestion:\nDoes Alice need to create 'Sunset Dreams'?"
    output5 = "Rule: If Person X is commissioned for Artwork Y, then Person X needs to create Artwork Y."

class UlogicFOLPrompt:
    system_prompt = "You are given a Context and a Question. Please write the inferential rule may help answer the question. The rule should be in FOL (first order language) format. The premise in the rule should be the abstraction of facts in the Context and the conclusion in the rule should be aboue the Question. I will give three examples. Just output the rule and do not ouptut anything else."
    input1 = "Context:\nJohn works at Google where he earns $100,000 per year, and the Tesla Model S is manufactured by Tesla Inc. which has set the price at $80,000, and if $100,000 is bigger than $80,000,\nQuestion:\nCan John own a Tesla Model S?"
    output1 = "WorkAt(Person X, Job A) ^ Pay(Job A, Money Z1) ^ ManufacturedBy(Vehicle Y, Organization C) ^ SetPrice(Organization C, Money Z2) ^ BiggerThan(Money Z1, Money Z2) => CanOwn(Person X, Vehicle Y)"
    input2 = "Context:\nThe annual tech conference TechGalaxy 2023 booked the main convention hall at the Downtown Convention Center.\nQuestion:\nCan TechGalaxy 2023 access the main convention hall at the Downtown Convention Center?"
    output2 = "Booked(Event X, Facility Y) => CanAccess(Event X, Facility Y)"
    input3 = "Context:\nThe smartphone model X137 is made of a special polymer Zortex, which is known to react aggressively with isopropyl alcohol, causing the material to weaken and crack.\nQuestion:\nCan the smartphone model X137 be cleaned with isopropyl alcohol?"
    output3 = "MaterialOf(Electronic Device X, Material Z1) ^ ReactsWith(Material Z1, Alcohol Y) => CanNotBeCleanedWith(Electronic Device X, Alcohol Y)"
    input4 = "Context:\nAuthorization for mining operations is granted by Environmental Protection Agency, and the Environmental Protection Agency operates in the Yellowstone National Park, and Yellowstone National Park is included in the State of Wyoming, and the State of Wyoming is a territory of the United States.\nQuestion:\nIs the authorization for mining operations legal in the United States?"
    output4 = "GrantedBy(Authorization X, Facility A) ^ OperateIn(Facility A, Natural Place C) ^ IncludedIn(Natural Place C, Region Z) ^ IsTerritory(Region Z, Region Y) => LegalInRegion(Authorization X, Region Y)"
    input5 = "Context:\nArtist Alice is commissioned for a large mural titled 'Sunset Dreams' in the city center, involving vibrant colors and abstract shapes to represent the diversity of the community.\nQuestion:\nDoes Alice need to create 'Sunset Dreams'?"
    output5 = "Commissioned(Person X, Artwork Y) => NeedToCreate(Person X, Artwork Y)"


class TheoremQAPrompt:
    system_prompt = "You are given a Question. Please write the inferential rule may help answer the question. I will give three examples. Just output the rule and do not ouptut anything else."
    input1 = "Question: If the annual earnings per share has mean $8.6 and standard deviation $3.4, what is the chance that an observed EPS less than $5.5?"
    output1 = "Rule: If a data point \\( X \\) in a dataset is given, and the mean (\\( \\mu \\)) and standard deviation (\\( \\sigma \\)) of the dataset are known, then the Z-score (\\( Z \\)) of the data point can be calculated using the formula \\( Z = (X - \\mu) / \\sigma \\).\n\n**Explanation**:\n- **Data point (\\( X \\))**: This is an individual value or observation from the dataset.\n- **Mean (\\( \\mu \\))**: This is the average value of all the data points in the dataset. It is calculated by adding all the data points and then dividing by the number of points.\n- **Standard deviation (\\( \\sigma \\))**: This measures how spread out the numbers in the dataset are around the mean. A higher standard deviation indicates that the data points are more spread out.\n- **Z-score (\\( Z \\))**: This score tells you how many standard deviations an element \\( X \\) is from the mean \\( \\mu \\). It is a way of comparing data points from different sets or assessing how unusual a data point is within its own set."
    input2 = "Question: Which of these codes cannot be Huffman codes for any probability assignment?"
    output2 = "Rule: If symbols in data are analyzed to determine their frequency of occurrence, and a binary Huffman tree is constructed by creating leaf nodes for each symbol based on these frequencies, merging the nodes with the lowest frequencies to form new internal nodes until only one node remains as the root, and if codes are assigned by traversing this tree from the root to each leaf while assigning '0' for each left branch and '1' for each right branch, then the original data can be uniquely reconstructed from this encoding without loss of information by traversing the Huffman tree according to the encoded bit sequence and outputting the corresponding symbols as leaf nodes are reached.\n\n**Explanation of Specific Terms:**\n- **Symbols**: These are the basic units of data (like characters or bytes) that make up the input.\n- **Frequency of occurrence**: This refers to how often each symbol appears in the data, which determines the length of each symbol's code in Huffman coding.\n- **Binary Huffman tree**: A type of data structure used in Huffman coding, where each node represents either a symbol (leaf node) or a combination of symbols (internal node) along with their combined frequencies.\n- **Leaf nodes**: The bottom-most nodes in the Huffman tree, representing individual symbols.\n- **Internal nodes**: Nodes formed by combining the two least frequent nodes or symbols, holding a frequency that is the sum of its children's frequencies.\n- **Root**: The single remaining node after all merges are complete, representing the entire dataset.\n- **Bitstream**: The sequence of bits (0s and 1s) that represents the encoded data.\n- **Prefix codes**: A set of codes where no code is a prefix of any other, ensuring unique decodability."
    input3 = "Question: You have a coin and you would like to check whether it is fair or biased. More specifically, let $\\theta$ be the probability of heads, $\\theta = P(H)$. Suppose that you need to choose between the following hypotheses: H_0 (null hypothesis): The coin is fair, i.e. $\\theta = \\theta_0 = 1 / 2$. H_1 (the alternative hypothesis): The coin is not fair, i.e. $\\theta > 1 / 2$. We toss 100 times and observe 60 heads. Can we reject H_0 at significance level $\\alpha = 0.01$?"
    output3 = "Rule: If the P-value is less than or equal to the significance level α, then the null hypothesis is rejected and the result is considered statistically significant; otherwise, if the P-value is greater than the significance level α, then the null hypothesis is not rejected and the result is considered not statistically significant.\n\nExplanation:\n- **P-value**: A statistical measure that helps to determine the likelihood of the result obtained in an experiment occurring by chance, under the assumption that the null hypothesis is correct.\n- **Null hypothesis**: A statement in a hypothesis test that typically asserts that there is no effect or relationship between the variables under investigation.\n- **Significance level (α)**: A threshold probability set before the study. Common values are 0.05 (5%), beyond which the results are unlikely to occur by chance if the null hypothesis is true.\n- **Statistically significant**: An indication that the observed result is unlikely to have occurred by chance alone, suggesting a real effect or relationship consistent with the alternative hypothesis.\n- **Reject the null hypothesis**: The decision made when the evidence (through a small P-value) strongly suggests that the null hypothesis does not adequately describe the observed data.\n- **Not rejected the null hypothesis**: The decision made when the evidence is insufficient to conclude that the observed effect or relationship is real (i.e., it might have occurred by chance)."

class Query2PythonPrompt:
    system_prompt = "You are given a input content,and you should generate python code of the . Please write the input content. I will give three examples. Just output the python code and do not ouptut anything else."
    input1 = "Input Content: python code to write bool value 1"
    output1 = "Python Code: def writeBoolean(self, n):\n        \"\"\"\n        Writes a Boolean to the stream.\n        \"\"\"\n        t = TYPE_BOOL_TRUE\n\n        if n is False:\n            t = TYPE_BOOL_FALSE\n\n        self.stream.write(t)"
    input2 = "Input Content: \"python how to manipulate clipboard\""
    output2 = "Python Code: def paste(xsel=False):\n    \"\"\"Returns system clipboard contents.\"\"\"\n    selection = \"primary\" if xsel else \"clipboard\"\n    try:\n        return subprocess.Popen([\"xclip\", \"-selection\", selection, \"-o\"], stdout=subprocess.PIPE).communicate()[0].decode(\"utf-8\")\n    except OSError as why:\n        raise XclipNotFound"
    input3 = "Input Content: python colored output to html"
    output3 = "Python Code: def _format_json(data, theme):\n    \"\"\"Pretty print a dict as a JSON, with colors if pygments is present.\"\"\"\n    output = json.dumps(data, indent=2, sort_keys=True)\n\n    if pygments and sys.stdout.isatty():\n        style = get_style_by_name(theme)\n        formatter = Terminal256Formatter(style=style)\n        return pygments.highlight(output, JsonLexer(), formatter)\n\n    return output"

    

def rule_induction(data, output_path, n, tokenizer, llm):
    # if 'fol' not in data_path:
    #     if 'clutrr' in data_path:
    #         Prompt = ClutrrPrompt
    #     elif 'deer' in data_path:
    #         Prompt = DeerPrompt
    #     elif 'law' in data_path:
    #         Prompt = LawPrompt
    #     elif "ulogic" in data_path:
    #         Prompt = UlogicPrompt
    #     elif 'theoremQA' in data_path:
    #         Prompt = TheoremQAPrompt
    # else:
    #     if 'clutrr-fol' in data_path:
    #         Prompt = ClutrrFOLPrompt
    #     elif 'ulogic-fol' in data_path:
    #         Prompt = UlogicFOLPrompt
    #     elif 'law-fol' in data_path:
    #         Prompt = LawFOLPrompt
    # if "code" in data_path:
    #     Prompt = Query2PythonPrompt
        
    Prompt = LawPrompt
    
    prompts = []
    for d in data:
        prompt = [{"role": "system", "content": Prompt.system_prompt}]
        prompt.append({"role": "user", "content": Prompt.input1})
        prompt.append({"role": "assistant", "content": Prompt.output1})
        prompt.append({"role": "user", "content": Prompt.input2})
        prompt.append({"role": "assistant", "content": Prompt.output2})
        prompt.append({"role": "user", "content": Prompt.input3})
        prompt.append({"role": "assistant", "content": Prompt.output3})
        # if 'ulogic' in data_path:
        #     prompt.append({"role": "user", "content": Prompt.input4})
        #     prompt.append({"role": "assistant", "content": Prompt.output4})
        #     prompt.append({"role": "user", "content": Prompt.input5})
        #     prompt.append({"role": "assistant", "content": Prompt.output5})
        prompt.append({"role": "user", "content": f"Query: {d['input']}"})
        
        prompts.append(prompt)
        
    if n == 1:
        outputs = inference(tokenizer, llm, prompts)
    elif n > 1:
        outputs = inference_n(tokenizer, llm, n, prompts)
    
    for d, o in zip(data, outputs):
        if n == 1:
            d['self_induction'] = o.strip()
        elif n > 1:
            o = [oo.split("Rule: ")[-1] for oo in o]
            d['self_induction_search'] = o
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def do_main(args):

    # llm = LLM(model=args.model_path, tensor_parallel_size=2)
    
    if args.model == None:
        llm = LLM(model=args.model_path)
        tokenizer = AutoTokenizer.from_pretrained(args.model_path)
    else:
        llm = args.model
        tokenizer = args.tokenizer
    
    rule_induction(args.query_list, args.output_path, args.n, tokenizer, llm)
    

if __name__ == "__main__":
    
    # parser = ArgumentParser()
    # parser.add_argument("--model_path", type=str)
    # parser.add_argument("--data_path", type=str)
    # parser.add_argument("--output_path", type=str)
    # parser.add_argument("--batch_size", type=int)
    # parser.add_argument("--n", type=int)
    # args = parser.parse_args()
    # do_main(args)
    
    pass