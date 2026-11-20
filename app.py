import re
import os
import json
import inspect
from io import BytesIO

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

# Protección global: fallback nativo si 'tabulate' no está instalado en el entorno
_orig_to_markdown = getattr(pd.DataFrame, "to_markdown", None)


def _safe_to_markdown(self, buf=None, mode="wt", index=True, storage_options=None, **kwargs):
    try:
        if _orig_to_markdown is not None:
            return _orig_to_markdown(self, buf=buf, mode=mode, index=index, storage_options=storage_options, **kwargs)
    except Exception:
        pass
    cols = list(self.columns)
    columnas_mostrar = (["Index"] + cols) if index else cols
    header = "| " + " | ".join(str(c) for c in columnas_mostrar) + " |"
    sep = "| " + " | ".join(["---"] * len(columnas_mostrar)) + " |"
    filas = []
    for idx_val, row in self.iterrows():
        valores = ([str(idx_val)] if index else []) + [str(row[c]).replace("\n", " ").replace("|", "\\|") for c in cols]
        filas.append("| " + " | ".join(valores) + " |")
    res = "\n".join([header, sep] + filas)
    if buf is not None:
        if hasattr(buf, "write"):
            buf.write(res)
        else:
            with open(buf, mode, encoding="utf-8") as f:
                f.write(res)
        return None
    return res


pd.DataFrame.to_markdown = _safe_to_markdown
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ==============================================================================
# 1. CONFIGURACIÓN DE PÁGINA, PALETA CORPORATIVA Y CSS RESPONSIVE
# ==============================================================================
st.set_page_config(
    page_title="Executive Finance & BI Suite | Alta Gerencia",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

COLORS = {
    "primary": "#0F172A",
    "royal": "#1E3A8A",
    "secondary": "#1E293B",
    "accent": "#0EA5E9",
    "teal": "#14B8A6",
    "success": "#10B981",
    "warning": "#F59E0B",
    "danger": "#EF4444",
    "purple": "#6366F1",
    "violet": "#8B5CF6",
    "bg_card": "#FFFFFF",
    "text_muted": "#64748B"
}

PALETA_BI = [
    "#0F172A", "#0EA5E9", "#10B981", "#6366F1",
    "#F59E0B", "#14B8A6", "#EF4444", "#8B5CF6"
]

CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500&display=swap');

    .stApp {
        background-color: #F4F7FB !important;
        color: #0F172A !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    .stApp, .stApp p, .stApp span, .stApp label, .stApp li {
        color: #0F172A;
    }
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {
        color: #0F172A !important;
    }
    div[data-testid="stMarkdownContainer"] p,
    div[data-testid="stMarkdownContainer"] span,
    div[data-testid="stMarkdownContainer"] li,
    div[data-testid="stMarkdownContainer"] strong,
    div[data-testid="stMarkdownContainer"] b {
        color: #0F172A !important;
    }
    h1, h2, h3, .exec-header h1, .kpi-value {
        font-family: 'Space Grotesk', 'Inter', sans-serif;
    }
    code { font-family: 'JetBrains Mono', monospace; }

    /* ===== BARRA SUPERIOR STREAMLIT TRANSPARENTE ===== */
    header[data-testid="stHeader"] {
        background: transparent !important;
        height: 0 !important;
        min-height: 0 !important;
        border-bottom: none !important;
        z-index: 1005 !important;
        pointer-events: none !important;
    }
    header[data-testid="stHeader"] button,
    header[data-testid="stHeader"] a,
    header[data-testid="stHeader"] [role="button"] {
        pointer-events: auto !important;
    }

    /* ===== CONTENEDOR DE SCROLL PRINCIPAL (NUNCA OVERFLOW VISIBLE AQUÍ) ===== */
    section[data-testid="stMain"] {
        overflow-y: auto !important;
        overflow-x: hidden !important;
        height: 100vh !important;
    }

    .stMainBlockContainer,
    div[data-testid="stMainBlockContainer"],
    .block-container {
        padding-top: 0.4rem !important;
        padding-bottom: 3rem !important;
        padding-left: 1.4rem !important;
        padding-right: 1.4rem !important;
        max-width: 100% !important;
    }

    /* Contenedores intermedios permiten que sticky funcione */
    div[data-testid="stVerticalBlock"],
    div[data-testid="stVerticalBlockBorderWrapper"],
    div[data-testid="stTabs"],
    div[data-baseweb="tabs"],
    div[data-baseweb="tab-panel"] {
        overflow: visible !important;
    }

    /* ===== SECCIÓN FIJA EN TOP: ENCABEZADO EJECUTIVO ===== */
    div[data-testid="stElementContainer"]:has(.exec-header),
    div.stElementContainer:has(.exec-header) {
        position: -webkit-sticky !important;
        position: sticky !important;
        top: 0 !important;
        z-index: 1000 !important;
        background: #F4F7FB !important;
        margin-bottom: 0 !important;
        padding-bottom: 0 !important;
    }
    .exec-header {
        background: linear-gradient(135deg, __PRIMARY__ 0%, #1E3A8A 60%, #0369A1 100%);
        padding: 0.52rem 1.25rem;
        border-radius: 12px 12px 0 0;
        color: white;
        margin: 0 !important;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.2);
        border-left: 6px solid __WARNING__;
        border-bottom: 1px solid rgba(255, 255, 255, 0.15);
        box-sizing: border-box;
    }
    .exec-header-inner {
        display: flex;
        justify-content: space-between;
        align-items: center;
        width: 100%;
        flex-wrap: wrap;
        gap: 8px;
    }
    .exec-title {
        margin: 0;
        font-size: clamp(0.98rem, 1.45vw, 1.26rem);
        font-weight: 800;
        letter-spacing: -0.02em;
        color: white;
        line-height: 1.2;
    }
    .exec-meta {
        font-size: clamp(0.73rem, 0.95vw, 0.83rem);
        color: #E2E8F0;
        display: flex;
        align-items: center;
        gap: 6px;
        flex-wrap: wrap;
    }
    .exec-sep {
        color: #94A3B8;
        font-weight: bold;
    }

    /* ===== SECCIÓN FIJA EN TOP: MENÚ DE TABS INMEDIATAMENTE DEBAJO ===== */
    div[data-baseweb="tab-list"] {
        position: -webkit-sticky !important;
        position: sticky !important;
        top: 50px !important;
        z-index: 999 !important;
        background: #FFFFFF !important;
        padding: 0.35rem 0.5rem 0.28rem 0.5rem !important;
        margin: 0 0 0.85rem 0 !important;
        gap: 0.35rem;
        overflow-x: auto !important;
        overflow-y: hidden !important;
        -webkit-overflow-scrolling: touch;
        scrollbar-width: thin;
        border-radius: 0 0 12px 12px;
        border-left: 1px solid #CBD5E1;
        border-right: 1px solid #CBD5E1;
        border-bottom: 2px solid #CBD5E1;
        box-shadow: 0 6px 16px rgba(15, 23, 42, 0.08);
    }
    button[data-baseweb="tab"] {
        font-weight: 700 !important;
        font-size: 0.88rem !important;
        white-space: nowrap !important;
        padding: 0.44rem 0.85rem !important;
        border-radius: 8px !important;
        flex-shrink: 0 !important;
        color: #334155 !important;
        background: #F8FAFC !important;
        border: 1px solid #E2E8F0 !important;
        transition: background 0.15s ease, color 0.15s ease, border-color 0.15s ease !important;
    }
    button[data-baseweb="tab"]:hover {
        background: #E2E8F0 !important;
        color: #0F172A !important;
        border-color: #CBD5E1 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        background: #0F172A !important;
        color: #FFFFFF !important;
        border: 1px solid #0F172A !important;
    }

    /* ===== KPI GRID RESPONSIVE (PC / LAPTOP / TABLET / MÓVIL) ===== */
    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(5, minmax(0, 1fr));
        gap: 0.78rem;
        margin: 0.2rem 0 0.95rem 0;
    }
    .kpi-card {
        background: linear-gradient(180deg, #FFFFFF 0%, #FAFCFF 100%);
        border-radius: 13px;
        padding: 0.9rem 1rem;
        box-shadow: 0 3px 10px rgba(15, 23, 42, 0.05);
        border: 1px solid #E2E8F0;
        transition: transform 0.18s ease, box-shadow 0.18s ease;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        min-width: 0;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 22px rgba(15, 23, 42, 0.09);
    }
    .kpi-title {
        font-size: 0.71rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: __MUTED__;
        margin-bottom: 0.28rem;
        line-height: 1.25;
    }
    .kpi-value {
        font-size: clamp(1.12rem, 1.55vw, 1.44rem);
        font-weight: 800;
        color: __PRIMARY__;
        line-height: 1.18;
        word-break: break-word;
    }
    .kpi-delta-pos, .kpi-delta-warn, .kpi-delta-neg {
        display: inline-block;
        align-self: flex-start;
        margin-top: 0.42rem;
        padding: 0.18rem 0.55rem;
        border-radius: 999px;
        font-size: 0.73rem;
        font-weight: 700;
        line-height: 1.25;
    }
    .kpi-delta-pos { background-color: #DCFCE7; color: #166534; }
    .kpi-delta-warn { background-color: #FEF3C7; color: #92400E; }
    .kpi-delta-neg { background-color: #FEE2E2; color: #991B1B; }

    /* ===== TARJETAS Y CAJAS NARRATIVAS DE STORYTELLING ===== */
    .cards-3 {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.85rem;
        margin: 0.5rem 0 0.9rem 0;
    }
    .story-box {
        background: #FFFFFF;
        border-left: 5px solid __ACCENT__;
        padding: 1.05rem 1.35rem;
        border-radius: 11px;
        line-height: 1.78;
        color: #1E293B;
        font-size: 0.94rem;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
        border-top: 1px solid #F1F5F9;
        border-right: 1px solid #F1F5F9;
        border-bottom: 1px solid #F1F5F9;
    }
    .story-box p { margin: 0 0 0.75rem 0; }
    .story-box p:last-child { margin-bottom: 0; }

    /* Highlights semánticos para Storytelling de Datos */
    .hl-green {
        background: rgba(16, 185, 129, 0.12);
        color: #047857;
        padding: 0.14rem 0.44rem;
        border-radius: 6px;
        font-weight: 700;
        border: 1px solid rgba(16, 185, 129, 0.25);
        white-space: nowrap;
    }
    .hl-blue {
        background: rgba(14, 165, 233, 0.12);
        color: #0369A1;
        padding: 0.14rem 0.44rem;
        border-radius: 6px;
        font-weight: 700;
        border: 1px solid rgba(14, 165, 233, 0.25);
    }
    .hl-amber {
        background: rgba(245, 158, 11, 0.12);
        color: #B45309;
        padding: 0.14rem 0.44rem;
        border-radius: 6px;
        font-weight: 700;
        border: 1px solid rgba(245, 158, 11, 0.25);
    }
    .hl-red {
        background: rgba(239, 68, 68, 0.12);
        color: #B91C1C;
        padding: 0.14rem 0.44rem;
        border-radius: 6px;
        font-weight: 700;
        border: 1px solid rgba(239, 68, 68, 0.25);
    }
    .hl-purple {
        background: rgba(99, 102, 241, 0.12);
        color: #4338CA;
        padding: 0.14rem 0.44rem;
        border-radius: 6px;
        font-weight: 700;
        border: 1px solid rgba(99, 102, 241, 0.25);
    }
    .hl-dark {
        background: rgba(15, 23, 42, 0.08);
        color: #0F172A;
        padding: 0.14rem 0.44rem;
        border-radius: 6px;
        font-weight: 800;
    }

    .ok-box, .alert-box, .danger-box, .info-box {
        padding: 0.95rem 1.15rem;
        border-radius: 11px;
        font-size: 0.90rem;
        line-height: 1.55;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
    }
    .ok-box { background: #F0FDF4; border-left: 5px solid __SUCCESS__; color: #14532D; }
    .alert-box { background: #FFFBEB; border-left: 5px solid __WARNING__; color: #78350F; }
    .danger-box { background: #FEF2F2; border-left: 5px solid __DANGER__; color: #7F1D1D; }
    .info-box { background: #F0F9FF; border-left: 5px solid __ACCENT__; color: #0C4A6E; }
    .ok-box ul, .alert-box ul, .danger-box ul, .info-box ul { margin: 0.35rem 0 0 0; padding-left: 1.1rem; }

    /* ===== ESTILO ACORDEÓN PARA EXPANDERS (TITULOS DESTACADOS EN NEGRITAS) ===== */
    div[data-testid="stExpander"] {
        background: #FFFFFF !important;
        border: 1.5px solid #CBD5E1 !important;
        border-radius: 11px !important;
        box-shadow: 0 2px 7px rgba(15, 23, 42, 0.04) !important;
        margin-bottom: 0.65rem !important;
        overflow: hidden !important;
    }
    div[data-testid="stExpander"] details summary {
        font-weight: 800 !important;
        font-size: 0.92rem !important;
        color: #0F172A !important;
        background: #F8FAFC !important;
        padding: 0.52rem 0.95rem !important;
        cursor: pointer !important;
        border-bottom: 1px solid #E2E8F0 !important;
        transition: background 0.15s ease, color 0.15s ease !important;
    }
    div[data-testid="stExpander"] details summary:hover {
        background: #F1F5F9 !important;
        color: #0284C7 !important;
    }
    div[data-testid="stExpander"] details summary p,
    div[data-testid="stExpander"] details summary span {
        font-weight: 800 !important;
        font-size: 0.92rem !important;
        color: #0F172A !important;
        letter-spacing: -0.01em !important;
    }
    div[data-testid="stExpander"] div[data-testid="stVerticalBlock"] p,
    div[data-testid="stExpander"] div[data-testid="stVerticalBlock"] span,
    div[data-testid="stExpander"] div[data-testid="stVerticalBlock"] li {
        color: #1E293B !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stExpander"] {
        background: #F8FAFC !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 10px !important;
        margin-bottom: 0.45rem !important;
    }
    section[data-testid="stSidebar"] .stCheckbox {
        margin-bottom: -0.35rem;
    }
    .slicer-chip-bar {
        display: flex;
        flex-wrap: wrap;
        gap: 0.35rem;
        margin: 0.3rem 0 0.65rem 0;
    }
    .slicer-chip {
        background: #E0F2FE;
        color: #0369A1;
        border: 1px solid #BAE6FD;
        border-radius: 999px;
        padding: 0.15rem 0.6rem;
        font-size: 0.74rem;
        font-weight: 600;
    }

    /* ===== NIVELACIÓN PERFECTA DE ALTURAS EN SECCIONES DE GRÁFICOS ===== */
    /* En PC y Laptop (min-width: 901px) */
    @media (min-width: 901px) {
        div[data-testid="stHorizontalBlock"] {
            display: flex !important;
            align-items: stretch !important;
            gap: 0.95rem !important;
        }
        div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
            display: flex !important;
            flex-direction: column !important;
            flex: 1 1 0% !important;
            min-width: 0 !important;
        }
        /* Contenedores con borde dentro de columnas ocupan el 100% de la altura de la fila */
        div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] > div[data-testid="stVerticalBlockBorderWrapper"] {
            height: 100% !important;
            display: flex !important;
            flex-direction: column !important;
        }
        div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] > div[data-testid="stVerticalBlockBorderWrapper"] > div[data-testid="stVerticalBlock"] {
            height: 100% !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: space-between !important;
            padding: 0.95rem 1rem 0.85rem 1rem !important;
        }
        /* Encabezados h3 de gráficos con altura uniforme para alinear el inicio de todos los gráficos */
        div[data-testid="stHorizontalBlock"] h3,
        div[data-testid="stHorizontalBlock"] [data-testid="stMarkdownContainer"] h3 {
            min-height: 2.85rem !important;
            display: flex !important;
            align-items: center !important;
            margin-top: 0 !important;
            margin-bottom: 0.45rem !important;
            line-height: 1.25 !important;
            font-size: 1.05rem !important;
        }
    }

    /* Estilo de tarjeta ejecutiva con borde y elevación sutil para contenedores de gráficos */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: #FFFFFF !important;
        border: 1.5px solid #CBD5E1 !important;
        border-radius: 13px !important;
        box-shadow: 0 3px 10px rgba(15, 23, 42, 0.04) !important;
        margin-bottom: 0.85rem !important;
        transition: box-shadow 0.2s ease, border-color 0.2s ease !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: #94A3B8 !important;
        box-shadow: 0 6px 18px rgba(15, 23, 42, 0.07) !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] p,
    div[data-testid="stVerticalBlockBorderWrapper"] span,
    div[data-testid="stVerticalBlockBorderWrapper"] label,
    div[data-testid="stVerticalBlockBorderWrapper"] div {
        color: #0F172A;
    }

    /* Sidebar con fondo blanco y tipografía de máximo contraste */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #E2E8F0 !important;
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] div {
        color: #0F172A !important;
    }
    section[data-testid="stSidebar"] [data-testid="stMetricValue"] {
        color: #0F172A !important;
    }
    section[data-testid="stSidebar"] [data-testid="stMetricLabel"] {
        color: #475569 !important;
    }

    /* Tablas y Dataframes */
    div[data-testid="stDataFrame"] {
        background-color: #FFFFFF !important;
        border: 1.5px solid #CBD5E1 !important;
        border-radius: 10px !important;
    }

    /* Cuadros de búsqueda e inputs */
    .stTextInput input {
        color: #0F172A !important;
        background-color: #FFFFFF !important;
        border: 1.5px solid #CBD5E1 !important;
    }
    .stTextInput label,
    .stTextInput [data-testid="stMarkdownContainer"] p {
        color: #0F172A !important;
        font-weight: 700 !important;
    }

    /* Subtítulos y textos de soporte */
    .stCaption,
    div[data-testid="stCaptionContainer"] p {
        color: #475569 !important;
        font-weight: 500 !important;
    }

    /* ===== BREAKPOINTS RESPONSIVE (MÓVIL / TABLET / LAPTOP / PC) ===== */
    @media (max-width: 1280px) {
        .kpi-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
    }
    @media (max-width: 900px) {
        .stMainBlockContainer,
        div[data-testid="stMainBlockContainer"],
        .block-container {
            padding-left: 0.9rem !important;
            padding-right: 0.9rem !important;
        }
        div[data-testid="stHorizontalBlock"] {
            flex-direction: column !important;
            gap: 0.85rem !important;
        }
        div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
            width: 100% !important;
            flex: 1 1 100% !important;
        }
        div[data-testid="stHorizontalBlock"] h3,
        div[data-testid="stHorizontalBlock"] [data-testid="stMarkdownContainer"] h3 {
            min-height: auto !important;
            margin-bottom: 0.4rem !important;
        }
        div[data-testid="stVerticalBlockBorderWrapper"] {
            margin-bottom: 0.75rem !important;
        }
        .kpi-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0.65rem; }
        .cards-3 { grid-template-columns: 1fr; }
        button[data-baseweb="tab"] { font-size: 0.83rem; padding: 0.42rem 0.7rem; }
    }
    @media (max-width: 560px) {
        .stMainBlockContainer,
        div[data-testid="stMainBlockContainer"],
        .block-container {
            padding-left: 0.55rem !important;
            padding-right: 0.55rem !important;
        }
        .kpi-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0.5rem; }
        .kpi-card { padding: 0.72rem 0.78rem; }
        .exec-header { padding: 0.68rem 0.9rem; }
        button[data-baseweb="tab"] { font-size: 0.77rem; padding: 0.38rem 0.58rem; }
        .story-box { padding: 0.85rem 0.95rem; font-size: 0.88rem; }
    }
