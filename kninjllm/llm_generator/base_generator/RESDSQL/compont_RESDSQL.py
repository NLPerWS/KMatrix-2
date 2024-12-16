import base64
import json
import shlex
import subprocess

def run_script(script_path, param1, param2,param3,param4):
    try:
        
        if isinstance(param2, dict):
            # 将 JSON 转换成字符串
            param2 = json.dumps(param2, ensure_ascii=False)
            param2 = param2.replace(" ","")
        
        # 构建命令列表，包括脚本路径和两个参数
        command = ['bash', script_path, param1, param2,param3,param4]
        
        # 执行命令并等待其完成
        result = subprocess.run(command, check=True)
        
        # 打印脚本结束后的返回码
        print(f"Script finished with return code {result.returncode}")
        
    except subprocess.CalledProcessError as e:
        # 捕获脚本错误并打印
        print(f"An error occurred while running the script: {e}")


def execute_file(test_data,tables):
    with open('data/dev.json','w',encoding='utf-8') as f:
        json.dump(test_data,f,ensure_ascii=False)
    with open('data/tables.json','w',encoding='utf-8') as f:
        json.dump(tables,f,ensure_ascii=False)
    with open('predictions/pred.sql','w',encoding='utf-8') as f:
        f.write('')
def read_predict():
    with open('predictions/pred.sql','r',encoding='utf-8') as f:
        data_list = f.readlines()
    for index,data in enumerate(data_list):
        data_list[index] = data.replace("\n","")
        
    return data_list

def do_text_to_sql(query_list,tables,root_path,db_info,device,model_path):
    
    query_list = list(map(lambda x:{"question":x,"db_id":db_info['database']},query_list))
    execute_file(query_list,tables)
    run_script('scripts/inference/infer_text2natsql_cspider.sh', root_path, db_info,device,model_path)
    data_list = read_predict()
    return data_list

if __name__ == "__main__":
    
    pass