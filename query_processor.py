import re

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

    def __repr__(self, level=0):
        ret = "\t" * level + f"[{self.node_type}] {self.value}" + "\n"
        for child in self.children:
            ret += child.__repr__(level + 1)
        return ret

# HU3 - Construção do Grafo de Operadores
def build_operator_graph(rel_alg_expr: str) -> Node:
    rel_alg_expr = rel_alg_expr.strip()
    pi_match = re.match(r'π\s+(.*?)\s*\((.*)\)', rel_alg_expr, re.DOTALL)
    sigma_match = re.match(r'σ\s+(.*?)\s*\((.*)\)', rel_alg_expr, re.DOTALL)
    if pi_match:
        attributes = pi_match.group(1).strip()
        child_expr = pi_match.group(2).strip()
        return Node("π", attributes, [build_operator_graph(child_expr)])
    elif sigma_match:
        condition = sigma_match.group(1).strip()
        child_expr = sigma_match.group(2).strip()
        return Node("σ", condition, [build_operator_graph(child_expr)])
    elif rel_alg_expr.startswith('(') and rel_alg_expr.endswith(')'):
        content = rel_alg_expr[1:-1]
        paren_level = 0
        split_index = -1
        for i, char in reversed(list(enumerate(content))):
            if char == ')':
                paren_level += 1
            elif char == '(':
                paren_level -= 1
            elif char == '⨝' and paren_level == 0:
                split_index = i
                break
        if split_index != -1:
            left_expr = content[:split_index].strip()
            rest = content[split_index + 1:].strip()
            rest_parts = rest.rsplit(' ', 1)
            condition = rest_parts[0].strip()
            right_expr = rest_parts[1].strip()
            return Node("⨝", condition, [build_operator_graph(left_expr), build_operator_graph(right_expr)])
    return Node("Tabela", rel_alg_expr)

# HU4 - Otimização da Consulta
def optimize_graph(node: Node, metadata: dict) -> Node:
    optimized_children = [optimize_graph(child, metadata) for child in node.children]
    node.children = optimized_children

    if node.node_type == 'σ' and node.children and node.children[0].node_type == '⨝':
        selection_node = node
        join_node = node.children[0]
        selection_condition = selection_node.value
        condition_without_literals = re.sub(r"\'(.*?)\'", " ", selection_condition)
        potential_attrs = re.findall(r'\b[a-z_][a-z0-9_.]+\b', condition_without_literals)
        attributes_in_condition = {attr.split('.')[-1] for attr in potential_attrs if not attr.isdigit()}
        left_child = join_node.children[0]
        right_child = join_node.children[1]
        left_attributes = set(metadata.get(left_child.value, []))
        right_attributes = set(metadata.get(right_child.value, []))

        if attributes_in_condition.issubset(left_attributes):
            join_node.children[0] = selection_node
            selection_node.children = [left_child] 
            return join_node
        elif attributes_in_condition.issubset(right_attributes):
            join_node.children[1] = selection_node
            selection_node.children = [right_child]
            return join_node
    return node

# HU5 - Geração do Plano de Execução
def generate_execution_plan(optimized_graph: Node) -> list:
    plan = []
    
    def post_order_traversal(node):
        for child in node.children:
            post_order_traversal(child)
        
        step = ""
        if node.node_type == 'Tabela':
            step = f"Acessar a tabela '{node.value}'."
        elif node.node_type == 'σ':
            step = f"Aplicar SELEÇÃO com a condição: {node.value}."
        elif node.node_type == '⨝':
            step = f"Realizar JUNÇÃO com a condição: {node.value}."
        elif node.node_type == 'π':
            step = f"Projetar os seguintes atributos: {node.value}."
        
        plan.append(step)

    post_order_traversal(optimized_graph)
    return plan