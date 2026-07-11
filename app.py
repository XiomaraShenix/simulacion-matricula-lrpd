from __future__ import annotations

from io import BytesIO
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from simulacion import (
    ConfiguracionEscenario,
    comparar_escenarios,
    construir_comparacion,
)


st.set_page_config(
    page_title="Simulación de Matrícula en Línea",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)


def aplicar_estilos() -> None:
    st.markdown(
        """
        <style>
        :root {
            --azul-oscuro: #172554;
            --azul: #1d4ed8;
            --celeste: #eaf2ff;
            --morado: #6d28d9;
            --gris: #64748b;
            --borde: #dbe4f0;
        }

        .stApp {
            background:
                radial-gradient(circle at top right, rgba(59, 130, 246, 0.10), transparent 32%),
                linear-gradient(180deg, #f8fbff 0%, #ffffff 42%, #f8fafc 100%);
        }

        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 3rem;
            max-width: 1450px;
        }

        .hero {
            padding: 2rem 2.2rem;
            border-radius: 24px;
            background: linear-gradient(125deg, #172554 0%, #1d4ed8 55%, #6d28d9 100%);
            color: white;
            box-shadow: 0 18px 45px rgba(30, 64, 175, 0.20);
            margin-bottom: 1.2rem;
        }

        .hero h1 {
            margin: 0;
            font-size: 2.2rem;
            line-height: 1.15;
        }

        .hero p {
            margin: 0.8rem 0 0;
            opacity: 0.92;
            font-size: 1.05rem;
            max-width: 950px;
        }

        .badge {
            display: inline-block;
            padding: 0.35rem 0.7rem;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.16);
            border: 1px solid rgba(255, 255, 255, 0.24);
            margin-bottom: 0.9rem;
            font-size: 0.85rem;
        }

        .info-card {
            background: rgba(255, 255, 255, 0.88);
            border: 1px solid var(--borde);
            border-radius: 18px;
            padding: 1rem 1.1rem;
            min-height: 120px;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
        }

        .info-card h3 {
            margin-top: 0;
            color: var(--azul-oscuro);
            font-size: 1rem;
        }

        .info-card p {
            margin-bottom: 0;
            color: var(--gris);
            line-height: 1.55;
        }

        div[data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.94);
            border: 1px solid var(--borde);
            border-radius: 16px;
            padding: 1rem;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
        }

        div[data-testid="stMetricLabel"] {
            color: #475569;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #f4f7ff 0%, #ffffff 100%);
            border-right: 1px solid #dbe4f0;
        }

        .section-title {
            margin-top: 0.4rem;
            color: #172554;
            font-weight: 750;
        }

        .nota {
            background: #eff6ff;
            border-left: 5px solid #2563eb;
            border-radius: 10px;
            padding: 0.9rem 1rem;
            color: #334155;
        }

        .footer {
            margin-top: 2rem;
            padding-top: 1rem;
            border-top: 1px solid #e2e8f0;
            color: #64748b;
            text-align: center;
            font-size: 0.88rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def crear_excel(resultados: dict) -> bytes:
    salida = BytesIO()
    comparacion = construir_comparacion(resultados)

    with pd.ExcelWriter(salida, engine="openpyxl") as writer:
        comparacion.to_excel(writer, sheet_name="Resumen", index=False)
        resultados["actual"].etapas.to_excel(
            writer, sheet_name="Etapas_actual", index=False
        )
        resultados["mejorado"].etapas.to_excel(
            writer, sheet_name="Etapas_mejorado", index=False
        )
        resultados["actual"].detalle.to_excel(
            writer, sheet_name="Detalle_actual", index=False
        )
        resultados["mejorado"].detalle.to_excel(
            writer, sheet_name="Detalle_mejorado", index=False
        )

        configuracion = pd.concat(
            [
                pd.DataFrame(
                    list(resultados["actual"].configuracion.items()),
                    columns=["Parámetro", "Escenario actual"],
                ).set_index("Parámetro"),
                pd.DataFrame(
                    list(resultados["mejorado"].configuracion.items()),
                    columns=["Parámetro", "Escenario mejorado"],
                ).set_index("Parámetro"),
            ],
            axis=1,
        ).reset_index()
        configuracion.to_excel(writer, sheet_name="Configuración", index=False)

    salida.seek(0)
    return salida.getvalue()


def texto_eventos(resultados: dict) -> str:
    partes = []
    for clave, titulo in (
        ("actual", "ESCENARIO ACTUAL"),
        ("mejorado", "ESCENARIO MEJORADO"),
    ):
        partes.append("=" * 80)
        partes.append(titulo)
        partes.append("=" * 80)
        partes.extend(resultados[clave].eventos)
        partes.append("")
    return "\n".join(partes)


def tarjeta_info(titulo: str, texto: str) -> None:
    st.markdown(
        f"""
        <div class="info-card">
            <h3>{titulo}</h3>
            <p>{texto}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def mostrar_recomendaciones(resultados: dict) -> None:
    actual = resultados["actual"].resumen.iloc[0]
    mejorado = resultados["mejorado"].resumen.iloc[0]
    etapas_actual = resultados["actual"].etapas

    cuello = etapas_actual.sort_values(
        "Espera promedio (min)", ascending=False
    ).iloc[0]

    espera_actual = float(actual["Espera promedio (min)"])
    espera_mejorada = float(mejorado["Espera promedio (min)"])
    reduccion = (
        (espera_actual - espera_mejorada) / espera_actual * 100
        if espera_actual > 0
        else 0
    )

    exito_actual = float(actual["Tasa de éxito (%)"])
    exito_mejorado = float(mejorado["Tasa de éxito (%)"])

    st.markdown("### Interpretación automática")
    st.markdown(
        f"""
        <div class="nota">
        <b>Cuello de botella principal:</b> la etapa de <b>{cuello["Etapa"]}</b>,
        con una espera promedio de <b>{cuello["Espera promedio (min)"]:.2f} minutos</b>
        y una cola máxima de <b>{int(cuello["Cola máxima"])}</b> estudiantes.<br><br>
        <b>Impacto del escenario mejorado:</b> la espera promedio cambia de
        <b>{espera_actual:.2f}</b> a <b>{espera_mejorada:.2f} minutos</b>,
        equivalente a una variación de <b>{reduccion:.2f}%</b>.
        La tasa de éxito pasa de <b>{exito_actual:.2f}%</b> a
        <b>{exito_mejorado:.2f}%</b>.
        </div>
        """,
        unsafe_allow_html=True,
    )

    recomendaciones = [
        f"Priorizar el aumento de capacidad en {cuello['Etapa']}, debido a que concentra la mayor espera.",
        "Mantener monitoreo de la longitud de cola durante los primeros días de matrícula.",
        "Aplicar ampliación temporal de recursos tecnológicos en las horas de mayor concurrencia.",
        "Revisar la cantidad de vacantes por curso para reducir rechazos por falta de cupos.",
    ]

    st.markdown("### Propuestas de mejora")
    for numero, recomendacion in enumerate(recomendaciones, start=1):
        st.write(f"**{numero}.** {recomendacion}")


aplicar_estilos()

st.markdown(
    """
    <div class="hero">
        <div class="badge">Optimización y Simulación de Sistemas · LRPD</div>
        <h1>Simulación del proceso de matrícula en línea</h1>
        <p>
            Modelo académico desarrollado en Python, Streamlit y SimPy. El flujo toma
            como referencia pública el proceso de matrícula en Campus Solutions de
            la UPSJB y lo agrupa en etapas para analizar colas, tiempos, vacantes y
            escenarios de mejora.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.info(
    "Alcance: esta aplicación no está conectada a Campus Solutions ni utiliza "
    "datos internos de la UPSJB. El procedimiento institucional se usa como "
    "referencia académica; los tiempos, capacidades y probabilidades son "
    "parámetros simulados."
)

st.markdown(
    """
    **Flujo de referencia agrupado:** acceso y condiciones académicas → selección
    de cursos y secciones → validación del carrito, restricciones y vacantes →
    inscripción, finalización y consulta de horario.
    """
)

with st.sidebar:
    st.markdown("## ⚙️ Configuración")
    st.caption("Los valores son parámetros de simulación y pueden modificarse.")

    with st.expander("Parámetros generales", expanded=True):
        estudiantes = st.number_input(
            "Cantidad de estudiantes",
            min_value=10,
            max_value=5000,
            value=200,
            step=10,
        )
        media_llegadas = st.number_input(
            "Tiempo medio entre llegadas (min)",
            min_value=0.05,
            max_value=10.0,
            value=0.35,
            step=0.05,
            format="%.2f",
        )
        semilla = st.number_input(
            "Semilla aleatoria",
            min_value=1,
            max_value=999999,
            value=42,
            step=1,
        )

    with st.expander("Escenario actual", expanded=True):
        vacantes_actual = st.number_input(
            "Vacantes actuales",
            min_value=1,
            max_value=5000,
            value=170,
            step=10,
            key="vac_actual",
        )
        prob_actual = st.slider(
            "Probabilidad de cumplir requisitos y pagos",
            min_value=0.50,
            max_value=1.00,
            value=0.96,
            step=0.01,
            key="prob_actual",
        )
        prob_carrito_actual = st.slider(
            "Probabilidad de superar validación del carrito",
            min_value=0.50,
            max_value=1.00,
            value=0.93,
            step=0.01,
            key="prob_carrito_actual",
        )
        cap_val_actual = st.number_input(
            "Capacidad: validación académica", 1, 50, 2, key="cva"
        )
        cap_sel_actual = st.number_input(
            "Capacidad: selección de cursos", 1, 50, 3, key="csa"
        )
        cap_ver_actual = st.number_input(
            "Capacidad: validación del carrito", 1, 50, 2, key="cvera"
        )
        cap_con_actual = st.number_input(
            "Capacidad: inscripción final", 1, 50, 2, key="cca"
        )

        st.markdown("**Tiempos promedio por etapa**")
        t_val_actual = st.number_input(
            "Validación académica (min)", 0.10, 30.0, 1.50, 0.10, key="tva"
        )
        t_sel_actual = st.number_input(
            "Selección de cursos (min)", 0.10, 30.0, 2.50, 0.10, key="tsa"
        )
        t_ver_actual = st.number_input(
            "Validación del carrito (min)", 0.10, 30.0, 1.00, 0.10, key="tvera"
        )
        t_con_actual = st.number_input(
            "Inscripción final (min)", 0.10, 30.0, 0.80, 0.10, key="tca"
        )

    with st.expander("Escenario mejorado", expanded=False):
        vacantes_mejorado = st.number_input(
            "Vacantes mejoradas",
            min_value=1,
            max_value=5000,
            value=190,
            step=10,
            key="vac_mejorado",
        )
        prob_mejorado = st.slider(
            "Probabilidad de cumplir requisitos y pagos",
            min_value=0.50,
            max_value=1.00,
            value=0.98,
            step=0.01,
            key="prob_mejorado",
        )
        prob_carrito_mejorado = st.slider(
            "Probabilidad de superar validación del carrito",
            min_value=0.50,
            max_value=1.00,
            value=0.97,
            step=0.01,
            key="prob_carrito_mejorado",
        )
        cap_val_mejorado = st.number_input(
            "Capacidad: validación académica", 1, 50, 4, key="cvm"
        )
        cap_sel_mejorado = st.number_input(
            "Capacidad: selección de cursos", 1, 50, 5, key="csm"
        )
        cap_ver_mejorado = st.number_input(
            "Capacidad: validación del carrito", 1, 50, 4, key="cverm"
        )
        cap_con_mejorado = st.number_input(
            "Capacidad: inscripción final", 1, 50, 4, key="ccm"
        )

        st.markdown("**Tiempos promedio por etapa**")
        t_val_mejorado = st.number_input(
            "Validación académica (min)", 0.10, 30.0, 1.20, 0.10, key="tvm"
        )
        t_sel_mejorado = st.number_input(
            "Selección de cursos (min)", 0.10, 30.0, 2.00, 0.10, key="tsm"
        )
        t_ver_mejorado = st.number_input(
            "Validación del carrito (min)", 0.10, 30.0, 0.75, 0.05, key="tverm"
        )
        t_con_mejorado = st.number_input(
            "Inscripción final (min)", 0.10, 30.0, 0.60, 0.10, key="tcm"
        )

    ejecutar = st.button(
        "▶ Ejecutar simulación",
        type="primary",
        use_container_width=True,
    )
    st.caption("La simulación se ejecuta localmente y no modifica sistemas reales.")

actual = ConfiguracionEscenario(
    nombre="Escenario actual",
    estudiantes=int(estudiantes),
    media_llegadas=float(media_llegadas),
    cap_validacion=int(cap_val_actual),
    cap_seleccion=int(cap_sel_actual),
    cap_verificacion=int(cap_ver_actual),
    cap_confirmacion=int(cap_con_actual),
    t_validacion=float(t_val_actual),
    t_seleccion=float(t_sel_actual),
    t_verificacion=float(t_ver_actual),
    t_confirmacion=float(t_con_actual),
    vacantes=int(vacantes_actual),
    prob_usuario_valido=float(prob_actual),
    prob_carrito_valido=float(prob_carrito_actual),
    semilla=int(semilla),
)

mejorado = ConfiguracionEscenario(
    nombre="Escenario mejorado",
    estudiantes=int(estudiantes),
    media_llegadas=float(media_llegadas),
    cap_validacion=int(cap_val_mejorado),
    cap_seleccion=int(cap_sel_mejorado),
    cap_verificacion=int(cap_ver_mejorado),
    cap_confirmacion=int(cap_con_mejorado),
    t_validacion=float(t_val_mejorado),
    t_seleccion=float(t_sel_mejorado),
    t_verificacion=float(t_ver_mejorado),
    t_confirmacion=float(t_con_mejorado),
    vacantes=int(vacantes_mejorado),
    prob_usuario_valido=float(prob_mejorado),
    prob_carrito_valido=float(prob_carrito_mejorado),
    semilla=int(semilla),
)

if ejecutar:
    with st.spinner("Ejecutando eventos, colas y atención por etapas..."):
        st.session_state["resultados"] = comparar_escenarios(actual, mejorado)
    st.success("Simulación terminada correctamente.")

if "resultados" not in st.session_state:
    columnas = st.columns(3)
    with columnas[0]:
        tarjeta_info(
            "1. Llegadas",
            "Cada estudiante llega en un momento específico, de acuerdo con una distribución exponencial.",
        )
    with columnas[1]:
        tarjeta_info(
            "2. Colas y recursos",
            "Los estudiantes esperan cuando se satura la validación académica, la selección, el carrito o la inscripción final.",
        )
    with columnas[2]:
        tarjeta_info(
            "3. Resultados",
            "La aplicación calcula tiempos, colas, éxitos, rechazos y compara una alternativa de mejora.",
        )

    st.info(
        "Configura los parámetros en el panel izquierdo y presiona "
        "“Ejecutar simulación” para visualizar los resultados."
    )
else:
    resultados = st.session_state["resultados"]
    comparacion = construir_comparacion(resultados)
    fila_actual = comparacion.iloc[0]
    fila_mejorada = comparacion.iloc[1]

    tab_resumen, tab_etapas, tab_detalle, tab_eventos, tab_reporte, tab_metodo = st.tabs(
        [
            "📊 Resumen",
            "⏱️ Etapas",
            "👥 Detalle",
            "🧾 Eventos",
            "⬇️ Reporte",
            "📘 Metodología",
        ]
    )

    with tab_resumen:
        st.markdown("## Indicadores principales")

        st.markdown("### Escenario actual")
        cols = st.columns(5)
        cols[0].metric("Matrículas exitosas", int(fila_actual["Matrículas exitosas"]))
        cols[1].metric("Solicitudes rechazadas", int(fila_actual["Solicitudes rechazadas"]))
        cols[2].metric("Tasa de éxito", f'{fila_actual["Tasa de éxito (%)"]:.2f}%')
        cols[3].metric(
            "Tiempo promedio",
            f'{fila_actual["Tiempo promedio total (min)"]:.2f} min',
        )
        cols[4].metric("Congestión", str(fila_actual["Congestión"]))

        st.markdown("### Escenario mejorado")
        cols = st.columns(5)
        cols[0].metric(
            "Matrículas exitosas",
            int(fila_mejorada["Matrículas exitosas"]),
            delta=int(
                fila_mejorada["Matrículas exitosas"]
                - fila_actual["Matrículas exitosas"]
            ),
        )
        cols[1].metric(
            "Solicitudes rechazadas",
            int(fila_mejorada["Solicitudes rechazadas"]),
            delta=int(
                fila_mejorada["Solicitudes rechazadas"]
                - fila_actual["Solicitudes rechazadas"]
            ),
            delta_color="inverse",
        )
        cols[2].metric(
            "Tasa de éxito",
            f'{fila_mejorada["Tasa de éxito (%)"]:.2f}%',
            delta=f'{fila_mejorada["Tasa de éxito (%)"] - fila_actual["Tasa de éxito (%)"]:.2f} pp',
        )
        cols[3].metric(
            "Tiempo promedio",
            f'{fila_mejorada["Tiempo promedio total (min)"]:.2f} min',
            delta=f'{fila_mejorada["Tiempo promedio total (min)"] - fila_actual["Tiempo promedio total (min)"]:.2f} min',
            delta_color="inverse",
        )
        cols[4].metric("Congestión", str(fila_mejorada["Congestión"]))

        st.markdown("### Comparación general")
        st.dataframe(comparacion, use_container_width=True, hide_index=True)

        izquierda, derecha = st.columns(2)

        with izquierda:
            figura, eje = plt.subplots(figsize=(7, 4))
            eje.bar(
                comparacion["Escenario"],
                comparacion["Tiempo promedio total (min)"],
            )
            eje.set_title("Tiempo promedio total")
            eje.set_ylabel("Minutos")
            eje.tick_params(axis="x", rotation=8)
            figura.tight_layout()
            st.pyplot(figura)
            plt.close(figura)

        with derecha:
            figura, eje = plt.subplots(figsize=(7, 4))
            eje.bar(
                comparacion["Escenario"],
                comparacion["Matrículas exitosas"],
                label="Exitosas",
            )
            eje.bar(
                comparacion["Escenario"],
                comparacion["Solicitudes rechazadas"],
                bottom=comparacion["Matrículas exitosas"],
                label="Rechazadas",
            )
            eje.set_title("Resultados por escenario")
            eje.set_ylabel("Estudiantes")
            eje.tick_params(axis="x", rotation=8)
            eje.legend()
            figura.tight_layout()
            st.pyplot(figura)
            plt.close(figura)

        mostrar_recomendaciones(resultados)

    with tab_etapas:
        st.markdown("## Análisis por etapa")
        st.caption(
            "Permite identificar la etapa con mayor espera, mayor cola y mayor utilización."
        )

        etapas = pd.concat(
            [resultados["actual"].etapas, resultados["mejorado"].etapas],
            ignore_index=True,
        )
        st.dataframe(etapas, use_container_width=True, hide_index=True)

        metrica = st.selectbox(
            "Variable para comparar",
            [
                "Espera promedio (min)",
                "Cola máxima",
                "Utilización estimada (%)",
                "Servicio promedio (min)",
            ],
        )

        tabla_grafico = etapas.pivot(
            index="Etapa",
            columns="Escenario",
            values=metrica,
        )
        st.bar_chart(tabla_grafico, use_container_width=True)

    with tab_detalle:
        st.markdown("## Detalle por estudiante")
        escenario_detalle = st.radio(
            "Selecciona el escenario",
            ["Escenario actual", "Escenario mejorado"],
            horizontal=True,
        )
        clave = "actual" if escenario_detalle == "Escenario actual" else "mejorado"
        detalle = resultados[clave].detalle

        estado = st.multiselect(
            "Filtrar por estado",
            options=detalle["Estado"].unique().tolist(),
            default=detalle["Estado"].unique().tolist(),
        )
        filtrado = detalle[detalle["Estado"].isin(estado)]
        st.dataframe(filtrado, use_container_width=True, hide_index=True)

        st.download_button(
            "Descargar detalle en CSV",
            data=filtrado.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"detalle_{clave}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with tab_eventos:
        st.markdown("## Registro cronológico de eventos")
        escenario_eventos = st.radio(
            "Escenario",
            ["Actual", "Mejorado"],
            horizontal=True,
            key="radio_eventos",
        )
        clave = "actual" if escenario_eventos == "Actual" else "mejorado"
        limite = st.slider(
            "Cantidad de eventos mostrados",
            min_value=20,
            max_value=min(1000, len(resultados[clave].eventos)),
            value=min(150, len(resultados[clave].eventos)),
            step=10,
        )
        st.code("\n".join(resultados[clave].eventos[:limite]), language="text")

    with tab_reporte:
        st.markdown("## Descarga de resultados")
        st.write(
            "El archivo Excel contiene el resumen, análisis por etapas, detalle "
            "de estudiantes y configuración utilizada."
        )

        excel = crear_excel(resultados)
        eventos_txt = texto_eventos(resultados)

        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "📥 Descargar reporte Excel",
                data=excel,
                file_name="reporte_simulacion_matricula.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True,
            )
        with col2:
            st.download_button(
                "📄 Descargar registro de eventos",
                data=eventos_txt.encode("utf-8"),
                file_name="registro_eventos.txt",
                mime="text/plain",
                use_container_width=True,
            )

        st.markdown("### Evidencias recomendadas para el informe")
        st.write(
            "1. Página inicial y panel de parámetros.\n"
            "2. Indicadores del escenario actual.\n"
            "3. Indicadores del escenario mejorado.\n"
            "4. Gráficos comparativos.\n"
            "5. Tabla de análisis por etapas.\n"
            "6. Registro cronológico de eventos.\n"
            "7. Reporte Excel generado."
        )

    with tab_metodo:
        st.markdown("## Cómo funciona el modelo")
        st.markdown(
            """
            **Entidad:** estudiante que intenta completar su matrícula.

            **Referencia institucional:** el flujo público de Campus Solutions
            se agrupó en cuatro etapas para mantener un modelo medible y
            comprensible.

            **Etapa 1 — Validación académica:** revisión de condiciones,
            requisitos y pagos pendientes.

            **Etapa 2 — Selección:** elección de cursos, secciones, turnos y
            componentes.

            **Etapa 3 — Validación del carrito:** revisión de créditos,
            cruces de horario, restricciones y disponibilidad de vacantes.

            **Etapa 4 — Inscripción final:** inscripción, finalización del
            proceso y disponibilidad del horario.

            **Eventos discretos:** llegada, inicio y fin de cada etapa,
            rechazo, confirmación y salida.

            **Resultados:** tiempo total, espera, cola máxima, utilización,
            matrículas completadas, rechazos y congestión.

            **Comparación:** el escenario mejorado aumenta capacidades,
            reduce tiempos o amplía vacantes para evaluar alternativas antes
            de intervenir un sistema real.
            """
        )

        st.warning(
            "Los resultados no representan métricas oficiales de la UPSJB. Para el "
            "informe final, los valores deben presentarse como supuestos de "
            "simulación o reemplazarse por datos observados y autorizados."
        )

        st.markdown(
            "[Consultar guía pública de matrícula en Campus Solutions de la UPSJB]"
            "(https://sae.upsjb.edu.pe/hc/es-419/articles/"
            "26611830588827-Pasos-para-realizar-una-matr%C3%ADcula-en-Campus-Solutions)"
        )

st.markdown(
    """
    <div class="footer">
        Proyecto académico · Flujo de referencia Campus Solutions UPSJB · Optimización del proceso de matrícula
        mediante simulación de eventos discretos
    </div>
    """,
    unsafe_allow_html=True,
)
