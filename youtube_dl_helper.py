import os
import json
import hashlib
import logging
from typing import Dict, Any, Optional, Tuple
import yt_dlp
from urllib.parse import urlparse, parse_qs
from datetime import datetime
import requests

from config import Config

logger = logging.getLogger(__name__)

class AudioExtractor:
    """Clase para extraer audio de diferentes plataformas"""
    
    def __init__(self):
        self.ydl_opts = Config.YTDL_OPTIONS.copy()
        self.cache_dir = Config.ABS_CACHE_DIR
        self.metadata_cache = {}
        
    def extract_info(self, url: str) -> Dict[str, Any]:
        """
        Extraer información del video/audio sin descargar
        """
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # yt-dlp devuelve None si falla y ignoreerrors=True
                if info is None:
                    return {
                        'error': 'No se pudo obtener información del video (posiblemente no disponible o restringido)',
                        'status': 'error',
                        'url': url
                    }

                if 'entries' in info:
                    # Es una playlist
                    return self._process_playlist(info)
                else:
                    # Es un solo video
                    return self._process_single(info, url)
                    
        except Exception as e:
            logger.error(f"Error extrayendo info de {url}: {e}")
            return {
                'error': str(e),
                'status': 'error',
                'url': url
            }
    
    def _process_single(self, info: Dict, url: str) -> Dict[str, Any]:
        """Procesar un solo video"""
        platform = self._detect_platform(url)
        
        return {
            'id': info.get('id'),
            'url': url,
            'title': info.get('title', 'Sin título'),
            'artist': info.get('artist') or info.get('uploader', 'Desconocido'),
            'duration': info.get('duration', 0),
            'thumbnail': info.get('thumbnail'),
            'platform': platform,
            'webpage_url': info.get('webpage_url'),
            'formats': self._extract_audio_formats(info),
            'status': 'available',
            'extracted_at': datetime.now().isoformat()
        }
    
    def _process_playlist(self, info: Dict) -> Dict[str, Any]:
        """Procesar una playlist"""
        entries = info.get('entries', [])
        playlist_info = []
        
        for entry in entries:
            if entry:
                track_info = self._process_single(entry, entry.get('webpage_url', ''))
                playlist_info.append(track_info)
        
        return {
            'type': 'playlist',
            'title': info.get('title', 'Playlist'),
            'entries': playlist_info,
            'count': len(playlist_info),
            'status': 'available'
        }
    
    def download_audio(self, url: str, quality: str = None) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        Descargar audio de la URL
        
        Returns:
            Tuple (filepath, metadata)
        """
        if quality and quality != Config.DEFAULT_QUALITY:
            opts = self.ydl_opts.copy()
            opts['postprocessors'][0]['preferredquality'] = quality
        else:
            opts = self.ydl_opts
        
        try:
            # Generar nombre de archivo único
            url_hash = hashlib.md5(url.encode()).hexdigest()
            platform = self._detect_platform(url)
            filename = f"{platform}_{url_hash}.mp3"
            filepath = os.path.join(self.cache_dir, platform, filename)
            
            # Verificar si ya existe en caché
            if os.path.exists(filepath):
                metadata = self._load_metadata(filepath)
                if metadata:
                    return filepath, metadata
            
            # Modificar opciones para usar ruta específica
            opts['outtmpl'] = os.path.splitext(filepath)[0]
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                # Buscar el archivo descargado
                downloaded_file = filepath
                if not os.path.exists(downloaded_file):
                    # yt-dlp puede usar extensión diferente
                    for ext in ['.mp3', '.m4a', '.webm', '.opus']:
                        alt_file = downloaded_file.replace('.mp3', ext)
                        if os.path.exists(alt_file):
                            downloaded_file = alt_file
                            break
                
                # Crear metadatos
                metadata = self._create_metadata(info, url, downloaded_file)
                
                # Guardar metadatos
                self._save_metadata(downloaded_file, metadata)
                
                return downloaded_file, metadata
                
        except Exception as e:
            logger.error(f"Error descargando audio de {url}: {e}")
            return None, {'error': str(e), 'status': 'error'}
    
    def _detect_platform(self, url: str) -> str:
        """Detectar la plataforma de la URL"""
        parsed = urlparse(url)
        hostname = parsed.hostname.lower() if parsed.hostname else ''
        
        if 'youtube.com' in hostname or 'youtu.be' in hostname:
            return 'youtube'
        elif 'vimeo.com' in hostname:
            return 'vimeo'
        elif 'facebook.com' in hostname or 'fb.watch' in hostname:
            return 'facebook'
        elif 'soundcloud.com' in hostname:
            return 'soundcloud'
        elif 'spotify.com' in hostname:
            return 'spotify'
        elif 'twitch.tv' in hostname:
            return 'twitch'
        else:
            return 'other'
    
    def _extract_audio_formats(self, info: Dict) -> list:
        """Extraer información de formatos de audio disponibles"""
        formats = []
        
        if 'formats' in info:
            for fmt in info['formats']:
                if fmt.get('acodec') != 'none' and fmt.get('vcodec') == 'none':
                    formats.append({
                        'format_id': fmt.get('format_id'),
                        'ext': fmt.get('ext'),
                        'abr': fmt.get('abr', 0),  # audio bitrate
                        'asr': fmt.get('asr', 0),  # audio sample rate
                        'filesize': fmt.get('filesize'),
                        'format_note': fmt.get('format_note', '')
                    })
        
        # Ordenar por calidad (bitrate)
        formats.sort(key=lambda x: x.get('abr', 0), reverse=True)
        return formats
    
    def _create_metadata(self, info: Dict, url: str, filepath: str) -> Dict[str, Any]:
        """Crear metadatos para el archivo de audio"""
        platform = self._detect_platform(url)
        
        metadata = {
            'id': info.get('id'),
            'title': info.get('title', 'Sin título'),
            'artist': info.get('artist') or info.get('uploader', 'Desconocido'),
            'album': info.get('album', ''),
            'duration': info.get('duration', 0),
            'thumbnail': info.get('thumbnail'),
            'platform': platform,
            'url': url,
            'webpage_url': info.get('webpage_url', url),
            'filepath': filepath,
            'filename': os.path.basename(filepath),
            'filesize': os.path.getsize(filepath) if os.path.exists(filepath) else 0,
            'download_date': datetime.now().isoformat(),
            'bitrate': self._extract_bitrate(info),
            'status': 'downloaded'
        }
        
        return metadata
    
    def _extract_bitrate(self, info: Dict) -> int:
        """Extraer bitrate de la información"""
        if 'formats' in info:
            for fmt in info['formats']:
                if fmt.get('abr'):
                    return fmt['abr']
        return 192  # Valor por defecto
    
    def _save_metadata(self, filepath: str, metadata: Dict[str, Any]):
        """Guardar metadatos en archivo JSON"""
        metadata_file = filepath + '.meta.json'
        try:
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error guardando metadatos: {e}")
    
    def _load_metadata(self, filepath: str) -> Optional[Dict[str, Any]]:
        """Cargar metadatos desde archivo"""
        metadata_file = filepath + '.meta.json'
        if os.path.exists(metadata_file):
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return None
    
    def clear_cache(self, platform: str = None, days_old: int = 7):
        """Limpiar caché de archivos antiguos"""
        from datetime import datetime, timedelta
        import time
        
        cutoff_time = datetime.now() - timedelta(days=days_old)
        
        if platform:
            cache_dirs = [os.path.join(self.cache_dir, platform)]
        else:
            cache_dirs = [os.path.join(self.cache_dir, p) for p in Config.ALLOWED_PLATFORMS]
            cache_dirs.append(self.cache_dir)
        
        deleted_files = 0
        for cache_dir in cache_dirs:
            if os.path.exists(cache_dir):
                for filename in os.listdir(cache_dir):
                    filepath = os.path.join(cache_dir, filename)
                    try:
                        # Verificar antigüedad
                        mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                        if mtime < cutoff_time:
                            os.remove(filepath)
                            deleted_files += 1
                    except:
                        continue
        
        return deleted_files