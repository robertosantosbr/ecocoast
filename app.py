import os
from pathlib import Path

import folium
import pandas as pd
import psycopg2
import streamlit as st
from folium.plugins import HeatMap
from streamlit_folium import st_folium

st.set_page_config(page_title="EcoCoast", page_icon="🌊", layout="wide")

IMAGE_DIR = Path("images/residuos")
IMAGE_DIR.mkdir(parents=True, exist_ok=True)


def get_db_config():
    """Lê credenciais do Streamlit Secrets ou variáveis de ambiente."""
    return {
        "host": st.secrets.get("DB_HOST", os.getenv("DB_HOST", "")),
        "port": int(st.secrets.get("DB_PORT", os.getenv("DB_PORT", "5432"))),
        "database": st.secrets.get("DB_NAME", os.getenv("DB_NAME", "")),
        "user": st.secrets.get("DB_USER", os.getenv("DB_USER", "")),
        "password": st.secrets.get("DB_PASSWORD", os.getenv("DB_PASSWORD", "")),
        "sslmode": st.secrets.get("DB_SSLMODE", os.getenv("DB_SSLMODE", "require")),
    }


@st.cache_data(ttl=60)
def carregar_dados():
    cfg = get_db_config()
    if not all([cfg["host"], cfg["database"], cfg["user"], cfg["password"]]):
        return pd.DataFrame()
    query = """
        SELECT id, data, categoria, descricao, latitude, longitude,
               imagem_residuo, imagem_residuo_box
        FROM residuos
        ORDER BY data DESC;
    """
    with psycopg2.connect(**cfg) as conn:
        df = pd.read_sql(query, conn)
    df["latitude_num"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude_num"] = pd.to_numeric(df["longitude"], errors="coerce")
    df = df.dropna(subset=["latitude_num", "longitude_num"])
    return df


def caminho_imagem(nome_arquivo):
    if not nome_arquivo:
        return None
    path = IMAGE_DIR / str(nome_arquivo)
    return str(path) if path.exists() else None


def card(titulo, valor, icone):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-icon">{icone}</div>
            <div>
                <div class="metric-title">{titulo}</div>
                <div class="metric-value">{valor}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def aplicar_css():
    st.markdown(
        """
        <style>
        .main {background-color: #f7f9fb;}
        .block-container {padding-top: 1rem;}
        .metric-card {
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 18px;
            display: flex;
            gap: 14px;
            align-items: center;
            box-shadow: 0 1px 4px rgba(0,0,0,0.05);
            min-height: 100px;
        }
        .metric-icon {
            background: #eef6ff;
            border-radius: 10px;
            padding: 10px;
            font-size: 24px;
        }
        .metric-title {font-size: 13px; color: #4b5563; font-weight: 600;}
        .metric-value {font-size: 28px; color: #111827; font-weight: 800;}
        .section-title {font-size: 18px; font-weight: 800; margin: 8px 0 10px 0;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def mapa_base(df, heat=False):
    if df.empty:
        return folium.Map(location=[40.62, -8.75], zoom_start=12, tiles="OpenStreetMap")
    centro = [df["latitude_num"].mean(), df["longitude_num"].mean()]
    m = folium.Map(location=centro, zoom_start=12, tiles="OpenStreetMap")
    if heat:
        HeatMap(df[["latitude_num", "longitude_num"]].values.tolist(), radius=25, blur=18).add_to(m)
    else:
        cores = {"Copo": "blue", "Garrafa": "green", "Papelao": "orange", "Papelão": "orange", "Lata": "red", "Sacola": "purple"}
        for _, r in df.iterrows():
            popup = f"<b>{r.get('categoria','')}</b><br>{r.get('descricao','')}<br>{r.get('data','')}"
            folium.Marker(
                location=[r["latitude_num"], r["longitude_num"]],
                popup=popup,
                tooltip=str(r.get("categoria", "")),
                icon=folium.Icon(color=cores.get(str(r.get("categoria", "")), "gray"), icon="trash", prefix="fa"),
            ).add_to(m)
    return m


def tabela_deteccoes(df):
    mostrar = df[["data", "categoria", "descricao", "latitude", "longitude", "imagem_residuo", "imagem_residuo_box"]].copy()
    mostrar = mostrar.rename(columns={
        "data": "Data/Hora",
        "categoria": "Classificação",
        "descricao": "Descrição",
        "latitude": "Latitude",
        "longitude": "Longitude",
        "imagem_residuo": "Imagem",
        "imagem_residuo_box": "Imagem Box",
    })
    st.dataframe(mostrar, use_container_width=True, hide_index=True)


aplicar_css()
st.sidebar.title("EcoCoast")
pagina = st.sidebar.radio("Dashboard", ["Geolocalização", "Mapa de calor"])
st.sidebar.caption("Monitoramento de Resíduos Litorâneos")

st.title("Monitoramento de Resíduos Litorâneos - EcoCoast")

df = carregar_dados()

if df.empty:
    st.warning("Nenhum dado encontrado ou credenciais do banco não configuradas.")
else:
    total_imagens = df["imagem_residuo"].nunique()
    total_residuos = len(df)
    categorias = df["categoria"].value_counts()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        card("Contagem Total de Imagens", f"{total_imagens:,}", "📷")
    with c2:
        card("Total de Resíduos Detectados", f"{total_residuos:,}", "♻️")
    with c3:
        top_txt = "<br>".join([f"{k}: {v}" for k, v in categorias.head(3).items()])
        st.markdown(f"<div class='metric-card'><div><div class='metric-title'>Principais Classificações</div><div style='font-size:16px;font-weight:700'>{top_txt}</div></div></div>", unsafe_allow_html=True)
    with c4:
        praias = df["descricao"].nunique()
        card("Praias Monitoradas", f"{praias}", "📍")

    st.markdown("<div class='section-title'>Filtros</div>", unsafe_allow_html=True)
    f1, f2 = st.columns(2)
    with f1:
        cats = st.multiselect("Categoria", sorted(df["categoria"].dropna().unique()), default=sorted(df["categoria"].dropna().unique()))
    with f2:
        praias_sel = st.multiselect("Praia", sorted(df["descricao"].dropna().unique()), default=sorted(df["descricao"].dropna().unique()))
    df_filtrado = df[df["categoria"].isin(cats) & df["descricao"].isin(praias_sel)]

    if pagina == "Geolocalização":
        st.markdown("<div class='section-title'>Mapa de Resíduos</div>", unsafe_allow_html=True)
        st_folium(mapa_base(df_filtrado, heat=False), width=None, height=430)
    else:
        st.markdown("<div class='section-title'>Mapa de Calor de Resíduos</div>", unsafe_allow_html=True)
        st_folium(mapa_base(df_filtrado, heat=True), width=None, height=430)

    st.markdown("<div class='section-title'>Deteções Recentes</div>", unsafe_allow_html=True)
    tabela_deteccoes(df_filtrado.head(50))
