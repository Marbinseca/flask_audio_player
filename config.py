import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class Config:
    """Configuración de la aplicación Flask"""
    
    # Configuración básica
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_key_12345')
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    # Límites
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16777216))  # 16MB
    
    # Directorios
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    AUDIO_CACHE_DIR = os.environ.get('AUDIO_CACHE_DIR', 'audio_cache')
    ABS_CACHE_DIR = os.path.join(BASE_DIR, AUDIO_CACHE_DIR)
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    
    # Configuración de calidad de audio
    AUDIO_QUALITIES = {
        '128': {'bitrate': '128k', 'format': 'mp3'},
        '192': {'bitrate': '192k', 'format': 'mp3'},
        '320': {'bitrate': '320k', 'format': 'mp3'},
        'flac': {'bitrate': None, 'format': 'flac'}
    }
    DEFAULT_QUALITY = os.environ.get('DEFAULT_QUALITY', '192')
    
    # Plataformas permitidas
    ALLOWED_PLATFORMS = os.environ.get(
        'ALLOWED_PLATFORMS', 
        'youtube,vimeo,facebook,soundcloud'
    ).split(',')
    
    # Configuración yt-dlp
    YTDL_OPTIONS = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': DEFAULT_QUALITY,
        }],
        'outtmpl': os.path.join(ABS_CACHE_DIR, '%(id)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0',
        'nocheckcertificate': True,
        'ignoreerrors': True,
        'logtostderr': False,
        'no_color': True,
    }
    
    # Configuración Redis/Celery (si se usa procesamiento en background)
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
    
    @classmethod
    def init_app(cls, app):
        """Inicializar configuración en la app Flask"""
        # Crear directorios necesarios
        os.makedirs(cls.ABS_CACHE_DIR, exist_ok=True)
        os.makedirs(cls.DATA_DIR, exist_ok=True)
        os.makedirs(os.path.join(cls.BASE_DIR, 'logs'), exist_ok=True)
        
        # Configurar subdirectorios por plataforma
        for platform in cls.ALLOWED_PLATFORMS:
            platform_dir = os.path.join(cls.ABS_CACHE_DIR, platform)
            os.makedirs(platform_dir, exist_ok=True)
        
        # Configurar app
        app.config.from_object(cls)