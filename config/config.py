import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    WHAPI_TOKEN = os.getenv('WHAPI_TOKEN')
    WHAPI_API_URL = os.getenv('WHAPI_API_URL')
    BOT_WEBHOOK_URL = os.getenv('BOT_WEBHOOK_URL')

    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB = int(os.getenv('REDIS_DB', 0))

    DEBUG = os.getenv('DEBUG', 'False') == 'True'
    PORT = int(os.getenv('PORT', 5000))
