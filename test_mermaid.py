import streamlit as st
import json
import io
import contextlib
import base64
import requests
from PIL import Image

# Importa as funções dos seus outros arquivos
from validator import validate_sql
from query_processor import (
    convert_to_relational_algebra,
    build_operator_graph,
    optimize_graph,
    generate_execution_plan
)

# --- Função para carregar os metadados ---
@st.cache_data
def load_metadata(filepath: str = "metadados.json"):
    # ... (código inalterado) ...
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return {key.lower(): [attr.lower() for attr in value] for key, value in data.items()}
    except FileNotFoundError:
        return None

# --- NOVA FUNÇÃO para renderizar o Mermaid como imagem ---
@st.cache_data # Usamos cache para não buscar a mesma imagem toda hora
def render_mermaid_to_image(mermaid_code: str):
    """
    Converte um código Mermaid em uma imagem usando o serviço mermaid.ink.
    """
    try:
        graphbytes = mermaid_code.encode("utf8")
        base64_bytes = base64.urlsafe_b64encode(graphbytes)
        base64_string = base64_bytes.decode("ascii")
        url = 'https://mermaid.ink/img/' + base64_string
        
        response = requests.get(url)
        # Verifica se a requisição foi bem sucedida
        response.raise_for_status()
        
        # Retorna a imagem aberta com a biblioteca Pillow
        return Image.open(io.BytesIO(response.content))
    except requests.exceptions.RequestException as e:
        st.error(f"Erro ao contatar o serviço de renderização de imagem: {e}")
        return None


# --- Início da Interface Gráfica ---
st.set_page_config(layout="wide")
st.title("⚙️ Processador de Consultas SQL")
st.write("Trabalho da Disciplina de Banco de Dados")

METADATA = load_metadata()

if METADATA is None:
    st.error("ERRO CRÍTICO: O arquivo 'metadados.json' não foi encontrado. A aplicação não pode continuar.")
else:
    user_query = st.text_area("Digite sua consulta SQL aqui:", height=150, placeholder="SELECT nome, email FROM cliente WHERE idcliente = 1")

    if st.button("Processar Consulta"):
        if user_query:
            # ... (Validação e Álgebra Relacional continuam iguais) ...
            output_buffer = io.StringIO()
            with contextlib.redirect_stdout(output_buffer):
                is_valid = validate_sql(user_query, METADATA)
            validation_output = output_buffer.getvalue()
            st.subheader("1. Validação (HU1)")
            st.code(validation_output, language='text')

            if is_valid:
                st.subheader("2. Conversão para Álgebra Relacional (HU2)")
                algebra_expression = convert_to_relational_algebra(user_query)
                st.code(algebra_expression, language='text')

                st.subheader("3. Grafo de Operadores (HU3 e HU4)")
                col1, col2 = st.columns(2)
                
                # --- LÓGICA DE EXIBIÇÃO MODIFICADA ---
                with col1:
                    st.write("**Grafo Não Otimizado (HU3):**")
                    operator_graph = build_operator_graph(algebra_expression)
                    mermaid_unoptimized = operator_graph.to_mermaid()
                    # Gera e exibe a imagem do grafo
                    image_unoptimized = render_mermaid_to_image(mermaid_unoptimized)
                    if image_unoptimized:
                        st.image(image_unoptimized)
                
                with col2:
                    st.write("**Grafo Otimizado (HU4):**")
                    opt_buffer = io.StringIO()
                    with contextlib.redirect_stdout(opt_buffer):
                        optimized_graph = optimize_graph(operator_graph, METADATA)
                    
                    optimization_log = opt_buffer.getvalue()
                    if optimization_log:
                        st.text(optimization_log)

                    mermaid_optimized = optimized_graph.to_mermaid()
                    # Gera e exibe a imagem do grafo
                    image_optimized = render_mermaid_to_image(mermaid_optimized)
                    if image_optimized:
                        st.image(image_optimized)

                # ... (Plano de Execução continua o mesmo) ...
                st.subheader("5. Plano de Execução (HU5)")
                execution_plan = generate_execution_plan(optimized_graph)
                plan_str = ""
                for i, step in enumerate(execution_plan, 1):
                    plan_str += f"{i}. {step}\n"
                st.code(plan_str, language='text')
        else:
            st.warning("Por favor, digite uma consulta SQL antes de processar.")