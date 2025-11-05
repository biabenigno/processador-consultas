
import streamlit as st
import json
import io
import contextlib
import base64
import requests
from PIL import Image
import copy 
from validator import *
from query_processor import *

# --- Funções Auxiliares ---

# cache do streamlit
@st.cache_data
def load_metadata(filepath: str = "metadados.json"):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # converte toudo para minúsculo.
            return {key.lower(): [attr.lower() for attr in value] for key, value in data.items()}
    except FileNotFoundError:
        st.error(f"ERRO CRÍTICO: O arquivo '{filepath}' não foi encontrado.")
        return None 
    except json.JSONDecodeError:
        st.error(f"ERRO CRÍTICO: O arquivo '{filepath}' não é um JSON válido.")
        return None 

@st.cache_data
def render_mermaid_to_image(mermaid_code: str):
    try:
        # string para bytes UTF-8
        graphbytes = mermaid_code.encode("utf8")
        # bytes para Base64 
        base64_bytes = base64.urlsafe_b64encode(graphbytes)
        # bytes Base64 para uma string 
        base64_string = base64_bytes.decode("ascii")

        #  código codificado na URL e adc o fundo preto (bgColor=000000)
        url = f'https://mermaid.ink/img/{base64_string}?bgColor=000000'
        response = requests.get(url, timeout=10) 
        response.raise_for_status() 

        # verifica se a resposta é realmente uma imagem
        content_type = response.headers.get('Content-Type', '')
        if 'image' in content_type:
            return Image.open(io.BytesIO(response.content))
        else:
            st.error("Falha ao renderizar o grafo. O serviço retornou um erro:")
            error_details = response.text
            st.code(f"Código Mermaid enviado:\n{mermaid_code}\n\nErro recebido do mermaid.ink:\n{error_details}", language='text')
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Erro de conexão ao contatar o serviço de renderização de imagem: {e}")
        return None

#visual streamlit app
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
            # .strip() remove espaços/quebras de linha no início/fim
            # .rstrip(';') remove o ponto e vírgula, *se* ele for o último caractere
            clean_query = user_query.strip().rstrip(';')


            # Validação (HU1) 
            output_buffer = io.StringIO()
            with contextlib.redirect_stdout(output_buffer):
                is_valid = validate_sql(clean_query, METADATA)
            validation_output = output_buffer.getvalue()
            
            st.subheader("1. Validação (HU1)")
            st.code(validation_output, language='text')

            # se for válido
            if is_valid:
                # Conversão para Álgebra Relacional (HU2)
                st.subheader("2. Conversão para Álgebra Relacional (HU2)")
                # Roda a função de conversão
                algebra_expression = convert_to_relational_algebra(clean_query)
                st.code(algebra_expression, language='text')

                try:
                    #Grafo de Operadores (HU3 e HU4)
                    st.subheader("3. Comparação de Grafos (HU3 vs HU4)")
                    
                    col1, col2 = st.columns(2)
                    operator_graph = build_operator_graph(algebra_expression)
                    
                    # grado não otimizado
                    with col1:
                        st.write("**Grafo Não Otimizado (HU3):**")
                        mermaid_unoptimized = operator_graph.to_mermaid()
                        image_unoptimized = render_mermaid_to_image(mermaid_unoptimized)
                        st.image(image_unoptimized)
                    
                    # grafo otimizado (para usar na HU5)
                    optimized_graph = None 
                    
                    # grafo otimizado
                    with col2:
                        st.write("**Grafo Otimizado (HU4):**")
                        opt_buffer = io.StringIO()
                        with contextlib.redirect_stdout(opt_buffer):
                            
                            # Otimização (HU4)
                            # faz uma cópia do grafo original
                            graph_to_optimize = copy.deepcopy(operator_graph)
                            # pega os atributos do nó raiz (o 'π' final)
                            root_attributes = get_attributes_from_string(graph_to_optimize.value)
                            #chama a otimização 
                            optimized_graph = optimize_graph(graph_to_optimize, METADATA, root_attributes)
                        
                        # converte o novo grafo otimizado para Mermaid
                        mermaid_optimized = optimized_graph.to_mermaid()
                        image_optimized = render_mermaid_to_image(mermaid_optimized)
                        st.image(image_optimized)

                    # Plano de Execução (HU5)
                    # verifica se a otimização foi bem-sucedida
                    if optimized_graph:
                        st.subheader("5. Plano de Execução (HU5)")
                        # gera o plano a partir do grafo otimizado
                        execution_plan = generate_execution_plan(optimized_graph)
                        
                        # formata a lista de passos em uma string numerada
                        plan_str = ""
                        for i, step in enumerate(execution_plan, 1):
                            plan_str += f"{i}. {step}\n"
                        st.code(plan_str, language='text')

                # se qualquer try falhar
                except Exception as e:
                    st.error(f"Ocorreu um erro durante a geração do grafo ou otimização: {e}")
                    st.exception(e) 
        else:
            st.warning("Por favor, digite uma consulta SQL antes de processar.")