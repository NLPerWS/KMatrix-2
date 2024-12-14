# export JAVA_HOME="/usr/lib/jvm/java-11-openjdk-amd64"
# export JVM_PATH="/usr/lib/jvm/java-11-openjdk-amd64/lib/server/libjvm.so"
export VLLM_WORKER_MULTIPROC_METHOD=spawn
# model_path="/mnt/publiccache/huggingface/Qwen2.5-72B-Instruct"

model_path="/mnt/publiccache/huggingface/Qwen2.5-14B-Instruct"


model="Qwen2.5-14B-Instruct"

dataset="law"
export HF_ENDPOINT="https://hf-mirror.com"
export CUDA_VISIBLE_DEVICES="2"

# step 1

# 规则检索第一步，将query转换为规则形式
# input: data_path="dataset/$dataset/test_data.json"
# output: output_path="dataset/$dataset/test_data_with_self_induction_rule.json"

data_path="dataset/$dataset/test_data.json"
output_path="dataset/$dataset/test_data_with_self_induction_rule.json"
n=1
echo "run self_induction for $data_path"
python query2rule.py --data_path $data_path --model_path $model_path --output_path $output_path --n $n
echo "self_induction done!"

# step 2

# 规则检索第二步，根据转换为规则形式的query,使用bge-zh 检索 规则库
# 做规则生成
# input: data_path="dataset/$dataset/test_data_with_self_induction_rule.json" / rule_dir="dataset/$dataset/test_rule_json" 
# output: 输出规则检索指标及答案生成指标，返回规则检索结果及答案生成列表

data_path="dataset/$dataset/test_data_with_self_induction_rule.json"
rule_path="dataset/$dataset/test_rule.json" #没用
rule_dir="dataset/$dataset/test_rule_json"
index_dir="index/$dataset"
retriever_path="BAAI/bge-base-zh-v1.5"

python main_rule.py --setting "retrieval" --dataset $dataset --data_path $data_path --rule_path $rule_path --rule_dir $rule_dir --retriever_path $retriever_path --model_path $model_path --index_dir $index_dir 





dataset="code"

# step 1

# 代码检索第一步，将query转换为代码形式
# input: data_path="dataset/$dataset/test_data.json"
# output: output_path="dataset/$dataset/test_data_with_self_induction_rule.json"

data_path="dataset/$dataset/test_data.json"
output_path="dataset/$dataset/test_data_with_self_induction_rule.json"
n=1
echo "run self_induction for $data_path"
python query2rule.py --data_path $data_path --model_path $model_path --output_path $output_path --n $n
echo "self_induction done!"

# step 2

# 代码检索第二步，根据转换为代码形式的query,使用bge-en 检索 规则库
# 做代码增强生成（先不考虑）
# input: data_path="dataset/$dataset/test_data_with_self_induction_rule.json" / rule_dir="dataset/$dataset/test_rule_json" 
# output：输出代码检索指标及答案生成指标，返回代码检索结果及答案生成列表

data_path="dataset/$dataset/test_data_with_self_induction_rule.json"
rule_path="dataset/$dataset/test_rule.json" #没用
rule_dir="dataset/$dataset/test_rule_json"
index_dir="index/$dataset"
retriever_path="/mnt/publiccache/huggingface/bge-base-en-v1.5"

python main_rule.py --setting "retrieval" --dataset $dataset --data_path $data_path --rule_path $rule_path --rule_dir $rule_dir --retriever_path $retriever_path --model_path $model_path --index_dir $index_dir 




