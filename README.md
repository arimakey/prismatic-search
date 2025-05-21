# Automatización de Revisiones Sistemáticas con PRISMA

Este proyecto tiene como objetivo automatizar el proceso de revisiones sistemáticas utilizando el marco PRISMA, integrando herramientas como ChatGPT para análisis, bibliotecas para scraping y una interfaz de consola mejorada.

## Configuración Inicial

1.  **Clonar el repositorio:**
    ```bash
    git clone <URL_DEL_REPOSITORIO>
    cd prismatic-search
    ```

2.  **Configurar variables de entorno:**
    Crea un archivo `.env` en la raíz del proyecto y añade tus claves API y configuraciones necesarias. Consulta el archivo `.env.example` (si existe) o el contenido del archivo `.env` creado inicialmente.

    ```dotenv
    OPENAI_API_KEY=tu_clave_api_de_openai
    # Otras variables...
    ```

3.  **Instalar dependencias:**
    Asegúrate de tener Python instalado (se recomienda Python 3.8+).

    ```bash
    pip install -r requirements.txt
    ```

## Estructura del Proyecto

-   `src/`: Contiene el código fuente principal del proyecto.
-   `data/`: Directorio para almacenar datos de entrada y salida (ej. resultados de scraping, datos procesados).
-   `requirements.txt`: Lista de dependencias de Python.
-   `.env`: Archivo para variables de entorno (no debe ser versionado).
-   `README.md`: Este archivo.

## Uso

Describe aquí cómo ejecutar el proyecto, los diferentes módulos, etc.

```bash
# Ejemplo de ejecución
python src/main.py
```

## Contribución

Información sobre cómo contribuir al proyecto.

## Licencia

Información sobre la licencia del proyecto.