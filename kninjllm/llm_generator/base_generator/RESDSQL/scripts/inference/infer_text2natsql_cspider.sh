
# sh scripts/inference/infer_text2natsql_cspider.sh
set -e

root_path=$1
dbInfo=$2
device=$3
model_path=$4

echo "-------------------------------------------"
echo "$root_path"
echo "$dbInfo"
echo "$device"
echo "$model_path"

# 测试数据json
input_dataset_path="./data/dev.json"
# 知识库本体描述文件
table_path="./data/tables.json"
# 知识库路径
db_path="./database"
# 生成结果路径
output="./predictions/pred.sql"

# 中间文件?
tables_for_natsql="./data/test_tables_for_natsql.json"

text2natsql_model="base"
if [ "$text2natsql_model" = "base" ]
then
    text2natsql_model_save_path="$model_path/text2natsql-t5-base/checkpoint-14352"
    
    text2natsql_model_bs=16
elif [ "$text2natsql_model" = "large" ]
then
    text2natsql_model_save_path="$model_path/text2natsql-mt5-large-cspider/checkpoint-73691"
    text2natsql_model_bs=8
elif [ "$text2natsql_model" = "3b" ]
then
    text2natsql_model_save_path="$model_path/text2sql-t5-3b/checkpoint-103292"
    text2natsql_model_bs=6
else
    echo "The first arg must be in [base, large, 3b]."
    exit
fi

model_name="resdsql_$1_natsql"


# prepare table file for natsql 直接赋值
python NatSQL/table_transform.py \
    --in_file $table_path \
    --out_file $tables_for_natsql \
    --correct_col_type \
    --remove_start_table  \
    --analyse_same_column \
    --table_transform \
    --correct_primary_keys \
    --use_extra_col_types \
    --db_path $db_path \
    --root_path $root_path \
    --dbInfo $dbInfo

echo "table_transform.py OK !!!"

# preprocess test set 直接赋值
python preprocessing.py \
    --mode "test" \
    --table_path $table_path \
    --input_dataset_path $input_dataset_path \
    --output_dataset_path "./data/preprocessed_test_natsql.json" \
    --db_path $db_path \
    --target_type "natsql" \
    --root_path $root_path \
    --dbInfo $dbInfo

echo "preprocessing.py OK !!!"

# predict probability for each schema item in the test set
python schema_item_classifier.py \
    --batch_size 32 \
    --device $device \
    --seed 42 \
    --save_path "$model_path/text2natsql_schema_item_classifier" \
    --dev_filepath "./data/preprocessed_test_natsql.json" \
    --output_filepath "./data/test_with_probs_natsql.json" \
    --use_contents \
    --mode "test"

echo "schema_item_classifier.py OK !!!"

# generate text2natsql test set
python text2sql_data_generator.py \
    --input_dataset_path "./data/test_with_probs_natsql.json" \
    --output_dataset_path "./data/resdsql_test_natsql.json" \
    --topk_table_num 4 \
    --topk_column_num 5 \
    --mode "test" \
    --use_contents \
    --output_skeleton \
    --target_type "natsql"

echo "text2sql_data_generator.py OK !!!"

# inference using the best text2natsql ckpt  直接赋值
python text2sql.py \
    --batch_size $text2natsql_model_bs \
    --device $device \
    --seed 42 \
    --save_path $text2natsql_model_save_path \
    --mode "test" \
    --dev_filepath "./data/resdsql_test_natsql.json" \
    --original_dev_filepath $input_dataset_path \
    --db_path $db_path \
    --tables_for_natsql $tables_for_natsql \
    --num_beams 8 \
    --num_return_sequences 8 \
    --target_type "natsql" \
    --output $output \
    --root_path $root_path \
    --dbInfo $dbInfo

echo "text2sql.py OK !!!"
