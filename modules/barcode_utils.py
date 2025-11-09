import qrcode
from barcode import Code128
from barcode.writer import ImageWriter
from PIL import Image
from io import BytesIO
import streamlit as st
import base64

# Geração de QR Code
def gerar_qrcode(dado: str) -> Image.Image:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(dado)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    return img

# Geração de código de barras (Code128)
def gerar_barcode(dado: str) -> Image.Image:
    barcode = Code128(dado, writer=ImageWriter())
    buffer = BytesIO()
    barcode.write(buffer)
    buffer.seek(0)
    img = Image.open(buffer)
    return img

class BarcodeManager:
    
    def generate_qr_code(self, data: str, size: int = 200) -> str:
        """Gera QR Code e retorna como base64"""
        img = gerar_qrcode(data)
        
        # Converter para base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        
        return base64.b64encode(buffer.getvalue()).decode()
    
    def generate_barcode(self, data: str) -> str:
        """Gera código de barras Code128 e retorna como base64"""
        try:
            img = gerar_barcode(data)
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            return base64.b64encode(buffer.getvalue()).decode()
        except Exception:
            # Fallback para QR code se barcode falhar
            return self.generate_qr_code(data)

def show_barcode_page():
    """Exibe página de geração de QR Codes e Códigos de Barras"""
    st.title("📱 QR Codes e Códigos de Barras")
    st.markdown("Geração de códigos para identificação de equipamentos e insumos")
    
    manager = BarcodeManager()
    
    tab1, tab2 = st.tabs(["🔳 Gerar QR Code", "📊 Gerar Código de Barras"])
    
    with tab1:
        st.subheader("Gerar QR Code")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            data = st.text_area("Dados para o QR Code:", 
                              placeholder="Digite os dados que deseja codificar",
                              height=100)
            
            if st.button("🔳 Gerar QR Code", use_container_width=True):
                if data:
                    qr_base64 = manager.generate_qr_code(data)
                    st.session_state.qr_generated = qr_base64
                    st.session_state.qr_data = data
        
        with col2:
            if 'qr_generated' in st.session_state:
                st.subheader("QR Code Gerado:")
                qr_html = f'<img src="data:image/png;base64,{st.session_state.qr_generated}" width="200">'
                st.markdown(qr_html, unsafe_allow_html=True)
                
                # Botão para download
                qr_bytes = base64.b64decode(st.session_state.qr_generated)
                st.download_button(
                    "💾 Download QR Code",
                    qr_bytes,
                    file_name=f"qrcode_{st.session_state.qr_data[:10]}.png",
                    mime="image/png"
                )
    
    with tab2:
        st.subheader("Gerar Código de Barras")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            barcode_data = st.text_input("Dados para o Código de Barras:",
                                       placeholder="Digite números ou texto")
            
            if st.button("📊 Gerar Código de Barras", use_container_width=True):
                if barcode_data:
                    barcode_base64 = manager.generate_barcode(barcode_data)
                    st.session_state.barcode_generated = barcode_base64
                    st.session_state.barcode_data = barcode_data
        
        with col2:
            if 'barcode_generated' in st.session_state:
                st.subheader("Código de Barras Gerado:")
                barcode_html = f'<img src="data:image/png;base64,{st.session_state.barcode_generated}" width="300">'
                st.markdown(barcode_html, unsafe_allow_html=True)
                
                # Botão para download
                barcode_bytes = base64.b64decode(st.session_state.barcode_generated)
                st.download_button(
                    "💾 Download Código de Barras",
                    barcode_bytes,
                    file_name=f"barcode_{st.session_state.barcode_data[:10]}.png",
                    mime="image/png"
                )
    
    # Instruções
    st.markdown("---")
    st.markdown("""
    ### 📖 Instruções de Uso:
    - **QR Codes**: Aceita qualquer tipo de texto ou dados
    - **Códigos de Barras**: Melhor compatibilidade com dados numéricos
    - Use QR Codes para informações complexas (URLs, JSON, etc.)
    - Use códigos de barras para identificadores simples
    """)
