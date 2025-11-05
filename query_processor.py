import re
import textwrap 
from typing import List, Dict

# Conversão para Álgebra Relacional (HU2)
def convert_to_relational_algebra(query: str) -> str:
    # converte tudo para minúsculo
    normalized_query = ' '.join(query.lower().split())
    
    # extrai as partes da query usando regex
    # re.search() encontra o primeiro padrão que bater, o .group(1) pega o conteúdo do primeiro parentesis (.*?)
    
    # pega o que ta entre "select" e "from"
    select_part = re.search(r'select\s+(.*?)\s+from', normalized_query).group(1)
    
    # pega o que ta entre "from" e "where" ou o fim da string
    from_part = re.search(r'from\s+(.*?)(?:\s+where|$)', normalized_query).group(1)
    
    # procuta o "where", pode nao existir.
    where_part_match = re.search(r'where\s+(.*)', normalized_query)
    #se 'where_part_match' não for 'None', pega o conteúdo dela (grupo 1)
    where_part = where_part_match.group(1) if where_part_match else None
    
    # álgebra Relacional (de dentro para fora).
    # começa com a primeira tabela da cláusula FROM.
    base_table = from_part.split()[0]
    
    # encontra todos os "join ... on ..." na parte "from".
    # re.findall() retorna uma lista de tuplas, onde cada tupla contém os grupos de captura.
    joins = re.findall(r'join\s+(.*?)\s+on\s+(.*?)(?=\s+join|$)', from_part)
    
    # inicia a expressão com a tabela base.
    rel_alg_expr = base_table
    
    # itera sobre cada join encontrado
    for join_table, on_condition in joins:
        # dai pega a expressão atual (rel_alg_expr) e junta com a nova tabela.
        rel_alg_expr = f"({rel_alg_expr} ⨝ {on_condition.strip()} {join_table.strip()})"
    
    # Se uma WHERE foi encontrada, junta a expressão com um Sigma (σ).
    if where_part:
        rel_alg_expr = f"σ {where_part.strip()} ({rel_alg_expr})"
        
    # dai junta a expressão com o Pi (π) da cláusula SELECT.
    rel_alg_expr = f"π {select_part.strip()} ({rel_alg_expr})"
    
    return rel_alg_expr

#Grafo de Operadores (HU3 e HU4)
class Node:
    def __init__(self, node_type, value, children=None):
        # tipo de nó (π , σ , ⨝, Tabela)
        self.node_type = node_type
        # valor ou condição do nó (ex: "cliente.nome" ou "id = 1")
        self.value = value
        # a lista de nós filhos 
        self.children = children if children is not None else []
        #id (debug)
        self.id = id(self)

    # imprimir o nó no console (debug).
    def __repr__(self, level=0):
        ret = "\t" * level + f"[{self.node_type}] {self.value}" + "\n"
        for child in self.children:
            ret += child.__repr__(level + 1)
        return ret

    # converter a árvore pro mermaid
    def to_mermaid(self):
        mermaid_string = '%%{init: {"theme": "dark"}}%%\n'
        mermaid_string += "graph TD;\n"
        mermaid_string += "    classDef default fontSize:12px,stroke-width:2px;\n"
        node_map = {}
        counter = 0
        def map_nodes(node):
            nonlocal counter 
            if node not in node_map:
                node_map[node] = f"N{counter}"
                counter += 1
                for child in node.children:
                    map_nodes(child)
        map_nodes(self)    
        rendered_nodes = set()
        def build_mermaid_string_v2(node):
            nonlocal mermaid_string
            short_id = node_map.get(node)
            if not short_id or short_id in rendered_nodes:
                return
            node_value_safe = str(node.value).replace('"', '&quot;')
            wrapped_value = textwrap.fill(node_value_safe, width=30).replace('\n', '<br/>')
            node_label = f'{node.node_type}<br/>{wrapped_value}'
            mermaid_string += f'    {short_id}(["{node_label}"]);\n'
            rendered_nodes.add(short_id)
            for child in node.children:
                child_short_id = node_map.get(child)
                if child_short_id:
                    mermaid_string += f'    {short_id} --> {child_short_id};\n'
                    build_mermaid_string_v2(child)
        build_mermaid_string_v2(self)
        return mermaid_string
    
