import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

class Config:
    """Базовые конфигурации"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///bot.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
class Settings:
    """Настройки для боте и API"""
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    
    # AI провайдеры
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
    
    # Tinkoff Payment
    TINKOFF_TERMINAL_KEY = os.getenv('TINKOFF_TERMINAL_KEY', '')
    TINKOFF_SECRET_KEY = os.getenv('TINKOFF_SECRET_KEY', '')
    TINKOFF_TEST_MODE = os.getenv('TINKOFF_TEST_MODE', 'true').lower() == 'true'
    TINKOFF_API_URL = 'https://api.tinkoff.ru/v2' if not TINKOFF_TEST_MODE else 'https://rest-api-test.tinkoff.ru/v2'
    
    # Сервисы видео/изображений
    REPLICATE_API_TOKEN = os.getenv('REPLICATE_API_TOKEN', '')
    FAL_KEY = os.getenv('FAL_KEY', '')
    STABILITY_API_KEY = os.getenv('STABILITY_API_KEY', '')
    
    # Flask
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'true').lower() == 'true'
    
    # Лимиты
    FREE_TEXT_WEEKLY_LIMIT = 30
    FREE_IMAGE_DAILY_LIMIT = 5
    FREE_VIDEO_DAILY_LIMIT = 1
    
    PREMIUM_TEXT_WEEKLY_LIMIT = 9999
    PREMIUM_IMAGE_DAILY_LIMIT = 9999
    PREMIUM_VIDEO_DAILY_LIMIT = 9999
    
    # Цена подписки
    SUBSCRIPTION_PRICE_RUB = 100
    SUBSCRIPTION_DAYS = 30
    
settings = Settings()
