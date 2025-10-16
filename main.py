from validator import validate_sql
from query_processor import (
    convert_to_relational_algebra,
    build_operator_graph,
    optimize_graph,
    generate_execution_plan
)
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

def main():
    METADATA = load_metadata()
    if METADATA is None:
        return

    print("\n" + "="*30)
    print("Processador de Consultas SQL")
    print("Digite 'sair' para terminar.")
    
    # HU1 - Interface com campo de entrada da consulta.
    # O loop abaixo serve como a interface de console para a entrada do usuário.
    while True:
        user_query = input("\nDigite sua consulta SQL: ")
        if user_query.lower() == 'sair':
            break
        
        # HU1 - Entrada e Validação da Consulta.
        is_valid = validate_sql(user_query, METADATA)
        
        if is_valid:
            print("\n--- Processamento da Consulta ---")
            
            # HU2 - Conversão para Álgebra Relacional
            algebra_expression = convert_to_relational_algebra(user_query)
            print(f"Álgebra Relacional: {algebra_expression}")

            # HU3 - Construção do Grafo de Operadores
            operator_graph = build_operator_graph(algebra_expression)
            # HU3 - Exibir o grafo na interface
            print("\nGrafo de Operadores (Não Otimizado):")
            print(operator_graph)

            # HU4 - Otimização da Consulta
            optimized_graph = optimize_graph(operator_graph, METADATA)
            # HU4 - Exibir o grafo otimizado
            print("\nGrafo de Operadores (Otimizado):")
            print(optimized_graph)
            
            # HU5 - Plano de Execução
            execution_plan = generate_execution_plan(optimized_graph)
            # HU5 - Exibir ordem de execução (plano de execução ordenado)
            print("\n--- Plano de Execução Ordenado ---")
            for i, step in enumerate(execution_plan, 1):
                print(f"{i}. {step}")

if __name__ == "__main__":
    main()