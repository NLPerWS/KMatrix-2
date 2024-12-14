from .natsql2sql.natsql_parser import create_sql_from_natSQL
from .natsql2sql.natsql2sql import Args
import traceback

natsql2sql_args = Args()
natsql2sql_args.not_infer_group = True

def natsql_to_sql(natsql, db_id, db_file_path, table_info,root_path,dbInfo):
    try:
        query, _, __ = create_sql_from_natSQL(
            natsql, 
            db_id, 
            db_file_path, 
            table_info, 
            sq=None, 
            remove_values=False, 
            remove_groupby_from_natsql=False, 
            args=natsql2sql_args,
            root_path=root_path,
            dbInfo=dbInfo
        )
    except:
        traceback.print_exc()
        query = "sql placeholder"
    
    if query == None:
        query = "sql placeholder"
    
    return query