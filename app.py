import atexit
import streamlit as st
import base64
import uuid
import os
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="PDF Chatbot",
    page_icon="💬",
    layout="wide"
)

# Função para salvar o PDF temporariamente


def save_uploaded_file(uploaded_file):
    # Criar diretório temporário se não existir
    if not os.path.exists("temp"):
        os.makedirs("temp")

    # Gerar nome de arquivo único
    file_path = os.path.join("temp", f"{str(uuid.uuid4())}.pdf")

    # Salvar o arquivo
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return file_path

# Função para exibir o PDF


def display_pdf(file_path):
    # Abrir e ler o arquivo PDF
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')

    # Exibir o PDF usando um iframe
    pdf_display = f"""
    <iframe
        src="data:application/pdf;base64,{base64_pdf}"
        width="100%"
        height="500"
        type="application/pdf"
    >
    </iframe>
"""
    st.markdown(pdf_display, unsafe_allow_html=True)


# Inicializar o estado da sessão
if 'pdf_uploaded' not in st.session_state:
    st.session_state.pdf_uploaded = False

if 'pdf_path' not in st.session_state:
    st.session_state.pdf_path = None

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Adicionar variável para controlar o envio de mensagens
if 'message_sent' not in st.session_state:
    st.session_state.message_sent = False

# Função para processar o envio de mensagem


def process_message():
    user_message = st.session_state.user_input
    if user_message:
        # Adicionar mensagem do usuário ao histórico
        st.session_state.chat_history.append(
            {"role": "user", "content": user_message})

        # Gerar resposta do bot (repetindo o que o usuário disse)
        bot_response = f'Você disse: "{user_message}"'

        # Adicionar resposta do bot ao histórico
        st.session_state.chat_history.append(
            {"role": "assistant", "content": bot_response})

        # Limpar o input definindo a variável de estado
        st.session_state.user_input = ""


# Título do aplicativo
st.title("📄 PDF Chatbot")

# Layout com duas colunas
col1, col2 = st.columns([1, 2])

with col1:
    st.header("Upload de Documento")

    # Widget de upload de arquivo
    uploaded_file = st.file_uploader(
        "Faça upload de um PDF para começar a conversa", type="pdf")

    if uploaded_file is not None and not st.session_state.pdf_uploaded:
        # Salvar o arquivo
        file_path = save_uploaded_file(uploaded_file)
        st.session_state.pdf_path = file_path
        st.session_state.pdf_uploaded = True
        st.success("PDF carregado com sucesso!")

        # Adicionar mensagem de boas-vindas ao histórico
        welcome_msg = "Olá! Estou pronto para conversar sobre o documento que você enviou. O que gostaria de saber?"
        st.session_state.chat_history.append(
            {"role": "assistant", "content": welcome_msg})

    # Exibir o PDF se estiver carregado
    if st.session_state.pdf_uploaded:
        st.subheader("Documento Carregado")
        display_pdf(st.session_state.pdf_path)

        # Botão para reiniciar
        if st.button("Carregar outro documento"):
            # Limpar o estado da sessão
            if st.session_state.pdf_path and os.path.exists(st.session_state.pdf_path):
                os.remove(st.session_state.pdf_path)
            st.session_state.pdf_uploaded = False
            st.session_state.pdf_path = None
            st.session_state.chat_history = []
            st.rerun()

with col2:
    st.header("Chat")

    # Container para o histórico de chat
    chat_container = st.container()

    # Área de entrada de mensagem
    message_container = st.container()

    # Exibir o histórico de chat
    with chat_container:
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                st.markdown(f"""
            <div style="display: flex; justify-content: flex-end;">
                <div style="background-color: #0084ff; color: white; border-radius: 20px; padding: 10px 15px; margin: 5px 0; max-width: 70%;">
                    {message["content"]}
                </div>
            </div>
            """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
            <div style="display: flex; justify-content: flex-start;">
                <div style="background-color: #e5e5ea; color: black; border-radius: 20px; padding: 10px 15px; margin: 5px 0; max-width: 70%;">
                    {message["content"]}
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Entrada de mensagem
    with message_container:
        if st.session_state.pdf_uploaded:
            # Usar o callback on_change para processar a mensagem
            st.text_input(
                "Digite sua mensagem:",
                key="user_input",
                on_change=process_message
            )

            # Adicionar um botão de envio como alternativa
            if st.button("Enviar"):
                process_message()
        else:
            st.info("Por favor, faça upload de um PDF para iniciar a conversa.")

# Rodapé
st.markdown("---")
st.markdown(
    f"© {datetime.now().year} PDF Chatbot App | Desenvolvido com Streamlit")

# Limpar arquivos temporários ao fechar o aplicativo


def cleanup():
    if os.path.exists("temp"):
        for file in os.listdir("temp"):
            os.remove(os.path.join("temp", file))
        os.rmdir("temp")


# Registrar função de limpeza
atexit.register(cleanup)
