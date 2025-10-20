import streamlit as st
import json
import io
import contextlib

from validator import validate_sql
from query_processor import (
    convert_to_relational_algebra,
    build_operator_graph,
    optimize_graph,
    generate_execution_plan
)

@st.cache_data 
def load_metadata(filepath: str = "metadados.json"):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return {key.lower(): [attr.lower() for attr in value] for key, value in data.items()}
    except FileNotFoundError:
        return None

st.set_page_config(layout="wide")
st.title("Processador de Consultas SQL")
st.write("Trabalho da Disciplina de Banco de Dados")

METADATA = load_metadata()

if METADATA is None:
    st.error("ERRO CRÍTICO: O arquivo 'metadados.json' não foi encontrado. A aplicação não pode continuar.")
else:
    # HU1 - Interface com campo de entrada da consulta
    user_query = st.text_area("Digite sua consulta SQL aqui:", height=150, placeholder="SELECT nome, email FROM cliente WHERE idcliente = 1")

    if st.button("Processar Consulta"):
        if user_query:
            # Captura toda a saída de 'print' para exibir na interface
            output_buffer = io.StringIO()
            with contextlib.redirect_stdout(output_buffer):
                # HU1 - Validação da Consulta
                is_valid = validate_sql(user_query, METADATA)
            
            # Pega o que foi capturado e exibe
            validation_output = output_buffer.getvalue()

            st.subheader("1. Validação (HU1)")
            st.code(validation_output, language='text')

            if is_valid:
                # Se for válida, executa as outras etapas
                st.subheader("2. Conversão para Álgebra Relacional (HU2)")
                algebra_expression = convert_to_relational_algebra(user_query)
                st.code(algebra_expression, language='text')

                st.subheader("3. Grafo de Operadores (HU3 e HU4)")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Grafo Não Otimizado (HU3):**")
                    operator_graph = build_operator_graph(algebra_expression)
                    st.code(str(operator_graph), language='text')
                
                with col2:
                    st.write("**Grafo Otimizado (HU4):**")
                    # Captura a saída da otimização também
                    opt_buffer = io.StringIO()
                    with contextlib.redirect_stdout(opt_buffer):
                        optimized_graph = optimize_graph(operator_graph, METADATA)
                    
                    st.code(opt_buffer.getvalue() + str(optimized_graph), language='text')

                st.subheader("5. Plano de Execução (HU5)")
                execution_plan = generate_execution_plan(optimized_graph)
                
                plan_str = ""
                for i, step in enumerate(execution_plan, 1):
                    plan_str += f"{i}. {step}\n"
                st.code(plan_str, language='text')

        else:
            st.warning("Por favor, digite uma consulta SQL antes de processar.")