#Grafo de Operadores (HU3)
def build_operator_graph(rel_alg_expr: str) -> Node:
    # remove os espaços em branco no começo e no fim
    rel_alg_expr = rel_alg_expr.strip()
    
    # tenta dar "match" com o padrão de pi
    # re.DOTALL faz com que o '.' (ponto) também inclua quebras de linha
    # re.IGNORECASE ignora maiúsculas/minúsculas
    pi_match = re.match(r'π\s+(.*?)\s*\((.*)\)', rel_alg_expr, re.DOTALL | re.IGNORECASE)
    if pi_match:
        attributes = pi_match.group(1).strip() # os atributos
        child_expr = pi_match.group(2).strip()  # o resto da expressão
        # Retorna um nó pi e chama recursivamente a função para construir o filho
        return Node("π", attributes, [build_operator_graph(child_expr)])

    # Se não for pi, tenta dar "match" com o padrão de seleção
    sigma_match = re.match(r'σ\s+(.*?)\s*\((.*)\)', rel_alg_expr, re.DOTALL | re.IGNORECASE)
    if sigma_match:
        condition = sigma_match.group(1).strip() #  condição
        child_expr = sigma_match.group(2).strip()  # o resto da expressão
        # Retorna um nó 'σ' e chama recursivamente a função para construir o filho
        return Node("σ", condition, [build_operator_graph(child_expr)])

    # Se não for π ou σ, tenta dar "match" com Junção
    # junções sempre começam e terminam com parênteses
    if rel_alg_expr.startswith('(') and rel_alg_expr.endswith(')'):
        #remove os parênteses externos
        content = rel_alg_expr[1:-1].strip()
        paren_level = 0 # contador para rastrear parênteses
        split_index = -1 # divisão da string
        
        # itera de trás para frente para encontrar o *último* ⨝ 
        for i, char in reversed(list(enumerate(content))):
            if char == ')': paren_level += 1
            elif char == '(': paren_level -= 1
            # se ele acha um ⨝ e não esta dentro de parênteses
            elif char == '⨝' and paren_level == 0:
                split_index = i # encontra o ponto de divisão
                break
                
        # se achar um ponto de divisão...
        if split_index != -1:
            left_expr = content[:split_index].strip() # O que está à esquerda do ⨝
            rest = content[split_index + 1:].strip()  # O que está à direita
            
            # divide o 'rest' na condição e na tabela direita
            rest_parts = rest.rsplit(' ', 1)
            if len(rest_parts) == 2:
                condition = rest_parts[0].strip() # condição
                right_expr = rest_parts[1].strip() #tabela/expressão da direita
                # Retorna um nó '⨝' e chama recursivamente para os dois filhos
                return Node("⨝", condition, [build_operator_graph(left_expr), build_operator_graph(right_expr)])
            else:
                return Node("⨝", "condição?", [build_operator_graph(left_expr), build_operator_graph(rest)])

    # se não for π, σ, ou ⨝, deve ser um nó Tabela que não tem filhos
    return Node("Tabela", rel_alg_expr)

# Otimização (HU4)
def get_attributes_from_string(text_str: str) -> set:
    # minusculo de novo
    text_str_lower = text_str.lower()
    # remove literais de string substituindo por espaço
    text_without_literals = re.sub(r"\'(.*?)\'", " ", text_str_lower)
    # pega todas as "palavras" que parecem atributos
    potential_attrs = re.findall(r'\b[a-z_][a-z0-9_.]+\b', text_without_literals)
    
    # Cria um conjunto (set) para evitar duplicatas:
    # 1. 'attr.split('.')[-1]' pega apenas a última parte ('nome')
    # 2. 'if not attr.isdigit()' filtra números
    return {attr.split('.')[-1] for attr in potential_attrs if not attr.isdigit()}

def _collect_all_attributes(node: Node) -> set:
    attrs = get_attributes_from_string(node.value)
    # itera sobre os filhos e chama a si mesma
    for child in node.children:
        # .update() adiciona todos os itens do conjunto retornado 
        attrs.update(_collect_all_attributes(child))
    # Retorna o conjunto completo de atributos
    return attrs

def optimize_graph(node: Node, metadata: Dict[str, List[str]], needed_attrs: set) -> Node:
    print(">>> Otimização: Iniciando...")
    #Aplica a heurística de "Empurrar Seleções" (Selection Pushdown)
    optimized_node = _push_selections_down(node, metadata)
    
    # Aplica a heurística de "Adicionar Projeções Intermediárias"
    # insere 'π' para descartar colunas desnecessárias o mais cedo possível.
    final_optimized_node = _add_intermediate_projections(optimized_node, metadata, needed_attrs)
    
    # Retorna a raiz da nova árvore, agora otimizada.
    return final_optimized_node


