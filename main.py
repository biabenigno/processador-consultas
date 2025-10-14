def validate_sql(query: str) -> bool:
    print("-" * 30)
    print(f"Analisando a consulta: \"{query}\"")

    # HU1: Ignorar maiúsculas/minúsculas e espaços repetidos 
    normalized_query = ' '.join(query.lower().split())

    # HU1: Validar comandos (SELECT, FROM, WHERE, JOIN, ON) 
    # A regex abaixo valida a estrutura básica e a ordem dos comandos.
    match = re.match(r"select\s+(.+)\s+from\s+(.+)", normalized_query)
    if not match:
        print(">>> ERRO: Estrutura da consulta inválida. Deve conter SELECT e FROM na ordem correta.")
        return False
        
    full_query_str = match.group(0)
    select_part = match.group(1).split('from')[0].strip()
    from_where_part = match.group(2)
    
    # HU1: Suportar múltiplos JOINs (0, 1,...,N) 
    # A lógica abaixo extrai todas as tabelas, tanto do FROM quanto dos JOINs.
    tables_in_query = re.findall(r'(?:from|join)\s+([a-z0-9_]+)', 'from ' + from_where_part)
    
    # HU1: Validar existência de Tabelas 
    valid_tables = {}
    for table in tables_in_query:
        if table not in METADATA:
            print(f">>> ERRO: Tabela '{table}' não existe no modelo de dados.")
            return False
        valid_tables[table] = METADATA[table]
    
    if not valid_tables:
        print(">>> ERRO: Nenhuma tabela válida foi encontrada na consulta.")
        return False
    print(">>> Tabelas validadas com sucesso:", list(valid_tables.keys()))

    # HU1: Validar existência de Atributos 
    all_available_attributes = {attr for attributes in valid_tables.values() for attr in attributes}
    allowed_keywords = {"select", "from", "where", "join", "on", "and", "or"}
    # A regex abaixo busca por todos os possíveis atributos, incluindo o formato tabela.atributo
    attributes_to_check = re.findall(r'\b[a-z_][a-z0-9_.]+\b', full_query_str)

    for attr in attributes_to_check:
        clean_attr = attr.split('.')[-1]
        if clean_attr not in all_available_attributes and clean_attr not in allowed_keywords and clean_attr not in valid_tables:
            # Ignora valores numéricos que podem ser capturados pela regex
            if not clean_attr.isdigit():
                print(f">>> ERRO: Atributo '{clean_attr}' não foi encontrado nas tabelas declaradas.")
                return False
    print(">>> Atributos validados com sucesso.")

    # HU1: Validar Operadores (=, >, <, <=, >=, <>, AND, ( )) 
    # Extrai as cláusulas de condição (WHERE e ON)
    conditions_part = ' '.join(re.findall(r'(?:where|on)\s+(.*?)(?:\s+join|\s+on|\s*$)', from_where_part))
    
    # Remove tudo que for válido (atributos, números, strings) para sobrar apenas os símbolos e palavras de operação
    potential_operators = re.sub(r"\'(.*?)\'", " ", conditions_part)
    potential_operators = re.sub(r"\b[a-z0-9_.]+\b", " ", potential_operators)
    tokens = potential_operators.split()
    
    allowed_operators = ['=', '>', '<', '<=', '>=', '<>', 'and', '(', ')']
    # O operador 'or' não estava na lista original, mas é comum estar junto com 'and'
    if 'or' in tokens:
        allowed_operators.append('or')

    for token in tokens:
        if token not in allowed_operators:
            print(f">>> ERRO: Operador ou sintaxe '{token}' não é válido.")
            return False
    print(">>> Operadores validados com sucesso.")
    
    print("\nConsulta VÁLIDA!")
    return True