import os
from dotenv import load_dotenv
from telethon import TelegramClient

# Cargar variables de entorno
load_dotenv()

# Obtener el token del bot y las credenciales de API
BOT_TOKEN = os.getenv('BOT_TOKEN')
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')

# Validar que las variables de entorno están definidas
if BOT_TOKEN is None:
    raise ValueError("No se ha encontrado el token del bot. Verifica que BOT_TOKEN esté definido en el archivo .env")
if API_ID is None:
    raise ValueError("No se ha encontrado el API ID. Verifica que API_ID esté definido en el archivo .env")
if API_HASH is None:
    raise ValueError("No se ha encontrado el API HASH. Verifica que API_HASH esté definido en el archivo .env")

# Inicialización del cliente de Telethon
client = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

