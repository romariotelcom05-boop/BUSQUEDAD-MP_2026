import pandas as pd
import streamlit as st

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="MP 2026 - Buscador Multitabla",
    page_icon="📇",
    layout="wide"
)

# --- CONFIGURACIÓN DE GOOGLE SHEETS ---
# ID extraído de tu enlace: 1wfnARSzpsT0jgZmoOGD0wVbDCGuuMEdh
SHEET_ID = "1wfnARSzpsT0jgZmoOGD0wVbDCGuuMEdh"
URL_EXCEL_DRIVE = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"

TABLAS = ["CONTROL_2026_REG", "CONTROL_2026_LIMA"]

# --- ESTILOS CSS ---
st.markdown(
    """
<style>
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 1rem !important;
    }
    div[data-testid="stMetricValue"] {
        font-size: 0.95rem !important;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.75rem !important;
    }
    hr {
        margin: 0.4rem 0 !important;
    }
    .element-container {
        margin-bottom: 0.2rem !important;
    }
</style>
""",
    unsafe_allow_html=True,
)


# --- CARGA Y CACHÉ DE DATOS DESDE GOOGLE DRIVE ---
@st.cache_data(ttl=600, show_spinner="🔄 Cargando datos desde Google Sheets...")
def cargar_datos_drive():
    """Descarga el Excel completo desde Google Sheets y combina las hojas en memoria."""
    try:
        excel_file = pd.ExcelFile(URL_EXCEL_DRIVE)
        dataframes = []

        for tabla in TABLAS:
            if tabla in excel_file.sheet_names:
                df = pd.read_excel(excel_file, sheet_name=tabla, dtype=str)
                df.columns = df.columns.str.strip()
                df["ORIGEN_TABLA"] = tabla
                dataframes.append(df)
            else:
                st.warning(f"⚠️ No se encontró la pestaña '{tabla}' en el Google Sheet.")

        if dataframes:
            df_unificado = pd.concat(dataframes, ignore_index=True)
            return df_unificado
        else:
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error al descargar la data desde Google Sheets: {e}")
        return pd.DataFrame()


# --- OBTENER NOMBRES PARA EL SELECTBOX ---
@st.cache_data
def obtener_lista_nombres(df):
    if df.empty or "NOMBRE" not in df.columns:
        return []
    nombres = df["NOMBRE"].dropna().str.strip().unique().tolist()
    return sorted([n for n in nombres if n])


# --- CARGAR DATASET ---
df_general = cargar_datos_drive()
lista_nombres = obtener_lista_nombres(df_general)

# --- INTERFAZ DE USUARIO ---
col_title, col_btn = st.columns([4, 1])
with col_title:
    st.markdown("### 📇 FLM ENTEL - MANTENIMIENTO PREVENTIVO 2026")
with col_btn:
    if st.button("🔄 Recargar Datos", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Buscador desplegable
nombre_seleccionado = st.selectbox(
    "🔍 **Nombre del Site:**",
    options=[""] + lista_nombres,
    label_visibility="collapsed",
    placeholder="🔍 Selecciona o escribe el NOMBRE de un site..."
)

if nombre_seleccionado:
    # Filtrar en memoria por el nombre exacto
    df_resultados = df_general[df_general["NOMBRE"].str.strip() == nombre_seleccionado]

    if not df_resultados.empty:
        df_mostrar = df_resultados.head(4)
        num_tarjetas = len(df_mostrar)

        # --- DATOS GENERALES DEL SITE ---
        primera_fila = df_mostrar.iloc[0]
        origen = primera_fila.get("ORIGEN_TABLA", "N/A")
        etiqueta_origen = "📍 LIMA" if origen == "CONTROL_2026_LIMA" else "🌎 REGIONES"

        with st.container(border=True):
            st.markdown(
                f"**Site:** `{nombre_seleccionado}` &nbsp;|&nbsp; "
                f"**Zona:** `{etiqueta_origen}` &nbsp;|&nbsp; "
                f"**Cat:** `{primera_fila.get('CATEGORÍA', 'N/A')}` &nbsp;|&nbsp; "
                f"**Prio:** `{primera_fila.get('PRIORIDAD', 'N/A')}` &nbsp;|&nbsp; "
                f"**Frec:** `{primera_fila.get('FRECUENCIA', 'N/A')}` &nbsp;|&nbsp; "
                f"**Infra:** `{primera_fila.get('INFRA_2026', 'N/A')}` &nbsp;|&nbsp; "
                f"**O&M:** `{primera_fila.get('O&M', 'N/A')}`"
            )

        # --- TARJETAS ---
        columnas = [st.container()] if num_tarjetas == 1 else st.columns(num_tarjetas)

        for idx, (_, row) in enumerate(df_mostrar.iterrows()):
            with columnas[idx]:
                obs_texto = ""
                if (
                    "QA_OBS_COMENTARIO" in row
                    and pd.notna(row["QA_OBS_COMENTARIO"])
                    and str(row["QA_OBS_COMENTARIO"]).strip() != ""
                ):
                    obs_texto = str(row["QA_OBS_COMENTARIO"])

                with st.container(border=True):
                    st.markdown(f"##### 🆔 {row.get('OT_ID', 'N/A')}")
                    st.markdown("---")

                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.metric("N° Visita", row.get("N_VISITA", "N/A"))
                    with c2:
                        st.metric("MES", row.get("MES_PLAN", "N/A"))
                    with c3:
                        st.metric("RESPONSABLE", row.get("RESPONSABILITY PM", "N/A"))

                    st.markdown("---")

                    col_qa, col_cl = st.columns(2)
                    with col_qa:
                        estado_qa = str(row.get("STATUS_CLIENTE", "N/A"))
                        mapa_iconos = {
                            "Val Indra": "🟢", "Val Entel": "🟢", "Obs Entel": "👀",
                            "Obs Indra": "👀", "Finalizado": "🟡", "Cancelado": "🔴",
                        }
                        icono_qa = mapa_iconos.get(estado_qa, "⚠️")
                        st.markdown(f"**Status QA:**\n\n{icono_qa} `{estado_qa}`")

                    with col_cl:
                        estado_cl = str(row.get("STATUS_CLIENTE_PLATAFORMA", "N/A"))
                        mapa_iconos_cl = {
                            "close": "🟢", "leave": "⏳", "redo": "🔴", "3rd Party Approval": "🟡",
                        }
                        icono_cl = mapa_iconos_cl.get(estado_cl, "⚠️")
                        st.markdown(f"**Status Cliente:**\n\n{icono_cl} `{estado_cl}`")

                    st.markdown("---")

                    contrata_val = str(row.get("CONTRATA", "N/A"))
                    st.markdown(f"**Contrata:** `{contrata_val}`")

                    if obs_texto:
                        st.markdown("---")
                        st.error(f"**🚨 OBS:** {obs_texto}")
    else:
        st.warning("⚠️ No se encontró ningún registro coincidente en Lima ni en Regiones.")