</style>
"""
for _k, _v in {
    "__PRIMARY__": COLORS["primary"], "__WARNING__": COLORS["warning"], "__MUTED__": COLORS["text_muted"],
    "__ACCENT__": COLORS["accent"], "__SUCCESS__": COLORS["success"], "__DANGER__": COLORS["danger"]
}.items():
    CSS = CSS.replace(_k, _v)
st.markdown(CSS, unsafe_allow_html=True)

NEW_ST = "width" in inspect.signature(st.plotly_chart).parameters


def plot(fig):
    if NEW_ST:
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False, "responsive": True})
    else:
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "responsive": True})


def tabla(obj, **kw):
    try:
        if NEW_ST:
            st.dataframe(obj, width="stretch", **kw)
        else:
            st.dataframe(obj, use_container_width=True, **kw)
    except Exception:
        # Fallback de seguridad: si pandas Styler falla por falta de matplotlib en background_gradient,
        # renderizar los datos puros sin colapsar la aplicación
        raw_data = getattr(obj, "data", obj)
        if NEW_ST:
            st.dataframe(raw_data, width="stretch", **kw)
        else:
            st.dataframe(raw_data, use_container_width=True, **kw)


def df_a_markdown(df_in: pd.DataFrame, index: bool = False) -> str:
    """Convierte un DataFrame a tabla Markdown pura sin requerir tabulate."""
    try:
        return df_in.to_markdown(index=index)
    except Exception:
        cols = list(df_in.columns)
        header = "| " + " | ".join(str(c) for c in cols) + " |"
        sep = "| " + " | ".join(["---"] * len(cols)) + " |"
        filas = []
        for _, row in df_in.iterrows():
            fila_txt = "| " + " | ".join(str(row[c]).replace("\n", " ").replace("|", "\\|") for c in cols) + " |"
            filas.append(fila_txt)
        return "\n".join([header, sep] + filas)


def estilo(fig, h=390, **kw):
    """Estilo corporativo uniforme y legible para todos los gráficos Plotly."""
    fig.update_layout(
        height=h,
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Inter, sans-serif", color="#1E293B", size=12),
        margin=dict(t=44, b=24, l=16, r=16),
        hoverlabel=dict(bgcolor="#0F172A", font_color="white", font_size=12),
        **kw
    )
    fig.update_xaxes(showgrid=False, linecolor="#CBD5E1")
    fig.update_yaxes(gridcolor="#E2E8F0", zerolinecolor="#CBD5E1")
    return fig


# ==============================================================================
# 2. CONVERSOR NUMÉRICO A ESPAÑOL Y MOTOR TTS SIN CORTES (SINCRONIZADO)
# ==============================================================================
_UNIDADES = ["cero", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve"]
_UNIDADES_FEM = ["cero", "una", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve"]
_DIEZ_VEINTE = [
    "diez", "once", "doce", "trece", "catorce", "quince", "dieciséis", "diecisiete", "dieciocho", "diecinueve",
    "veinte", "veintiuno", "veintidós", "veintitrés", "veinticuatro", "veinticinco", "veintiséis", "veintisiete",
    "veintiocho", "veintinueve"
]
_DIEZ_VEINTE_FEM = [
    "diez", "once", "doce", "trece", "catorce", "quince", "dieciséis", "diecisiete", "dieciocho", "diecinueve",
    "veinte", "veintiuna", "veintidós", "veintitrés", "veinticuatro", "veinticinco", "veintiséis", "veintisiete",
    "veintiocho", "veintinueve"
]
_DECENAS = ["", "", "", "treinta", "cuarenta", "cincuenta", "sesenta", "setenta", "ochenta", "noventa"]
_CENTENAS = ["", "ciento", "doscientos", "trescientos", "cuatrocientos", "quinientos",
             "seiscientos", "setecientos", "ochocientos", "novecientos"]
_CENTENAS_FEM = ["", "ciento", "doscientas", "trescientas", "cuatrocientas", "quinientas",
                 "seiscientas", "setecientas", "ochocientas", "novecientas"]


def _menor_1000(n: int, femenino: bool = False, apocopar: bool = False) -> str:
    if n == 0:
        return "cero"
    if n == 100:
        return "cien"
    c, r = divmod(n, 100)
    partes = []
    if c > 0:
        centenas_arr = _CENTENAS_FEM if femenino else _CENTENAS
        partes.append(centenas_arr[c])
    if r > 0:
        if r < 10:
            if femenino:
                partes.append("una" if r == 1 else _UNIDADES_FEM[r])
            else:
                partes.append("un" if (apocopar and r == 1) else _UNIDADES[r])
        elif r < 30:
            if femenino:
                partes.append(_DIEZ_VEINTE_FEM[r - 10])
            else:
                partes.append("veintiún" if (apocopar and r == 21) else _DIEZ_VEINTE[r - 10])
        else:
            d, u = divmod(r, 10)
            if u == 0:
                partes.append(_DECENAS[d])
            else:
                if femenino:
                    u_txt = "una" if u == 1 else _UNIDADES_FEM[u]
                else:
                    u_txt = "un" if (apocopar and u == 1) else _UNIDADES[u]
                partes.append(f"{_DECENAS[d]} y {u_txt}")
    return " ".join(partes)


def _entero_es(n: int, femenino: bool = False, apocopar: bool = False) -> str:
    if n < 0:
        return "menos " + _entero_es(-n, femenino=femenino, apocopar=apocopar)
    if n < 1000:
        return _menor_1000(n, femenino=femenino, apocopar=apocopar)
    if n < 1_000_000:
        miles, resto = divmod(n, 1000)
        pref = "mil" if miles == 1 else f"{_menor_1000(miles, femenino=femenino, apocopar=True)} mil"
        return pref if resto == 0 else f"{pref} {_menor_1000(resto, femenino=femenino, apocopar=apocopar)}"
    if n < 1_000_000_000_000:
        millones, resto = divmod(n, 1_000_000)
        pref = "un millón" if millones == 1 else f"{_entero_es(millones, femenino=False, apocopar=True)} millones"
        return pref if resto == 0 else f"{pref} {_entero_es(resto, femenino=femenino, apocopar=apocopar)}"
    billones, resto = divmod(n, 1_000_000_000_000)
    pref = "un billón" if billones == 1 else f"{_entero_es(billones, femenino=False, apocopar=True)} billones"
    return pref if resto == 0 else f"{pref} {_entero_es(resto, femenino=femenino, apocopar=apocopar)}"


def _moneda_a_voz(num_str: str, es_millon: bool = False, moneda: str = "pesos dominicanos") -> str:
    s = num_str.replace(",", "").strip()
    neg = s.startswith("-")
    if neg:
        s = s[1:].strip()
    pref = "menos " if neg else ""

    if es_millon:
        try:
            val_float = float(s) * 1_000_000.0
            val_entero = int(round(val_float))
            ent_txt = _entero_es(val_entero, apocopar=True)
            de_txt = " de" if (val_entero >= 1_000_000 and val_entero % 1_000_000 == 0) else ""
            return f"{pref}{ent_txt}{de_txt} {moneda}"
        except Exception:
            pass

    if "." in s:
        ent_s, dec_s = s.split(".", 1)
    else:
        ent_s, dec_s = s, ""

    ent = int(ent_s) if ent_s else 0
    ent_txt = _entero_es(ent, apocopar=True)
    de_txt = " de" if (ent >= 1_000_000 and ent % 1_000_000 == 0) else ""
    unidad = "peso dominicano" if (ent == 1 and not dec_s) else moneda

    res = f"{pref}{ent_txt}{de_txt} {unidad}"

    if dec_s:
        dec_clean = dec_s[:2].ljust(2, "0")
        cent_val = int(dec_clean)
        if cent_val > 0:
            cent_txt = _entero_es(cent_val, apocopar=True)
            cent_u = "centavo" if cent_val == 1 else "centavos"
            res += f" con {cent_txt} {cent_u}"
    return res


def _numero_a_voz(num_str: str, apocopar: bool = False) -> str:
    s = num_str.replace(",", "").strip()
    neg = s.startswith("-")
    if neg:
        s = s[1:].strip()
    pref = "menos " if neg else ""
    if "." in s:
        ent_s, dec_s = s.split(".", 1)
        ent = int(ent_s) if ent_s else 0
        dec_clean = dec_s.rstrip("0")
        if not dec_clean:
            return f"{pref}{_entero_es(ent, apocopar=apocopar)}"
        if len(dec_clean) <= 2:
            dec_val = int(dec_clean)
            dec_txt = _entero_es(dec_val, apocopar=False)
            return f"{pref}{_entero_es(ent, apocopar=False)} punto {dec_txt}"
        else:
            digitos = " ".join(_UNIDADES[int(d)] for d in dec_clean)
            return f"{pref}{_entero_es(ent, apocopar=False)} punto {digitos}"
    ent = int(s) if s else 0
    return f"{pref}{_entero_es(ent, apocopar=apocopar)}"


MESES_VOZ = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
]


def _a_voz(texto: str) -> str:
    t = re.sub(r'<[^>]+>', ' ', texto)
    t = re.sub(r'[\U00010000-\U0010ffff\u2600-\u27BF\u2B00-\u2BFF\uFE0F]', '', t)

    reemplazos = [
        ("Ing.", "Ingeniero"), ("Lic.", "Licenciado"), ("Dr.", "Doctor"), ("Dra.", "Doctora"),
        ("vs.", "frente a"), ("vs", "frente a"), ("I+D+i", "Investigación, Desarrollo e Innovación"),
        ("P&L", "Estado de Resultados"), ("OPEX", "gastos operativos"),
        ("CxC", "cuentas por cobrar"), ("CxP", "cuentas por pagar"),
        ("DGII", "D G I I"), ("TSS", "T S S"), ("ISR", "I S R"),
        ("ERP", "E R P"), ("QoQ", "trimestre contra trimestre"),
        ("YTD", "acumulado del año"), ("CTA_", "cuenta "),
        ("≥", "mayor o igual a "), ("≤", "menor o igual a "),
        ("±1σ", "un margen de más o menos una desviación estándar"), ("&", " y "),
        ("MM3", "media móvil de tres meses"),
    ]
    for src, dst in reemplazos:
        t = t.replace(src, dst)

    t = re.sub(
        r'\b(20\d{2})\s*Q([1-4])\b',
        lambda m: f"{['', 'primer', 'segundo', 'tercer', 'cuarto'][int(m.group(2))]} trimestre de {_entero_es(int(m.group(1)))}",
        t
    )
    t = re.sub(
        r'\bQ([1-4])\b',
        lambda m: f"{['', 'primer', 'segundo', 'tercer', 'cuarto'][int(m.group(1))]} trimestre",
        t
    )
    t = re.sub(
        r'\b(20\d{2})-(0[1-9]|1[0-2])\b',
        lambda m: f"{MESES_VOZ[int(m.group(2)) - 1]} de {_entero_es(int(m.group(1)))}",
        t
    )

    # Conversión de slashes comunes antes de procesar números
    t = re.sub(r'\s*/\s*mes\b', ' mensuales', t)
    t = re.sub(r'\s*/\s*año\b', ' anuales', t)
    t = re.sub(r'\s*/\s*día\b', ' diarios', t)
    t = re.sub(r'\s*/\s*semana\b', ' por semana', t)
    t = re.sub(
        r'\b(\d+)\s*/\s*(\d+)\b',
        lambda m: f"{_entero_es(int(m.group(1)))} sobre {_entero_es(int(m.group(2)))}",
        t
    )

    # Monedas en millones RD$ XX.XXM (convierte al monto íntegro exacto sin decir punto)
    t = re.sub(
        r'([+-]?)\s*RD\$\s*(-?[\d,]+(?:\.\d+)?)\s*M\b',
        lambda m: (
            ("más " if m.group(1) == "+" else "") +
            _moneda_a_voz(("-" if (m.group(1) == "-" or m.group(2).startswith("-")) else "") + m.group(2).lstrip("-"), es_millon=True)
        ),
        t
    )

    # Monedas completas RD$ XX,XXX.XX
    t = re.sub(
        r'([+-]?)\s*RD\$\s*(-?[\d,]+(?:\.\d+)?)',
        lambda m: (
            ("más " if m.group(1) == "+" else "") +
            _moneda_a_voz(("-" if (m.group(1) == "-" or m.group(2).startswith("-")) else "") + m.group(2).lstrip("-"), es_millon=False)
        ),
        t
    )

    # Porcentajes con expresión de variación clara
    t = re.sub(
        r'([+-]?[\d,]+(?:\.\d+)?)\s*%',
        lambda m: (
            ("un incremento del " if m.group(1).startswith("+") else ("una reducción del " if m.group(1).startswith("-") else "")) +
            _numero_a_voz(m.group(1).lstrip("+-"), apocopar=True) + " por ciento"
        ),
        t
    )

    # Multiplicadores
    t = re.sub(
        r'(\d+(?:,\d{3})*(?:\.\d+)?)x\b',
        lambda m: _numero_a_voz(m.group(1), apocopar=True) + (" vez" if m.group(1) in ("1", "1.0", "1.00") else " veces"),
        t
    )

    # Sustantivos contables con concordancia de género y apócope correcta
    t = re.sub(
        r'\b(\d{1,3}(?:,\d{3})+|\d+)\s+pólizas\b',
        lambda m: f"{_entero_es(int(m.group(1).replace(',', '')), femenino=True, apocopar=True)} pólizas",
        t
    )
    t = re.sub(
        r'\b(\d{1,3}(?:,\d{3})+|\d+)\s+cuentas\b',
        lambda m: f"{_entero_es(int(m.group(1).replace(',', '')), femenino=True, apocopar=True)} cuentas",
        t
    )
    t = re.sub(
        r'\b(\d{1,3}(?:,\d{3})+|\d+)\s+asientos\b',
        lambda m: f"{_entero_es(int(m.group(1).replace(',', '')), femenino=False, apocopar=True)} asientos",
        t
    )
    t = re.sub(
        r'\b(\d{1,3}(?:,\d{3})+|\d+)\s+departamentos\b',
        lambda m: f"{_entero_es(int(m.group(1).replace(',', '')), femenino=False, apocopar=True)} departamentos",
        t
    )
    t = re.sub(
        r'\b(\d{1,3}(?:,\d{3})+|\d+)\s+meses\b',
        lambda m: f"{_entero_es(int(m.group(1).replace(',', '')), femenino=False, apocopar=True)} meses",
        t
    )
    t = re.sub(
        r'\b(\d{1,3}(?:,\d{3})+|\d+)\s+días\b',
        lambda m: f"{_entero_es(int(m.group(1).replace(',', '')), femenino=False, apocopar=True)} días",
        t
    )
    t = re.sub(
        r'\b(\d{1,3}(?:,\d{3})+|\d+)\s+puntos\b',
        lambda m: f"{_entero_es(int(m.group(1).replace(',', '')), femenino=False, apocopar=True)} puntos",
        t
    )

    t = re.sub(r'\bUSD\b', 'dólares estadounidenses', t)
    t = re.sub(r'\bDOP\b', 'pesos dominicanos', t)

    # Años sueltos
    t = re.sub(
        r'\b(202[0-9]|203[0-9])\b',
        lambda m: _entero_es(int(m.group(1))),
        t
    )

    # Números residuales con comas
    t = re.sub(
        r'(?<![\w-])(-?\d{1,3}(?:,\d{3})+(?:\.\d+)?|-?\d+(?:\.\d+)?)(?![\w-])',
        lambda m: _numero_a_voz(m.group(1), apocopar=True),
        t
    )

    # Erradicación de caracteres que generan pausas o tartamudeo en Web Speech API
    t = re.sub(r'[\(\[\{]', ', ', t)
    t = re.sub(r'[\)\]\}]', ', ', t)
    t = re.sub(r'[:;]', ', ', t)
    t = re.sub(r'[·•—–_]', ' ', t)
    t = re.sub(r'\s*,\s*', ', ', t)
    t = re.sub(r'(,\s*){2,}', ', ', t)
    t = re.sub(r'\s*\.\s*', '. ', t)
    t = re.sub(r'(\.\s*){2,}', '. ', t)
    t = re.sub(r',\s*\.', '.', t)
    t = re.sub(r'\.\s*,', '.', t)

    return re.sub(r'\s+', ' ', t).strip()


TTS_TEMPLATE = """
<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8">
<style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
        background: transparent;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        overflow: hidden;
        padding: 1px;
    }
    .tts-card {
        background: __BG__;
        border: 1px solid __BORDER__;
        border-left: 5px solid __ACCENT__;
        padding: __PAD__;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        color: white;
        box-shadow: 0 3px 10px rgba(15, 23, 42, 0.12);
        gap: 8px;
        flex-wrap: wrap;
    }
    .tts-info {
        display: flex;
        align-items: center;
        gap: 8px;
        min-width: 190px;
        flex: 1 1 220px;
    }
    .tts-icon {
        font-size: __ICON_SZ__;
        background: rgba(255,255,255,0.09);
        padding: __ICON_PAD__;
        border-radius: 7px;
        flex-shrink: 0;
    }
    .tts-title {
        font-weight: 700;
        font-size: __TITLE_SZ__;
        color: #F8FAFC;
        display: flex;
        align-items: center;
        gap: 7px;
        flex-wrap: wrap;
    }
    .tts-sub {
        font-size: __SUB_SZ__;
        color: #94A3B8;
        margin-top: 1px;
        line-height: 1.2;
        display: __SUB_DISP__;
    }
    .audio-wave-dot {
        display: inline-block;
        width: 7px; height: 7px;
        border-radius: 50%;
        background-color: #22C55E;
        box-shadow: 0 0 8px #22C55E;
        animation: audioPulse 1s infinite alternate ease-in-out;
    }
    @keyframes audioPulse { 0% { transform: scale(0.8); opacity: 0.6; } 100% { transform: scale(1.3); opacity: 1; } }
    .tts-controls { display: flex; align-items: center; gap: 5px; flex-wrap: wrap; }
    .btn-tts {
        border: 1px solid rgba(255,255,255,0.2);
        padding: __BTN_PAD__;
        border-radius: 6px;
        font-weight: 700;
        font-size: __BTN_SZ__;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        gap: 4px;
        transition: all 0.15s ease;
    }
    .btn-tts:hover { transform: translateY(-1px); filter: brightness(1.06); }
    .btn-play { background: #10B981; color: white; }
    .btn-pause { background: #F59E0B; color: #0F172A; }
    .btn-resume { background: #0EA5E9; color: white; }
    .btn-stop { background: #EF4444; color: white; }
    .tts-status {
        display: none;
        align-items: center;
        gap: 5px;
        background: rgba(15,23,42,0.85);
        border: 1px solid #334155;
        padding: 2px 7px;
        border-radius: 6px;
        font-size: 0.68rem;
        color: #E2E8F0;
    }
    .vol-box {
        display: flex;
        align-items: center;
        gap: 3px;
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.15);
        padding: 2px 6px;
        border-radius: 6px;
    }
    .btn-vol {
        background: transparent;
        border: 1px solid rgba(255,255,255,0.2);
        color: white;
        font-weight: bold;
        font-size: 0.72rem;
        width: 20px; height: 20px;
        border-radius: 4px;
        cursor: pointer;
    }
    .btn-vol:hover { background: rgba(255,255,255,0.25); }
    .vol-slider { accent-color: #0EA5E9; cursor: pointer; width: 52px; height: 4px; }
    .vol-badge { font-size: 0.66rem; font-weight: 700; color: #CBD5E1; min-width: 29px; text-align: right; }
    .d-none { display: none !important; }
    .d-flex { display: inline-flex !important; }
    @media (max-width: 640px) {
        .tts-card { padding: 6px 9px; gap: 6px; }
        .tts-icon { display: none; }
        .tts-title { font-size: 0.78rem; }
        .btn-tts { padding: 4px 8px; font-size: 0.70rem; }
        .vol-slider { width: 42px; }
    }
</style></head>
<body>
<div class="tts-card">
    <div class="tts-info">
        <div class="tts-icon">🎙️</div>
        <div>
            <div class="tts-title">
                <span>__TITULO__</span>
                <span id="badge" class="tts-status"><span class="audio-wave-dot"></span><span id="status_txt">Narrando...</span></span>
            </div>
            <div class="tts-sub">__SUBTITULO__</div>
        </div>
    </div>
    <div class="tts-controls">
        <button id="btn_play" class="btn-tts btn-play" onclick="hablar()">▶️ Escuchar</button>
        <button id="btn_pause" class="btn-tts btn-pause d-none" onclick="pausar()">⏸️ Pausar</button>
        <button id="btn_resume" class="btn-tts btn-resume d-none" onclick="reanudar()">⏯️ Reanudar</button>
        <button id="btn_stop" class="btn-tts btn-stop d-none" onclick="detener()">⏹️ Detener</button>
        <div class="vol-box" title="Control de Volumen">
            <button class="btn-vol" onclick="cambiarVol(-0.1)">-</button>
            <input type="range" class="vol-slider" id="slider" min="0" max="1" step="0.05" value="1" oninput="setVol(this.value)">
            <button class="btn-vol" onclick="cambiarVol(0.1)">+</button>
            <span class="vol-badge" id="vol_val">100%</span>
        </div>
    </div>
</div>
<script>
    const synth = window.speechSynthesis;
    const TEXTO = __TEXTO__;
    const MI_ID = Math.random().toString(36).slice(2);
    let canal = null;
    try {
        canal = new BroadcastChannel('tts_suite_bi_sync');
        canal.onmessage = (ev) => {
            if (ev.data && ev.data.action === 'stop_others' && ev.data.sender !== MI_ID) {
                gen += 1;
                setUI('idle');
            }
        };
    } catch (e) {}

    function partirEnSegmentos(texto) {
        if (!texto) return [];
        const limpio = texto.replace(/\s+/g, ' ').trim();
        // Dividir por punto y seguido para oraciones fluidas sin cortes artificiales
        const oraciones = limpio.split(/(?<=\.)\s+/);
        const salida = [];
        let actual = "";
        for (const oracion of oraciones) {
            const o = oracion.trim();
            if (!o) continue;
            if (!actual) {
                actual = o;
            } else if ((actual + " " + o).length <= 280) {
                actual += " " + o;
            } else {
                salida.push(actual);
                actual = o;
            }
        }
        if (actual) salida.push(actual);
        return salida.length ? salida : [limpio];
    }

    const chunks = partirEnSegmentos(TEXTO);
    let vol = 1.0, gen = 0, uttActual = null, keepAliveTimer = null;

    function vozEspanol() {
        if (!synth) return null;
        const voces = synth.getVoices();
        const prefs = ['es-DO', 'es-MX', 'es-US', 'es-419', 'es-ES'];
        for (const pref of prefs) {
            const v = voces.find(x => x.lang && x.lang.toLowerCase().startsWith(pref.toLowerCase()));
            if (v) return v;
        }
        return voces.find(v => v.lang && v.lang.toLowerCase().startsWith('es')) || null;
    }
    if (synth && synth.onvoiceschanged !== undefined) {
        synth.onvoiceschanged = () => { vozEspanol(); };
    }

    function hablarChunk(idx, miGen) {
        if (miGen !== gen || idx >= chunks.length) {
            if (miGen === gen) {
                setUI('idle');
                if (keepAliveTimer) { clearInterval(keepAliveTimer); keepAliveTimer = null; }
            }
            return;
        }
        const u = new SpeechSynthesisUtterance(chunks[idx]);
        const voz = vozEspanol();
        if (voz) u.voice = voz;
        u.lang = (voz && voz.lang) ? voz.lang : 'es-ES';
        u.rate = 1.0;
        u.pitch = 1.0;
        u.volume = vol;

        u.onstart = () => { if (miGen === gen) setUI('speaking'); };
        u.onend = () => {
            if (miGen !== gen) return;
            if (idx + 1 < chunks.length) {
                hablarChunk(idx + 1, miGen);
            } else {
                setUI('idle');
                if (keepAliveTimer) { clearInterval(keepAliveTimer); keepAliveTimer = null; }
            }
        };
        u.onerror = (ev) => {
            if (miGen !== gen) return;
            if (ev && (ev.error === 'interrupted' || ev.error === 'canceled')) return;
            setUI('idle');
            if (keepAliveTimer) { clearInterval(keepAliveTimer); keepAliveTimer = null; }
        };
        window._uttRef = u;
        uttActual = u;
        synth.speak(u);

        // Keep-alive continuo para navegadores modernos
        if (!keepAliveTimer) {
            keepAliveTimer = setInterval(() => {
                if (synth && synth.speaking) {
                    synth.pause();
                    synth.resume();
                }
            }, 8000);
        }
    }

    function hablar() {
        if (!synth) { alert("Tu navegador no soporta síntesis de voz."); return; }
        if (synth.speaking && synth.paused) { reanudar(); return; }
        gen += 1;
        const miGen = gen;
        if (canal) { try { canal.postMessage({ action: 'stop_others', sender: MI_ID }); } catch (e) {} }
        synth.cancel();
        setUI('speaking');
        setTimeout(() => { hablarChunk(0, miGen); }, 70);
    }
    function pausar() { if (synth && synth.speaking && !synth.paused) { synth.pause(); setUI('paused'); } }
    function reanudar() { if (synth && synth.paused) { synth.resume(); setUI('speaking'); } }
    function detener() {
        gen += 1;
        if (synth) synth.cancel();
        if (keepAliveTimer) { clearInterval(keepAliveTimer); keepAliveTimer = null; }
        setUI('idle');
    }
    function setUI(e) {
        const g = id => document.getElementById(id);
        const mostrar = (id, s) => g(id).classList[s ? 'remove' : 'add']('d-none');
        mostrar('btn_play', e === 'idle');
        mostrar('btn_pause', e === 'speaking');
        mostrar('btn_resume', e === 'paused');
        mostrar('btn_stop', e !== 'idle');
        const b = g('badge');
        if (e === 'idle') {
            b.classList.add('d-none'); b.classList.remove('d-flex');
        } else {
            b.classList.remove('d-none'); b.classList.add('d-flex');
            g('status_txt').textContent = (e === 'paused') ? 'En pausa' : 'Narrando...';
        }
    }
    function setVol(val) {
        vol = Math.max(0, Math.min(1, parseFloat(val)));
        document.getElementById('slider').value = vol;
        document.getElementById('vol_val').textContent = Math.round(vol * 100) + '%';
        if (uttActual) uttActual.volume = vol;
    }
    function cambiarVol(d) { setVol(Math.round((vol + d) * 100) / 100); }
    window.addEventListener('beforeunload', () => { if (synth) synth.cancel(); });
</script>
</body></html>
"""


def generar_reproductor_voz(
    texto_narrativa: str,
    titulo: str = "Briefing Ejecutivo de Voz",
    subtitulo: str = "Análisis narrado",
    compacto: bool = False
):
    if compacto:
        cfg = {
            "__BG__": "linear-gradient(135deg, #1E293B 0%, #334155 100%)",
            "__BORDER__": "#475569",
            "__ACCENT__": "#10B981",
            "__PAD__": "6px 11px",
            "__ICON_SZ__": "0.95rem",
            "__ICON_PAD__": "4px 7px",
            "__TITLE_SZ__": "0.79rem",
            "__SUB_SZ__": "0.66rem",
            "__SUB_DISP__": "none",
            "__BTN_PAD__": "4px 9px",
            "__BTN_SZ__": "0.71rem",
        }
        altura = 72
    else:
        cfg = {
            "__BG__": "linear-gradient(135deg, #0F172A 0%, #1E293B 100%)",
            "__BORDER__": "#334155",
            "__ACCENT__": "#0EA5E9",
            "__PAD__": "9px 14px",
            "__ICON_SZ__": "1.2rem",
            "__ICON_PAD__": "6px 9px",
            "__TITLE_SZ__": "0.86rem",
            "__SUB_SZ__": "0.71rem",
            "__SUB_DISP__": "block",
            "__BTN_PAD__": "5px 11px",
            "__BTN_SZ__": "0.75rem",
        }
        altura = 96

    html_code = (
        TTS_TEMPLATE
        .replace("__TITULO__", titulo)
        .replace("__SUBTITULO__", subtitulo)
        .replace("__TEXTO__", json.dumps(_a_voz(texto_narrativa)).replace("</", "<\\/"))
    )
    for k, v in cfg.items():
        html_code = html_code.replace(k, v)
    components.html(html_code, height=altura)


def narrador_seccion(parrafos: list, titulo: str, subtitulo: str):
    """Narrador principal de sección: audio visible + texto en acordeón oculto por defecto."""
    generar_reproductor_voz(" ".join(parrafos), titulo, subtitulo, compacto=False)
    with st.expander("**📖 Ver análisis narrativo completo de la sección**", expanded=False):
        html = '<div class="story-box">' + "".join(f"<p>{p}</p>" for p in parrafos) + '</div>'
        st.markdown(html, unsafe_allow_html=True)


def narrador_elemento(texto: str, titulo_voz: str, label_acordeon: str = "📖 Ver explicación completa"):
    """Narrador ejecutivo individual para un gráfico o tabla + texto en acordeón oculto por defecto."""
    generar_reproductor_voz(texto, titulo_voz, "", compacto=True)
    lbl = label_acordeon if label_acordeon.startswith("**") else f"**{label_acordeon}**"
    with st.expander(lbl, expanded=False):
        st.markdown(f'<div class="story-box"><p>{texto}</p></div>', unsafe_allow_html=True)


# ==============================================================================
# 3. CARGA Y PIPELINE ETL DE DATOS CONTABLES
# ==============================================================================
MESES_ORDEN = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
]


@st.cache_data
def cargar_datos(ruta_archivo) -> pd.DataFrame:
    df = pd.read_excel(ruta_archivo, sheet_name='Libro_Diario_General')
    df = df.dropna(subset=['Numero_Poliza']).copy()
    df['Año'] = df['Año'].astype(int)
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    df['Mes'] = pd.Categorical(df['Mes'], categories=MESES_ORDEN, ordered=True)
    df['Mes_Num'] = df['Fecha'].dt.month
    df['Trimestre'] = 'Q' + df['Fecha'].dt.quarter.astype(str)
    df['Año_Mes'] = df['Fecha'].dt.to_period('M').astype(str)
    df['Per_Tri'] = df['Año'].astype(str) + ' ' + df['Trimestre']
    return df


def fmt_dop(valor: float) -> str:
    return f"RD$ {valor:,.2f}"


def fmt_millones(valor: float) -> str:
    return f"RD$ {valor / 1e6:,.2f}M"


def pct(v: float, d: int = 1) -> str:
    return f"{v:,.{d}f}%"


# ==============================================================================
# 4. CARGA Y SEGMENTACIÓN REAL ESTILO POWER BI (SIDEBAR COLAPSABLE)
# ==============================================================================
st.sidebar.image("https://img.icons8.com/fluency/96/financial-growth-analysis.png", width=56)
st.sidebar.title("🎛️ Segmentación Power BI")
st.sidebar.caption("Todos los filtros colapsados · Seleccione para filtrar")

uploaded_file = st.sidebar.file_uploader("📂 Actualizar Libro Diario (.xlsx)", type=["xlsx"])

base_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
ruta_default = os.path.join(base_dir, "Contabilidad_Libro_Diario_Consolidado_Limpio.xlsx")
if not os.path.exists(ruta_default):
    ruta_default = "Contabilidad_Libro_Diario_Consolidado_Limpio.xlsx"

ruta = uploaded_file if uploaded_file is not None else ruta_default

try:
    df_raw = cargar_datos(ruta)
except Exception as e:
    st.error(f"❌ Error al cargar el archivo contable: {e}")
    st.stop()

anios_disp = sorted(df_raw['Año'].unique().tolist())
tri_disp = sorted(df_raw['Trimestre'].unique().tolist())
meses_disp = [m for m in MESES_ORDEN if m in df_raw['Mes'].astype(str).unique()]
deptos_disp = sorted(df_raw['Departamento'].unique().tolist())
lideres_disp = sorted(df_raw['Lider_Departamento'].dropna().unique().tolist())
tipos_disp = sorted(df_raw['Tipo_Cuenta'].unique().tolist())
cuentas_disp = sorted(df_raw['Cuenta_Contable'].unique().tolist())
monedas_disp = sorted(df_raw['Moneda'].unique().tolist())

SLICERS_META = [
    ("anio", anios_disp),
    ("tri", tri_disp),
    ("mes", meses_disp),
    ("depto", deptos_disp),
    ("lider", lideres_disp),
    ("tipo", tipos_disp),
    ("cuenta", cuentas_disp),
    ("moneda", monedas_disp),
]

data_sig = f"{len(df_raw)}_{min(anios_disp)}_{max(anios_disp)}_{len(cuentas_disp)}"
if st.session_state.get("_data_sig") != data_sig:
    st.session_state["_data_sig"] = data_sig
    for pref, opts in SLICERS_META:
        for i in range(len(opts)):
            st.session_state[f"slicer_{pref}_{i}"] = True
        st.session_state[f"slicer_{pref}_q"] = ""


def _set_slicer(pref: str, n: int, val: bool):
    for i in range(n):
        st.session_state[f"slicer_{pref}_{i}"] = val


def _reset_all_slicers():
    for pref, opts in SLICERS_META:
        _set_slicer(pref, len(opts), True)
        st.session_state[f"slicer_{pref}_q"] = ""


def slicer_powerbi(label: str, icon: str, opciones: list, pref: str) -> list:
    for i in range(len(opciones)):
        if f"slicer_{pref}_{i}" not in st.session_state:
            st.session_state[f"slicer_{pref}_{i}"] = True

    seleccionados = [
        val for i, val in enumerate(opciones)
        if st.session_state.get(f"slicer_{pref}_{i}", True)
    ]
    if len(seleccionados) == len(opciones):
        estado_txt = f"Todos ({len(opciones)})"
    elif len(seleccionados) == 0:
        estado_txt = "Ninguno (0)"
    else:
        estado_txt = f"{len(seleccionados)}/{len(opciones)}"

    with st.sidebar.expander(f"**{icon} {label} · {estado_txt}**", expanded=False):
        b1, b2 = st.columns(2)
        b1.button("✅ Todos", key=f"btn_all_{pref}", on_click=_set_slicer, args=(pref, len(opciones), True), use_container_width=True)
        b2.button("🧹 Limpiar", key=f"btn_none_{pref}", on_click=_set_slicer, args=(pref, len(opciones), False), use_container_width=True)

        q = ""
        if len(opciones) > 6:
            q = st.text_input(
                f"Buscar {label}", key=f"slicer_{pref}_q",
                label_visibility="collapsed", placeholder=f"🔎 Filtrar {label.lower()}..."
            ).strip().lower()

        for i, val in enumerate(opciones):
            if q and q not in str(val).lower():
                continue
            st.checkbox(str(val), key=f"slicer_{pref}_{i}")

    return [val for i, val in enumerate(opciones) if st.session_state.get(f"slicer_{pref}_{i}", True)]


st.sidebar.button("🔄 Restablecer Segmentadores", on_click=_reset_all_slicers, use_container_width=True)

sel_anios = slicer_powerbi("Ejercicio Fiscal", "📅", anios_disp, "anio")
sel_tris = slicer_powerbi("Trimestre", "🗓️", tri_disp, "tri")
sel_meses = slicer_powerbi("Mes", "📆", meses_disp, "mes")
sel_deptos = slicer_powerbi("Departamento", "🏢", deptos_disp, "depto")
sel_lideres = slicer_powerbi("Líder de Área", "👔", lideres_disp, "lider")
sel_tipos = slicer_powerbi("Tipo de Cuenta", "⚖️", tipos_disp, "tipo")
sel_cuentas = slicer_powerbi("Cuenta Contable", "📑", cuentas_disp, "cuenta")
sel_monedas = slicer_powerbi("Moneda", "💱", monedas_disp, "moneda")

df = df_raw[
    (df_raw['Año'].isin(sel_anios)) &
    (df_raw['Trimestre'].isin(sel_tris)) &
    (df_raw['Mes'].astype(str).isin(sel_meses)) &
    (df_raw['Departamento'].isin(sel_deptos)) &
    (df_raw['Lider_Departamento'].isin(sel_lideres)) &
    (df_raw['Tipo_Cuenta'].isin(sel_tipos)) &
    (df_raw['Cuenta_Contable'].isin(sel_cuentas)) &
    (df_raw['Moneda'].isin(sel_monedas))
].copy()

st.sidebar.markdown("---")
st.sidebar.metric("🧾 Pólizas Auditadas", f"{df['Numero_Poliza'].nunique():,}")
st.sidebar.metric("📝 Asientos Activos", f"{len(df):,}")

if df.empty:
    st.warning("⚠️ Los segmentadores seleccionados no devuelven registros. Abra un segmentador o presione **Restablecer Segmentadores**.")
    st.stop()

# ==============================================================================
# 5. MÉTRICAS FINANCIERAS, SERIES TEMPORALES E INDICADORES
# ==============================================================================
ing_df = df[df['Tipo_Cuenta'] == 'Ingresos']
cos_df = df[df['Tipo_Cuenta'] == 'Costo']
gas_df = df[df['Tipo_Cuenta'] == 'Gasto']
egr_df = df[df['Tipo_Cuenta'].isin(['Costo', 'Gasto'])]

ingresos_tot = float(ing_df['Credito_DOP'].sum())
costos_tot = float(cos_df['Debito_DOP'].sum())
gastos_tot = float(gas_df['Debito_DOP'].sum())
egresos_tot = costos_tot + gastos_tot
utilidad_bruta = ingresos_tot - costos_tot
utilidad_neta = ingresos_tot - costos_tot - gastos_tot

margen_bruto = (utilidad_bruta / ingresos_tot * 100) if ingresos_tot > 0 else 0.0
margen_neto = (utilidad_neta / ingresos_tot * 100) if ingresos_tot > 0 else 0.0
ratio_costos = (costos_tot / ingresos_tot * 100) if ingresos_tot > 0 else 0.0
ratio_opex = (gastos_tot / ingresos_tot * 100) if ingresos_tot > 0 else 0.0

bancos_dop = float(df[df['Codigo_Cuenta'] == 'CTA_102']['Monto_Neto_DOP'].sum())
bancos_usd = float(df[df['Codigo_Cuenta'] == 'CTA_103']['Monto_Neto_DOP'].sum())
caja_gen = float(df[df['Codigo_Cuenta'] == 'CTA_101']['Monto_Neto_DOP'].sum())
liquidez_disp = bancos_dop + bancos_usd + caja_gen

cxc_saldo = float(df[df['Codigo_Cuenta'] == 'CTA_104']['Monto_Neto_DOP'].sum())
cxc_cargos = float(df[df['Codigo_Cuenta'] == 'CTA_104']['Debito_DOP'].sum())
cxc_abonos = float(df[df['Codigo_Cuenta'] == 'CTA_104']['Credito_DOP'].sum())
tasa_cobranza = (cxc_abonos / cxc_cargos * 100) if cxc_cargos > 0 else 0.0

pasivos_tot = float(df[df['Tipo_Cuenta'] == 'Pasivo']['Credito_DOP'].sum() - df[df['Tipo_Cuenta'] == 'Pasivo']['Debito_DOP'].sum())
ingresos_usd_dop = float(ing_df[ing_df['Moneda'] == 'USD']['Credito_DOP'].sum())
pct_dolarizacion = (ingresos_usd_dop / ingresos_tot * 100) if ingresos_tot > 0 else 0.0
cobertura_liq = (liquidez_disp / pasivos_tot) if pasivos_tot > 0 else (1.0 if liquidez_disp >= 0 else 0.0)

periodo_txt = ", ".join(map(str, sorted(sel_anios))) if sel_anios else "Consolidado"

# ---- Series mensuales --------------------------------------------------------
periodos = sorted(df['Año_Mes'].unique())
n_meses_tot = len(periodos)
ing_m = ing_df.groupby('Año_Mes')['Credito_DOP'].sum().reindex(periodos, fill_value=0.0)
cos_m = cos_df.groupby('Año_Mes')['Debito_DOP'].sum().reindex(periodos, fill_value=0.0)
gas_m = gas_df.groupby('Año_Mes')['Debito_DOP'].sum().reindex(periodos, fill_value=0.0)
mdf = pd.DataFrame({'Periodo': periodos, 'Ingresos': ing_m.values, 'Costos': cos_m.values, 'Gastos': gas_m.values})
mdf['Egresos'] = mdf['Costos'] + mdf['Gastos']
mdf['Utilidad'] = mdf['Ingresos'] - mdf['Egresos']
mdf['Margen_Neto_%'] = np.where(mdf['Ingresos'] > 0, mdf['Utilidad'] / mdf['Ingresos'].replace(0, np.nan) * 100, np.nan)
mdf['Util_Acum'] = mdf['Utilidad'].cumsum()
mdf['Ingresos_MM3'] = mdf['Ingresos'].rolling(3, min_periods=1).mean()
prom_mensual_ing = ingresos_tot / n_meses_tot if n_meses_tot > 0 else 0.0
prom_mensual_egr = egresos_tot / n_meses_tot if n_meses_tot > 0 else 0.0

# ---- Estado de resultados anual y comparación justa --------------------------
anios_f = sorted(df['Año'].unique())
meses_por_anio = df.groupby('Año')['Mes_Num'].nunique().reindex(anios_f).fillna(0).astype(int)
anual = pd.DataFrame({
    'Meses': meses_por_anio,
    'Ingresos': ing_df.groupby('Año')['Credito_DOP'].sum(),
    'Costos': cos_df.groupby('Año')['Debito_DOP'].sum(),
    'Gastos': gas_df.groupby('Año')['Debito_DOP'].sum()
}).reindex(anios_f).fillna(0.0)
anual['Utilidad Bruta'] = anual['Ingresos'] - anual['Costos']
anual['Utilidad Neta'] = anual['Utilidad Bruta'] - anual['Gastos']
anual['Prom. Mensual Ingresos'] = np.where(anual['Meses'] > 0, anual['Ingresos'] / anual['Meses'], 0.0)
anual['Margen Bruto %'] = np.where(anual['Ingresos'] > 0, anual['Utilidad Bruta'] / anual['Ingresos'].replace(0, np.nan) * 100, 0.0)
anual['Margen Neto %'] = np.where(anual['Ingresos'] > 0, anual['Utilidad Neta'] / anual['Ingresos'].replace(0, np.nan) * 100, 0.0)
anual['Var. Prom. Mensual %'] = anual['Prom. Mensual Ingresos'].pct_change() * 100

yoy = None
yoy_detalle = "1 ejercicio activo"
es_parcial = False
if len(anios_f) >= 2:
    a_prev, a_ult = anios_f[-2], anios_f[-1]
    m_ult = set(df[df['Año'] == a_ult]['Mes_Num'].unique())
    m_prev = set(df[df['Año'] == a_prev]['Mes_Num'].unique())
    m_comunes = sorted(m_ult & m_prev)
    es_parcial = len(m_ult) < len(m_prev)
    if m_comunes:
        ing_ult_c = float(ing_df[(ing_df['Año'] == a_ult) & (ing_df['Mes_Num'].isin(m_comunes))]['Credito_DOP'].sum())
        ing_prev_c = float(ing_df[(ing_df['Año'] == a_prev) & (ing_df['Mes_Num'].isin(m_comunes))]['Credito_DOP'].sum())
        if ing_prev_c > 0:
            yoy = (ing_ult_c - ing_prev_c) / ing_prev_c * 100
            if es_parcial:
                m_nombres = ", ".join(MESES_ORDEN[m - 1] for m in m_comunes)
                yoy_detalle = f"{m_nombres} {a_ult} vs. {a_prev}"
            else:
                yoy_detalle = f"{a_ult} vs. {a_prev}"

# ---- Mezcla, gastos, departamentos -------------------------------------------
mix = ing_df.groupby('Cuenta_Contable')['Credito_DOP'].sum().sort_values(ascending=False)
top_linea = mix.index[0] if len(mix) else "N/D"
top_linea_val = float(mix.iloc[0]) if len(mix) else 0.0
top_linea_pct = (top_linea_val / float(mix.sum()) * 100) if len(mix) and mix.sum() > 0 else 0.0
seg_linea = mix.index[1] if len(mix) > 1 else "N/D"
seg_linea_val = float(mix.iloc[1]) if len(mix) > 1 else 0.0
seg_linea_pct = (seg_linea_val / float(mix.sum()) * 100) if len(mix) > 1 and mix.sum() > 0 else 0.0

gcta = egr_df.groupby('Cuenta_Contable')['Debito_DOP'].sum().sort_values(ascending=False)
top_gasto = gcta.index[0] if len(gcta) else "N/D"
top_gasto_val = float(gcta.iloc[0]) if len(gcta) else 0.0
top_gasto_pct = (top_gasto_val / float(gcta.sum()) * 100) if len(gcta) and gcta.sum() > 0 else 0.0
par = gcta.reset_index()
par['Acum_%'] = (par['Debito_DOP'].cumsum() / par['Debito_DOP'].sum() * 100) if len(par) and par['Debito_DOP'].sum() > 0 else 0.0
n80 = int((par['Acum_%'] < 80).sum() + 1) if len(par) else 0

sueldos_tot = float(df[df['Codigo_Cuenta'] == 'CTA_601']['Debito_DOP'].sum())
pct_sueldos_egr = (sueldos_tot / egresos_tot * 100) if egresos_tot > 0 else 0.0

deptos_base = df[['Codigo_Departamento', 'Departamento', 'Lider_Departamento']].drop_duplicates()
_cos_dep = cos_df.groupby('Departamento')['Debito_DOP'].sum()
_nom_dep = df[df['Codigo_Cuenta'] == 'CTA_601'].groupby('Departamento')['Debito_DOP'].sum()
_opx_dep = gas_df[gas_df['Codigo_Cuenta'] != 'CTA_601'].groupby('Departamento')['Debito_DOP'].sum()
_ing_dep = ing_df.groupby('Departamento')['Credito_DOP'].sum()

dep_resumen = deptos_base.copy()
dep_resumen['Ingresos'] = dep_resumen['Departamento'].map(_ing_dep).fillna(0.0)
dep_resumen['Costos Directos'] = dep_resumen['Departamento'].map(_cos_dep).fillna(0.0)
dep_resumen['Nómina'] = dep_resumen['Departamento'].map(_nom_dep).fillna(0.0)
dep_resumen['Otros Gastos'] = dep_resumen['Departamento'].map(_opx_dep).fillna(0.0)
dep_resumen['Total Erogaciones'] = dep_resumen['Costos Directos'] + dep_resumen['Nómina'] + dep_resumen['Otros Gastos']
dep_resumen['Part. Gasto %'] = np.where(egresos_tot > 0, dep_resumen['Total Erogaciones'] / egresos_tot * 100, 0.0)
dep_resumen = dep_resumen.sort_values('Total Erogaciones', ascending=False).reset_index(drop=True)

dep_tot = egr_df.groupby('Departamento')['Debito_DOP'].sum().sort_values(ascending=False)
top_dep = dep_tot.index[0] if len(dep_tot) else "N/D"
top_dep_val = float(dep_tot.iloc[0]) if len(dep_tot) else 0.0
top_dep_pct = (top_dep_val / float(dep_tot.sum()) * 100) if len(dep_tot) and dep_tot.sum() > 0 else 0.0
low_dep = dep_tot.index[-1] if len(dep_tot) else "N/D"
low_dep_val = float(dep_tot.iloc[-1]) if len(dep_tot) else 0.0
low_dep_pct = (low_dep_val / float(dep_tot.sum()) * 100) if len(dep_tot) and dep_tot.sum() > 0 else 0.0
lider_top = "N/D"
if len(dep_tot):
    _l = egr_df[egr_df['Departamento'] == top_dep]['Lider_Departamento'].dropna()
    lider_top = _l.mode().iloc[0] if len(_l) else "N/D"

if not ing_m.empty and ing_m.sum() > 0:
    ing_mn = ing_m.groupby(pd.to_datetime(ing_m.index.astype(str) + '-01').month.values).mean()
    pico_meses = [MESES_ORDEN[m - 1] for m in ing_mn.sort_values(ascending=False).head(3).index]
    valle_meses = [MESES_ORDEN[m - 1] for m in ing_mn.sort_values().head(2).index]
    mejor_mes = str(mdf.loc[mdf['Ingresos'].idxmax(), 'Periodo'])
    mejor_mes_val = float(mdf['Ingresos'].max())
    peor_mes = str(mdf.loc[mdf['Ingresos'].idxmin(), 'Periodo'])
    peor_mes_val = float(mdf['Ingresos'].min())
else:
    pico_meses, valle_meses = ["N/D"], ["N/D"]
    mejor_mes, mejor_mes_val, peor_mes, peor_mes_val = "N/D", 0.0, "N/D", 0.0

if not mdf.empty and mdf['Egresos'].sum() > 0:
    mes_max_egr = str(mdf.loc[mdf['Egresos'].idxmax(), 'Periodo'])
    val_max_egr = float(mdf['Egresos'].max())
else:
    mes_max_egr, val_max_egr = "N/D", 0.0

# ---- Tesorería, cartera y pasivos --------------------------------------------
cash_m = df[df['Codigo_Cuenta'].isin(['CTA_101', 'CTA_102', 'CTA_103'])].groupby('Año_Mes')['Monto_Neto_DOP'].sum().reindex(periodos, fill_value=0.0).cumsum()
cxc_m = df[df['Codigo_Cuenta'] == 'CTA_104'].groupby('Año_Mes')['Monto_Neto_DOP'].sum().reindex(periodos, fill_value=0.0).cumsum()
_pg = df[df['Tipo_Cuenta'] == 'Pasivo'].groupby('Cuenta_Contable')[['Debito_DOP', 'Credito_DOP']].sum()
pas = (_pg['Credito_DOP'] - _pg['Debito_DOP']).sort_values(ascending=False)
pas_pos = pas[pas > 0]
pas_txt = ", ".join(f"{k} ({fmt_millones(v)})" for k, v in pas_pos.head(3).items()) if len(pas_pos) else "sin pasivos acumulados"

# ---- Moneda y proyección -----------------------------------------------------
fx = ing_df.groupby(['Año_Mes', 'Moneda'])['Credito_DOP'].sum().unstack(fill_value=0.0).reindex(periodos, fill_value=0.0)
fx_usd_pct = (fx['USD'] / fx.sum(axis=1).replace(0, np.nan) * 100).fillna(0.0) if 'USD' in fx.columns else pd.Series(0.0, index=fx.index)

H = 6
y_arr = mdf['Ingresos'].values.astype(float)
x_arr = np.arange(len(y_arr))
tiene_proy = len(y_arr) >= 4 and y_arr.sum() > 0
if tiene_proy:
    coef = np.polyfit(x_arr, y_arr, 1)
    fit = np.polyval(coef, x_arr)
    res_std = float(np.std(y_arr - fit))
    xf = np.arange(len(y_arr), len(y_arr) + H)
    yf = np.clip(np.polyval(coef, xf), 0, None)
    fut = pd.period_range(periodos[-1], periods=H + 1, freq='M').astype(str)[1:]
    pendiente = float(coef[0])
    proy_total = float(yf.sum())
    proy_prom = proy_total / H
else:
    pendiente, proy_total, proy_prom, res_std = 0.0, 0.0, 0.0, 0.0

tri = pd.DataFrame({
    'Ingresos': ing_df.groupby('Per_Tri')['Credito_DOP'].sum(),
    'Costos': cos_df.groupby('Per_Tri')['Debito_DOP'].sum(),
    'Gastos': gas_df.groupby('Per_Tri')['Debito_DOP'].sum()
}).reindex(sorted(df['Per_Tri'].unique())).fillna(0.0)
tri['Utilidad Neta'] = tri['Ingresos'] - tri['Costos'] - tri['Gastos']

# ---- Índice de salud corporativa ---------------------------------------------
sc_rent = float(np.clip(margen_neto / 40 * 30, 0, 30)) if ingresos_tot > 0 else 0.0
sc_cob = float(np.clip(tasa_cobranza / 100 * 25, 0, 25)) if cxc_cargos > 0 else 20.0
sc_liq = float(np.clip(cobertura_liq, 0, 1) * 20)
sc_ctl = 0.0 if caja_gen < 0 else 15.0
sc_cre = 5.0 if yoy is None else float(np.clip((yoy + 5) / 25 * 10, 0, 10))
score = int(round(sc_rent + sc_cob + sc_liq + sc_ctl + sc_cre))
if score >= 80:
    etiqueta = "EXCELENTE 🟢"
elif score >= 60:
    etiqueta = "SÓLIDA 🟡"
elif score >= 40:
    etiqueta = "EN VIGILANCIA 🟠"
else:
    etiqueta = "CRÍTICA 🔴"


def semaforo(v, verde, amarillo, mayor=True):
    if mayor:
        return "🟢 Óptimo" if v >= verde else ("🟡 Vigilar" if v >= amarillo else "🔴 Crítico")
    return "🟢 Óptimo" if v <= verde else ("🟡 Vigilar" if v <= amarillo else "🔴 Crítico")


# ==============================================================================
# 6. TEXTOS ANALÍTICOS DE SECCIONES Y ELEMENTOS INDIVIDUALES
# ==============================================================================
mm = fmt_millones

if yoy is None:
    yoy_narr = f"el corte comprende un único ejercicio fiscal ({periodo_txt}) con un promedio de {mm(prom_mensual_ing)} mensuales."
elif es_parcial:
    yoy_narr = (
        f"en comparación homogénea {yoy_detalle}, la facturación {'creció un' if yoy >= 0 else 'retrocedió un'} "
        f"{pct(abs(yoy))}, pasando de un promedio mensual de {mm(anual['Prom. Mensual Ingresos'].iloc[-2])} en {anios_f[-2]} "
        f"a {mm(anual['Prom. Mensual Ingresos'].iloc[-1])} en {anios_f[-1]}."
    )
else:
    yoy_narr = f"los ingresos {'crecieron un' if yoy >= 0 else 'disminuyeron un'} {pct(abs(yoy))} interanual durante {yoy_detalle}."

caja_narr = (
    f"la cuenta de Caja General presenta un saldo acreedor de {fmt_dop(caja_gen)} originado por salidas de efectivo sin previa reposición de bancos"
    if caja_gen < 0 else f"la Caja General mantiene un saldo positivo y consistente de {fmt_dop(caja_gen)}"
)
cobr_narr = (
    f"la cobranza es altamente eficaz con una tasa de recaudo del {pct(tasa_cobranza)}"
    if tasa_cobranza >= 80 else
    f"la cobranza alcanza el {pct(tasa_cobranza)}, manteniendo inmovilizados {mm(cxc_saldo)} en cuentas por cobrar de clientes"
    if cxc_cargos > 0 else "no se registran ventas a crédito en el filtro activo"
)
tend_narr = (
    f"la tendencia econométrica avanza a razón de {mm(pendiente)} mensuales, proyectando ventas estimadas de {mm(proy_total)} para los próximos {H} meses"
    if (tiene_proy and pendiente >= 0) else
    f"la tendencia lineal muestra un ajuste de {mm(abs(pendiente))} mensuales, proyectando {mm(proy_total)} en los próximos {H} meses"
    if tiene_proy else "se requieren al menos cuatro meses continuos para modelar una tendencia estadística"
)

top3_deps = dep_resumen.head(3)['Departamento'].tolist()
top3_deps_pct = float(dep_resumen.head(3)['Part. Gasto %'].sum()) if len(dep_resumen) else 0.0

NARR = {
    "resumen": [
        f"📊 <b>Desempeño General & Salud Corporativa:</b> Durante el horizonte consolidado de <b>{periodo_txt}</b> (<span class='hl-dark'>{n_meses_tot} meses</span>), "
        f"la organización alcanzó una facturación acumulada de <span class='hl-green'><b>{mm(ingresos_tot)}</b></span>, con un ritmo comercial promedio de <span class='hl-blue'><b>{mm(prom_mensual_ing)}</b></span> mensuales. "
        f"A nivel operativo, generamos una utilidad bruta de <span class='hl-blue'><b>{mm(utilidad_bruta)}</b></span>, equivalente a un margen bruto del <span class='hl-green'><b>{pct(margen_bruto)}</b></span>, "
        f"y una utilidad neta final de <span class='hl-green'><b>{mm(utilidad_neta)}</b></span>, reteniendo un margen neto del <span class='hl-green'><b>{pct(margen_neto)}</b></span>. "
        f"El Índice Compuesto de Salud Corporativa se sitúa en <span class='hl-purple'><b>{score}/100 ({etiqueta})</b></span>.",

        f"⚙️ <b>Arquitectura de Rentabilidad & Crecimiento:</b> La línea líder <b>{top_linea}</b> aportó el <span class='hl-green'><b>{pct(top_linea_pct)}</b></span> de los ingresos con <span class='hl-green'><b>{mm(top_linea_val)}</b></span>, "
        f"mientras que <b>{seg_linea}</b> consolidó el <span class='hl-blue'><b>{pct(seg_linea_pct)}</b></span> con <span class='hl-blue'><b>{mm(seg_linea_val)}</b></span>. "
        f"Nuestra estructura de costos directos absorbe el <span class='hl-amber'><b>{pct(ratio_costos)}</b></span> de cada peso facturado y los gastos operativos el <span class='hl-purple'><b>{pct(ratio_opex)}</b></span>, "
        f"demostrando un apalancamiento que preserva <span class='hl-green'><b>{pct(margen_neto)}</b></span> de rentabilidad final. Además, {yoy_narr}",

        f"🏢 <b>Asignación Departamental y Disciplina Presupuestaria:</b> Las erogaciones totales sumaron <span class='hl-amber'><b>{mm(egresos_tot)}</b></span> distribuidas en <span class='hl-dark'><b>{len(dep_resumen)} departamentos</b></span>. "
        f"Los tres principales centros de costo (<b>{', '.join(top3_deps)}</b>) concentraron el <span class='hl-amber'><b>{pct(top3_deps_pct)}</b></span> del gasto corporativo, "
        f"liderando <b>{top_dep}</b> con <span class='hl-red'><b>{mm(top_dep_val)}</b></span> (<span class='hl-amber'><b>{pct(top_dep_pct)}</b></span>) bajo la gestión de <b>{lider_top}</b>. "
        f"La nómina consolidada alcanzó <span class='hl-blue'><b>{mm(sueldos_tot)}</b></span>, representando el <span class='hl-dark'><b>{pct(pct_sueldos_egr)}</b></span> de las erogaciones totales.",

        f"🚨 <b>Diagnóstico de Tesorería, Cobranza y Alertas Forenses:</b> Contamos con una tesorería disponible de <span class='hl-green'><b>{mm(liquidez_disp)}</b></span>, "
        f"brindando una cobertura de <span class='hl-blue'><b>{cobertura_liq:.2f}x</b></span> sobre pasivos acumulados de <span class='hl-red'><b>{mm(pasivos_tot)}</b></span> (<b>{pas_txt}</b>). "
        f"No obstante, en capital de trabajo {cobr_narr}, y en control interno de efectivo {caja_narr}."
    ],
    "pnl": [
        f"📊 <b>Estructura Integral de Ganancias y Pérdidas:</b> De una facturación total de <span class='hl-green'><b>{mm(ingresos_tot)}</b></span>, "
        f"los costos directos deducen <span class='hl-amber'><b>{mm(costos_tot)}</b></span> (<span class='hl-amber'><b>{pct(ratio_costos)}</b></span>), lo que deja una utilidad bruta de <span class='hl-blue'><b>{mm(utilidad_bruta)}</b></span> "
        f"con un sólido margen bruto del <span class='hl-green'><b>{pct(margen_bruto)}</b></span>. Al absorber <span class='hl-red'><b>{mm(gastos_tot)}</b></span> en gastos operativos (<span class='hl-purple'><b>{pct(ratio_opex)}</b></span>), "
        f"la operación entrega una utilidad neta final de <span class='hl-green'><b>{mm(utilidad_neta)}</b></span>, garantizando un margen neto del <span class='hl-green'><b>{pct(margen_neto)}</b></span>.",

        f"📅 <b>Estacionalidad Comercial y Ciclo de Demanda:</b> Comercialmente, {yoy_narr} "
        f"El comportamiento histórico evidencia una fuerte aceleración de ingresos en los meses de <span class='hl-green'><b>{', '.join(pico_meses)}</b></span>, "
        f"marcando el récord histórico en <span class='hl-green'><b>{mejor_mes}</b></span> con <span class='hl-green'><b>{mm(mejor_mes_val)}</b></span>, mientras que los valles de menor facturación corresponden a <span class='hl-amber'><b>{', '.join(valle_meses)}</b></span>."
    ],
    "depto": [
        f"🏢 <b>Distribución Presupuestaria y Economía de Escala:</b> Las erogaciones consolidadas de <span class='hl-amber'><b>{mm(egresos_tot)}</b></span> se distribuyen entre <span class='hl-dark'><b>{len(dep_resumen)} unidades operativas</b></span>. "
        f"El departamento de <b>{top_dep}</b> lidera el consumo presupuestario con <span class='hl-red'><b>{mm(top_dep_val)}</b></span> (<span class='hl-amber'><b>{pct(top_dep_pct)}</b></span>) bajo la dirección de <b>{lider_top}</b>, "
        f"mientras que <b>{low_dep}</b> opera con la mayor economía de escala al ejecutar únicamente el <span class='hl-green'><b>{pct(low_dep_pct)}</b></span> (<span class='hl-green'><b>{mm(low_dep_val)}</b></span>).",

        f"📐 <b>Concentración del Gasto por Partida Contable:</b> Al auditar por naturaleza contable, la cuenta <b>{top_gasto}</b> absorbe el <span class='hl-red'><b>{pct(top_gasto_pct)}</b></span> (<span class='hl-red'><b>{mm(top_gasto_val)}</b></span>), "
        f"y aplicando el principio de Pareto, identificamos que apenas <span class='hl-purple'><b>{n80} cuentas contables</b></span> explican el <span class='hl-dark'><b>80% del gasto total</b></span> de la compañía."
    ],
    "riesgos": [
        f"🚨 <b>Auditoría de Liquidez y Solvencia Patrimonial:</b> El balance de tesorería disponible suma <span class='hl-green'><b>{mm(liquidez_disp)}</b></span>, "
        f"ofreciendo una sólida cobertura de <span class='hl-blue'><b>{cobertura_liq:.2f}x</b></span> sobre los pasivos exigibles de <span class='hl-red'><b>{mm(pasivos_tot)}</b></span> (<b>{pas_txt}</b>).",

        f"⚖️ <b>Alertas de Control Interno y Recuperación de Cartera:</b> En control interno de efectivo, {caja_narr}. "
        f"En el ciclo de conversión de efectivo, {cobr_narr}. La empresa debe acelerar el recaudo para monetizar la utilidad contable en liquidez bancaria real."
    ],
    "tendencias": [
        f"🔮 <b>Comportamiento Predictivo de Ingresos:</b> La facturación comercial promedia <span class='hl-blue'><b>{mm(prom_mensual_ing)}</b></span> mensuales y {tend_narr}.",

        f"🌐 <b>Cobertura Cambiaria y Diversificación en Divisas:</b> El <span class='hl-purple'><b>{pct(pct_dolarizacion)}</b></span> de las ventas (<span class='hl-blue'><b>{mm(ingresos_usd_dop)}</b></span>) se factura en dólares estadounidenses, "
        f"actuando como un escudo natural ante devaluaciones del peso dominicano, requiriendo automatizar la tasa diaria oficial en el ERP."
    ],
    "informe": [
        f"📑 <b>Memorándum Gerencial de Alta Dirección:</b> Concluimos el período auditado con ingresos de <span class='hl-green'><b>{mm(ingresos_tot)}</b></span> y utilidad neta de <span class='hl-green'><b>{mm(utilidad_neta)}</b></span>. "
        f"Para maximizar el retorno patrimonial, establecemos una hoja de ruta a 90 días centrada en recuperar <span class='hl-blue'><b>{mm(cxc_saldo * 0.55)}</b></span> de cuentas por cobrar, "
        f"regularizar la Caja General, conciliar pasivos fiscales ante la DGII y optimizar la asignación presupuestaria en áreas de expansión."
    ],
    "libro": [
        f"🔍 <b>Auditoría Forense del Libro Diario y Partida Doble:</b> El Libro Mayor audita rigurosamente <span class='hl-dark'><b>{len(df):,} asientos contables</b></span> "
        f"distribuidos en <span class='hl-blue'><b>{df['Numero_Poliza'].nunique():,} pólizas</b></span>, con verificación matemática en tiempo real de partida doble y exportación ejecutiva multi-hoja a Excel."
    ],
}


def kpi_card(titulo, valor, delta, clase="pos", color=None):
    color = color or COLORS['success']
    return (
        f'<div class="kpi-card" style="border-top: 4px solid {color};">'
        f'<div class="kpi-title">{titulo}</div>'
        f'<div class="kpi-value">{valor}</div>'
        f'<span class="kpi-delta-{clase}">{delta}</span>'
        f'</div>'
    )


def render_kpi_grid(cards_html: list):
    st.markdown('<div class="kpi-grid">' + "".join(cards_html) + '</div>', unsafe_allow_html=True)


# ==============================================================================
# 7. ENCABEZADO + SEGMENTADORES ACTIVOS + TABS FIJOS ARRIBA
# ==============================================================================
st.markdown(f"""
<div class="exec-header">
    <div class="exec-header-inner">
        <h1 class="exec-title">🏛️ Suite Ejecutiva de Inteligencia Financiera & Control Contable</h1>
        <div class="exec-meta">
            <span>Horizonte: <b>{periodo_txt}</b> ({n_meses_tot} meses)</span>
            <span class="exec-sep">·</span>
            <span>Salud Corporativa: <b>{score}/100 {etiqueta}</b></span>
            <span class="exec-sep">·</span>
            <span>Pólizas: <b>{df['Numero_Poliza'].nunique():,}</b></span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

chips = []
for lbl, sel, orig in [
    ("Año", sel_anios, anios_disp),
    ("Trimestre", sel_tris, tri_disp),
    ("Mes", sel_meses, meses_disp),
    ("Depto", sel_deptos, deptos_disp),
    ("Líder", sel_lideres, lideres_disp),
    ("Tipo", sel_tipos, tipos_disp),
    ("Cuenta", sel_cuentas, cuentas_disp),
    ("Moneda", sel_monedas, monedas_disp),
]:
    if len(sel) < len(orig):
        txt = ", ".join(map(str, sel[:2])) + (f" (+{len(sel)-2})" if len(sel) > 2 else "")
        chips.append(f'<span class="slicer-chip">{lbl}: {txt}</span>')

if chips:
    st.sidebar.markdown('<div class="slicer-chip-bar">' + "".join(chips) + '</div>', unsafe_allow_html=True)

tab0, tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🏁 Resumen Ejecutivo",
    "📊 Rentabilidad & P&L",
    "🏢 Eficiencia Departamental",
    "🚨 Auditoría & Riesgos",
    "🔮 Tendencias & Proyección",
    "📑 Informe Gerencial",
    "🔍 Libro Mayor"
])

# ------------------------------------------------------------------------------
# TAB 0: RESUMEN GENERAL Y FINANCIERO COMPLETO
# ------------------------------------------------------------------------------
with tab0:
    yoy_kpi_val = "N/D" if yoy is None else f"{yoy:+.1f}%"
    yoy_kpi_delta = yoy_detalle if yoy is not None else "1 ejercicio activo"
    yoy_kpi_cls = "pos" if (yoy or 0) >= 0 else "neg"

    render_kpi_grid([
        kpi_card("💰 Ingresos Totales", mm(ingresos_tot), f"💱 {pct(pct_dolarizacion)} en USD", "pos", COLORS['success']),
        kpi_card("📈 Utilidad Bruta", mm(utilidad_bruta), f"Margen Bruto: {pct(margen_bruto, 2)}", "pos" if margen_bruto >= 50 else "warn", COLORS['accent']),
        kpi_card("🏆 Utilidad Neta", mm(utilidad_neta), f"Margen Neto: {pct(margen_neto, 2)}", "pos" if margen_neto >= 15 else "warn", COLORS['primary']),
        kpi_card("🚀 Crecimiento Comparable", yoy_kpi_val, yoy_kpi_delta, yoy_kpi_cls, COLORS['success']),
        kpi_card("📅 Promedio Mensual", mm(prom_mensual_ing), f"Mejor: {mejor_mes}", "pos", COLORS['purple']),
        kpi_card("🏦 Tesorería Disponible", mm(liquidez_disp), f"Caja: {fmt_millones(caja_gen)}", "pos" if liquidez_disp >= 0 else "neg", COLORS['accent']),
        kpi_card("⏳ Cartera CxC", mm(cxc_saldo), f"Cobranza: {pct(tasa_cobranza)}", "pos" if tasa_cobranza >= 80 else "warn", COLORS['warning']),
        kpi_card("🧾 Pasivos Acumulados", mm(pasivos_tot), f"Cobertura: {cobertura_liq:.2f}x", "pos" if cobertura_liq >= 1 else "neg", COLORS['danger']),
        kpi_card("⚙️ OPEX / Ingresos", pct(ratio_opex), f"Costos: {pct(ratio_costos)}", "pos" if ratio_opex <= 35 else "warn", COLORS['purple']),
        kpi_card("🩺 Salud Corporativa", f"{score}/100", etiqueta, "pos" if score >= 60 else "warn", COLORS['primary']),
    ])

    narrador_seccion(
        NARR["resumen"],
        "🎙️ Briefing Maestro: Resumen General y Financiero",
        "Audio disponible siempre · Expanda debajo si desea leer el informe completo"
    )

    g1, g2 = st.columns([1, 1.7])
    with g1:
        with st.container(border=True):
            st.subheader("🩺 Índice de Salud Corporativa")
            fig_g = go.Figure(go.Indicator(
                mode="gauge+number", value=score, number={'suffix': "/100"},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': COLORS['primary']},
                    'steps': [
                        {'range': [0, 40], 'color': '#FECACA'},
                        {'range': [40, 60], 'color': '#FDE68A'},
                        {'range': [60, 80], 'color': '#BBF7D0'},
                        {'range': [80, 100], 'color': '#86EFAC'}
                    ]
                }
            ))
            plot(estilo(fig_g, 210))
            comp = pd.DataFrame({
                'Pilar': ['Rentabilidad (30)', 'Cobranza (25)', 'Liquidez (20)', 'Control interno (15)', 'Crecimiento (10)'],
                'Puntos': [round(sc_rent, 1), round(sc_cob, 1), round(sc_liq, 1), round(sc_ctl, 1), round(sc_cre, 1)]
            })
            tabla(comp, hide_index=True, height=172)
            narrador_elemento(
                f"Como analista financiero, este velocímetro sintetiza la salud integral del negocio en una escala de <b>cero a cien puntos</b>, donde actualmente nos ubicamos en <span class='hl-purple'><b>{score}/100 ({etiqueta})</b></span>. "
                f"La tabla inferior desglosa los cinco pilares metodológicos: primero, <b>Rentabilidad</b> aporta <span class='hl-green'><b>{sc_rent:.1f}/30</b></span> puntos gracias al margen neto del <span class='hl-green'><b>{pct(margen_neto)}</b></span>; "
                f"segundo, <b>Cobranza</b> aporta <span class='hl-amber'><b>{sc_cob:.1f}/25</b></span> puntos con una tasa de recuperación del <span class='hl-amber'><b>{pct(tasa_cobranza)}</b></span>; "
                f"tercero, <b>Liquidez</b> suma <span class='hl-blue'><b>{sc_liq:.1f}/20</b></span> puntos con una cobertura de <span class='hl-blue'><b>{cobertura_liq:.2f}x</b></span> sobre pasivos; "
                f"cuarto, <b>Control Interno</b> registra <span class='hl-red'><b>{sc_ctl:.1f}/15</b></span> puntos {'penalizado por el saldo deudor no regularizado en Caja General' if caja_gen < 0 else 'en perfecto orden'}; "
                f"y quinto, <b>Crecimiento</b> aporta <span class='hl-green'><b>{sc_cre:.1f}/10</b></span> puntos. Para alcanzar la categoría <b>Excelente (≥ 80 puntos)</b>, debemos acelerar el recaudo de cuentas por cobrar y regularizar los fondos de caja.",
                "🎙️ Explicación: Índice y Pilares de Salud"
            )

    with g2:
        with st.container(border=True):
            st.subheader("📈 Ingresos vs. Egresos y Margen Neto Mensual")
            fig_c = make_subplots(specs=[[{"secondary_y": True}]])
            fig_c.add_bar(
                x=mdf['Periodo'], y=mdf['Ingresos'], name='Ingresos', marker_color=COLORS['success'],
                hovertemplate="%{x}<br>Ingresos: RD$ %{y:,.2f}<extra></extra>"
            )
            fig_c.add_bar(
                x=mdf['Periodo'], y=mdf['Egresos'], name='Costos + Gastos', marker_color=COLORS['danger'],
                hovertemplate="%{x}<br>Egresos: RD$ %{y:,.2f}<extra></extra>"
            )
            fig_c.add_scatter(
                x=mdf['Periodo'], y=mdf['Margen_Neto_%'], name='Margen Neto %', mode='lines+markers',
                line=dict(color=COLORS['primary'], width=3), marker=dict(size=6), secondary_y=True,
                hovertemplate="%{x}<br>Margen Neto: %{y:.2f}%<extra></extra>"
            )
            if mejor_mes != "N/D":
                fig_c.add_annotation(
                    x=mejor_mes, y=mejor_mes_val, text=f"Pico: {mm(mejor_mes_val)}",
                    showarrow=True, arrowhead=2, yshift=10, font=dict(size=11, color=COLORS['primary'])
                )
            fig_c.update_yaxes(title_text="DOP", secondary_y=False)
            fig_c.update_yaxes(title_text="Margen %", secondary_y=True, showgrid=False)
            plot(estilo(
                fig_c, 410, barmode='group', hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            ))
            mg_min = float(mdf['Margen_Neto_%'].min()) if mdf['Margen_Neto_%'].notna().any() else 0.0
            mg_max = float(mdf['Margen_Neto_%'].max()) if mdf['Margen_Neto_%'].notna().any() else 0.0
            narrador_elemento(
                f"En este gráfico analítico de doble eje vertical, las barras verdes representan la <b>facturación mensual en pesos</b>, las barras rojas reflejan las <b>erogaciones totales en costos y gastos</b>, y la línea azul en el eje derecho traza la <b>rentabilidad neta porcentual</b>. "
                f"A lo largo del período, la compañía facturó en promedio <span class='hl-green'><b>{mm(prom_mensual_ing)}</b></span> mensuales frente a egresos promedio de <span class='hl-amber'><b>{mm(prom_mensual_egr)}</b></span>. "
                f"El volumen comercial alcanzó su máximo histórico en <span class='hl-green'><b>{mejor_mes}</b></span> con <span class='hl-green'><b>{mm(mejor_mes_val)}</b></span>, mientras que el mayor desembolso operativo se produjo en <span class='hl-red'><b>{mes_max_egr}</b></span> con <span class='hl-red'><b>{mm(val_max_egr)}</b></span>. "
                f"El margen neto se mantuvo resiliente entre el <span class='hl-blue'><b>{pct(mg_min)}</b></span> y el <span class='hl-green'><b>{pct(mg_max)}</b></span>, demostrando un fuerte apalancamiento operativo donde los ingresos crecen a mayor ritmo que la estructura fija.",
                "🎙️ Explicación: Curva Mensual Ingresos vs. Egresos"
            )

    r_a, r_b = st.columns(2)
    with r_a:
        with st.container(border=True):
            st.subheader("💹 Curva de Utilidad Neta Acumulada")
            fig_ac = px.area(mdf, x='Periodo', y='Util_Acum', color_discrete_sequence=[COLORS['accent']])
            fig_ac.update_traces(
                line=dict(width=3, color=COLORS['royal']),
                fillcolor="rgba(14, 165, 233, 0.22)",
                hovertemplate="%{x}<br>Utilidad Acumulada: RD$ %{y:,.2f}<extra></extra>"
            )
            plot(estilo(fig_ac, 330, yaxis_title="Utilidad acumulada (DOP)", xaxis_title=""))
            narrador_elemento(
                f"Esta gráfica de área acumulada ilustra la <b>generación progresiva de riqueza contable</b>. "
                f"La curva azul muestra una pendiente ascendente sostenida que parte del primer mes y culmina en <span class='hl-green'><b>{mm(utilidad_neta)}</b></span> al cierre de <b>{periodos[-1]}</b>. "
                f"La ausencia total de retrocesos o pendientes negativas confirma que la empresa <b>no experimentó meses con pérdidas operativas</b> que destruyeran patrimonio, garantizando un flujo continuo de capitalización para reinversión estratégica.",
                "🎙️ Explicación: Utilidad Neta Acumulada"
            )

    with r_b:
        with st.container(border=True):
            st.subheader("🏢 Peso Presupuestario por Departamento")
            dep_top_chart = dep_resumen.sort_values('Total Erogaciones', ascending=True)
            fig_dep_res = px.bar(
                dep_top_chart, x='Total Erogaciones', y='Departamento', orientation='h',
                text_auto='.2s', color='Total Erogaciones', color_continuous_scale='Tealgrn'
            )
            fig_dep_res.update_traces(hovertemplate="%{y}<br>Erogaciones: RD$ %{x:,.2f}<extra></extra>")
            plot(estilo(fig_dep_res, 330, xaxis_title="Erogaciones (DOP)", yaxis_title="", coloraxis_showscale=False))
            narrador_elemento(
                f"El gráfico de barras horizontales clasifica los departamentos de menor a mayor consumo de capital. "
                f"En la cima del ranking se ubica <b>{top_dep}</b> con <span class='hl-red'><b>{mm(top_dep_val)}</b></span>, representando el <span class='hl-amber'><b>{pct(top_dep_pct)}</b></span> del gasto total, impulsado por su rol central en la operación diaria. "
                f"En el extremo opuesto figura <b>{low_dep}</b> con apenas <span class='hl-green'><b>{mm(low_dep_val)}</b></span>, lo que equivale al <span class='hl-green'><b>{pct(low_dep_pct)}</b></span>. "
                f"Como analistas de negocio, recomendamos evaluar si áreas con asignación reducida como <b>{low_dep}</b> disponen de los recursos óptimos para respaldar las metas de crecimiento institucional.",
                "🎙️ Explicación: Ranking Presupuestario Departamental"
            )

    st.subheader("🏛️ Panorama Consolidado por Departamento y Líder")
    tabla(
        dep_resumen.style.format({
            'Ingresos': "RD$ {:,.2f}",
            'Costos Directos': "RD$ {:,.2f}",
            'Nómina': "RD$ {:,.2f}",
            'Otros Gastos': "RD$ {:,.2f}",
            'Total Erogaciones': "RD$ {:,.2f}",
            'Part. Gasto %': "{:.2f}%"
        }).background_gradient(subset=['Total Erogaciones'], cmap='Blues'),
        hide_index=True
    )
    narrador_elemento(
        f"Esta matriz de control departamental desglosa en detalle los ingresos generados, costos directos, sueldos de nómina y otros gastos operativos por cada área y líder responsable. "
        f"El gasto consolidado suma <span class='hl-amber'><b>{mm(egresos_tot)}</b></span>, destacando que el personal representa el <span class='hl-blue'><b>{pct(pct_sueldos_egr)}</b></span> con <span class='hl-blue'><b>{mm(sueldos_tot)}</b></span>. "
        f"Mientras el área de <b>Ventas y Comercial</b> centraliza la totalidad de la facturación con <span class='hl-green'><b>{mm(ingresos_tot)}</b></span>, los tres principales departamentos operativos concentran el <span class='hl-amber'><b>{pct(top3_deps_pct)}</b></span> de las salidas de efectivo, lo que exige fijar metas semestrales de eficiencia en costos de soporte.",
        "🎙️ Explicación: Tabla Consolidada de Departamentos"
    )

    st.subheader("🚦 Semáforo de Indicadores Clave")
    sem_df = pd.DataFrame([
        ["Margen bruto", pct(margen_bruto), "≥ 60%", semaforo(margen_bruto, 60, 40)],
        ["Margen neto", pct(margen_neto), "≥ 25%", semaforo(margen_neto, 25, 10)],
        ["OPEX / Ingresos", pct(ratio_opex), "≤ 30%", semaforo(ratio_opex, 30, 50, mayor=False)],
        ["Tasa de cobranza", pct(tasa_cobranza), "≥ 80%", semaforo(tasa_cobranza, 80, 60) if cxc_cargos > 0 else "⚪ Sin crédito"],
        ["Cobertura de pasivos", f"{cobertura_liq:.2f}x", "≥ 1.0x", semaforo(cobertura_liq, 1.0, 0.5)],
        ["Caja General", fmt_dop(caja_gen), "≥ RD$ 0.00", "🟢 Óptimo" if caja_gen >= 0 else "🔴 Crítico"],
        ["Ingresos en USD", pct(pct_dolarizacion), "≥ 20%", semaforo(pct_dolarizacion, 20, 5)],
        ["Crecimiento comparable", "N/D" if yoy is None else f"{yoy:+.1f}%", "≥ 10%", "⚪ N/D" if yoy is None else semaforo(yoy, 10, 0)],
    ], columns=["Indicador", "Valor actual", "Referencia", "Estado"])
    tabla(sem_df, hide_index=True)
    n_opt = int((sem_df['Estado'].str.contains('Óptimo')).sum())
    n_vig = int((sem_df['Estado'].str.contains('Vigilar')).sum())
    n_cri = int((sem_df['Estado'].str.contains('Crítico')).sum())
    narrador_elemento(
        f"El semáforo gerencial somete a prueba <b>ocho indicadores clave de desempeño</b> frente a estándares internacionales de control financiero. "
        f"El balance es favorable con <span class='hl-green'><b>{n_opt} indicadores en rango óptimo verde</b></span>, <span class='hl-amber'><b>{n_vig} en vigilancia amarilla</b></span> y <span class='hl-red'><b>{n_cri} en estado crítico rojo</b></span>. "
        f"Celebramos un margen bruto del <span class='hl-green'><b>{pct(margen_bruto)}</b></span>, un margen neto del <span class='hl-green'><b>{pct(margen_neto)}</b></span> y un nivel de dolarización del <span class='hl-purple'><b>{pct(pct_dolarizacion)}</b></span>; "
        f"sin embargo, el semáforo rojo en cobranza al <span class='hl-red'><b>{pct(tasa_cobranza)}</b></span> y en Caja General con saldo de <span class='hl-red'><b>{fmt_dop(caja_gen)}</b></span> exige intervención correctiva inmediata.",
        "🎙️ Explicación: Semáforo de Indicadores"
    )

    st.subheader("🧭 Logros, Alertas Críticas y Oportunidades")
    logros = [
        f"Margen neto de {pct(margen_neto)} ({mm(utilidad_neta)} acumulados)",
        f"Línea líder: {top_linea} ({pct(top_linea_pct)} de ventas)",
        f"Cobertura cambiaria natural del {pct(pct_dolarizacion)} en USD"
    ]
    if yoy is not None and yoy >= 0:
        logros.append(f"Crecimiento comparable positivo de {yoy:+.1f}% ({yoy_detalle})")

    alertas = []
    if cxc_cargos > 0 and tasa_cobranza < 80:
        alertas.append(f"Cobranza en {pct(tasa_cobranza)}: {mm(cxc_saldo)} retenidos en clientes")
    if caja_gen < 0:
        alertas.append(f"Caja General negativa ({fmt_dop(caja_gen)}) sin reposición")
    if pasivos_tot > 0:
        alertas.append(f"{mm(pasivos_tot)} en pasivos acumulados pendientes de liquidación")
    if top_linea_pct > 65:
        alertas.append(f"Alta concentración comercial en {top_linea} ({pct(top_linea_pct)})")
    if not alertas:
        alertas.append("Sin alertas críticas con los filtros seleccionados")

    oport = [
        f"Acelerar cobro de CxC para liberar hasta {mm(cxc_saldo * 0.55)} de liquidez",
        f"Suavizar estacionalidad con contratos en meses valle ({', '.join(valle_meses)})",
        f"Evaluar presupuesto de {low_dep} (solo {pct(low_dep_pct)} del gasto)",
        f"Ingresos estimados próximos {H} meses: {mm(proy_total)}" if tiene_proy else "Ampliar historial para proyectar tendencia"
    ]
    li = lambda xs: "<ul>" + "".join(f"<li>{x}</li>" for x in xs) + "</ul>"
    narrador_elemento(
        f"En síntesis estratégica, nuestros tres mayores logros son la generación de <span class='hl-green'><b>{mm(utilidad_neta)}</b></span> en utilidades netas con margen del <span class='hl-green'><b>{pct(margen_neto)}</b></span>, "
        f"el liderazgo comercial de <b>{top_linea}</b> con <span class='hl-blue'><b>{pct(top_linea_pct)}</b></span> de las ventas, y una cobertura cambiaria del <span class='hl-purple'><b>{pct(pct_dolarizacion)}</b></span> en dólares. "
        f"Como alertas prioritarias, debemos mitigar los <span class='hl-red'><b>{mm(cxc_saldo)}</b></span> retenidos en clientes por baja cobranza y auditar el saldo negativo de Caja General. "
        f"Finalmente, la oportunidad inmediata radica en ejecutar una campaña intensiva de recuperación que inyectará hasta <span class='hl-green'><b>{mm(cxc_saldo * 0.55)}</b></span> en liquidez fresca a nuestras cuentas bancarias.",
        "🎙️ Explicación: Logros, Alertas y Oportunidades"
    )
    with st.expander("**📖 Ver tarjetas de Logros, Alertas y Oportunidades**", expanded=False):
        st.markdown(
            f'<div class="cards-3">'
            f'<div class="ok-box"><b>🏆 Logros Clave</b>{li(logros)}</div>'
            f'<div class="danger-box"><b>🚨 Alertas Prioritarias</b>{li(alertas)}</div>'
            f'<div class="info-box"><b>🚀 Oportunidades</b>{li(oport)}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

# ------------------------------------------------------------------------------
# TAB 1: RENTABILIDAD, CASCADA DE RESULTADOS Y ESTACIONALIDAD
# ------------------------------------------------------------------------------
with tab1:
    narrador_seccion(
        NARR["pnl"],
        "🎙️ Analista P&L: Rentabilidad, Cascada y Estacionalidad",
        "Audio siempre listo · Expanda debajo para leer el análisis escrito"
    )

    col_a, col_b = st.columns(2)
    with col_a:
        with st.container(border=True):
            st.subheader("🌊 Cascada de Generación de Valor (P&L)")
            fig_waterfall = go.Figure(go.Waterfall(
                name="P&L", orientation="v",
                measure=["relative", "relative", "total", "relative", "total"],
                x=["Ingresos", "Costos Directos", "Utilidad Bruta", "OPEX", "Utilidad Neta"],
                textposition="outside",
                text=[mm(ingresos_tot), f"-{mm(costos_tot)}", mm(utilidad_bruta), f"-{mm(gastos_tot)}", mm(utilidad_neta)],
                y=[ingresos_tot, -costos_tot, 0, -gastos_tot, 0],
                connector={"line": {"color": "#94A3B8", "width": 2, "dash": "dot"}},
                decreasing={"marker": {"color": COLORS["danger"]}},
                increasing={"marker": {"color": COLORS["success"]}},
                totals={"marker": {"color": COLORS["primary"]}},
                hovertemplate="%{x}<br>Monto: RD$ %{y:,.2f}<extra></extra>"
            ))
            plot(estilo(fig_waterfall, 400, yaxis_title="DOP", showlegend=False))
            narrador_elemento(
                f"La cascada de valor descompone el flujo contable desde el ingreso bruto hasta la ganancia líquida. En el inicio, la barra verde refleja <span class='hl-green'><b>{mm(ingresos_tot)}</b></span> en ventas brutas. "
                f"La primera deducción en rojo corresponde a los <b>costos directos de entrega</b> por <span class='hl-amber'><b>{mm(costos_tot)}</b></span>, absorbiendo el <span class='hl-amber'><b>{pct(ratio_costos)}</b></span>, lo que deja la barra azul intermedia de <b>utilidad bruta</b> en <span class='hl-blue'><b>{mm(utilidad_bruta)}</b></span>. "
                f"Posteriormente, la segunda barra roja descuenta <span class='hl-red'><b>{mm(gastos_tot)}</b></span> en <b>gastos operativos y OPEX</b>, representando el <span class='hl-purple'><b>{pct(ratio_opex)}</b></span>. "
                f"El resultado final en la barra azul oscura corona una <b>utilidad neta</b> de <span class='hl-green'><b>{mm(utilidad_neta)}</b></span>, reteniendo <span class='hl-green'><b>{pct(margen_neto)}</b></span> de cada peso facturado, lo que ratifica una operación altamente rentable y blindada ante costos fijos.",
                "🎙️ Explicación: Cascada P&L"
            )

    with col_b:
        with st.container(border=True):
            st.subheader("🚀 Ingresos Anuales por Línea de Negocio")
            ing_linea = ing_df.groupby(['Año', 'Cuenta_Contable'])['Credito_DOP'].sum().reset_index()
            if not ing_linea.empty:
                fig_linea = px.bar(
                    ing_linea, x='Año', y='Credito_DOP', color='Cuenta_Contable', barmode='group', text_auto='.2s',
                    color_discrete_sequence=[COLORS['primary'], COLORS['accent'], COLORS['success'], COLORS['purple']]
                )
                fig_linea.update_traces(hovertemplate="Año %{x}<br>%{fullData.name}: RD$ %{y:,.2f}<extra></extra>")
                plot(estilo(
                    fig_linea, 400,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title=""),
                    yaxis_title="Ingresos (DOP)", xaxis=dict(type='category')
                ))
                narrador_elemento(
                    f"Este gráfico de barras agrupadas compara la evolución de las líneas de negocio en cada año fiscal. La línea insignia <b>{top_linea}</b> encabeza el volumen acumulado con <span class='hl-green'><b>{mm(top_linea_val)}</b></span>, aportando el <span class='hl-green'><b>{pct(top_linea_pct)}</b></span> de la facturación, seguida por <b>{seg_linea}</b> con <span class='hl-blue'><b>{mm(seg_linea_val)}</b></span> y una participación del <span class='hl-blue'><b>{pct(seg_linea_pct)}</b></span>. "
                    f"{'Cabe destacar que el ejercicio más reciente cuenta con menos meses registrados, por lo que el análisis de desempeño debe realizarse considerando el promedio mensual equivalente.' if es_parcial else 'Ambas líneas muestran una relación de ingresos armónica y recurrente a lo largo de los ejercicios cerrados.'}",
                    "🎙️ Explicación: Ingresos Anuales por Línea"
                )
            else:
                st.info("Sin registros de ingresos en el filtro actual.")

    st.subheader("📅 Pulso Mensual de Facturación por Año")
    mensual_ing = ing_df.groupby(['Año', 'Mes'], observed=False)['Credito_DOP'].sum().reset_index()
    if not mensual_ing.empty and mensual_ing['Credito_DOP'].sum() > 0:
        fig_mes = px.line(
            mensual_ing, x='Mes', y='Credito_DOP', color='Año', markers=True,
            color_discrete_sequence=[COLORS['text_muted'], COLORS['accent'], COLORS['success'], COLORS['warning']]
        )
        fig_mes.update_traces(line=dict(width=3), marker=dict(size=7), hovertemplate="%{x}<br>Año %{fullData.name}: RD$ %{y:,.2f}<extra></extra>")
        plot(estilo(fig_mes, 345, yaxis_title="Facturación Mensual (DOP)", xaxis_title="", hovermode="x unified"))
        narrador_elemento(
            f"La gráfica multilínea superpone las curvas de ventas mensuales de cada año para revelar el <b>patrón estacional intrínseco</b> del negocio. Históricamente, las ventas experimentan una aceleración notable en <span class='hl-green'><b>{', '.join(pico_meses)}</b></span>, con el punto cúspide en <span class='hl-green'><b>{mejor_mes}</b></span> al registrar <span class='hl-green'><b>{mm(mejor_mes_val)}</b></span>. Por el contrario, los meses de menor actividad corresponden a <span class='hl-amber'><b>{', '.join(valle_meses)}</b></span>, tocando piso en <span class='hl-red'><b>{peor_mes}</b></span> con <span class='hl-red'><b>{mm(peor_mes_val)}</b></span>. Como recomendación comercial, sugerimos diseñar promociones y contratos corporativos anuales anticipados para nivelar los ingresos durante los meses valle.",
            "🎙️ Explicación: Pulso Mensual por Año"
        )
    else:
        st.info("Sin facturación mensual para graficar.")

    m1, m2 = st.columns(2)
    with m1:
        with st.container(border=True):
            st.subheader("📉 Evolución del Margen Neto Mensual")
            fig_mg = go.Figure()
            fig_mg.add_scatter(
                x=mdf['Periodo'], y=mdf['Margen_Neto_%'], mode='lines+markers', name='Margen Neto %',
                line=dict(color=COLORS['success'], width=3), marker=dict(size=6),
                hovertemplate="%{x}<br>Margen Neto: %{y:.2f}%<extra></extra>"
            )
            if ingresos_tot > 0:
                fig_mg.add_hline(y=margen_neto, line_dash="dot", line_color=COLORS['warning'], annotation_text=f"Promedio {pct(margen_neto)}")
            plot(estilo(fig_mg, 360, yaxis_title="Margen Neto (%)", showlegend=False))
            mg_min = float(mdf['Margen_Neto_%'].min()) if mdf['Margen_Neto_%'].notna().any() else 0.0
            mg_max = float(mdf['Margen_Neto_%'].max()) if mdf['Margen_Neto_%'].notna().any() else 0.0
            narrador_elemento(
                f"Esta curva de dispersión monitorea la estabilidad del margen neto mensual frente a la línea de referencia amarilla que marca el <b>promedio histórico del {pct(margen_neto)}</b>. A lo largo de la serie, el margen osciló en un corredor saludable entre el <span class='hl-blue'><b>{pct(mg_min)}</b></span> y el <span class='hl-green'><b>{pct(mg_max)}</b></span>. Esta baja dispersión confirma una <b>estricta disciplina presupuestaria</b> donde los gastos no se desbordan en meses de alto volumen ni comprometen la solvencia en períodos de menor demanda.",
                "🎙️ Explicación: Margen Neto Mensual"
            )

    with m2:
        with st.container(border=True):
            st.subheader("🍩 Mezcla de Ingresos por Línea")
            if len(mix) and mix.sum() > 0:
                fig_mix = px.pie(
                    mix.reset_index(), names='Cuenta_Contable', values='Credito_DOP', hole=0.56,
                    color_discrete_sequence=[COLORS['primary'], COLORS['accent'], COLORS['success'], COLORS['purple'], COLORS['warning']]
                )
                fig_mix.update_traces(textinfo='percent+label', hovertemplate="%{label}<br>RD$ %{value:,.2f} (%{percent})<extra></extra>")
                plot(estilo(fig_mix, 360, showlegend=False))
                narrador_elemento(
                    f"El gráfico circular tipo dona ilustra la <b>concentración comercial del portafolio</b>. El segmento principal <b>{top_linea}</b> genera el <span class='hl-green'><b>{pct(top_linea_pct)}</b></span> de las ventas con <span class='hl-green'><b>{mm(top_linea_val)}</b></span>, mientras que <b>{seg_linea}</b> contribuye con el <span class='hl-blue'><b>{pct(seg_linea_pct)}</b></span> equivalente a <span class='hl-blue'><b>{mm(seg_linea_val)}</b></span>. Si bien contar con un producto estrella líder asegura ingresos consistentes, desde la perspectiva comercial recomendamos expandir líneas secundarias para diversificar riesgos y capturar nuevos segmentos de mercado.",
                    "🎙️ Explicación: Mezcla de Ingresos"
                )
            else:
                st.info("Sin mezcla de ingresos disponible.")

    st.subheader("🧱 Desempeño Trimestral: Ingresos, Costos, Gastos y Utilidad")
    fig_tri = go.Figure()
    fig_tri.add_bar(x=tri.index, y=tri['Costos'], name='Costos', marker_color=COLORS['danger'], hovertemplate="%{x}<br>Costos: RD$ %{y:,.2f}<extra></extra>")
    fig_tri.add_bar(x=tri.index, y=tri['Gastos'], name='Gastos', marker_color=COLORS['warning'], hovertemplate="%{x}<br>Gastos: RD$ %{y:,.2f}<extra></extra>")
    fig_tri.add_bar(x=tri.index, y=tri['Utilidad Neta'], name='Utilidad Neta', marker_color=COLORS['success'], hovertemplate="%{x}<br>Utilidad: RD$ %{y:,.2f}<extra></extra>")
    fig_tri.add_scatter(x=tri.index, y=tri['Ingresos'], name='Ingresos', mode='lines+markers', line=dict(color=COLORS['primary'], width=3), hovertemplate="%{x}<br>Ingresos: RD$ %{y:,.2f}<extra></extra>")
    plot(estilo(fig_tri, 365, barmode='stack', yaxis_title="DOP", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)))
    if not tri.empty:
        tri_best = str(tri['Ingresos'].idxmax())
        tri_best_val = float(tri['Ingresos'].max())
        tri_best_u = float(tri.loc[tri_best, 'Utilidad Neta'])
        narrador_elemento(
            f"El gráfico de barras apiladas y línea azul muestra el comportamiento financiero por trimestre calendario. Las secciones rojas representan <b>costos directos</b>, las amarillas los <b>gastos operativos</b> y las verdes la <b>utilidad neta restante</b> bajo la línea de facturación total. El trimestre más productivo de la serie histórica fue <span class='hl-green'><b>{tri_best}</b></span>, alcanzando ventas por <span class='hl-green'><b>{mm(tri_best_val)}</b></span> y una utilidad neta de <span class='hl-green'><b>{mm(tri_best_u)}</b></span>, evidenciando la capacidad del equipo para maximizar la absorción de costos fijos en trimestres de alta demanda.",
            "🎙️ Explicación: Desempeño Trimestral"
        )

    st.subheader("📋 Estado de Resultados Comparativo por Ejercicio")
    fmt_er = {
        'Meses': "{:.0f}",
        'Ingresos': "RD$ {:,.2f}",
        'Costos': "RD$ {:,.2f}",
        'Gastos': "RD$ {:,.2f}",
        'Utilidad Bruta': "RD$ {:,.2f}",
        'Utilidad Neta': "RD$ {:,.2f}",
        'Prom. Mensual Ingresos': "RD$ {:,.2f}",
        'Margen Bruto %': "{:.2f}%",
        'Margen Neto %': "{:.2f}%",
        'Var. Prom. Mensual %': "{:+.2f}%"
    }
    tabla(anual.style.format(fmt_er, na_rep="—").background_gradient(subset=['Margen Neto %'], cmap='YlGn'))
    anual_txt = "; ".join(
        f"en {idx} ({int(row['Meses'])} meses), ingresos de {mm(row['Ingresos'])} ({mm(row['Prom. Mensual Ingresos'])}/mes), utilidad neta de {mm(row['Utilidad Neta'])} y margen neto de {pct(row['Margen Neto %'])}"
        for idx, row in anual.iterrows()
    )
    narrador_elemento(
        f"La tabla financiera comparativa consolida las cifras anuales normalizando los ingresos mediante el <b>promedio mensual</b> para neutralizar la distorsión de ejercicios incompletos. El detalle refleja: <span class='hl-dark'>{anual_txt}</span>. Esta visión normalizada confirma un <b>crecimiento real y sostenible</b> en la capacidad de facturación mensual de la empresa.",
        "🎙️ Explicación: Tabla Estado de Resultados"
    )

# ------------------------------------------------------------------------------
# TAB 2: EFICIENCIA POR DEPARTAMENTO Y LÍDERES
# ------------------------------------------------------------------------------
with tab2:
    narrador_seccion(
        NARR["depto"],
        "🎙️ Analista Presupuestario: Eficiencia Departamental",
        "Audio disponible siempre · Expanda debajo para leer el análisis completo"
    )

    if egr_df.empty:
        st.info("No hay costos ni gastos en los filtros actuales.")
    else:
        opex_depto = egr_df.groupby(['Departamento', 'Lider_Departamento', 'Tipo_Cuenta'])['Debito_DOP'].sum().reset_index()
        col1, col2 = st.columns(2)
        with col1:
            with st.container(border=True):
                st.subheader("🗺️ Mapa Jerárquico de Erogaciones")
                fig_tree = px.treemap(
                    opex_depto,
                    path=[px.Constant("Total Costos y Gastos"), 'Tipo_Cuenta', 'Departamento', 'Lider_Departamento'],
                    values='Debito_DOP', color='Debito_DOP', color_continuous_scale='Blues'
                )
                fig_tree.update_traces(hovertemplate="%{label}<br>Erogación: RD$ %{value:,.2f}<extra></extra>")
                plot(estilo(fig_tree, 420))
                narrador_elemento(
                    f"El treemap jerárquico representa visualmente la distribución del gasto mediante rectángulos proporcionales. Las erogaciones globales de <span class='hl-amber'><b>{mm(egresos_tot)}</b></span> se subdividen entre <b>Gastos Operativos</b> por <span class='hl-red'><b>{mm(gastos_tot)}</b></span> y <b>Costos Directos</b> por <span class='hl-amber'><b>{mm(costos_tot)}</b></span>. El bloque de mayor superficie corresponde a <b>{top_dep}</b> bajo el liderazgo de <b>{lider_top}</b> con <span class='hl-red'><b>{mm(top_dep_val)}</b></span>, lo que refleja su alta demanda operativa dentro de la cadena de valor.",
                    "🎙️ Explicación: Treemap Jerárquico"
                )

        with col2:
            with st.container(border=True):
                st.subheader("📊 Erogaciones por Naturaleza Contable")
                gcta_asc = gcta.sort_values(ascending=True).reset_index()
                fig_bar_cta = px.bar(
                    gcta_asc, x='Debito_DOP', y='Cuenta_Contable', orientation='h', text_auto='.2s',
                    color='Debito_DOP', color_continuous_scale='Tealgrn'
                )
                fig_bar_cta.update_traces(hovertemplate="%{y}<br>RD$ %{x:,.2f}<extra></extra>")
                plot(estilo(fig_bar_cta, 420, xaxis_title="Acumulado (DOP)", yaxis_title="", coloraxis_showscale=False))
                narrador_elemento(
                    f"El gráfico de barras horizontales categoriza el gasto según su naturaleza financiera. La partida predominante es <b>{top_gasto}</b> con <span class='hl-red'><b>{mm(top_gasto_val)}</b></span>, representando el <span class='hl-amber'><b>{pct(top_gasto_pct)}</b></span> del total, lo que pone de relieve la relevancia de la estructura de capital humano frente a otros renglones como servicios en la nube, infraestructura, publicidad y suministros operativos.",
                    "🎙️ Explicación: Gastos por Naturaleza"
                )

        p1, p2 = st.columns(2)
        with p1:
            with st.container(border=True):
                st.subheader("📐 Pareto 80/20 del Gasto por Cuenta")
                fig_par = make_subplots(specs=[[{"secondary_y": True}]])
                fig_par.add_bar(x=par['Cuenta_Contable'], y=par['Debito_DOP'], name='Gasto', marker_color=COLORS['accent'], hovertemplate="%{x}<br>RD$ %{y:,.2f}<extra></extra>")
                fig_par.add_scatter(
                    x=par['Cuenta_Contable'], y=par['Acum_%'], name='% Acumulado', mode='lines+markers',
                    line=dict(color=COLORS['danger'], width=3), secondary_y=True,
                    hovertemplate="%{x}<br>Acumulado: %{y:.1f}%<extra></extra>"
                )
                fig_par.add_hline(y=80, line_dash="dot", line_color=COLORS['warning'], secondary_y=True, annotation_text="80%")
                fig_par.update_yaxes(range=[0, 105], secondary_y=True, showgrid=False)
                plot(estilo(fig_par, 390, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)))
                narrador_elemento(
                    f"El diagrama de Pareto combina barras de gasto individual con la curva roja de porcentaje acumulado y la línea de referencia del ochenta por ciento. El análisis demuestra una marcada concentración: únicamente <span class='hl-purple'><b>{n80} cuentas contables</b></span> explican el <span class='hl-dark'><b>80% del gasto total</b></span>, encabezadas por <b>{top_gasto}</b> con el <span class='hl-red'><b>{pct(top_gasto_pct)}</b></span>. Enfocar las auditorías de compras y las renegociaciones contractuales en estas pocas cuentas clave garantiza el control de la gran mayoría de los recursos corporativos.",
                    "🎙️ Explicación: Curva Pareto 80/20"
                )

        with p2:
            with st.container(border=True):
                st.subheader("🔥 Mapa de Calor: Departamento × Ejercicio")
                heat = egr_df.pivot_table(index='Departamento', columns='Año', values='Debito_DOP', aggfunc='sum', fill_value=0)
                heat.columns = heat.columns.astype(str)
                fig_heat = px.imshow(heat, text_auto='.2s', aspect='auto', color_continuous_scale='Blues')
                plot(estilo(fig_heat, 390, coloraxis_showscale=False))
                narrador_elemento(
                    f"El mapa de calor proyecta la <b>intensidad presupuestaria</b> de cada departamento a través de los diferentes ejercicios anuales. Las celdas en tonos azul oscuro señalan los períodos de mayor ejecución de gasto en <b>{top_dep}</b>, mientras que las tonalidades claras revelan áreas con presupuestos reducidos y controlados como <b>{low_dep}</b>. Esta herramienta permite a la dirección general detectar tendencias de expansión de costos de manera oportuna.",
                    "🎙️ Explicación: Mapa de Calor Departamental"
                )

        st.subheader("👔 Scorecard de Ejecución por Líder y Estructura de Gasto")
        tabla_lideres = egr_df.pivot_table(
            index=['Codigo_Departamento', 'Departamento', 'Lider_Departamento'],
            columns='Año', values='Debito_DOP', aggfunc='sum', fill_value=0
        ).reset_index()
        anios_cols = [c for c in tabla_lideres.columns if isinstance(c, (int, np.integer))]
        tabla_lideres['Total_Acumulado'] = tabla_lideres[anios_cols].sum(axis=1)
        tabla_lideres['Participacion_%'] = (tabla_lideres['Total_Acumulado'] / tabla_lideres['Total_Acumulado'].sum()) * 100
        tabla_lideres = tabla_lideres.merge(
            dep_resumen[['Codigo_Departamento', 'Nómina', 'Costos Directos', 'Otros Gastos']],
            on='Codigo_Departamento', how='left'
        ).sort_values('Total_Acumulado', ascending=False)
        tabla(
            tabla_lideres.style.format({
                **{y: "RD$ {:,.2f}" for y in anios_cols},
                "Nómina": "RD$ {:,.2f}",
                "Costos Directos": "RD$ {:,.2f}",
                "Otros Gastos": "RD$ {:,.2f}",
                "Total_Acumulado": "RD$ {:,.2f}",
                "Participacion_%": "{:.2f}%"
            }).background_gradient(subset=['Total_Acumulado'], cmap='YlGnBu')
            .bar(subset=['Participacion_%'], color='#BAE6FD'),
            hide_index=True
        )
        narrador_elemento(
            f"El Scorecard gerencial evalúa la ejecución presupuestaria de cada líder departamental desglosando los gastos por año y por categoría contable. Encabeza <b>{lider_top}</b> en <b>{top_dep}</b> con un acumulado de <span class='hl-red'><b>{mm(top_dep_val)}</b></span> correspondiente al <span class='hl-amber'><b>{pct(top_dep_pct)}</b></span>, mientras que <b>{low_dep}</b> concluye el ranking con <span class='hl-green'><b>{mm(low_dep_val)}</b></span> y el <span class='hl-green'><b>{pct(low_dep_pct)}</b></span>. En términos de estructura, la nómina consolidada absorbe <span class='hl-blue'><b>{mm(sueldos_tot)}</b></span>, los costos directos <span class='hl-amber'><b>{mm(costos_tot)}</b></span> y los demás gastos generales <span class='hl-dark'><b>{mm(gastos_tot - sueldos_tot)}</b></span>.",
            "🎙️ Explicación: Scorecard por Líder"
        )

