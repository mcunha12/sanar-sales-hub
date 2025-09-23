# styles.py
import streamlit as st

def load_css():
    """Carrega o CSS customizado para aplicar o design system."""
    st.markdown("""
        <style>
            /* Remove o padding padrão do Streamlit para controle total */
            .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
                padding-left: 3rem;
                padding-right: 3rem;
            }
            
            /* Estilo geral para os cards */
            .custom-card {
                background-color: #FFFFFF;
                border: 1px solid #E0E0E0;
                border-radius: 0.75rem;
                padding: 1.5rem;
                margin-bottom: 1rem;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
            }
            
            /* Estilo para os cards de métricas (KPIs) */
            div[data-testid="metric-container"] {
                background-color: #FFFFFF;
                border: 1px solid #E0E0E0;
                border-radius: 0.75rem;
                padding: 1.5rem;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
            }
            div[data-testid="metric-container"] label { /* Título da métrica */
                font-size: 1rem; color: #4A4A4A; font-weight: 500;
            }
            div[data-testid="metric-container"] div:nth-of-type(2) { /* Valor da métrica */
                font-size: 2.5rem; font-weight: 700; color: #1E1E1E;
            }

            /* Badge "Negociando" */
            .badge-negociando {
                display: inline-block; background-color: #E0F7FA; color: #00796B;
                padding: 0.25rem 0.75rem; border-radius: 1rem;
                font-size: 0.75rem; font-weight: 600;
                margin-left: 0.5rem; vertical-align: middle;
            }
        </style>
    """, unsafe_allow_html=True)

def render_header(title: str, subtitle: str, icon_svg: str):
    """Renderiza um cabeçalho de página padronizado."""
    st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 2rem;">
            <div style="background-color: #0072C6; border-radius: 10px; padding: 10px;">
                {icon_svg}
            </div>
            <div>
                <h1 style="margin-bottom: 0; color: #1E1E1E;">{title}</h1>
                <p style="margin-top: 0; color: #888888;">{subtitle}</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

# Definições dos ícones SVG para usar nas páginas
icon_dashboard = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-bar-chart-3"><path d="M3 3v18h18"/><path d="M18 17V9"/><path d="M13 17V5"/><path d="M8 17v-3"/></svg>'
icon_rag = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-brain-circuit"><path d="M12 5a3 3 0 1 0-5.993.142"/><path d="M18 13a3 3 0 1 0-4.472 2.5"/><path d="M2.007 12.5A2.999 2.999 0 1 0 5 15"/><path d="M12 21a3 3 0 1 0 3-5.5"/><path d="M12 5a3 3 0 0 0 5.993.142"/><path d="M18 13a3 3 0 0 0 4.472 2.5"/><path d="M21.993 12.5A2.999 2.999 0 1 0 19 15"/><path d="M12 21a3 3 0 0 0-3-5.5"/><path d="M6 15h12"/><path d="m6 15-1-1"/><path d="m18 15 1-1"/><path d="M12 5V2"/><path d="M12 21v-2"/><path d="M12 13V9"/></svg>'
icon_home = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-home"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>'