def _push_selections_down(node: Node, metadata: Dict[str, List[str]]) -> Node:
    # se for um nó folha (Tabela) não tem filhos para otimizar
    if not node.children:
        return node

    # otimiza os filhos primeiro
    node.children = [_push_selections_down(child, metadata) for child in node.children]

    # verifica se o nó atual é um 'σ' (Seleção) e se seu filho é um '⨝' (Junção)
    if node.node_type == 'σ' and node.children and node.children[0].node_type == '⨝':
        
        # renomeia os nós 
        selection_node = node
        join_node = node.children[0]
        
        # divide as condições do 'σ' em uma lista
        conditions = re.split(r'\s+and\s+', selection_node.value, flags=re.IGNORECASE)
        
        #separa as condições
        pushed_conditions = {'left': [], 'right': [], 'stay': []}
        
        # pega os filhos da junção 
        left_child, right_child = join_node.children
        
        # encontra todas as tabelas abaixo de um nó
        def get_tables(n):
            if n.node_type == 'Tabela':
                return {n.value.lower()} 
            tables = set()
            for c in n.children: 
                tables.update(get_tables(c))
            return tables
        
        # pega todas as tabelas nos ramos esquerdo e direito
        left_tables = get_tables(left_child)
        right_tables = get_tables(right_child)
        
        # usa os metadados para encontrar TODOS os atributos disponíveis em cada lado
        left_attributes = {attr for tbl in left_tables for attr in metadata.get(tbl, [])}
        right_attributes = {attr for tbl in right_tables for attr in metadata.get(tbl, [])}

        # itera sobre cada condição
        for cond in conditions:
            # pega os atributos da condição
            cond_attrs = get_attributes_from_string(cond)
            
            # .issubset() verifica se todos os itens de estão no conjunto
            is_left = cond_attrs.issubset(left_attributes)
            is_right = cond_attrs.issubset(right_attributes)

            # se os atributos SÓ existem na esquerda
            if is_left and not is_right:
                pushed_conditions['left'].append(cond)
            #se os atributos SÓ existem na direita
            elif is_right and not is_left:
                pushed_conditions['right'].append(cond)
            # ou se usa atributos de ambos  ou de nenhum
            else:
                pushed_conditions['stay'].append(cond)
        
        # reconstrução da árvore
        
        # se houver condições para o lado esquerdo
        if pushed_conditions['left']:
            # cria um novo nó 'σ' com essas condições
            # e o insere entre a junção (join_node) e seu filho esquerdo (left_child)
            join_node.children[0] = Node("σ", " AND ".join(pushed_conditions['left']), [left_child])
        
        # se houver condições para o lado direito
        if pushed_conditions['right']:
            # cria um novo nó 'σ' com essas condições
            # e o insere entre a junção (join_node) e seu filho direito (right_child)
            join_node.children[1] = Node("σ", " AND ".join(pushed_conditions['right']), [right_child])
        
        # verifica se sobraram condições para o nó de seleção original
        if pushed_conditions['stay']:
            # se sobraram condições, atualiza o nó de seleção original com apenas essas condições
            selection_node.value = " AND ".join(pushed_conditions['stay'])
            selection_node.children = [join_node] #o filho dele continua sendo a junção
            return selection_node # mantém o 'σ' na árvore
        else:
            # Se não sobraram condições, remove o nó 'σ' original da árvore, retornando a junção em seu lugar.
            return join_node
            
    # se não for o padrão σ -> ⨝, apenas retorna o nó
    return node

def _add_intermediate_projections(node: Node, metadata: Dict[str, List[str]], needed_attrs: set) -> Node:
    
    # se for um nó tabela, para.
    if not node.children:
        return node

    #  atributos que o nó ATUAL precisa
    current_node_attrs = get_attributes_from_string(node.value)
    
    # atributos que os filhos deste nó precisam fornecer:
    # a união do que os pais precisam (needed_attrs) + o que o nó atual precisa.
    new_needed_attrs = needed_attrs | current_node_attrs

    # chama a recursão PRIMEIRO nos filhos
    node.children = [_add_intermediate_projections(c, metadata, new_needed_attrs) for c in node.children]

    #depois que os filhos foram processados, insere projeções ACIMA deles.
    if node.node_type == '⨝':
        for i, child in enumerate(node.children):
            def get_tables(n): 
                if n.node_type == 'Tabela': return {n.value.lower()}
                tables = set()
                for c in n.children: tables.update(get_tables(c))
                return tables
            
            child_tables = get_tables(child)
            # todos os atributos da sub-árvore filha
            child_attributes = {attr for tbl in child_tables for attr in metadata.get(tbl, [])}

            # Intersecção do que é necessário "para cima" (new_needed_attrs)
            # E o que o filho pode fornecer (child_attributes)
            projection_attrs = new_needed_attrs & child_attributes
            

            if projection_attrs:
                # evita projeções redundantes
                child_attrs = set()
                if child.node_type == 'π':
                    child_attrs = get_attributes_from_string(child.value)

                # se a projeção calculada for diferente da projeção do filho...
                if child_attrs != projection_attrs:
                     # insere um novo nó 'π' entre o '⨝' e seu 'child'
                     node.children[i] = Node("π", ", ".join(sorted(list(projection_attrs))), [child])
    
    return node

# Plano de Execução (HU5)
def generate_execution_plan(optimized_graph: Node) -> list:
    # lista para armazenar os passos
    plan = []
    
    # define uma função interna recursiva
    def post_order_traversal(node):
        # vsita os filhos 
        for child in node.children:
            post_order_traversal(child)
            
        # depois que os filhos foram processados, processa o nó atual
        step = ""
        if node.node_type == 'Tabela':
            step = f"Acessar a tabela '{node.value}'."
        elif node.node_type == 'σ':
            step = f"Aplicar SELEÇÃO com a condição: {node.value}."
        elif node.node_type == '⨝':
            step = f"Realizar JUNÇÃO com a condição: {node.value}."
        elif node.node_type == 'π':
            step = f"Projetar os seguintes atributos: {node.value}."
        
        # adiciona o passo à lista do plano
        plan.append(step)
        
    # inicia a travessia a partir da raiz do grafo
    post_order_traversal(optimized_graph)
    
    # retorna a lista de passos
    return plan