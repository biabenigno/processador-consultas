import re
import json

def load_metadata(filepath: str = "metadados.json"):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            print(f"Carregando metadados de '{filepath}'...")
            data = json.load(f)
            return {key.lower(): [attr.lower() for attr in value] for key, value in data.items()}
    except FileNotFoundError:
        print(f"ERRO CRÍTICO: O arquivo de metadados '{filepath}' não foi encontrado.")
        return None
    except json.JSONDecodeError:
        print(f"ERRO CRÍTICO: O arquivo '{filepath}' não é um JSON válido.")
        return None

# HU1 - Entrada e Validação da Consulta
def validate_sql(query: str, metadata: dict) -> bool:
    if metadata is None:
        print("Não foi possível validar a consulta pois os metadados não foram carregados.")
        return False
        
    print(f"Analisando a consulta: \"{query}\"")

    # HU1 - Requisito: Ignorar maiúsculas/minúsculas e espaços repetidos.
    normalized_query = ' '.join(query.lower().split())

    # HU1 - Requisito: Validar comandos.
    match = re.match(r"select\s+(.+)\s+from\s+(.+)", normalized_query)
    if not match:
        print(">>> ERRO: Estrutura da consulta inválida. Deve conter SELECT e FROM na ordem correta.")
        return False
    full_query_str = match.group(0)
    if 'join' in normalized_query and 'on' not in normalized_query:
        print(">>> ERRO: A consulta contém um JOIN mas não possui a cláusula ON.")
        return False

    # HU1 - Requisito: Suportar múltiplos JOINs.
    tables_in_query = re.findall(r'(?:from|join)\s+([a-z0-9_]+)', normalized_query)
    
    # HU1 - Requisito: Validar existência de Tabelas.
    valid_tables = {}
    for table in tables_in_query:
        if table not in metadata:
            print(f">>> ERRO: Tabela '{table}' não existe no modelo de dados.")
            return False
        valid_tables[table] = metadata[table]
    
    if not valid_tables:
        print(">>> ERRO: Nenhuma tabela válida foi encontrada na consulta.")
        return False
    print(">>> Tabelas validadas com sucesso:", list(valid_tables.keys()))

    # HU1 - Requisito: Validar existência de Atributos.
    query_without_literals = re.sub(r"\'(.*?)\'", " ", full_query_str)
    
    all_available_attributes = {attr for attributes in valid_tables.values() for attr in attributes}
    allowed_keywords = {"select", "from", "where", "join", "on", "and", "or"}
    attributes_to_check = re.findall(r'\b[a-z_][a-z0-9_.]+\b', query_without_literals)

    for attr in attributes_to_check:
        clean_attr = attr.split('.')[-1]
        if clean_attr not in all_available_attributes and clean_attr not in allowed_keywords and clean_attr not in valid_tables:
            if not clean_attr.isdigit():
                print(f">>> ERRO: Atributo '{clean_attr}' não foi encontrado nas tabelas declaradas.")
                return False
    print(">>> Atributos validados com sucesso.")

    # HU1 - Requisito: Validar Operadores (=, >, <, <=, >=, <>, AND, ( )).
    from_where_part = match.group(2)
    conditions_part = ' '.join(re.findall(r'(?:where|on)\s+(.*?)(?:\s+join|\s+on|\s*$)', from_where_part))
    potential_operators = re.sub(r"\'(.*?)\'", " ", conditions_part)
    potential_operators = re.sub(r"\b[a-z0-9_.]+\b", " ", potential_operators)
    tokens = potential_operators.split()
    
    allowed_operators = ['=', '>', '<', '<=', '>=', '<>', 'and', '(', ')']
    if 'or' in tokens:
        allowed_operators.append('or')

    for token in tokens:
        if token not in allowed_operators:
            print(f">>> ERRO: Operador ou sintaxe '{token}' não é válido.")
            return False
    print(">>> Operadores validados com sucesso.")
    
    print("\nConsulta VÁLIDA!")
    return True