# -*- coding: utf-8 -*-
"""
Reto C4SC4: Dashboard de desempeño de colaboradores
Aplicación desarrollada en Streamlit para analizar KPIs de empleados
de Socialize your knowledge.

Para ejecutar:
    streamlit run app.py
"""

import base64
from io import StringIO

import pandas as pd
import plotly.express as px
import streamlit as st


# ============================================================
# 1. CONFIGURACIÓN GENERAL DE LA APLICACIÓN
# ============================================================

st.set_page_config(
    page_title="Dashboard de desempeño | Socialize your knowledge",
    page_icon="📊",
    layout="wide",
)


# ============================================================
# 2. LOGOTIPO DE LA EMPRESA
#    Se usa un SVG embebido para que la app funcione sin archivos externos.
# ============================================================

LOGO_SVG = """
<svg width="430" height="110" viewBox="0 0 430 110" xmlns="http://www.w3.org/2000/svg">
  <rect x="4" y="4" width="422" height="102" rx="22" fill="#F7FAFC" stroke="#1E3A8A" stroke-width="4"/>
  <circle cx="60" cy="55" r="28" fill="#1E3A8A"/>
  <circle cx="60" cy="55" r="17" fill="#14B8A6"/>
  <text x="105" y="47" font-family="Arial, Helvetica, sans-serif" font-size="24" font-weight="700" fill="#1E3A8A">
    Socialize
  </text>
  <text x="105" y="78" font-family="Arial, Helvetica, sans-serif" font-size="22" font-weight="600" fill="#14B8A6">
    your knowledge
  </text>
</svg>
"""


def show_logo() -> None:
    """Despliega el logotipo en la aplicación."""
    logo_base64 = base64.b64encode(LOGO_SVG.encode("utf-8")).decode("utf-8")
    st.markdown(
        f"""
        <div style="display:flex; justify-content:center; margin-bottom:10px;">
            <img src="data:image/svg+xml;base64,{logo_base64}" width="430">
        </div>
        """,
        unsafe_allow_html=True,
    )


show_logo()


# ============================================================
# 3. TÍTULO Y DESCRIPCIÓN DEL DASHBOARD
# ============================================================

st.title("Dashboard de desempeño de colaboradores")
st.write(
    """
    Esta aplicación web permite consultar indicadores de desempeño de los colaboradores
    de **Socialize your knowledge**. El tablero integra filtros interactivos por género,
    rango de puntaje de desempeño y estado civil, con el fin de identificar fortalezas,
    áreas de oportunidad y patrones generales asociados al rendimiento laboral.
    """
)


# ============================================================
# 4. CARGA Y LIMPIEZA DE DATOS
# ============================================================

@st.cache_data
def load_data(file) -> pd.DataFrame:
    """
    Carga la base de datos Employee_data.csv y realiza una limpieza mínima:
    - elimina espacios en nombres de columnas;
    - elimina espacios en variables categóricas;
    - convierte fechas y variables numéricas.
    """
    data = pd.read_csv(file)

    # Limpieza de nombres de columnas
    data.columns = data.columns.str.strip()

    # Limpieza de textos categóricos
    text_columns = data.select_dtypes(include=["object"]).columns
    for column in text_columns:
        data[column] = data[column].astype(str).str.strip()

    # Conversión de fechas
    date_columns = ["birth_date", "hiring_date", "last_performance_date"]
    for column in date_columns:
        if column in data.columns:
            data[column] = pd.to_datetime(data[column], errors="coerce")

    # Conversión de variables numéricas relevantes
    numeric_columns = [
        "age",
        "salary",
        "performance_score",
        "average_work_hours",
        "satisfaction_level",
        "absences",
    ]
    for column in numeric_columns:
        if column in data.columns:
            data[column] = pd.to_numeric(data[column], errors="coerce")

    return data


uploaded_file = st.sidebar.file_uploader(
    "Carga la base Employee_data.csv",
    type=["csv"],
)

if uploaded_file is not None:
    df = load_data(uploaded_file)
else:
    try:
        df = load_data("Employee_data.csv")
        st.sidebar.info("Se cargó automáticamente el archivo Employee_data.csv.")
    except FileNotFoundError:
        st.error(
            "No se encontró Employee_data.csv. Carga el archivo desde el panel lateral."
        )
        st.stop()


# ============================================================
# 5. VALIDACIÓN DE COLUMNAS SOLICITADAS
# ============================================================

