# WhastApp-web-examen-practico-final-Inteligencia-Artificial-
Instrucciones de uso del proyecto whatsapp_web

1. Requisitos:
   - Python 3.8 o superior.
   - (Opcional) crear un entorno virtual.

2. Instalar dependencias:
   pip install -r requirements.txt

3. Ejecutar el servidor (desde la carpeta whatsapp_web):
   python app.py

4. Abrir en el navegador:
   http://127.0.0.1:5000/

5. Subir el archivo ejemplo_chat.txt o tu propio chat exportado desde WhatsApp (.txt).

Notas:
- El proyecto genera una carpeta output con la imagen del gráfico y csv.
- Si el parser no reconoce el formato, revisa las primeras líneas del chat y adapta PATTERNS en parse_utils.py.
