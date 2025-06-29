import atexit
import streamlit as st
import base64
import uuid
import os
import PyPDF2
import cohere
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="PDF Chatbot",
    page_icon="💬",
    layout="wide"
)


@st.cache_resource
def load_cohere_client():
    api_key = os.getenv("COHERE_API_KEY", "")
    if not api_key:
        st.error(
            "API Key do Cohere não encontrada. Configure a variável de ambiente COHERE_API_KEY.")
        return None
    try:
        return cohere.Client(api_key)
    except Exception as e:
        st.error(f"Erro ao inicializar o cliente Cohere: {e}")
        return None


def extract_text_from_pdf(file_path):
    text = ""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num in range(len(pdf_reader.pages)):
                text += pdf_reader.pages[page_num].extract_text() + "\n"
    except Exception as e:
        st.error(f"Erro ao extrair texto do PDF: {e}")
    return text


def generate_response(question, pdf_text, co_client):
    if co_client is None:
        return "Erro: Cliente Cohere não inicializado. Verifique sua API key."

    if not pdf_text or len(pdf_text.strip()) == 0:
        return "Não há texto no documento para analisar."

    max_context_length = 4000
    context = pdf_text[:max_context_length] if len(
        pdf_text) > max_context_length else pdf_text

    prompt = f"""
        Documento:
        {context}
        
        Pergunta: {question}
        
        Responda à pergunta acima com base apenas nas informações contidas no documento. Se a resposta não estiver no documento, diga "Não encontrei essa informação no documento."
        
        Resposta:
    """

    try:
        response = co_client.generate(
            model='command',
            prompt=prompt,
            max_tokens=300,
            temperature=0.2,
            k=0,
            stop_sequences=["Documento:", "Pergunta:"],
            return_likelihoods='NONE'
        )
        generated_text = response.generations[0].text.strip()
        return generated_text

    except Exception as e:
        st.error(f"Erro ao gerar resposta: {e}")
        return f"Desculpe, ocorreu um erro ao processar sua pergunta: {str(e)}"


def save_uploaded_file(uploaded_file):
    if 'pdf_path' in st.session_state and st.session_state.pdf_path and os.path.exists(st.session_state.pdf_path):
        try:
            os.remove(st.session_state.pdf_path)
        except:
            pass
    if not os.path.exists("temp"):
        os.makedirs("temp")
    file_path = os.path.join("temp", f"{str(uuid.uuid4())}.pdf")
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path


if 'pdf_uploaded' not in st.session_state:
    st.session_state.pdf_uploaded = False

if 'pdf_path' not in st.session_state:
    st.session_state.pdf_path = None

if 'pdf_text' not in st.session_state:
    st.session_state.pdf_text = ""

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'model_loaded' not in st.session_state:
    st.session_state.model_loaded = False

if 'debug_mode' not in st.session_state:
    st.session_state.debug_mode = False

if 'submit_question' not in st.session_state:
    st.session_state.submit_question = False

if 'last_uploaded_file' not in st.session_state:
    st.session_state.last_uploaded_file = None

with st.spinner("Inicializando o modelo de IA..."):
    co_client = load_cohere_client()
    st.session_state.model_loaded = co_client is not None


def process_message():
    st.session_state.submit_question = True


st.title("📄 PDF Chatbot")

col1, col2 = st.columns([1, 2])

with col1:
    st.header("Upload de Documento")
    uploaded_file = st.file_uploader(
        "Faça upload de um PDF para começar a conversa", type="pdf")

    if uploaded_file is not None:
        is_new_file = (st.session_state.last_uploaded_file !=
                       uploaded_file.name)

        if is_new_file:
            st.session_state.last_uploaded_file = uploaded_file.name

            with st.spinner("Processando o PDF..."):
                file_path = save_uploaded_file(uploaded_file)
                st.session_state.pdf_path = file_path

                pdf_text = extract_text_from_pdf(file_path)
                st.session_state.pdf_text = pdf_text

                if pdf_text.strip():
                    if st.session_state.pdf_uploaded:
                        st.session_state.chat_history = []

                    st.session_state.pdf_uploaded = True
                    st.success("PDF carregado e processado com sucesso!")

                    welcome_msg = "Olá! Analisei seu documento e estou pronto para responder perguntas sobre ele. O que gostaria de saber?"
                    st.session_state.chat_history.append(
                        {"role": "assistant", "content": welcome_msg})

                    st.rerun()
                else:
                    st.error(
                        "Não foi possível extrair texto do PDF. Verifique se o documento não está protegido ou se é um PDF escaneado.")