required_columns = [
    "name_employee",
    "birth_date",
    "age",
    "gender",
    "marital_status",
    "hiring_date",
    "position",
    "salary",
    "performance_score",
    "last_performance_date",
    "average_work_hours",
    "satisfaction_level",
    "absences",
]

missing_columns = [column for column in required_columns if column not in df.columns]

if missing_columns:
    st.error(
        "La base de datos no contiene todas las columnas requeridas. "
        f"Columnas faltantes: {missing_columns}"
    )
    st.stop()


# ============================================================
# 6. CONTROLES DE FILTRO
# ============================================================

st.sidebar.header("Filtros del análisis")

# 6.1 Control para seleccionar género
gender_options = ["Todos"] + sorted(df["gender"].dropna().unique().tolist())
selected_gender = st.sidebar.selectbox(
    "Selecciona el género del empleado",
    gender_options,
)

# 6.2 Control para seleccionar rango de desempeño
selected_performance_range = st.sidebar.slider(
    "Selecciona el rango del puntaje de desempeño",
    min_value=1,
    max_value=5,
    value=(1, 5),
    step=1,
)

# 6.3 Control para seleccionar estado civil
marital_options = ["Todos"] + sorted(df["marital_status"].dropna().unique().tolist())
selected_marital_status = st.sidebar.selectbox(
    "Selecciona el estado civil del empleado",
    marital_options,
)


# ============================================================
# 7. APLICACIÓN DE FILTROS
# ============================================================

filtered_df = df.copy()

if selected_gender != "Todos":
    filtered_df = filtered_df[filtered_df["gender"] == selected_gender]

filtered_df = filtered_df[
    filtered_df["performance_score"].between(
        selected_performance_range[0],
        selected_performance_range[1],
    )
]

if selected_marital_status != "Todos":
    filtered_df = filtered_df[
        filtered_df["marital_status"] == selected_marital_status
    ]

st.subheader("Base filtrada")
st.write(f"Registros disponibles después de aplicar filtros: **{len(filtered_df)}**")

if filtered_df.empty:
    st.warning("No hay registros para la combinación de filtros seleccionada.")
    st.stop()


# ============================================================
# 8. KPI'S PRINCIPALES DE LOS COLABORADORES
# ============================================================

st.subheader("KPI's principales")

kpi_1, kpi_2, kpi_3, kpi_4, kpi_5 = st.columns(5)

kpi_1.metric("Colaboradores", f"{len(filtered_df):,}")
kpi_2.metric("Desempeño promedio", f"{filtered_df['performance_score'].mean():.2f}")
kpi_3.metric("Satisfacción promedio", f"{filtered_df['satisfaction_level'].mean():.2f}")
kpi_4.metric("Salario promedio", f"${filtered_df['salary'].mean():,.0f}")
kpi_5.metric("Ausencias promedio", f"{filtered_df['absences'].mean():.1f}")


# ============================================================
# 9. VISUALIZACIÓN: DISTRIBUCIÓN DE PUNTAJES DE DESEMPEÑO
# ============================================================

st.subheader("Distribución de los puntajes de desempeño")

performance_distribution = (
    filtered_df["performance_score"]
    .value_counts()
    .sort_index()
    .reset_index()
)
performance_distribution.columns = ["performance_score", "count"]

fig_performance = px.bar(
    performance_distribution,
    x="performance_score",
    y="count",
    text="count",
    labels={
        "performance_score": "Puntaje de desempeño",
        "count": "Número de colaboradores",
    },
    title="Distribución de puntajes de desempeño",
)

fig_performance.update_traces(textposition="outside")
fig_performance.update_layout(xaxis=dict(dtick=1))
st.plotly_chart(fig_performance, use_container_width=True)


# ============================================================
# 10. VISUALIZACIÓN: PROMEDIO DE HORAS TRABAJADAS POR GÉNERO
# ============================================================

st.subheader("Promedio de horas trabajadas por género")

hours_by_gender = (
    filtered_df.groupby("gender", as_index=False)["average_work_hours"]
    .mean()
    .sort_values("average_work_hours", ascending=False)
)

fig_hours_gender = px.bar(
    hours_by_gender,
    x="gender",
    y="average_work_hours",
    text=hours_by_gender["average_work_hours"].round(1),
    labels={
        "gender": "Género",
        "average_work_hours": "Promedio de horas trabajadas",
    },
    title="Promedio de horas trabajadas por género",
)

