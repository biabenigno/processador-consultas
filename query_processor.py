import re
import html
import textwrap
from typing import List, Set, Dict, Any # Adicionei os imports de typing

# HU2 - Conversão para Álgebra Relacional
def convert_to_relational_algebra(query: str) -> str:
    normalized_query = ' '.join(query.lower().split())
    select_part = re.search(r'select\s+(.*?)\s+from', normalized_query).group(1)
    from_part = re.search(r'from\s+(.*?)(?:\s+where|$)', normalized_query).group(1)
    where_part_match = re.search(r'where\s+(.*)', normalized_query)
    where_part = where_part_match.group(1) if where_part_match else None
    base_table = from_part.split()[0]
    joins = re.findall(r'join\s+(.*?)\s+on\s+(.*?)(?=\s+join|$)', from_part)
    rel_alg_expr = base_table
    
    for join_table, on_condition in joins:
        rel_alg_expr = f"({rel_alg_expr} ⨝ {on_condition.strip()} {join_table.strip()})"
    
    if where_part:
        rel_alg_expr = f"σ {where_part.strip()} ({rel_alg_expr})"
        
    rel_alg_expr = f"π {select_part.strip()} ({rel_alg_expr})"
    return rel_alg_expr

# Estrutura de Dados (Nó) para o Grafo de Operadores (HU3, HU4, HU5)
class Node:
    def __init__(self, node_type, value, children=None):
        self.node_type = node_type
        self.value = value
        self.children = children if children is not None else []
        self.id = id(self)

    # Console
    def __repr__(self, level=0):
        ret = "\t" * level + f"[{self.node_type}] {self.value}" + "\n"
        for child in self.children:
            ret += child.__repr__(level + 1)
        return ret

    # Mermaid
    def to_mermaid(self):
        mermaid_string = '%%{init: {"theme": "dark"}}%%\n'
        mermaid_string += "graph TD;\n"
        mermaid_string += "    classDef default fontSize:12px,stroke-width:2px;\n"

        node_map = {}
        counter = 0

        #Recursão para ID
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

            node_value_escaped = html.escape(str(node.value))
            # Quebra de linha manual para valores longos
            wrapped_value = textwrap.fill(node_value_escaped, width=30).replace('\n', '<br/>')
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
    
# HU3 - Construção do Grafo de Operadores
def build_operator_graph(rel_alg_expr: str) -> Node:
    rel_alg_expr = rel_alg_expr.strip()
    
    # Tenta fazer match com Projeção (π)
    pi_match = re.match(r'π\s+(.*?)\s*\((.*)\)', rel_alg_expr, re.DOTALL | re.IGNORECASE)
    if pi_match:
        attributes = pi_match.group(1).strip()
        child_expr = pi_match.group(2).strip()
        return Node("π", attributes, [build_operator_graph(child_expr)])

    # Tenta fazer match com Seleção (σ)
    sigma_match = re.match(r'σ\s+(.*?)\s*\((.*)\)', rel_alg_expr, re.DOTALL | re.IGNORECASE)
    if sigma_match:
        condition = sigma_match.group(1).strip()
        child_expr = sigma_match.group(2).strip()
        return Node("σ", condition, [build_operator_graph(child_expr)])

    # Tenta fazer match com Junção (⨝)
    if rel_alg_expr.startswith('(') and rel_alg_expr.endswith(')'):
        content = rel_alg_expr[1:-1].strip()
        paren_level = 0
        split_index = -1
        
        # Encontra o operador de junção principal (⨝) lendo de trás para frente
        for i, char in reversed(list(enumerate(content))):
            if char == ')': paren_level += 1
            elif char == '(': paren_level -= 1
            elif char == '⨝' and paren_level == 0:
                split_index = i
                break
                
        if split_index != -1:
            left_expr = content[:split_index].strip()
            rest = content[split_index + 1:].strip()
            
            # Tenta extrair a condição da junção
            # (Isso assume "expr ⨝ cond expr")
            parts = rest.split(' ', 1)
            if len(parts) == 2:
                # Tenta dividir de forma mais robusta
                # Encontra o último espaço antes do nome da tabela final
                condition = ""
                right_expr = ""
                
                # Heurística para separar "condicao" de "tabela"
                # Isso é frágil, um parser de verdade seria melhor
                rest_parts = rest.rsplit(' ', 1)
                if len(rest_parts) == 2:
                    condition = rest_parts[0].strip()
                    right_expr = rest_parts[1].strip()
                else: # Se não houver espaço, assume que é só a tabela
                    condition = "Junção Natural"
                    right_expr = rest
                    
                return Node("⨝", condition, [build_operator_graph(left_expr), build_operator_graph(right_expr)])

    # Se não for nenhum dos anteriores, é um nó folha (Tabela)
    return Node("Tabela", rel_alg_expr)

# HU4 - Otimização da Consulta
def get_attributes_from_string(text_str: str) -> set:
    # Normaliza para minúsculas para consistência
    text_str_lower = text_str.lower()
    text_without_literals = re.sub(r"\'(.*?)\'", " ", text_str_lower)
    potential_attrs = re.findall(r'\b[a-z_][a-z0-9_.]+\b', text_without_literals)
    # Pega apenas o nome da coluna (ex: 'cliente.nome' -> 'nome')
    return {attr.split('.')[-1] for attr in potential_attrs if not attr.isdigit()}

def _collect_all_attributes(node: Node) -> set:
    attrs = get_attributes_from_string(node.value)
    for child in node.children:
        attrs.update(_collect_all_attributes(child))
    return attrs

