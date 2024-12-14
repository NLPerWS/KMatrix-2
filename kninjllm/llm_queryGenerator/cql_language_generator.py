from typing import Any, Dict, List, Optional
from graphq_trans.sparql.translator import Translator as SparqlTranslator
from graphq_trans.ir.translator import Translator as IRTranslator


class Cql_language_generator:

    def __init__(
        self,
    ):
        pass
    
    def run(
        self,
        query: str
    ):
        # this query is sparql_query
        
        sparql_translator = SparqlTranslator() # Create a SparqlTranslator that translates SPARQL to graphqIR
        ir_translator = IRTranslator() # Create a IRTranslator that translates graphqIR to Cypher

        # query = 'SELECT DISTINCT ?e WHERE { ?e <pred:instance_of> ?c . ?c <pred:name> "human" } '

        ir = sparql_translator.to_ir(query) # translates sparql to ir
        cypher_query = ir_translator.to_cypher(ir) # translates ir to cypher
        
        # # 示例
        # res_query = '''
        #     MATCH (a:Officer {name:"Ross, Jr. - Wilbur Louis"})-[r:officer_of|intermediary_of|registered_address*..10]-(b)
        #     RETURN b.name as name LIMIT 20
        # '''
        
        return {"final_result":cypher_query}