fig_hours_gender.update_traces(textposition="outside")
st.plotly_chart(fig_hours_gender, use_container_width=True)


# ============================================================
# 11. VISUALIZACIÓN: EDAD DE LOS EMPLEADOS VS. SALARIO
# ============================================================

st.subheader("Edad de los empleados con respecto al salario")

fig_age_salary = px.scatter(
    filtered_df,
    x="age",
    y="salary",
    color="gender",
    hover_name="name_employee",
    hover_data={
        "position": True,
        "marital_status": True,
        "performance_score": True,
        "average_work_hours": True,
        "salary": ":,.0f",
    },
    labels={
        "age": "Edad",
        "salary": "Salario",
        "gender": "Género",
    },
    title="Relación entre edad y salario",
)

st.plotly_chart(fig_age_salary, use_container_width=True)


# ============================================================
# 12. VISUALIZACIÓN: HORAS TRABAJADAS VS. PUNTAJE DE DESEMPEÑO
# ============================================================

st.subheader("Promedio de horas trabajadas versus puntaje de desempeño")

fig_hours_performance = px.scatter(
    filtered_df,
    x="average_work_hours",
    y="performance_score",
    color="gender",
    size="satisfaction_level",
    hover_name="name_employee",
    hover_data={
        "position": True,
        "salary": ":,.0f",
        "absences": True,
        "satisfaction_level": True,
    },
    labels={
        "average_work_hours": "Promedio de horas trabajadas",
        "performance_score": "Puntaje de desempeño",
        "gender": "Género",
        "satisfaction_level": "Nivel de satisfacción",
    },
    title="Relación entre horas trabajadas y desempeño",
)

fig_hours_performance.update_layout(yaxis=dict(dtick=1))
st.plotly_chart(fig_hours_performance, use_container_width=True)


# ============================================================
# 13. TABLA DE DATOS RELEVANTES
# ============================================================

st.subheader("Detalle de colaboradores")

columns_to_show = [
    "name_employee",
    "age",
    "gender",
    "marital_status",
    "position",
    "salary",
    "performance_score",
    "last_performance_date",
    "average_work_hours",
    "satisfaction_level",
    "absences",
]

st.dataframe(
    filtered_df[columns_to_show].sort_values(
        by=["performance_score", "satisfaction_level"],
        ascending=False,
    ),
    use_container_width=True,
)


# ============================================================
# 14. CONCLUSIONES DEL ANÁLISIS
# ============================================================

st.subheader("Conclusiones del análisis")

mean_performance = filtered_df["performance_score"].mean()
mean_satisfaction = filtered_df["satisfaction_level"].mean()
mean_absences = filtered_df["absences"].mean()
dominant_score = int(filtered_df["performance_score"].mode().iloc[0])
highest_salary = filtered_df["salary"].max()
lowest_salary = filtered_df["salary"].min()

st.markdown(
    f"""
    A partir de los filtros seleccionados se analizaron **{len(filtered_df)} colaboradores**.
    El puntaje promedio de desempeño fue de **{mean_performance:.2f}**, mientras que el
    puntaje más frecuente fue **{dominant_score}**. La satisfacción promedio se ubicó en
    **{mean_satisfaction:.2f}** y el promedio de ausencias fue de **{mean_absences:.1f}**.

    En términos generales, el tablero permite identificar grupos con mejor desempeño,
    revisar si existen diferencias entre género y horas trabajadas, y observar la relación
    entre edad, salario y rendimiento. También facilita detectar colaboradores que podrían
    requerir acompañamiento cuando presentan bajo desempeño, menor satisfacción o niveles
    altos de ausentismo.

    El rango salarial observado en la selección va de **${lowest_salary:,.0f}** a
    **${highest_salary:,.0f}**, por lo que la visualización edad-salario ayuda a reconocer
    posibles diferencias asociadas al puesto, experiencia o nivel de responsabilidad.
    """
)


# ============================================================
# 15. DESCARGA DE DATOS FILTRADOS
# ============================================================

csv_buffer = StringIO()
filtered_df.to_csv(csv_buffer, index=False)

st.download_button(
    label="Descargar datos filtrados en CSV",
    data=csv_buffer.getvalue(),
    file_name="employee_data_filtrado.csv",
    mime="text/csv",
)