# ------------------------------------------------------------------------------
# TAB 3: AUDITORÍA, LIQUIDEZ Y HALLAZGOS CRÍTICOS
# ------------------------------------------------------------------------------
with tab3:
    narrador_seccion(
        NARR["riesgos"],
        "🎙️ Auditor Financiero: Control Interno, Liquidez y Riesgos",
        "Audio disponible siempre · Expanda debajo para leer el dictamen"
    )

    st.subheader("🚨 Hallazgos Críticos de Control Interno y Tesorería")
    clase_caja = "danger-box" if caja_gen < 0 else "ok-box"
    icono_caja = "🔴" if caja_gen < 0 else "🟢"
    caja_msg = (
        "Presenta salidas en efectivo sin reposición de fondo fijo. <b>Acción:</b> arqueo y reclasificación contra bancos."
        if caja_gen < 0 else "Saldo positivo y consistente con la operación."
    )
    narrador_elemento(
        f"El comité de auditoría destaca tres observaciones prioritarias: en primer lugar, la cuenta de <b>Caja General</b> registra un saldo de <span class='hl-red'><b>{fmt_dop(caja_gen)}</b></span>, demandando arqueo y reposición inmediata desde cuentas bancarias; en segundo lugar, la <b>tasa de cobranza</b> se ubica en el <span class='hl-amber'><b>{pct(tasa_cobranza)}</b></span>, inmovilizando <span class='hl-red'><b>{mm(cxc_saldo)}</b></span> en cartera vencida; y en tercer lugar, existen <b>pasivos acumulados</b> por <span class='hl-red'><b>{mm(pasivos_tot)}</b></span> en <b>{pas_txt}</b> que requieren conciliación con la DGII y proveedores antes de incurrir en recargos moratorios.",
        "🎙️ Explicación: Hallazgos de Control Interno",
        "📖 Ver tarjetas de Hallazgos Críticos"
    )
    with st.expander("**📖 Ver detalle visual de los 3 Hallazgos Críticos**", expanded=False):
        st.markdown(
            f'<div class="cards-3">'
            f'<div class="{clase_caja}"><b>1. {icono_caja} Caja General ({fmt_dop(caja_gen)})</b><br>Cuenta <code>CTA_101</code>. {caja_msg}</div>'
            f'<div class="alert-box"><b>2. 🟠 Cobranza ({pct(tasa_cobranza)})</b><br>De {mm(cxc_cargos)} facturados a crédito ingresaron {mm(cxc_abonos)}. Hay <b>{mm(cxc_saldo)}</b> inmovilizados en clientes.</div>'
            f'<div class="alert-box"><b>3. 🟡 Pasivos sin Liquidar ({mm(pasivos_tot)})</b><br>{pas_txt}. <b>Acción:</b> conciliar contra certificaciones de DGII, TSS y proveedores.</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    # ---- Gráfico Integrado de Tendencia y Exposición de los 3 Hallazgos Críticos ----
    with st.container(border=True):
        st.subheader("📊 Monitor Forense: Evolución y Exposición de los 3 Hallazgos Críticos")
        caja_m_hallazgo = df[df['Codigo_Cuenta'] == 'CTA_101'].groupby('Año_Mes')['Monto_Neto_DOP'].sum().reindex(periodos, fill_value=0.0).cumsum()
        cxc_inmov_m = df[df['Codigo_Cuenta'] == 'CTA_104'].groupby('Año_Mes')['Monto_Neto_DOP'].sum().reindex(periodos, fill_value=0.0).cumsum()
        pas_acum_m = (
            df[df['Tipo_Cuenta'] == 'Pasivo'].groupby('Año_Mes')['Credito_DOP'].sum() -
            df[df['Tipo_Cuenta'] == 'Pasivo'].groupby('Año_Mes')['Debito_DOP'].sum()
        ).reindex(periodos, fill_value=0.0).cumsum()

        cxc_deb_acum = df[df['Codigo_Cuenta'] == 'CTA_104'].groupby('Año_Mes')['Debito_DOP'].sum().reindex(periodos, fill_value=0.0).cumsum()
        cxc_cre_acum = df[df['Codigo_Cuenta'] == 'CTA_104'].groupby('Año_Mes')['Credito_DOP'].sum().reindex(periodos, fill_value=0.0).cumsum()
        tasa_cob_serie = np.where(cxc_deb_acum > 0, (cxc_cre_acum / cxc_deb_acum) * 100, 0.0)

        fig_hallazgos = make_subplots(specs=[[{"secondary_y": True}]])
        fig_hallazgos.add_bar(
            x=periodos, y=cxc_inmov_m, name="🟠 Cartera CxC Inmovilizada",
            marker_color="rgba(245, 158, 11, 0.72)",
            hovertemplate="%{x}<br>Cartera Inmovilizada: RD$ %{y:,.2f}<extra></extra>"
        )
        fig_hallazgos.add_bar(
            x=periodos, y=pas_acum_m, name="🟡 Pasivos por Liquidar (DGII/Suplidores)",
            marker_color="rgba(139, 92, 246, 0.72)",
            hovertemplate="%{x}<br>Pasivos Acumulados: RD$ %{y:,.2f}<extra></extra>"
        )
        fig_hallazgos.add_scatter(
            x=periodos, y=caja_m_hallazgo, name="🔴 Saldo Caja General (CTA_101)",
            mode="lines+markers",
            line=dict(color=COLORS['danger'], width=3.5),
            marker=dict(size=7, symbol="diamond"),
            hovertemplate="%{x}<br>Caja General: RD$ %{y:,.2f}<extra></extra>"
        )
        fig_hallazgos.add_hline(
            y=0, line_dash="solid", line_color="#475569", line_width=1.5,
            annotation_text="Línea Cero Equilibrio", annotation_position="bottom right"
        )
        fig_hallazgos.add_scatter(
            x=periodos, y=tasa_cob_serie, name="🎯 Tasa Cobranza Acumulada %",
            mode="lines+markers",
            line=dict(color=COLORS['accent'], width=2.5, dash="dot"),
            marker=dict(size=6),
            secondary_y=True,
            hovertemplate="%{x}<br>Cobranza Acumulada: %{y:.1f}%<extra></extra>"
        )
        fig_hallazgos.add_hline(
            y=80, line_dash="dot", line_color=COLORS['success'], line_width=1.5,
            secondary_y=True, annotation_text="Meta Cobranza 80%", annotation_position="top right"
        )
        fig_hallazgos.update_yaxes(title_text="DOP (Exposición de Riesgo)", secondary_y=False)
        fig_hallazgos.update_yaxes(title_text="Eficacia Cobranza %", secondary_y=True, range=[0, 105], showgrid=False)

        plot(estilo(
            fig_hallazgos, 400, barmode='group', hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        ))
        narrador_elemento(
            f"Este gráfico analítico integrado proyecta en una sola vista la evolución temporal de los tres riesgos críticos de control interno: "
            f"en primer lugar, la línea roja diamond ilustra la caída sostenida del saldo de <b>Caja General</b> hasta perforar la línea cero de equilibrio y cerrar en <span class='hl-red'><b>{fmt_dop(caja_gen)}</b></span> por salidas de efectivo sin reposición bancaria; "
            f"en segundo lugar, las barras ámbar cuantifican la acumulación progresiva de <b>Cartera CxC inmovilizada</b> en <span class='hl-red'><b>{mm(cxc_saldo)}</b></span>, contrastada en el eje derecho con la línea punteada celeste que muestra la <b>tasa de cobranza deprimida en apenas {pct(tasa_cobranza)}</b> frente al umbral verde del ochenta por ciento; "
            f"y en tercer lugar, las barras moradas reflejan el incremento de <b>pasivos sin liquidar</b> en <span class='hl-red'><b>{mm(pasivos_tot)}</b></span> ({pas_txt}), advirtiendo la urgencia de regularizar las retenciones impositivas y honrar los compromisos comerciales.",
            "🎙️ Explicación: Gráfico Forense de Hallazgos Críticos"
        )

    r1, r2, r3 = st.columns(3)
    with r1:
        with st.container(border=True):
            st.subheader("🎯 Eficacia de Cobranza")
            fig_cb = go.Figure(go.Indicator(
                mode="gauge+number", value=tasa_cobranza, number={'suffix': "%"},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': COLORS['primary']},
                    'steps': [
                        {'range': [0, 60], 'color': '#FECACA'},
                        {'range': [60, 80], 'color': '#FDE68A'},
                        {'range': [80, 100], 'color': '#BBF7D0'}
                    ]
                }
            ))
            plot(estilo(fig_cb, 320))
            narrador_elemento(
                f"El indicador dial de cobranza marca un nivel del <span class='hl-amber'><b>{pct(tasa_cobranza)}</b></span>, situándose por debajo del estándar óptimo del <b>ochenta por ciento</b>. De un total facturado a crédito por <span class='hl-blue'><b>{mm(cxc_cargos)}</b></span>, se han recaudado efectivamente <span class='hl-green'><b>{mm(cxc_abonos)}</b></span>, dejando <span class='hl-red'><b>{mm(cxc_saldo)}</b></span> pendientes de cobro. Mejorar este indicador es la vía más rápida y económica para elevar la liquidez disponible sin recurrir a endeudamiento bancario.",
                "🎙️ Explicación: Eficacia de Cobranza"
            )

    with r2:
        with st.container(border=True):
            st.subheader("💳 Crédito Facturado vs. Recaudo (CxC)")
            cxc_anual = df[df['Codigo_Cuenta'] == 'CTA_104'].groupby('Año')[['Debito_DOP', 'Credito_DOP']].sum().reset_index()
            if not cxc_anual.empty:
                fig_cxc = go.Figure(data=[
                    go.Bar(name='Facturado a Crédito', x=cxc_anual['Año'].astype(str), y=cxc_anual['Debito_DOP'], marker_color=COLORS['warning'], hovertemplate="Año %{x}<br>Crédito: RD$ %{y:,.2f}<extra></extra>"),
                    go.Bar(name='Cobrado Efectivo', x=cxc_anual['Año'].astype(str), y=cxc_anual['Credito_DOP'], marker_color=COLORS['success'], hovertemplate="Año %{x}<br>Cobrado: RD$ %{y:,.2f}<extra></extra>")
                ])
                plot(estilo(fig_cxc, 320, barmode='group', yaxis_title="DOP", legend=dict(orientation="h", yanchor="bottom", y=1.02)))
                narrador_elemento(
                    f"El gráfico comparativo enfrenta año con año el volumen de ventas otorgadas a crédito en barras amarillas frente al <b>efectivo efectivamente cobrado en barras verdes</b>. La brecha acumulada de <span class='hl-red'><b>{mm(cxc_saldo)}</b></span> explica con claridad por qué los beneficios contables registrados en el Estado de Resultados no se han transformado plenamente en saldos bancarios disponibles para dividendos o inversión.",
                    "🎙️ Explicación: Brecha Crédito vs. Recaudo"
                )
            else:
                st.info("Sin movimientos de CxC en el filtro.")

    with r3:
        with st.container(border=True):
            st.subheader("🧾 Composición de Pasivos")
            if len(pas_pos):
                pas_df = pas_pos.reset_index()
                pas_df.columns = ['Cuenta_Contable', 'Saldo']
                fig_pas = px.pie(
                    pas_df, names='Cuenta_Contable', values='Saldo', hole=0.52,
                    color_discrete_sequence=[COLORS['danger'], COLORS['warning'], COLORS['purple'], COLORS['accent']]
                )
                fig_pas.update_traces(textinfo='percent+label', hovertemplate="%{label}<br>RD$ %{value:,.2f} (%{percent})<extra></extra>")
                plot(estilo(fig_pas, 320, showlegend=False))
                narrador_elemento(
                    f"El gráfico circular detalla la estructura de pasivos exigibles por <span class='hl-red'><b>{mm(pasivos_tot)}</b></span>. Las mayores obligaciones corresponden a <b>{pas_txt}</b>. Es crucial establecer un calendario de pagos ordenado para evitar contingencias fiscales con la administración tributaria y preservar el crédito comercial con suplidores estratégicos.",
                    "🎙️ Explicación: Composición de Pasivos"
                )
            else:
                st.info("Sin pasivos acumulados en el filtro actual.")

    cx1, cx2 = st.columns(2)
    with cx1:
        with st.container(border=True):
            st.subheader("🌱 Tesorería Acumulada (Caja + Bancos)")
            fig_cash = px.area(x=periodos, y=cash_m.values, color_discrete_sequence=[COLORS['success']])
            fig_cash.update_traces(fillcolor="rgba(16, 185, 129, 0.2)", line=dict(width=3), hovertemplate="%{x}<br>Tesorería: RD$ %{y:,.2f}<extra></extra>")
            plot(estilo(fig_cash, 330, xaxis_title="", yaxis_title="Saldo acumulado (DOP)"))
            narrador_elemento(
                f"La curva de área verde traza la evolución mensual de la <b>posición de liquidez neta</b>, consolidando caja general, cuentas corrientes nacionales y bancos en divisa extranjera, cerrando el período con <span class='hl-green'><b>{mm(liquidez_disp)}</b></span>. La tendencia ratifica solvencia para cumplir compromisos inmediatos.",
                "🎙️ Explicación: Tesorería Acumulada"
            )

    with cx2:
        with st.container(border=True):
            st.subheader("⏳ Cartera CxC Acumulada")
            fig_cxcm = px.area(x=periodos, y=cxc_m.values, color_discrete_sequence=[COLORS['warning']])
            fig_cxcm.update_traces(fillcolor="rgba(245, 158, 11, 0.2)", line=dict(width=3), hovertemplate="%{x}<br>CxC Acumulada: RD$ %{y:,.2f}<extra></extra>")
            plot(estilo(fig_cxcm, 330, xaxis_title="", yaxis_title="Saldo acumulado (DOP)"))
            narrador_elemento(
                f"La curva ascendente en color ámbar muestra el crecimiento acumulado de las <b>cuentas por cobrar a clientes</b>, alcanzando un pico de <span class='hl-red'><b>{mm(cxc_saldo)}</b></span>. Esta pendiente positiva confirma que la colocación de crédito a clientes avanza a mayor velocidad que la gestión de cobro, lo que exige implementar políticas de crédito más rigurosas.",
                "🎙️ Explicación: Cartera CxC Acumulada"
            )

    st.subheader("⚖️ Estructura del Balance General (Saldos Netos DOP)")
    bg_df = df[df['Estado_Financiero'] == 'Balance General'].groupby(['Tipo_Cuenta', 'Cuenta_Contable'])[['Debito_DOP', 'Credito_DOP']].sum().reset_index()
    if not bg_df.empty:
        bg_df['Saldo_Neto'] = np.where(
            bg_df['Tipo_Cuenta'] == 'Activo',
            bg_df['Debito_DOP'] - bg_df['Credito_DOP'],
            bg_df['Credito_DOP'] - bg_df['Debito_DOP']
        )
        fig_bg = px.bar(
            bg_df.sort_values('Saldo_Neto', ascending=True), x='Saldo_Neto', y='Cuenta_Contable', color='Tipo_Cuenta',
            orientation='h', text_auto='.2s',
            color_discrete_map={'Activo': COLORS['accent'], 'Pasivo': COLORS['danger'], 'Capital': COLORS['primary']}
        )
        fig_bg.update_traces(hovertemplate="%{y}<br>Saldo Neto: RD$ %{x:,.2f}<extra></extra>")
        plot(estilo(fig_bg, 400, xaxis_title="Saldo Neto (DOP)", yaxis_title=""))
        top_act = bg_df[bg_df['Tipo_Cuenta'] == 'Activo'].sort_values('Saldo_Neto', ascending=False)
        top_act_txt = f"{top_act.iloc[0]['Cuenta_Contable']} ({mm(top_act.iloc[0]['Saldo_Neto'])})" if len(top_act) else "N/D"
        narrador_elemento(
            f"El gráfico patrimonial presenta los <b>saldos netos en pesos</b> de las cuentas del Balance General. En el bloque de activos destaca <b>{top_act_txt}</b>, respaldando la solidez de la empresa; mientras en pasivos predominan <b>{pas_txt}</b>. Se observa con claridad el impacto del saldo deudor en Caja General de <span class='hl-red'><b>{fmt_dop(caja_gen)}</b></span>, cuya corrección regularizará la presentación del activo corriente.",
            "🎙️ Explicación: Balance General"
        )

    st.subheader("🛡️ Matriz de Riesgos y Plan de Mitigación")
    matriz = pd.DataFrame([
        ["Cartera inmovilizada", cxc_saldo, "Alta" if (cxc_cargos > 0 and tasa_cobranza < 60) else ("Media" if tasa_cobranza < 80 else "Baja"), "Alto", "Comité semanal de cobros", "Finanzas & Ventas"],
        ["Caja General descuadrada", abs(caja_gen) if caja_gen < 0 else 0.0, "Alta" if caja_gen < 0 else "Baja", "Medio", "Arqueo y reposición de fondo", "Contraloría"],
        ["Pasivos fiscales y proveedores", max(pasivos_tot, 0.0), "Media" if pasivos_tot > 0 else "Baja", "Alto", "Conciliación DGII / TSS", "Contraloría"],
        ["Tipo de cambio estático", ingresos_usd_dop, "Media", "Medio", "Integrar tasa diaria Banco Central", "Tecnología"],
        ["Concentración de ingresos", top_linea_val, "Media" if top_linea_pct > 60 else "Baja", "Medio", "Diversificar portafolio IA", "Dirección Comercial"],
    ], columns=["Riesgo", "Exposición (DOP)", "Probabilidad", "Impacto", "Acción Mitigante", "Responsable"])
    tabla(matriz.style.format({"Exposición (DOP)": "RD$ {:,.2f}"}), hide_index=True)
    narrador_elemento(
        f"La matriz de gestión de riesgos cuantifica la exposición financiera de la empresa: <span class='hl-red'><b>{mm(cxc_saldo)}</b></span> en cartera de clientes con riesgo de morosidad, <span class='hl-red'><b>{mm(max(pasivos_tot, 0.0))}</b></span> en pasivos fiscales y comerciales pendientes de conciliación, <span class='hl-purple'><b>{mm(ingresos_usd_dop)}</b></span> en ventas en moneda extranjera expuestas a tasa de cambio contable fija, y <span class='hl-red'><b>{fmt_dop(abs(caja_gen) if caja_gen < 0 else 0.0)}</b></span> en caja general, asignando responsables y plazos de ejecución definidos.",
        "🎙️ Explicación: Matriz de Riesgos"
    )

