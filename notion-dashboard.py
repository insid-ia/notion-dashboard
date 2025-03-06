import requests
import pandas as pd
import streamlit as st
import plotly.express as px

# Configurar la API de Notion
NOTION_API_KEY = st.secrets["NOTION_API_KEYntn_143925415892CWpAIVqUoXjBXbzDtu16fAWBwmJwJ568i5"]  # Se leerá desde Streamlit Secrets
DATABASE_ID = st.secrets["18b359dcc19580e69c2bd70d6ac384a3"]  # Se leerá desde Streamlit Secrets

# Función para obtener datos de Notion
def get_notion_data():
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
        st.error("Error al obtener datos de Notion")
        return None

# Procesar los datos en un DataFrame
def parse_notion_data(data):
    proyectos = []
    for result in data["results"]:
        props = result["properties"]
        proyectos.append({
            "Nombre": props["Nombre"]["title"][0]["text"]["content"] if props["Nombre"]["title"] else "",
            "Estado": props["Estado"]["select"]["name"] if props["Estado"]["select"] else "",
            "Valor": props["Valor"]["number"] if props["Valor"]["number"] else 0,
            "Fecha Estimada Cierre": props["Fecha Estimada de Cierre"]["date"]["start"] if props["Fecha Estimada de Cierre"]["date"] else "",
            "Fecha Real Cierre": props["Fecha Real de Cierre"]["date"]["start"] if props["Fecha Real de Cierre"]["date"] else ""
        })
    return pd.DataFrame(proyectos)

# Aplicación Streamlit
st.title("Dashboard de Proyectos - Notion")

# Obtener y procesar datos
data = get_notion_data()
if data:
    df = parse_notion_data(data)
    
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