with col2:
    st.header("Chat")

    st.markdown("""
        <style>
            .chat-message {
                padding: 10px 15px;
                border-radius: 20px;
                margin-bottom: 10px;
                display: inline-block;
                max-width: 70%;
                word-wrap: break-word;
            }
            
            .user-message {
                background-color: #0084ff;
                color: white;
                border-bottom-right-radius: 5px;
                float: right;
                clear: both;
            }
            
            .assistant-message {
                background-color: #e5e5ea;
                color: black;
                border-bottom-left-radius: 5px;
                float: left;
                clear: both;
            }
            
            /* Limpar os floats após cada mensagem */
            .clearfix::after {
                content: "";
                clear: both;
                display: table;
            }
        </style>
    """, unsafe_allow_html=True)

    chat_container = st.container()

    for message in st.session_state.chat_history:
        if message["role"] == "user":
            chat_container.markdown(
                f'<div class="clearfix"><div class="chat-message user-message">{message["content"]}</div></div>',
                unsafe_allow_html=True
            )
        else:
            chat_container.markdown(
                f'<div class="clearfix"><div class="chat-message assistant-message">{message["content"]}</div></div>',
                unsafe_allow_html=True
            )

    chat_container.markdown('</div>', unsafe_allow_html=True)

    message_container = st.container()
    with message_container:
        if st.session_state.pdf_uploaded:
            with st.form(key="question_form", clear_on_submit=True):
                user_input = st.text_input(
                    "Digite sua pergunta sobre o documento:", key="user_input")
                submit_button = st.form_submit_button(
                    "Enviar", on_click=process_message)

            if st.session_state.submit_question and user_input:
                st.session_state.chat_history.append(
                    {"role": "user", "content": user_input})

                with st.spinner("Gerando resposta..."):
                    bot_response = generate_response(
                        user_input, st.session_state.pdf_text, co_client)

                st.session_state.chat_history.append(
                    {"role": "assistant", "content": bot_response})

                st.session_state.submit_question = False

                st.rerun()
        else:
            st.info("Por favor, faça upload de um PDF para iniciar a conversa.")

with st.sidebar:
    st.title("Configurações")

    st.session_state.debug_mode = st.checkbox(
        "Modo Debug", value=st.session_state.debug_mode)

    if st.session_state.debug_mode:
        st.subheader("Informações de Debug")

        st.write("Modelo carregado:", st.session_state.model_loaded)
        st.write("PDF carregado:", st.session_state.pdf_uploaded)

        if st.session_state.pdf_uploaded:
            st.write("Nome do arquivo:", st.session_state.last_uploaded_file)

        if st.button("Testar modelo com texto simples"):
            test_text = "O céu é azul durante o dia e escuro à noite. As estrelas são visíveis apenas à noite quando o céu está escuro."
            test_question = "Quando as estrelas são visíveis?"

            with st.spinner("Testando modelo..."):
                try:
                    response = generate_response(
                        test_question, test_text, co_client)
                    st.success(f"Pergunta: {test_question}")
                    st.success(f"Resposta: {response}")
                except Exception as e:
                    st.error(f"Erro ao testar modelo: {str(e)}")

        if st.session_state.pdf_uploaded:
            if st.button("Ver texto extraído do PDF"):
                st.text_area("Texto do PDF", st.session_state.pdf_text[:5000] + "..." if len(
                    st.session_state.pdf_text) > 5000 else st.session_state.pdf_text, height=200)

            if st.button("Ver histórico de chat"):
                st.json(st.session_state.chat_history)

            if st.button("Limpar histórico de chat"):
                welcome_msg = "Olá! Analisei seu documento e estou pronto para responder perguntas sobre ele. O que gostaria de saber?"
                st.session_state.chat_history = [
                    {"role": "assistant", "content": welcome_msg}]
                st.success("Histórico de chat limpo!")
                st.rerun()

            st.subheader("Configurações do Modelo")
            model_options = ["command", "command-light", "command-nightly"]
            selected_model = st.selectbox(
                "Modelo Cohere", model_options, index=0)

            temperature = st.slider(
                "Temperatura", min_value=0.0, max_value=1.0, value=0.2, step=0.1)

            if st.button("Testar configurações"):
                test_question = "Do que trata este documento?"
                with st.spinner("Testando configurações..."):
                    try:
                        prompt = f"""
                    Documento:
                    {st.session_state.pdf_text[:1000]}
                    
                    Pergunta: {test_question}
                    
                    Responda à pergunta acima com base apenas nas informações contidas no documento.
                    
                    Resposta:
                    """

                        response = co_client.generate(
                            model=selected_model,
                            prompt=prompt,
                            max_tokens=300,
                            temperature=temperature,
                            k=0,
                            stop_sequences=["Documento:", "Pergunta:"],
                            return_likelihoods='NONE'
                        )

                        st.success(f"Pergunta: {test_question}")
                        st.success(
                            f"Resposta: {response.generations[0].text.strip()}")
                    except Exception as e:
                        st.error(f"Erro ao testar configurações: {str(e)}")

st.markdown("---")
st.markdown(
    f"© {datetime.now().year} PDF Chatbot App | Desenvolvido com Streamlit")


def cleanup():
    if os.path.exists("temp"):
        for file in os.listdir("temp"):
            os.remove(os.path.join("temp", file))
        os.rmdir("temp")


atexit.register(cleanup)