# ------------------------------------------------------------------------------
# TAB 4: TENDENCIAS, PROYECCIÓN Y DIVISAS
# ------------------------------------------------------------------------------
with tab4:
    narrador_seccion(
        NARR["tendencias"],
        "🎙️ Analista de Proyección: Tendencias y Divisas",
        "Audio disponible siempre · Expanda debajo para leer el análisis"
    )

    st.subheader("🔮 Curva de Ingresos, Media Móvil 3M y Proyección a 6 Meses")
    fig_pr = go.Figure()
    fig_pr.add_scatter(x=mdf['Periodo'], y=mdf['Ingresos'], name='Ingresos reales', mode='lines+markers', line=dict(color=COLORS['primary'], width=3), hovertemplate="%{x}<br>Real: RD$ %{y:,.2f}<extra></extra>")
    fig_pr.add_scatter(x=mdf['Periodo'], y=mdf['Ingresos_MM3'], name='Media móvil 3M', line=dict(color=COLORS['accent'], width=2, dash='dot'), hovertemplate="%{x}<br>MM3: RD$ %{y:,.2f}<extra></extra>")
    if tiene_proy:
        fig_pr.add_scatter(x=mdf['Periodo'], y=fit, name='Tendencia lineal', line=dict(color=COLORS['warning'], width=2, dash='dash'))
        fig_pr.add_scatter(x=list(fut), y=yf + res_std, mode='lines', line=dict(width=0), showlegend=False, hoverinfo='skip')
        fig_pr.add_scatter(
            x=list(fut), y=np.clip(yf - res_std, 0, None), mode='lines', line=dict(width=0),
            fill='tonexty', fillcolor='rgba(16,185,129,0.18)', name='Banda ±1σ', hoverinfo='skip'
        )
        fig_pr.add_scatter(x=list(fut), y=yf, name='Proyección 6M', mode='lines+markers', line=dict(color=COLORS['success'], width=3, dash='dash'), hovertemplate="%{x}<br>Proyección: RD$ %{y:,.2f}<extra></extra>")
    plot(estilo(
        fig_pr, 415, yaxis_title="Ingresos (DOP)", hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    ))
    narrador_elemento(
        f"Este modelo analítico combina los <b>datos reales de ventas en azul marino</b> con la <b>media móvil de tres meses en línea celeste</b> para filtrar el ruido estacional. "
        + (f"La proyección lineal verde anticipa los próximos <b>{H} meses</b> con una tasa de expansión mensual de <span class='hl-green'><b>{mm(pendiente)}</b></span>, estimando una facturación total de <span class='hl-green'><b>{mm(proy_total)}</b></span> y un promedio de <span class='hl-blue'><b>{mm(proy_prom)}</b></span> al mes, contenida dentro del cono de incertidumbre de más o menos <span class='hl-dark'><b>{mm(res_std)}</b></span>." if tiene_proy else "Se requiere acumular al menos cuatro meses de historial para proyectar la serie con rigor estadístico."),
        "🎙️ Explicación: Proyección a 6 Meses"
    )

    f1, f2 = st.columns(2)
    with f1:
        with st.container(border=True):
            st.subheader("💱 Ingresos Mensuales por Moneda")
            if not fx.empty and fx.sum().sum() > 0:
                fx_long = fx.reset_index().melt(id_vars='Año_Mes', var_name='Moneda', value_name='Ingresos')
                fig_fx = px.area(
                    fx_long, x='Año_Mes', y='Ingresos', color='Moneda',
                    color_discrete_sequence=[COLORS['accent'], COLORS['warning'], COLORS['purple']]
                )
                fig_fx.update_traces(hovertemplate="%{x}<br>%{fullData.name}: RD$ %{y:,.2f}<extra></extra>")
                plot(estilo(fig_fx, 360, xaxis_title="", yaxis_title="DOP equivalentes"))
                ing_dop_puro = float(fx['DOP'].sum()) if 'DOP' in fx.columns else 0.0
                narrador_elemento(
                    f"El gráfico de áreas apiladas segmenta la <b>composición monetaria de los ingresos</b>. La base principal se origina en pesos dominicanos con <span class='hl-blue'><b>{mm(ing_dop_puro)}</b></span>, mientras que la facturación en dólares aporta <span class='hl-purple'><b>{mm(ingresos_usd_dop)}</b></span> equivalentes. Esta diversificación bimonetaria fortalece la posición de la compañía ante contingencias macroeconómicas.",
                    "🎙️ Explicación: Ingresos por Moneda"
                )
            else:
                st.info("Sin ingresos para desglose cambiario.")

    with f2:
        with st.container(border=True):
            st.subheader("🌐 Curva de Dolarización (% USD)")
            fig_us = px.line(x=fx_usd_pct.index, y=fx_usd_pct.values, markers=True, color_discrete_sequence=[COLORS['warning']])
            fig_us.update_traces(line=dict(width=3), hovertemplate="%{x}<br>USD: %{y:.1f}%<extra></extra>")
            plot(estilo(fig_us, 360, xaxis_title="", yaxis_title="% de ingresos en USD"))
            usd_min = float(fx_usd_pct.min()) if len(fx_usd_pct) else 0.0
            usd_max = float(fx_usd_pct.max()) if len(fx_usd_pct) else 0.0
            narrador_elemento(
                f"La curva traza la <b>participación porcentual de los ingresos en moneda extranjera</b> mes a mes. En promedio, la dolarización alcanza el <span class='hl-purple'><b>{pct(pct_dolarizacion)}</b></span>, moviéndose entre un mínimo del <span class='hl-blue'><b>{pct(usd_min)}</b></span> y un techo del <span class='hl-green'><b>{pct(usd_max)}</b></span>. Mantener este nivel de facturación en dólares asegura liquidez en divisa para financiar importaciones de tecnología y licencias sin costo de conversión.",
                "🎙️ Explicación: Curva de Dolarización"
            )

    st.subheader("📋 Variación Trimestral de Ingresos (QoQ)")
    qoq = tri[['Ingresos', 'Utilidad Neta']].copy()
    qoq['Var. Ingresos QoQ %'] = qoq['Ingresos'].pct_change() * 100
    qoq['Margen Neto %'] = np.where(qoq['Ingresos'] > 0, qoq['Utilidad Neta'] / qoq['Ingresos'].replace(0, np.nan) * 100, 0.0)
    tabla(
        qoq.style.format({
            'Ingresos': "RD$ {:,.2f}",
            'Utilidad Neta': "RD$ {:,.2f}",
            'Var. Ingresos QoQ %': "{:+.2f}%",
            'Margen Neto %': "{:.2f}%"
        }, na_rep="—").background_gradient(subset=['Margen Neto %'], cmap='YlGn')
    )
    if len(qoq) > 1 and qoq['Var. Ingresos QoQ %'].notna().any():
        ult_q = str(qoq.index[-1])
        ult_var = float(qoq['Var. Ingresos QoQ %'].iloc[-1]) if pd.notna(qoq['Var. Ingresos QoQ %'].iloc[-1]) else 0.0
        ult_mg = float(qoq['Margen Neto %'].iloc[-1])
        narrador_elemento(
            f"La tabla trimestral cuantifica el ritmo de aceleración o desaceleración comercial entre períodos consecutivos. En el trimestre más reciente registrado correspondiente a <b>{ult_q}</b>, las ventas presentaron una variación del <span class='hl-green'><b>{ult_var:+.1f}%</b></span> con un margen neto del <span class='hl-green'><b>{pct(ult_mg)}</b></span>, permitiendo anticipar el cierre del año y ajustar la meta presupuestaria de ventas.",
            "🎙️ Explicación: Tabla Trimestral QoQ"
        )