# --- ESTA É A FUNÇÃO CORRIGIDA ---
def optimize_graph(node: Node, metadata: dict, needed_attrs: set) -> Node:
    """
    Função principal que orquestra as otimizações heurísticas.
    Recebe os atributos necessários (needed_attrs) do nó raiz.
    """
    print(">>> Otimização: Iniciando...")
    
    # 1. A coleta de atributos agora é feita no streamlit_app.py
    #    A linha 'needed_attrs = get_attributes_from_string(node.value)' foi REMOVIDA.
    
    # 2. Aplica a heurística de empurrar seleções.
    optimized_node = _push_selections_down(node, metadata)
    
    # 3. Aplica a heurística de adicionar projeções intermediárias.
    #    Usa o 'needed_attrs' recebido como argumento.
    final_optimized_node = _add_intermediate_projections(optimized_node, metadata, needed_attrs)
    
    return final_optimized_node
# --- FIM DA CORREÇÃO ---


def _push_selections_down(node: Node, metadata: dict) -> Node:
    if not node.children:
        return node

    # Otimiza os filhos primeiro
    node.children = [_push_selections_down(child, metadata) for child in node.children]

    # Padrão: σ (Seleção) sobre ⨝ (Junção)
    if node.node_type == 'σ' and node.children and node.children[0].node_type == '⨝':
        selection_node = node
        join_node = node.children[0]
        # Divide condições 'AND'
        conditions = re.split(r'\s+and\s+', selection_node.value, flags=re.IGNORECASE)
        pushed_conditions = {'left': [], 'right': [], 'stay': []}
        
        left_child, right_child = join_node.children
        
        def get_tables(n):
            """Função auxiliar para encontrar todas as tabelas abaixo de um nó."""
            if n.node_type == 'Tabela': 
                return {n.value.lower()} # Normaliza para minúsculas
            tables = set()
            for c in n.children: 
                tables.update(get_tables(c))
            return tables
        
        # Pega todos os atributos de todas as tabelas em cada lado
        left_tables = get_tables(left_child)
        right_tables = get_tables(right_child)
        
        # Usa os metadados (já em minúsculas)
        left_attributes = {attr for tbl in left_tables for attr in metadata.get(tbl, [])}
        right_attributes = {attr for tbl in right_tables for attr in metadata.get(tbl, [])}

        for cond in conditions:
            cond_attrs = get_attributes_from_string(cond)
            
            is_left = cond_attrs.issubset(left_attributes)
            is_right = cond_attrs.issubset(right_attributes)

            if is_left and not is_right:
                pushed_conditions['left'].append(cond)
            elif is_right and not is_left:
                pushed_conditions['right'].append(cond)
            else:
                # Fica se usar atributos de ambos os lados, ou de nenhum (ex: 1=1)
                pushed_conditions['stay'].append(cond)
        
        # Reconstrói a árvore
        if pushed_conditions['left']:
            join_node.children[0] = Node("σ", " AND ".join(pushed_conditions['left']), [left_child])
        if pushed_conditions['right']:
            join_node.children[1] = Node("σ", " AND ".join(pushed_conditions['right']), [right_child])
        
        if pushed_conditions['stay']:
            # Se sobraram condições, atualiza o nó de seleção
            selection_node.value = " AND ".join(pushed_conditions['stay'])
            selection_node.children = [join_node]
            return selection_node
        else:
            # Se não sobraram, remove o nó de seleção
            return join_node
            
    return node

def _add_intermediate_projections(node: Node, metadata: dict, needed_attrs: set) -> Node:
    if not node.children:
        return node
    
    # Atributos que o nó atual precisa (ex: condição de junção)
    current_node_attrs = get_attributes_from_string(node.value)
    
    # Filhos precisam fornecer o que os pais precisam + o que o nó atual precisa
    new_needed_attrs = needed_attrs | current_node_attrs
    
    if node.node_type == '⨝':
        for i, child in enumerate(node.children):
            
            def get_tables(n): # (Duplicada, idealmente seria refatorada)
                if n.node_type == 'Tabela': return {n.value.lower()}
                tables = set()
                for c in n.children: tables.update(get_tables(c))
                return tables
            
            child_tables = get_tables(child)
            child_attributes = {attr for tbl in child_tables for attr in metadata.get(tbl, [])}
            
            # Intersecção: o que é necessário (pais) E o que o filho fornece
            projection_attrs = new_needed_attrs & child_attributes

            # Insere projeção se for útil (remove colunas)
            if projection_attrs and projection_attrs != child_attributes:
                # Só insere se o filho ainda não for uma projeção idêntica
                if not (child.node_type == 'π' and get_attributes_from_string(child.value) == projection_attrs):
                     node.children[i] = Node("π", ", ".join(sorted(list(projection_attrs))), [child])

    # Continua a recursão para os filhos
    node.children = [_add_intermediate_projections(c, metadata, new_needed_attrs) for c in node.children]
    return node

# HU5 - Geração do Plano de Execução
def generate_execution_plan(optimized_graph: Node) -> list:
    plan = []
    def post_order_traversal(node):
        for child in node.children:
            post_order_traversal(child)
        step = ""
        if node.node_type == 'Tabela': step = f"Acessar a tabela '{node.value}'."
        elif node.node_type == 'σ': step = f"Aplicar SELEÇÃO com a condição: {node.value}."
        elif node.node_type == '⨝': step = f"Realizar JUNÇÃO com a condição: {node.value}."
        elif node.node_type == 'π': step = f"Projetar os seguintes atributos: {node.value}."
        plan.append(step)
    post_order_traversal(optimized_graph)
    return plan

