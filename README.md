# Herramientas de Traducción de Textos de Juego

Este proyecto contiene dos scripts de Python para ayudar en la traducción de archivos de texto de un juego.

- `extractor.py`: Extrae el texto en inglés de los archivos `.txt` y lo prepara para la traducción en un archivo CSV.
- `injector.py`: Toma el texto traducido del archivo CSV y lo reinserta en copias nuevas de los archivos originales.

## Flujo de Trabajo

Siga estos pasos para traducir sus archivos:

### Paso 1: Preparar sus archivos

1.  **Coloque sus archivos de texto originales (en inglés) en la carpeta `ingles`.**
    -   Asegúrese de que todos sus archivos a traducir estén dentro de esta carpeta y terminen con la extensión `.txt`.

### Paso 2: Extraer el texto a traducir

1.  **Ejecute el script de extracción.** Abra una terminal o línea de comandos y ejecute el siguiente comando:
    ```bash
    python3 extractor.py
    ```
2.  **Revise los archivos generados.** El script creará dos archivos importantes en la carpeta `textos`:
    -   `text_to_translate.csv`: Este es el archivo que necesita traducir. Contiene dos columnas: `ID` y `Text`.
    -   `metadata.json`: Este archivo contiene información estructural que el script de inyección necesita. **No modifique este archivo.**

### Paso 3: Traducir el texto

1.  **Abra `textos/text_to_translate.csv`** con un editor de hojas de cálculo (como Microsoft Excel, Google Sheets, o LibreOffice Calc).
2.  **Traduzca el texto de la segunda columna (`Text`)** al español.
3.  **Guarde el archivo CSV** después de terminar la traducción. Asegúrese de guardarlo en el mismo formato (CSV con codificación UTF-8).

### Paso 4: Inyectar el texto traducido

1.  **Ejecute el script de inyección.** Una vez que haya guardado sus traducciones en el archivo CSV, ejecute el siguiente comando en su terminal:
    ```bash
    python3 injector.py
    ```
2.  **Encuentre sus archivos traducidos.** El script creará copias de sus archivos de texto originales, ahora con el texto en español, dentro de la carpeta `espanol`. Los archivos originales en la carpeta `ingles` no serán modificados.

## Resumen de Carpetas

- `ingles/`: Ponga aquí sus archivos `.txt` originales.
- `textos/`: Contiene el `.csv` para traducir y la metadata.
- `espanol/`: Contendrá los archivos `.txt` finales con la traducción inyectada.
- `extractor.py`: El primer script que debe ejecutar.
- `injector.py`: El segundo script que debe ejecutar.