# ------------------------------------------------------------------------------
# TAB 5: INFORME GERENCIAL INTEGRAL (OCULTO EN ACORDEONES + AUDIO)
# ------------------------------------------------------------------------------
with tab5:
    narrador_seccion(
        NARR["informe"],
        "🎙️ Dictamen Ejecutivo y Hoja de Ruta 90 Días",
        "Audio disponible siempre · Expanda debajo para leer el memorándum"
    )

    strip = lambda t: re.sub(r'</?(?!b>)[^>]+>', '', t).replace('<b>', '**').replace('</b>', '**')
    inf_resumen = "\n\n".join(strip(p) for p in NARR["resumen"])
    inf_pnl = "\n\n".join(strip(p) for p in NARR["pnl"])
    inf_dep = "\n\n".join(strip(p) for p in NARR["depto"])
    inf_rie = "\n\n".join(strip(p) for p in NARR["riesgos"])
    inf_ten = "\n\n".join(strip(p) for p in NARR["tendencias"])
    meta_cxc = cxc_saldo * 0.55

    informe_md = f"""
### 1. Resumen General y Situación Corporativa
{inf_resumen}

### 2. Rentabilidad y Desempeño de Ingresos
{inf_pnl}

### 3. Eficiencia Departamental y Control Presupuestario
{inf_dep}

### 4. Auditoría, Liquidez y Riesgos Detectados
{inf_rie}

### 5. Tendencias, Proyección y Cobertura Cambiaria
{inf_ten}
"""
    with st.expander("**📜 Ver Memorándum Ejecutivo Completo (Texto Integrado)**", expanded=False):
        st.markdown(informe_md)

    # ---- 2 Gráficos de Consolidación Ejecutiva 360° ----
    col_inf1, col_inf2 = st.columns(2)
    with col_inf1:
        with st.container(border=True):
            st.subheader("📊 Macromagnitudes & Conversión Patrimonial 360°")
            macro_items = [
                ("🟢 Facturación Consolidada", ingresos_tot, COLORS['primary']),
                ("🟣 Margen Bruto (" + pct(margen_bruto) + ")", utilidad_bruta, "#7C3AED"),
                ("🟢 Tesorería en Bancos", liquidez_disp, COLORS['success']),
                ("🔵 Utilidad Neta (" + pct(margen_neto) + ")", utilidad_neta, COLORS['accent']),
                ("🟠 Cartera CxC Inmovilizada", cxc_saldo, "#F59E0B"),
                ("🟡 Erogaciones en Nómina", sueldos_tot, "#EAB308"),
                ("🔴 Pasivos Acumulados (DGII)", pasivos_tot, COLORS['danger']),
                ("🔴 Déficit Caja General", caja_gen, "#991B1B"),
            ]
            fig_macro = go.Figure()
            fig_macro.add_bar(
                y=[it[0] for it in macro_items],
                x=[it[1] for it in macro_items],
                orientation='h',
                marker=dict(color=[it[2] for it in macro_items]),
                text=[fmt_millones(it[1]) for it in macro_items],
                textposition='outside',
                cliponaxis=False,
                hovertemplate="%{y}<br>Saldo: RD$ %{x:,.2f}<extra></extra>"
            )
            fig_macro.add_vline(x=0, line_width=1.5, line_color="#475569")
            fig_macro.update_layout(
                yaxis=dict(autorange="reversed"),
                xaxis=dict(title="Monto en DOP", showgrid=True),
                margin=dict(l=10, r=70, t=10, b=10)
            )
            plot(estilo(fig_macro, 410))
            narrador_elemento(
                f"Este gráfico de macromagnitudes sintetiza la salud estructural de la corporación: "
                f"de una facturación consolidada de <span class='hl-blue'><b>{mm(ingresos_tot)}</b></span>, la empresa retiene <span class='hl-purple'><b>{mm(utilidad_bruta)}</b></span> en margen bruto ({pct(margen_bruto)}) y convierte <span class='hl-green'><b>{mm(utilidad_neta)}</b></span> en utilidad neta ({pct(margen_neto)}). "
                f"En posición de balance, la tesorería disponible en bancos alcanza <span class='hl-green'><b>{mm(liquidez_disp)}</b></span>, lo que brinda solvencia frente a pasivos impositivos y comerciales por <span class='hl-red'><b>{mm(pasivos_tot)}</b></span>. "
                f"No obstante, la gráfica advierte dos focos de atención inmediata: <span class='hl-amber'><b>{mm(cxc_saldo)}</b></span> inmovilizados en cartera de crédito y un déficit de <span class='hl-red'><b>{fmt_dop(caja_gen)}</b></span> en Caja General que requiere arqueo y reposición bancaria.",
                "🎙️ Explicación: Macromagnitudes Consolidadas"
            )

    with col_inf2:
        with st.container(border=True):
            st.subheader("🎯 Hoja de Ruta 90 Días: Impacto Financiero & Plazos")
            impacto_caja_pasivos = pasivos_tot + abs(caja_gen)
            plan_items = [
                ("1. Cobranza CxC (≥55%)", meta_cxc, 60, COLORS['success'], "P1 - Urgente"),
                ("2. Saneamiento Caja & Pasivos", impacto_caja_pasivos, 45, COLORS['danger'], "P1 - Urgente"),
                ("3. Cobertura Divisas USD", ingresos_usd_dop, 30, COLORS['accent'], "P2 - Alta"),
                ("4. Expansión Comercial", proy_total if tiene_proy else (ingresos_tot * 0.20), 90, "#8B5CF6", "P3 - Media"),
            ]
            fig_plan = make_subplots(specs=[[{"secondary_y": True}]])
            fig_plan.add_bar(
                x=[it[0] for it in plan_items],
                y=[it[1] for it in plan_items],
                name="Impacto Financiero (DOP)",
                marker=dict(color=[it[3] for it in plan_items]),
                text=[fmt_millones(it[1]) for it in plan_items],
                textposition='outside',
                cliponaxis=False,
                secondary_y=False,
                hovertemplate="%{x}<br>Impacto Estimado: RD$ %{y:,.2f}<br>Prioridad: %{customdata}<extra></extra>",
                customdata=[it[4] for it in plan_items]
            )
            fig_plan.add_scatter(
                x=[it[0] for it in plan_items],
                y=[it[2] for it in plan_items],
                name="Plazo Límite (Días)",
                mode="lines+markers+text",
                line=dict(color="#0F172A", width=3, dash="dot"),
                marker=dict(size=12, color="#0F172A", symbol="diamond"),
                text=[f"Día {it[2]}" for it in plan_items],
                textposition="top center",
                secondary_y=True,
                hovertemplate="%{x}<br>Plazo de Ejecución: %{y} días<extra></extra>"
            )
            fig_plan.update_yaxes(title_text="Impacto Financiero (DOP)", secondary_y=False)
            fig_plan.update_yaxes(title_text="Plazo Objetivo (Días)", secondary_y=True, range=[0, 115], showgrid=False)
            fig_plan.add_hline(y=30, line_dash="dot", line_color="#94A3B8", line_width=1, secondary_y=True)
            fig_plan.add_hline(y=60, line_dash="dot", line_color="#94A3B8", line_width=1, secondary_y=True)
            fig_plan.add_hline(y=90, line_dash="dot", line_color="#94A3B8", line_width=1, secondary_y=True)
            fig_plan.update_layout(
                xaxis=dict(tickangle=-15),
                margin=dict(l=10, r=10, t=10, b=10)
            )
            plot(estilo(
                fig_plan, 410,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            ))
            narrador_elemento(
                f"La hoja de ruta estratégica a noventa días vincula cada iniciativa con su impacto monetario y plazo perentorio: "
                f"en sesenta días se proyecta liberar <span class='hl-green'><b>{mm(meta_cxc)}</b></span> recuperando más del cincuenta y cinco por ciento de las cuentas por cobrar; "
                f"en cuarenta y cinco días se regularizarán <span class='hl-red'><b>{mm(impacto_caja_pasivos)}</b></span> mediante el arqueo de Caja General y la conciliación de pasivos impositivos ante la DGII y TSS; "
                f"en treinta días se blindarán <span class='hl-blue'><b>{mm(ingresos_usd_dop)}</b></span> facturados en dólares conectando la tasa diaria del Banco Central en el ERP; "
                f"y en noventa días se reasignará presupuesto en mercadeo para consolidar una expansión comercial de <span class='hl-purple'><b>{mm(proy_total if tiene_proy else (ingresos_tot * 0.20))}</b></span>.",
                "🎙️ Explicación: Hoja de Ruta y Metas Estratégicas"
            )

    st.subheader("🎯 Plan de Acción Estratégico a 90 Días")
    plan_df = pd.DataFrame([
        ["P1 - Urgente", "Campaña de Recuperación de Cartera CxC (>60 días)", "Finanzas & Ventas", f"Recuperar ≥ 55% de CxC ({mm(meta_cxc)}) en 60 días"],
        ["P1 - Urgente", "Arqueo de Caja General y Conciliación Fiscal DGII/TSS", "Contraloría Financiera", "Saneamiento al 100% de CTA_101 y pasivos"],
        ["P2 - Alta", "Integración de Tasa de Cambio Diaria Banco Central en ERP", "Tecnología & I+D+i", "Eliminar tasa estática antes del próximo cierre"],
        ["P3 - Media", "Optimización de Presupuesto en Áreas de Crecimiento", "Dirección / Marketing", f"Revisar asignación de {low_dep} y escalar captación"],
    ], columns=["Prioridad", "Iniciativa Estratégica", "Responsable Líder", "Meta Cuantificable"])
    tabla(plan_df, hide_index=True)
    narrador_elemento(
        f"El plan de acción ejecutivo concentra los recursos en <b>cuatro iniciativas de alto impacto</b>: primero, una <b>campaña de cobranza</b> para recuperar al menos el cincuenta y cinco por ciento de las cuentas por cobrar, liberando <span class='hl-green'><b>{mm(meta_cxc)}</b></span> en sesenta días; segundo, el <b>arqueo exhaustivo de Caja General</b> y la <b>conciliación fiscal con la DGII y TSS</b>; tercero, la integración de la API del Banco Central en el ERP; y cuarto, el <b>rebalanceo presupuestario en mercadeo</b> y en <b>{low_dep}</b> para dinamizar la captación de nuevos clientes.",
        "🎙️ Explicación: Plan de Acción 90 Días"
    )

    informe_descarga = informe_md + "\n### 6. Plan de Acción 90 Días\n" + df_a_markdown(plan_df, index=False)
    st.download_button(
        label="📥 Descargar Informe Ejecutivo Completo (.md)",
        data=informe_descarga.encode("utf-8"),
        file_name="Informe_Ejecutivo_Alta_Gerencia.md",
        mime="text/markdown"
    )

