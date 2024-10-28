import os
import pytz
import json
import random
import config
import asyncio
import logging
from telebot import TeleBot
from datetime import datetime
from html2image import Html2Image
from telethon import TelegramClient, events
from jinja2 import Environment, FileSystemLoader


def obtener_emoji_por_disciplina(disciplina):
    emojis = {
        "física": "🔬",
        "programación": "💻",
        "matemáticas": "📐",
        "química": "⚗️",
        "biología": "🧬"
    }
    return emojis.get(disciplina, "📘")  # Emoji por defecto si no hay coincidencia

def obtener_frase_aleatoria():
    with open('frases.json', 'r', encoding='utf-8') as file:
        frases = json.load(file)
    frase_aleatoria = random.choice(frases)
    # Obtener el emoji según la disciplina
    emoji = obtener_emoji_por_disciplina(frase_aleatoria['disciplina'])
    # Retornar la frase sin comillas
    return f"{emoji} {frase_aleatoria['frase']} \n— {frase_aleatoria['autor']}"

# Define la zona horaria de Argentina
zona_argentina = pytz.timezone('America/Argentina/Buenos_Aires')
fecha_hora_argentina = datetime.now(zona_argentina)
fecha_argentina = fecha_hora_argentina.strftime('%Y-%m-%d')
hora_argentina = fecha_hora_argentina.strftime('%H:%M:%S')

# Configuración de logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

bot = TeleBot(config.BOT_TOKEN)
client = TelegramClient('NewBotSession', config.API_ID, config.API_HASH).start(bot_token=config.BOT_TOKEN)

env = Environment(loader=FileSystemLoader('.'))
hti = Html2Image()

# Bloqueo para asegurar que el archivo no esté en uso por múltiples procesos
async def bloquear_y_esperar(file_path):
    while os.path.exists(file_path) and os.path.isfile(file_path):
        try:
            os.rename(file_path, file_path)  # Intenta renombrar el archivo a sí mismo
            break  # Si el renombrado tiene éxito, el archivo está listo
        except OSError:
            await asyncio.sleep(0.1)  # Espera activa si el archivo aún está en uso
async def obtener_datos_usuario(event):
    try:
        user = await client.get_entity(event.user_id)
        user_photo_path = await client.download_profile_photo(user, file="static/images/user_photo.jpg") if user.photo else "static/images/Desconocido.jpg"
        
        # Esperar hasta que la imagen esté disponible y no esté en uso
        await bloquear_y_esperar(user_photo_path)
        
        # Obtener nombre del grupo
        group_chat = await event.get_chat()
        

        # Formatear datos del usuario
        user_data = {
            "id": user.id,
            "first_name": user.first_name or "N/A",
            "last_name": user.last_name or "N/A",
            "username": user.username or "N/A",
            "bio": getattr(user, 'about', "N/A"),
            "restricted": user.restricted,
            "verified": user.verified,
            "premium": user.premium,
            "user_photo": os.path.abspath(user_photo_path),  # Ruta absoluta
            "hora_GTM": hora_argentina,
            "Fecha_GTM": fecha_argentina,
            "nombre_del_grupo": group_chat.title  # Aquí agregamos el nombre del grupo

        }
        return user_data
    except Exception as e:
        logging.error(f"Error al obtener datos del usuario: {e}")
        return None

async def crear_html_bienvenida(user_data):
    temp_image_path = 'temp_bienvenida_foto.png'
    final_image_path = 'bienvenida_foto.png'

    try:
        # Eliminar el archivo temporal si existe
        if os.path.exists(temp_image_path):
            os.remove(temp_image_path)

        # Renderizar el HTML con Jinja2
        template_foto = env.get_template('Bienvenida_foto.html')
        html_renderizado_foto = template_foto.render(user_data)

        # Crear la captura de pantalla
        hti.screenshot(html_str=html_renderizado_foto, save_as=temp_image_path)

        # Esperar a que el archivo esté completamente generado
        await bloquear_y_esperar(temp_image_path)

        # Renombrar el archivo temporal al archivo final
        if os.path.exists(final_image_path):
            os.remove(final_image_path)
        os.rename(temp_image_path, final_image_path)
        
        # Obtener una frase aleatoria
        frase = obtener_frase_aleatoria()
        
        # Agregar la frase al contexto de bienvenida
        user_data["frase"] = frase

        # Renderizar el HTML para el mensaje de bienvenida
        template_texto = env.get_template('Bienvenida_texto.html')
        html_renderizado_texto = template_texto.render(user_data)
        
        # Limpiar el HTML y retornar el texto junto a la ruta de la imagen
        return html_renderizado_texto.replace("<!DOCTYPE html>", "").replace("<html>", "").replace("</html>", "").replace("<head>", "").replace("</head>", "").replace("<body>", "").replace("</body>", "").strip(), final_image_path
    except Exception as e:
        logging.error(f"Error al crear HTML de bienvenida: {e}")
        return "Error al crear el mensaje de bienvenida.", None


@client.on(events.ChatAction)
async def handler(event):
    if event.user_joined or event.user_added:
        user_id = event.user_id
        user_data = await obtener_datos_usuario(event)
        
        if user_data:
            texto_bienvenida, temp_image_path = await crear_html_bienvenida(user_data)

            if temp_image_path and os.path.exists(temp_image_path):
                await bloquear_y_esperar(temp_image_path)
                try:
                    await client.send_file(event.chat_id, temp_image_path, caption=texto_bienvenida, parse_mode='html')
                    logging.info(f"Bienvenida enviada al usuario {user_id}.")
                    logging.info(f"Fecha: {fecha_argentina}")
                    logging.info(f"Hora: {hora_argentina}")
                except Exception as e:
                    logging.error(f"Error al enviar la imagen de bienvenida: {e}")
                    if os.path.exists(temp_image_path):
                        os.remove(temp_image_path)

client.start()
client.run_until_disconnected()