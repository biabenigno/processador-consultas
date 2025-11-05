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

    #Requisito: Normalizar a query
    # query.lower(): Converte toda a string para minúsculas.
    # .split(): Quebra a string em uma lista de palavras (ex: ['select', 'nome', 'from', 'cliente'])
    # ' '.join(...): Junta a lista de volta, usando um único espaço como separador.
    normalized_query = ' '.join(query.lower().split())

    # Requisito: Validar comandos (SELECT ... FROM ...) ---
    match = re.match(r"select\s+(.+)\s+from\s+(.+)", normalized_query)
    
    # se 'match' for 'None', a query não começou com "select ... from ..."
    if not match:
        print(">>> ERRO: Estrutura da consulta inválida. Deve conter SELECT e FROM na ordem correta.")
        return False
        
    # pega o texto inteiro que foi "match"
    full_query_str = match.group(0)
    
    # validação de JOIN/ON
    if 'join' in normalized_query and 'on' not in normalized_query:
        print(">>> ERRO: A consulta contém um JOIN mas não possui a cláusula ON.")
        return False

    # Requisito: Suportar múltiplos JOINs
    #pega todas as tabelas usadas na query
    tables_in_query = re.findall(r'(?:from|join)\s+([a-z0-9_]+)', normalized_query)
    
    # Requisito: Validar existência de Tabelas
    valid_tables = {} # dicionário para as tabelas que são válidas.
    for table in tables_in_query:
        # verifica se a tabela extraída da query NÃO está no metadata
        if table not in metadata:
            print(f">>> ERRO: Tabela '{table}' não existe no modelo de dados.")
            return False
        # se existe, adiciona ao dicionário 'valid_tables'
        valid_tables[table] = metadata[table]
    
    # se nenhuma tabela válida foi encontrada
    if not valid_tables:
        print(">>> ERRO: Nenhuma tabela válida foi encontrada na consulta.")
        return False
    print(">>> Tabelas validadas com sucesso:", list(valid_tables.keys()))

    # Requisito: Validar existência de Atributos ---
    # remove literais de string da query completa
    query_without_literals = re.sub(r"\'(.*?)\'", " ", full_query_str)

    # cria um set com os atributos das as tabelas válidas.
    # !!!! isso é feito com "Set Comprehension" e um loop aninhado
    all_available_attributes = {attr for attributes in valid_tables.values() for attr in attributes}
    
    # palavras chave do sql permitidas
    allowed_keywords = {"select", "from", "where", "join", "on", "and", "or"}
    
    # pega todas as palavras que parecem ser atributos na query sem literais
    attributes_to_check = re.findall(r'\b[a-z_][a-z0-9_.]+\b', query_without_literals)

    # passa sobre cada atributo encontrado.
    for attr in attributes_to_check:
        # Pega apenas a parte final do atributo (ex: 'cliente.nome' = 'nome')
        clean_attr = attr.split('.')[-1]
        
        # se o atributo é invalido
        if clean_attr not in all_available_attributes and clean_attr not in allowed_keywords and clean_attr not in valid_tables:
            # e fnao for um número
            if not clean_attr.isdigit():
                print(f">>> ERRO: Atributo '{clean_attr}' não foi encontrado nas tabelas declaradas.")
                return False
    print(">>> Atributos validados com sucesso.")

    # Requisito: Validar Operadores (=, >, <, <=, >=, <>, AND, ( ))
    
    # pega a parte da query depois do 'from' 
    from_where_part = match.group(2)
    
    # pega só o texto que vem depois de 'where' ou 'on'.
    conditions_part = ' '.join(re.findall(r'(?:where|on)\s+(.*?)(?:\s+join|\s+on|\s*$)', from_where_part))
    
    # limpa a string de condições:
    # remove literais de string (ex: 'Aberto')
    potential_operators = re.sub(r"\'(.*?)\'", " ", conditions_part)
    # remove todos os nomes de atributos/tabelas
    potential_operators = re.sub(r"\b[a-z0-9_.]+\b", " ", potential_operators)
    
    # sobram operadores e parentesis
    tokens = potential_operators.split()
    
    # operadores permitidos
    allowed_operators = ['=', '>', '<', '<=', '>=', '<>', 'and', '(', ')']
    
    # permite 'or' tambem (embora não fosse requisito)
    if 'or' in tokens:
        allowed_operators.append('or')

    # verifica cada token
    for token in tokens:
        if token not in allowed_operators:
            print(f">>> ERRO: Operador ou sintaxe '{token}' não é válido.")
            return False
    print(">>> Operadores validados com sucesso.")
    
    print("\nConsulta VÁLIDA!")
    return True