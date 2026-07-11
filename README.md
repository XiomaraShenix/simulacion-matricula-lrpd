# LRPD - Simulación del proceso de matrícula en línea

Aplicación visual desarrollada con Python, Streamlit y SimPy.

## Archivos

- `app.py`: página principal en Streamlit.
- `simulacion.py`: modelo de eventos discretos.
- `requirements.txt`: librerías necesarias.
- `.streamlit/config.toml`: configuración visual.

## Instalación en VS Code

Abre la terminal dentro de la carpeta del proyecto y ejecuta:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -r requirements.txt
```

## Ejecutar la página

```powershell
python -m streamlit run app.py
```

Streamlit abrirá la aplicación en el navegador. Si no se abre automáticamente,
copia en el navegador la dirección que aparece en la terminal, normalmente:

```text
http://localhost:8501
```

## Uso

1. Configura la cantidad de estudiantes, llegadas, capacidades, tiempos y vacantes.
2. Presiona **Ejecutar simulación**.
3. Revisa el resumen, etapas, detalle y eventos.
4. Descarga el reporte Excel y el registro de eventos.

## Compartir el proyecto en otra computadora Windows

1. Comprime o copia toda esta carpeta, excepto `.venv`.
2. En la otra computadora, descomprime el archivo.
3. Instala Python 3.10 o superior.
4. Ejecuta `INSTALAR_PROYECTO.bat` una sola vez.
5. Después abre `EJECUTAR_PAGINA.bat`.

La carpeta `.venv` no debe copiarse entre computadoras porque contiene rutas y archivos propios del equipo donde se creó.

## Uso sin instalar en otras computadoras

Para abrir el sistema mediante un enlace desde cualquier computadora, despliega el proyecto en Streamlit Community Cloud usando un repositorio de GitHub.

