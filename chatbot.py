import streamlit as st
import pandas as pd
import warnings
from datetime import datetime

pd.set_option('display.max_columns', None)
warnings.filterwarnings('ignore')

st.set_page_config(layout="wide", page_title="Dashboard Storytelling - CLV", initial_sidebar_state="auto")

# ---------- Config ----------
CSV_PATH = "CLV.csv"  # Cambia si necesitas otra ruta

# Paleta de colores solicitada (hex)
COLOR_PALETTE = ["#A8FBD3", "#4FB7B3", "#637AB9", "#31326F"]

# Cambiar fondo y estilo de los filtros
st.markdown(
    """
    <style>
    /* Fondo general del dashboard */
    .stApp {
        background-color: #31326F;
        color: white; /* cambia color de texto a blanco para contraste */
    }

    /* Inputs y filtros (multiselect, selectbox, slider, etc.) */
    .stSelectbox [data-baseweb="select"] {
        background-color: white !important;
        color: black !important;
    }

    .stMultiSelect [data-baseweb="select"] {
        background-color: white !important;
        color: black !important;
    }

    /* Cuando se seleccionan opciones en multiselect */
    .stMultiSelect span[data-baseweb="tag"] {
        background-color: #31326F !important;
        color: white !important;
    }

    /* Slider */
    .stSlider [data-baseweb="slider"] > div {
        background: #31326F !important;
    }

    /* Títulos */
    h1, h2, h3, h4, h5, h6 {
        color: #A8FBD3;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ---------- Utilities ----------
@st.cache_data
def load_and_prepare(path):
    df = pd.read_csv(path, sep=";", dtype=str)

    mapping_exact = {
    "Customer": "Cliente",
    "State": "Estado",
    "Customer Lifetime Value": "Valor Vida Cliente",
    "Response": "Respuesta",
    "Coverage": "Cobertura",
    "Education": "Educacion",
    "Effective To Date": "Fecha Efectiva",
    "EmploymentStatus": "Estado Empleo",
    "Gender": "Genero",
    "Income": "Ingreso",
    "Location Code": "Codigo Ubicacion",
    "Marital Status": "Estado Civil",
    "Monthly Premium Auto": "Prima Mensual Auto",
    "Months Since Last Claim": "Meses Desde Ultimo Reclamo",
    "Months Since Policy Inception": "Meses Desde Inicio Poliza",
    "Number of Open Complaints": "Numero Quejas Abiertas",
    "Number of Policies": "Numero Polizas",
    "Policy Type": "Tipo Poliza",
    "Policy": "Poliza",
    "Renew Offer Type": "Tipo Oferta Renovacion",
    "Sales Channel": "Canal Ventas",
    "Total Claim Amount": "Monto Total Reclamos",
    "Vehicle Class": "Clase Vehiculo",
    "Vehicle Size": "Dimension Vehiculo"
    }

    # Renombrar columnas
    existing_map = {k: v for k, v in mapping_exact.items() if k in df.columns}
    df.rename(columns=existing_map, inplace=True)

    # Columnas a convertir a numéricas (con limpieza: primero quitar ".", luego cambiar a número)
    numeric_cols = ["Valor Vida Cliente", "Monto Total Reclamos", "Prima Mensual Auto", 
                    "Meses Desde Ultimo Reclamo", "Meses Desde Inicio Poliza", "Numero Quejas Abiertas", 
                    "Numero Polizas", "Ingreso",]

    for col in numeric_cols:
        if col in df.columns:
            # Aseguramos string y rellenamos nulos para evitar errores con .str methods
            s = df[col].fillna("").astype(str)

            # 1) Quitar puntos (.) primero
            s = s.str.replace(".", "", regex=False)

            # 2) Quitar comas, signo $, espacios sobrantes
            s = s.str.replace(",", "", regex=False)
            s = s.str.replace("$", "", regex=False)
            s = s.str.strip()

            # 3) Convertir a numérico (coerce -> NaN donde no se pueda)
            df[col] = pd.to_numeric(s, errors="coerce")

    # Convertir Fecha Efectiva -> datetime (se espera dd/mm/YYYY)
        if "Fecha Efectiva" in df.columns:
            df["Fecha Efectiva"] = pd.to_datetime(
                df["Fecha Efectiva"].astype(str).str.strip(),
                dayfirst=True,
                errors="coerce"
            )

            # Crear columna Year-Month solo si es datetime válido
            if pd.api.types.is_datetime64_any_dtype(df["Fecha Efectiva"]):
                df["year_month"] = df["Fecha Efectiva"].dt.to_period("M").astype(str)
                df["year_month_display"] = df["Fecha Efectiva"].dt.strftime("%Y-%m")
            else:
                df["year_month"] = pd.NA
                df["year_month_display"] = pd.NA

    return df

# ---------- Load data ----------
with st.spinner("Cargando datos..."):
    df = load_and_prepare(CSV_PATH)

# ============================
# 2. Chatbot
# ============================

st.title("💬 Chat Bot de Seguros")
st.markdown("""
Este es un chatbot interactivo.  
Opciones de consulta:
- Estadísticas de clientes  
- Coberturas disponibles  
- Canales de venta  
- Información sobre pólizas  
""")

# Diccionario de respuestas predefinidas
respuestas = {
    "saludo": "Hola, ¿en qué te puedo ayudar?",
    "clientes": "Actualmente tenemos un total de {} clientes registrados.".format(df["Cliente"].nunique()),
    "cobertura": "Las coberturas disponibles son: {}".format(", ".join(df["Cobertura"].unique())),
    "cargo_mensual": "Los cargos mensuales acumulados son: {}".format(df["Prima Mensual Auto"].sum()),
    "ventas": "Los canales de venta disponibles son: {}".format(", ".join(df["Canal Ventas"].unique())),
    "poliza": "Existen {} tipos de pólizas: {}".format(
        df["Tipo Poliza"].nunique(), ", ".join(df["Tipo Poliza"].unique())
    ),
    "estado": "Los estados donde tenemos clientes son: {}".format(", ".join(df["Estado"].unique())),
}

mapeo_entradas = {
    "cargo_mensual": ["ventas", "cargo mensual", "acumulado mensual", "cómo van las ventas", "informe de ventas", "total de ventas este mes", "ventas acumuladas"],
    "ventas": ["dime los canales de ventas", "canales de ventas", "informe canales de ventas", "canales"],
    "clientes": ["cuántos clientes nuevos", "clientes ganados", "estadísticas de clientes", "informe de clientes", "nuevos clientes trimestre"],
    "cobertura": ["cobertura", "rendimiento de cobertura", "coberturas", "coberturas disponibles", "estadísticas de cobertura"],
    "poliza": ["poliza", "tipo poliza", "polizas", "generar poliza"],
    "saludo": ["hola", "buenas", "qué tal", "hey", "saludos"]
}

# Inicializar historial de chat
if "historial" not in st.session_state:
    st.session_state.historial = []

# Entrada del usuario
entrada = st.text_input("Escribe tu consulta:")

def buscar_intencion(user_input, training_phrases):
    user_input = user_input.lower().strip()
    for intent, phrases in training_phrases.items():
        if user_input in [p.lower() for p in phrases]:
            return intent
    return ""

# Procesar consulta
if entrada:
    entrada_lower = entrada.lower()
    entrada_lower = buscar_intencion(entrada_lower, mapeo_entradas)
    respuesta = "Lo siento, no entendí tu consulta. Intenta con otra pregunta."

    for clave, texto in respuestas.items():
        if clave in entrada_lower:
            respuesta = texto
            break
        else:
            respuesta = "Lo siento, no entendí tu consulta. Intenta con otra pregunta."

    # Guardar en historial
    st.session_state.historial.append(("Tú", entrada))
    st.session_state.historial.append(("Bot", respuesta))

# Mostrar historial
for emisor, mensaje in st.session_state.historial:
    if emisor == "Tú":
        st.markdown(f"**{emisor}:** {mensaje}")
    else:
        st.markdown(f"<div style='background-color:#31326F;color:white;padding:10px;border-radius:10px;margin:5px 0;'>{mensaje}</div>", unsafe_allow_html=True)