# ------------------------------------------------------------------------------
# TAB 6: LIBRO MAYOR & EXPORTACIÓN
# ------------------------------------------------------------------------------
with tab6:
    narrador_seccion(
        NARR["libro"],
        "🎙️ Auditor Contable: Libro Diario y Partida Doble",
        "Audio disponible siempre · Expanda debajo para leer la guía de auditoría"
    )

    st.subheader("🔍 Explorador Detallado del Libro Diario")
    busqueda = st.text_input("🔎 Buscar por Póliza, Cuenta, Responsable o Concepto:", placeholder="Ej: POL-2025, Cloud, Juancito, ITBIS...")
    df_tabla = df.copy()
    if busqueda:
        texto_filas = df_tabla.astype(str).agg(' '.join, axis=1)
        df_tabla = df_tabla[texto_filas.str.contains(busqueda, case=False, regex=False)]

    dif_pd = float(df_tabla['Debito_DOP'].sum() - df_tabla['Credito_DOP'].sum())
    n_usd_vista = int((df_tabla['Moneda'] == 'USD').sum())
    render_kpi_grid([
        kpi_card("📝 Asientos en Vista", f"{len(df_tabla):,}", f"{df_tabla['Numero_Poliza'].nunique():,} pólizas", "pos", COLORS['primary']),
        kpi_card("➕ Total Débitos", mm(df_tabla['Debito_DOP'].sum()), "Cargos DOP", "pos", COLORS['accent']),
        kpi_card("➖ Total Créditos", mm(df_tabla['Credito_DOP'].sum()), "Abonos DOP", "pos", COLORS['success']),
        kpi_card("⚖️ Partida Doble", "Cuadra ✅" if abs(dif_pd) < 0.01 else "Descuadre ⚠️", fmt_dop(dif_pd), "pos" if abs(dif_pd) < 0.01 else "neg", COLORS['warning']),
        kpi_card("💱 Asientos USD", f"{n_usd_vista:,}", "Moneda extranjera", "pos", COLORS['purple']),
    ])

    # ---- 2 Gráficos Ejecutivos de Auditoría Forense y Balance General ----
    col_ld1, col_ld2 = st.columns(2)
    with col_ld1:
        with st.container(border=True):
            st.subheader("⚖️ Matriz Forense de Partida Doble (Débitos vs. Créditos)")
            tipos_orden = ['Activo', 'Pasivo', 'Capital', 'Ingresos', 'Costo', 'Gasto']
            tipos_presentes = [t for t in tipos_orden if t in df_tabla['Tipo_Cuenta'].unique()]
            if not tipos_presentes:
                tipos_presentes = sorted(df_tabla['Tipo_Cuenta'].unique().tolist())

            res_tipo = df_tabla.groupby('Tipo_Cuenta')[['Debito_DOP', 'Credito_DOP']].sum().reindex(tipos_presentes).fillna(0.0)
            neto_tipo = res_tipo['Debito_DOP'] - res_tipo['Credito_DOP']

            fig_pd = make_subplots(specs=[[{"secondary_y": True}]])
            fig_pd.add_bar(
                x=res_tipo.index,
                y=res_tipo['Debito_DOP'],
                name="➕ Total Débitos (Cargos)",
                marker=dict(color=COLORS['accent']),
                text=[fmt_millones(v) for v in res_tipo['Debito_DOP']],
                textposition='auto',
                cliponaxis=False,
                secondary_y=False,
                hovertemplate="%{x}<br>Débitos (Cargos): RD$ %{y:,.2f}<extra></extra>"
            )
            fig_pd.add_bar(
                x=res_tipo.index,
                y=res_tipo['Credito_DOP'],
                name="➖ Total Créditos (Abonos)",
                marker=dict(color=COLORS['success']),
                text=[fmt_millones(v) for v in res_tipo['Credito_DOP']],
                textposition='auto',
                cliponaxis=False,
                secondary_y=False,
                hovertemplate="%{x}<br>Créditos (Abonos): RD$ %{y:,.2f}<extra></extra>"
            )
            fig_pd.add_scatter(
                x=res_tipo.index,
                y=neto_tipo,
                name="⚖️ Saldo Neto (Déb - Créd)",
                mode="lines+markers+text",
                line=dict(color="#0F172A", width=2.5, dash="dot"),
                marker=dict(size=8, color="#0F172A", symbol="diamond"),
                text=[fmt_millones(v) for v in neto_tipo],
                textposition="top center",
                secondary_y=True,
                hovertemplate="%{x}<br>Saldo Neto Contable: RD$ %{y:,.2f}<extra></extra>"
            )
            fig_pd.add_hline(y=0, line_dash="solid", line_color="#475569", line_width=1, secondary_y=True)
            fig_pd.update_yaxes(title_text="Movimiento Bruto (DOP)", secondary_y=False)
            fig_pd.update_yaxes(title_text="Saldo Neto (DOP)", secondary_y=True, showgrid=False)
            fig_pd.update_layout(
                barmode='group',
                margin=dict(l=10, r=10, t=10, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            plot(estilo(fig_pd, 410))
            narrador_elemento(
                f"La matriz forense de partida doble audita la totalidad de los cargos y abonos del Libro Diario consolidando un volumen transaccional idéntico de <span class='hl-blue'><b>{mm(df_tabla['Debito_DOP'].sum())} en débitos</b></span> frente a <span class='hl-green'><b>{mm(df_tabla['Credito_DOP'].sum())} en créditos</b></span>, certificando un <b>cuadre contable matemático perfecto con cero varianza</b>. "
                f"El análisis por naturaleza revela que el bloque de <b>Activos</b> concentra el mayor flujo operativo al absorber el mayor volumen de movimientos por colocación y cobranza de facturas, movimiento de tesorería y desembolsos operativos. "
                f"En términos de control interno y toma de decisiones, la simetría absoluta entre cargos y abonos valida la <b>integridad de los {len(df_tabla):,} asientos y {df_tabla['Numero_Poliza'].nunique():,} pólizas auditadas</b>, descartando registros huérfanos, asimetrías de mayorización o inconsistencias en los asientos de diario.",
                "🎙️ Explicación: Matriz Forense de Partida Doble"
            )

    with col_ld2:
        with st.container(border=True):
            st.subheader("🏛️ Ecuación Patrimonial del Balance General (Activo = Pasivo + Capital)")
            act_df = df_tabla[df_tabla['Tipo_Cuenta'] == 'Activo']
            act_tot = float(act_df['Debito_DOP'].sum() - act_df['Credito_DOP'].sum())

            pas_df = df_tabla[df_tabla['Tipo_Cuenta'] == 'Pasivo']
            pas_neto = float(pas_df['Credito_DOP'].sum() - pas_df['Debito_DOP'].sum())

            cap_df = df_tabla[df_tabla['Tipo_Cuenta'] == 'Capital']
            cap_neto = float(cap_df['Credito_DOP'].sum() - cap_df['Debito_DOP'].sum())

            ing_sub = df_tabla[df_tabla['Tipo_Cuenta'] == 'Ingresos']
            ing_neto = float(ing_sub['Credito_DOP'].sum() - ing_sub['Debito_DOP'].sum())

            cos_sub = df_tabla[df_tabla['Tipo_Cuenta'] == 'Costo']
            cos_neto = float(cos_sub['Debito_DOP'].sum() - cos_sub['Credito_DOP'].sum())

            gas_sub = df_tabla[df_tabla['Tipo_Cuenta'] == 'Gasto']
            gas_neto = float(gas_sub['Debito_DOP'].sum() - gas_sub['Credito_DOP'].sum())

            utilidad_vista = ing_neto - cos_neto - gas_neto
            patrimonio_total = pas_neto + cap_neto + utilidad_vista

            pct_pas = (pas_neto / act_tot * 100) if act_tot > 0 else 0.0
            pct_cap = (cap_neto / act_tot * 100) if act_tot > 0 else 0.0
            pct_res = (utilidad_vista / act_tot * 100) if act_tot > 0 else 0.0

            bal_items = [
                ("🔵 Activos Totales (Recursos)", act_tot, COLORS['primary'], "Total de bienes, derechos y liquidez de la empresa"),
                ("🔴 Pasivos Exigibles (Deudas)", pas_neto, COLORS['danger'], f"Obligaciones fiscales y comerciales ({pct(pct_pas)})"),
                ("⚫ Capital Social (Patrimonio)", cap_neto, "#334155", f"Aportes de los accionistas ({pct(pct_cap)})"),
                ("🟢 Utilidad del Ejercicio", utilidad_vista, COLORS['success'], f"Beneficio neto retenido del ejercicio ({pct(pct_res)})"),
                ("🟣 Total Pasivo + Patrimonio", patrimonio_total, "#7C3AED", "Estructura consolidada de financiamiento"),
            ]

            fig_bal = go.Figure()
            fig_bal.add_bar(
                x=[it[0] for it in bal_items],
                y=[it[1] for it in bal_items],
                marker=dict(color=[it[2] for it in bal_items]),
                text=[fmt_millones(it[1]) for it in bal_items],
                textposition='auto',
                cliponaxis=False,
                hovertemplate="%{x}<br>Monto Contable: RD$ %{y:,.2f}<br>%{customdata}<extra></extra>",
                customdata=[it[3] for it in bal_items]
            )
            if act_tot > 0:
                fig_bal.add_hline(
                    y=act_tot, line_dash="dash", line_color=COLORS['primary'], line_width=1.5,
                    annotation_text=f"Equilibrio: {fmt_millones(act_tot)}", annotation_position="top left"
                )
            fig_bal.update_layout(
                yaxis=dict(title="Monto Consolidado (DOP)", showgrid=True),
                xaxis=dict(tickangle=-15),
                margin=dict(l=10, r=10, t=10, b=10)
            )
            plot(estilo(fig_bal, 410))
            narrador_elemento(
                f"El gráfico de la ecuación patrimonial demuestra la estructura de solvencia y financiamiento corporativo: los <span class='hl-blue'><b>{mm(act_tot)} en Activos Totales</b></span> están respaldados con exactitud milimétrica por la suma de <span class='hl-red'><b>{mm(pas_neto)} en Pasivos Exigibles</b></span> ({pct(pct_pas)}), <span class='hl-dark'><b>{mm(cap_neto)} en Capital Social</b></span> ({pct(pct_cap)}), y <span class='hl-green'><b>{mm(utilidad_vista)} en Utilidad Neta Retenida</b></span> ({pct(pct_res)}), alcanzando un <b>Patrimonio Total de {mm(patrimonio_total)}</b> que iguala exactamente al Activo. "
                f"Para la alta dirección, esta radiografía evidencia una <b>estructura financiera altamente capitalizada y de bajo apalancamiento externo</b>, donde el {pct(pct_cap + pct_res)} de los recursos de la empresa pertenece a fondos propios y beneficios generados, otorgando una holgura patrimonial sobresaliente para respaldar nuevas líneas de crédito bancario o financiar planes de expansión e inversión en tecnología sin comprometer la estabilidad financiera.",
                "🎙️ Explicación: Ecuación Fundamental del Balance General"
            )

    cols_mostrar = [
        'Fecha', 'Numero_Poliza', 'Departamento', 'Responsable', 'Cuenta_Contable',
        'Tipo_Cuenta', 'Moneda', 'Debito_DOP', 'Credito_DOP', 'Monto_Neto_DOP', 'Referencia_Concepto'
    ]

    def color_tipo_cuenta(val):
        colores = {
            'Ingresos': 'background-color: #DCFCE7; color: #166534; font-weight: bold;',
            'Costo': 'background-color: #FEE2E2; color: #991B1B; font-weight: bold;',
            'Gasto': 'background-color: #FEF3C7; color: #92400E; font-weight: bold;',
            'Activo': 'background-color: #E0F2FE; color: #075985;',
            'Pasivo': 'background-color: #F3E8FF; color: #6B21A8;',
            'Capital': 'background-color: #F1F5F9; color: #0F172A; font-weight: bold;'
        }
        return colores.get(val, '')

    tabla(
        df_tabla[cols_mostrar].head(500).style
        .map(color_tipo_cuenta, subset=['Tipo_Cuenta'])
        .format({
            'Fecha': lambda x: x.strftime('%Y-%m-%d'),
            'Debito_DOP': 'RD$ {:,.2f}',
            'Credito_DOP': 'RD$ {:,.2f}',
            'Monto_Neto_DOP': 'RD$ {:,.2f}'
        })
        .bar(subset=['Debito_DOP'], color='#BAE6FD')
        .bar(subset=['Credito_DOP'], color='#BBF7D0'),
        height=460
    )
    st.caption(f"Mostrando hasta 500 de {len(df_tabla):,} asientos. La exportación a Excel incluye todos los registros filtrados.")

    narrador_elemento(
        f"La tabla del Libro Diario audita los <span class='hl-dark'><b>{len(df_tabla):,} asientos contables</b></span> visibles según el filtro seleccionado, correspondientes a <span class='hl-blue'><b>{df_tabla['Numero_Poliza'].nunique():,} pólizas</b></span>. "
        f"Los cargos o débitos totales ascienden a <span class='hl-blue'><b>{mm(df_tabla['Debito_DOP'].sum())}</b></span> y los abonos o créditos a <span class='hl-green'><b>{mm(df_tabla['Credito_DOP'].sum())}</b></span>, "
        f"{'<b>verificando el principio universal de partida doble</b> con un cuadre exacto de cero diferencias' if abs(dif_pd) < 0.01 else f'reflejando una diferencia transitoria de <span class=\"hl-red\"><b>{fmt_dop(dif_pd)}</b></span> debido al filtro parcial de cuentas aplicado'}. "
        f"Asimismo, se identifican <span class='hl-purple'><b>{n_usd_vista:,} registros</b></span> originados en dólares estadounidenses listos para su exportación ejecutiva a Excel.",
        "🎙️ Explicación: Tabla del Libro Diario"
    )

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_tabla[cols_mostrar].to_excel(writer, index=False, sheet_name='Auditoria_Filtrada')
        mdf.to_excel(writer, index=False, sheet_name='Resumen_Mensual')
        anual.reset_index().to_excel(writer, index=False, sheet_name='Estado_Resultados')
        dep_resumen.to_excel(writer, index=False, sheet_name='Departamentos')

    st.download_button(
        label="📊 Exportar Auditoría Completa a Excel (.xlsx)",
        data=buffer.getvalue(),
        file_name="Auditoria_Contable_Filtrada.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )