# Simulación del proceso de matrícula en línea

Aplicación académica de simulación de eventos discretos desarrollada con
Python, Streamlit y SimPy.

## Alcance

El modelo toma como referencia pública el procedimiento de matrícula en
Campus Solutions de la Universidad Privada San Juan Bautista. No se conecta
con el sistema real, no procesa datos institucionales y no representa métricas
oficiales. Los tiempos, capacidades y probabilidades son parámetros de
simulación.

## Flujo agrupado

1. Validación académica, requisitos y pagos.
2. Selección de cursos, secciones, turnos y componentes.
3. Validación del carrito, cruces, restricciones y vacantes.
4. Inscripción, finalización y consulta del horario.

## Ejecución local

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Despliegue

Subir `app.py`, `simulacion.py`, `requirements.txt` y `.streamlit/config.toml`
a GitHub y desplegar `app.py` en Streamlit Community Cloud.
