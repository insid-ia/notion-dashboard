import requests
import pandas as pd
import streamlit as st
import plotly.express as px

# Configurar la API de Notion (usando Streamlit Secrets para seguridad)
NOTION_API_KEY = st.secrets["NOTION_API_KEY"]  # Clave de API de Notion
DATABASE_ID = st.secrets["DATABASE_ID"]  # ID de la base de datos de Notion

# Función para obtener datos de Notion
def get_notion_data():
    """
    Realiza una consulta a la API de Notion para obtener los datos de la base de datos.
    Devuelve un JSON con los datos o muestra un error si la solicitud falla.
    """
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    response = requests.post(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error al obtener datos de Notion: {response.status_code}")
        st.json(response.json())  # Muestra el error en la interfaz para depuración
        return None

# Función para procesar los datos de Notion y convertirlos en un DataFrame
def parse_notion_data(data):
    """
    Convierte los datos de Notion en un DataFrame de Pandas, manejando valores faltantes.
    """
    proyectos = []
    for result in data["results"]:
        props = result.get("properties", {})  # Obtiene las propiedades o un diccionario vacío si no existen
        
        # Extraer valores de cada propiedad con validación para evitar errores
        nombre = props.get("Nombre", {}).get("title", [])
        nombre = nombre[0]["text"]["content"] if nombre else "Sin Nombre"
        
        estado = props.get("Estado", {}).get("status", {})
        estado = estado.get("name", "Sin Estado") if estado else "Sin Estado"

        valor = props.get("Valor", {}).get("number", 0)
        
        fecha_estimada = props.get("Fecha Estimada de Cierre", {}).get("date", {})
        fecha_estimada = fecha_estimada.get("start", "")
        
        fecha_real = props.get("Fecha Real de Cierre", {}).get("date", {})
        fecha_real = fecha_real.get("start", "")
        
        proyectos.append({
            "Nombre": nombre,
            "Estado": estado,
            "Valor": valor,
            "Fecha Estimada Cierre": fecha_estimada,
            "Fecha Real Cierre": fecha_real
        })
    return pd.DataFrame(proyectos)

# Aplicación Streamlit
st.title("Dashboard de Proyectos - Notion")

# Obtener y procesar datos
data = get_notion_data()
if data:
    df = parse_notion_data(data)
    
    if df.empty:
        st.warning("No hay datos disponibles en la base de Notion.")
    else:
        # Métricas clave
        total_proyectos = len(df)
        proyectos_activos = len(df[df["Estado"] == "En curso"])
        proyectos_finalizados = len(df[df["Estado"] == "Finalizado"])
        proyectos_retrasados = len(df[df["Estado"] == "Retrasado"])
        
        st.metric("Total Proyectos", total_proyectos)
        st.metric("Proyectos Activos", proyectos_activos)
        st.metric("Proyectos Finalizados", proyectos_finalizados)
        st.metric("Proyectos Retrasados", proyectos_retrasados)
        
        # Gráfico de estados de proyectos
        fig1 = px.bar(df["Estado"].value_counts(), labels={'index':'Estado', 'value':'Cantidad'}, title="Distribución de Estado de Proyectos")
        st.plotly_chart(fig1)
        
        # Evolución de retrasos
        df["Fecha Real Cierre"] = pd.to_datetime(df["Fecha Real Cierre"], errors='coerce')
        df["Fecha Estimada Cierre"] = pd.to_datetime(df["Fecha Estimada Cierre"], errors='coerce')
        df["Retraso (días)"] = (df["Fecha Real Cierre"] - df["Fecha Estimada Cierre"]).dt.days
        retraso_promedio = df.groupby(df["Fecha Real Cierre"].dt.to_period("M"))["Retraso (días)"].mean()
        fig2 = px.line(retraso_promedio, labels={'index':'Mes', 'value':'Retraso Promedio (días)'}, title="Evolución de Retrasos en los Proyectos")
        st.plotly_chart(fig2)

st.write("Actualizado dinámicamente desde Notion API 🚀")

