import streamlit as st
import json
import io
import contextlib
import base64
import requests
from PIL import Image
import copy # Importado para a otimização

from validator import validate_sql
from query_processor import (
    convert_to_relational_algebra,
    build_operator_graph,
    optimize_graph,
    generate_execution_plan,
    get_attributes_from_string # Importado para a otimização
)

@st.cache_data
def load_metadata(filepath: str = "metadados.json"):
    """Carrega e normaliza o arquivo de metadados."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Normaliza tudo para minúsculas para consistência
            return {key.lower(): [attr.lower() for attr in value] for key, value in data.items()}
    except FileNotFoundError:
        st.error(f"ERRO CRÍTICO: O arquivo '{filepath}' não foi encontrado.")
        return None
    except json.JSONDecodeError:
        st.error(f"ERRO CRÍTICO: O arquivo '{filepath}' não é um JSON válido.")
        return None

# --- Mermaid para imagem ---
@st.cache_data
def render_mermaid_to_image(mermaid_code: str):
    """Renderiza um código Mermaid para uma imagem usando o serviço mermaid.ink."""
    try:
        graphbytes = mermaid_code.encode("utf8")
        base64_bytes = base64.urlsafe_b64encode(graphbytes)
        base64_string = base64_bytes.decode("ascii")
        
        # URL para fundo escuro (preto)
        url = f'https://mermaid.ink/img/{base64_string}?bgColor=000000'

        response = requests.get(url, timeout=10) # Adicionado timeout
        response.raise_for_status() # Verifica erros de HTTP

        content_type = response.headers.get('Content-Type', '')
        if 'image' in content_type:
            return Image.open(io.BytesIO(response.content))
        else:
            # Se a resposta não for uma imagem, é um erro do mermaid.ink
            st.error("Falha ao renderizar o grafo. O serviço retornou um erro:")
            error_details = response.text
            st.code(f"Código Mermaid enviado:\n{mermaid_code}\n\nErro recebido do mermaid.ink:\n{error_details}", language='text')
            return None

    except requests.exceptions.RequestException as e:
        st.error(f"Erro de conexão ao contatar o serviço de renderização de imagem: {e}")
        return None


# --- Início da Interface Gráfica ---
st.set_page_config(layout="wide")
st.title("⚙️ Processador de Consultas SQL")
st.write("Trabalho da Disciplina de Banco de Dados")

METADATA = load_metadata()

if METADATA is None:
    st.warning("A aplicação não pode continuar sem o 'metadados.json'.")
else:
    user_query = st.text_area("Digite sua consulta SQL aqui:", height=150, placeholder="SELECT cliente.nome, pedido.idPedido FROM Cliente JOIN Pedido ON cliente.idcliente = pedido.Cliente_idCliente WHERE cliente.TipoCliente_idTipoCliente = 1")

    if st.button("Processar Consulta"):
        if user_query:
            # --- 1. Validação (HU1) ---
            output_buffer = io.StringIO()
            with contextlib.redirect_stdout(output_buffer):
                is_valid = validate_sql(user_query, METADATA)
            validation_output = output_buffer.getvalue()
            
            st.subheader("1. Validação (HU1)")
            st.code(validation_output, language='text')

            # --- Continua apenas se for válido ---
            if is_valid:
                # --- 2. Conversão para Álgebra Relacional (HU2) ---
                st.subheader("2. Conversão para Álgebra Relacional (HU2)")
                algebra_expression = convert_to_relational_algebra(user_query)
                st.code(algebra_expression, language='text')

                try:
                    # --- 3. Grafo de Operadores (HU3 e HU4) - Lado a Lado ---
                    st.subheader("3. Comparação de Grafos (HU3 vs HU4)")
                    
                    col1, col2 = st.columns(2)
                    
                    # Constrói o grafo não otimizado
                    operator_graph = build_operator_graph(algebra_expression)
                    
                    with col1:
                        st.write("**Grafo Não Otimizado (HU3):**")
                        mermaid_unoptimized = operator_graph.to_mermaid()
                        image_unoptimized = render_mermaid_to_image(mermaid_unoptimized)
                        #if image_unoptimized:
                        st.image(image_unoptimized)
                    
                    # Variável para guardar o grafo otimizado
                    optimized_graph = None 
                    
                    with col2:
                        st.write("**Grafo Otimizado (HU4):**")
                        opt_buffer = io.StringIO()
                        with contextlib.redirect_stdout(opt_buffer):
                            
                            # --- Aplicação da correção lógica ---
                            # 1. Clona o grafo para não afetar o original
                            graph_to_optimize = copy.deepcopy(operator_graph)
                            
                            # 2. Pega os atributos da raiz (necessários para a projeção)
                            root_attributes = get_attributes_from_string(graph_to_optimize.value)

                            # 3. Chama a função de otimização com os 3 argumentos
                            optimized_graph = optimize_graph(graph_to_optimize, METADATA, root_attributes)
                        
                        #st.write(opt_buffer.getvalue()) # Mostra o print ">>> Otimização..."
                        mermaid_optimized = optimized_graph.to_mermaid()
                        image_optimized = render_mermaid_to_image(mermaid_optimized)
                        #if image_optimized:
                        st.image(image_optimized)

                    # --- 4. Grafo Otimizado em Formato de Texto (Conforme solicitado) ---
                    # if optimized_graph:
                    #     st.subheader("4. Grafo Otimizado (Formato de Texto)")
                    #     # Chama str() no nó, que ativará o seu método __repr__
                    #     st.code(str(optimized_graph), language='text')

                    # --- 5. Plano de Execução (HU5) ---
                    if optimized_graph:
                        st.subheader("5. Plano de Execução (HU5)")
                        # Gera o plano a partir do grafo JÁ otimizado
                        execution_plan = generate_execution_plan(optimized_graph)
                        
                        plan_str = ""
                        for i, step in enumerate(execution_plan, 1):
                            plan_str += f"{i}. {step}\n"
                        st.code(plan_str, language='text')

                except Exception as e:
                    st.error(f"Ocorreu um erro durante a geração do grafo ou otimização: {e}")
                    st.exception(e) # Mostra o stack trace para debug

        else:
            st.warning("Por favor, digite uma consulta SQL antes de processar.")

