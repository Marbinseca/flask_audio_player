import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from flask import Flask, render_template, request, jsonify, send_file, Response, url_for
from flask_cors import CORS
from werkzeug.utils import secure_filename

from config import Config
from youtube_dl_helper import AudioExtractor
from playlist_manager import Playlist, Track
from audio_processor import AudioProcessor

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Inicializar Flask app
app = Flask(__name__)
Config.init_app(app)

# Habilitar CORS
CORS(app)

# Inicializar componentes
audio_extractor = AudioExtractor()
playlist = Playlist()
audio_processor = AudioProcessor()

@app.route('/')
def index():
    """Página principal del reproductor"""
    return render_template('index.html')

@app.route('/api/playlist', methods=['GET'])
def get_playlist():
    """Obtener lista de reproducción completa"""
    try:
        tracks = [track.to_dict() for track in playlist.tracks]
        stats = playlist.get_stats()
        
        return jsonify({
            'success': True,
            'tracks': tracks,
            'stats': stats,
            'current_track': playlist.get_current_track().to_dict() if playlist.get_current_track() else None
        })
    except Exception as e:
        logger.error(f"Error obteniendo playlist: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/playlist/add', methods=['POST'])
def add_to_playlist():
    """Agregar URL a la playlist"""
    try:
        data = request.get_json()
        
        if not data or 'url' not in data:
            return jsonify({'success': False, 'error': 'URL requerida'}), 400
        
        url = data['url'].strip()
        position = data.get('position')
        
        # Extraer información del audio
        info = audio_extractor.extract_info(url)
        
        if 'error' in info:
            return jsonify({'success': False, 'error': info['error']}), 400
        
        # Si es playlist, agregar todas las entradas
        if info.get('type') == 'playlist':
            tracks_added = []
            for entry in info.get('entries', []):
                track = playlist.add_track(entry, position)
                if position is not None:
                    position += 1
                tracks_added.append(track.to_dict())
            
            return jsonify({
                'success': True,
                'message': f'Playlist agregada: {len(tracks_added)} pistas',
                'tracks': tracks_added,
                'playlist_info': {
                    'title': info.get('title'),
                    'count': info.get('count')
                }
            })
        
        # Si es un solo track
        track = playlist.add_track(info, position)
        
        return jsonify({
            'success': True,
            'message': 'Pista agregada exitosamente',
            'track': track.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error agregando a playlist: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/playlist/remove/<track_id>', methods=['DELETE'])
def remove_from_playlist(track_id):
    """Remover pista de la playlist"""
    try:
        success = playlist.remove_track(track_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Pista removida exitosamente'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Pista no encontrada'
            }), 404
            
    except Exception as e:
        logger.error(f"Error removiendo de playlist: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/playlist/move', methods=['POST'])
def move_track():
    """Mover pista en la playlist"""
    try:
        data = request.get_json()
        
        if not data or 'track_id' not in data or 'position' not in data:
            return jsonify({'success': False, 'error': 'Datos incompletos'}), 400
        
        success = playlist.move_track(data['track_id'], data['position'])
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Pista movida exitosamente'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Error moviendo pista'
            }), 400
            
    except Exception as e:
        logger.error(f"Error moviendo pista: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/playlist/clear', methods=['DELETE'])
def clear_playlist():
    """Limpiar playlist completa"""
    try:
        playlist.clear()
        return jsonify({
            'success': True,
            'message': 'Playlist limpiada exitosamente'
        })
    except Exception as e:
        logger.error(f"Error limpiando playlist: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/playlist/shuffle', methods=['POST'])
def shuffle_playlist():
    """Mezclar playlist"""
    try:
        playlist.shuffle()
        return jsonify({
            'success': True,
            'message': 'Playlist mezclada exitosamente'
        })
    except Exception as e:
        logger.error(f"Error mezclando playlist: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/playlist/current', methods=['GET', 'POST'])
def current_track():
    """Obtener o establecer track actual"""
    try:
        if request.method == 'GET':
            track = playlist.get_current_track()
            if track:
                return jsonify({
                    'success': True,
                    'track': track.to_dict()
                })
            else:
                return jsonify({
                    'success': True,
                    'track': None,
                    'message': 'No hay track actual'
                })
        
        elif request.method == 'POST':
            data = request.get_json()
            
            if not data or 'track_id' not in data:
                return jsonify({'success': False, 'error': 'track_id requerido'}), 400
            
            success = playlist.set_current_track(data['track_id'])
            
            if success:
                track = playlist.get_current_track()
                return jsonify({
                    'success': True,
                    'message': 'Track actual establecido',
                    'track': track.to_dict()
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Track no encontrado'
                }), 404
                
    except Exception as e:
        logger.error(f"Error con track actual: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/playlist/next', methods=['POST'])
def next_track():
    """Obtener siguiente track"""
    try:
        track = playlist.next_track()
        
        if track:
            return jsonify({
                'success': True,
                'track': track.to_dict(),
                'message': 'Siguiente track'
            })
        else:
            return jsonify({
                'success': True,
                'track': None,
                'message': 'Fin de la playlist'
            })
    except Exception as e:
        logger.error(f"Error obteniendo siguiente track: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/playlist/previous', methods=['POST'])
def previous_track():
    """Obtener track anterior"""
    try:
        track = playlist.previous_track()
        
        if track:
            return jsonify({
                'success': True,
                'track': track.to_dict(),
                'message': 'Track anterior'
            })
        else:
            return jsonify({
                'success': True,
                'track': None,
                'message': 'Inicio de la playlist'
            })
    except Exception as e:
        logger.error(f"Error obteniendo track anterior: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/audio/stream/<track_id>', methods=['GET'])
def stream_audio(track_id):
    """Stream de audio para el reproductor"""
    try:
        track = playlist.get_track(track_id)
        
        if not track:
            return jsonify({'success': False, 'error': 'Track no encontrado'}), 404
        
        # Si no hay archivo descargado, descargarlo
        if not track.filepath or not os.path.exists(track.filepath):
            filepath, metadata = audio_extractor.download_audio(track.url)
            
            if not filepath:
                return jsonify({'success': False, 'error': 'Error descargando audio'}), 500
            
            # Actualizar track con información de descarga
            track.filepath = filepath
            track.metadata = metadata
            playlist.save()
        
        # Verificar que el archivo existe
        if not os.path.exists(track.filepath):
            return jsonify({'success': False, 'error': 'Archivo no encontrado'}), 404
        
        # Stream del archivo
        file_size = os.path.getsize(track.filepath)
        range_header = request.headers.get('Range')
        
        if range_header:
            # Soporte para HTTP Range requests (para streaming)
            start, end = parse_range_header(range_header, file_size)
            
            with open(track.filepath, 'rb') as f:
                f.seek(start)
                data = f.read(end - start + 1)
            
            response = Response(
                data,
                206,  # Partial Content
                mimetype='audio/mpeg',
                direct_passthrough=True
            )
            
            response.headers.add('Content-Range', f'bytes {start}-{end}/{file_size}')
            response.headers.add('Accept-Ranges', 'bytes')
            response.headers.add('Content-Length', str(end - start + 1))
            
        else:
            # Envío completo del archivo
            response = send_file(
                track.filepath,
                mimetype='audio/mpeg',
                as_attachment=False,
                download_name=f"{track.title}.mp3"
            )
        
        # Headers para streaming
        response.headers.add('Cache-Control', 'no-cache')
        response.headers.add('Content-Disposition', 'inline')
        
        return response
        
    except Exception as e:
        logger.error(f"Error en stream de audio: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/audio/download/<track_id>', methods=['GET'])
def download_audio(track_id):
    """Descargar archivo de audio"""
    try:
        track = playlist.get_track(track_id)
        
        if not track:
            return jsonify({'success': False, 'error': 'Track no encontrado'}), 404
        
        # Asegurar que el archivo existe
        if not track.filepath or not os.path.exists(track.filepath):
            filepath, metadata = audio_extractor.download_audio(track.url)
            
            if not filepath:
                return jsonify({'success': False, 'error': 'Error descargando audio'}), 500
            
            track.filepath = filepath
            playlist.save()
        
        return send_file(
            track.filepath,
            as_attachment=True,
            download_name=f"{track.title}.mp3"
        )
        
    except Exception as e:
        logger.error(f"Error descargando audio: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/audio/info', methods=['POST'])
def get_audio_info():
    """Obtener información de audio sin agregar a playlist"""
    try:
        data = request.get_json()
        
        if not data or 'url' not in data:
            return jsonify({'success': False, 'error': 'URL requerida'}), 400
        
        info = audio_extractor.extract_info(data['url'])
        
        if 'error' in info:
            return jsonify({'success': False, 'error': info['error']}), 400
        
        return jsonify({
            'success': True,
            'info': info
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo info de audio: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/settings', methods=['GET', 'POST'])
def settings():
    """Obtener o guardar configuraciones"""
    settings_file = os.path.join(Config.DATA_DIR, 'settings.json')
    
    try:
        if request.method == 'GET':
            if os.path.exists(settings_file):
                try:
                    with open(settings_file, 'r') as f:
                        settings = json.load(f)
                except json.JSONDecodeError:
                    # Si el archivo está corrupto o vacío, usar defaults
                    logger.warning(f"Archivo de configuración corrupto: {settings_file}. Usando defaults.")
                    settings = {
                        'quality': '192',
                        'theme': 'dark',
                        'autoplay': True,
                        'notifications': True,
                        'cache_size': 1000,
                        'default_platform': 'youtube'
                    }
            else:
                settings = {
                    'quality': '192',
                    'theme': 'dark',
                    'autoplay': True,
                    'notifications': True,
                    'cache_size': 1000,
                    'default_platform': 'youtube'
                }
            
            return jsonify({
                'success': True,
                'settings': settings
            })
        
        elif request.method == 'POST':
            data = request.get_json()
            
            if not data:
                return jsonify({'success': False, 'error': 'Datos requeridos'}), 400
            
            # Cargar configuración existente
            current_settings = {}
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    current_settings = json.load(f)
            
            # Actualizar configuración
            current_settings.update(data)
            
            # Guardar configuración
            with open(settings_file, 'w') as f:
                json.dump(current_settings, f, indent=2)
            
            # Actualizar configuración de calidad si es necesario
            if 'quality' in data:
                Config.DEFAULT_QUALITY = data['quality']
            
            return jsonify({
                'success': True,
                'message': 'Configuración guardada',
                'settings': current_settings
            })
            
    except Exception as e:
        logger.error(f"Error en configuración: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/cache/clear', methods=['POST'])
def clear_cache():
    """Limpiar caché de audio"""
    try:
        data = request.get_json() or {}
        platform = data.get('platform')
        days_old = data.get('days_old', 7)
        
        deleted = audio_extractor.clear_cache(platform, days_old)
        
        return jsonify({
            'success': True,
            'message': f'{deleted} archivos eliminados del caché'
        })
        
    except Exception as e:
        logger.error(f"Error limpiando caché: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/cache/info', methods=['GET'])
def cache_info():
    """Obtener información del caché"""
    try:
        cache_info = {
            'total_size': 0,
            'file_count': 0,
            'by_platform': {}
        }
        
        for root, dirs, files in os.walk(Config.ABS_CACHE_DIR):
            for file in files:
                if file.endswith(('.mp3', '.m4a', '.webm', '.opus', '.flac')):
                    filepath = os.path.join(root, file)
                    cache_info['total_size'] += os.path.getsize(filepath)
                    cache_info['file_count'] += 1
                    
                    # Determinar plataforma por directorio
                    rel_path = os.path.relpath(root, Config.ABS_CACHE_DIR)
                    platform = rel_path.split(os.sep)[0] if os.sep in rel_path else 'other'
                    
                    if platform not in cache_info['by_platform']:
                        cache_info['by_platform'][platform] = {
                            'size': 0,
                            'count': 0
                        }
                    
                    cache_info['by_platform'][platform]['size'] += os.path.getsize(filepath)
                    cache_info['by_platform'][platform]['count'] += 1
        
        # Convertir tamaño a MB
        cache_info['total_size_mb'] = cache_info['total_size'] / (1024 * 1024)
        
        return jsonify({
            'success': True,
            'cache_info': cache_info
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo info de caché: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Endpoint de verificación de salud"""
    components = {
        'flask': True,
        'playlist': len(playlist.tracks),
        'cache_dir': os.path.exists(Config.ABS_CACHE_DIR),
        'data_dir': os.path.exists(Config.DATA_DIR),
        'ffmpeg': audio_processor.is_ffmpeg_available()
    }
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'components': components
    })

def parse_range_header(range_header: str, file_size: int):
    """Parsear header Range HTTP"""
    try:
        range_type, range_spec = range_header.split('=')
        if range_type.strip() != 'bytes':
            raise ValueError
        
        start_str, end_str = range_spec.split('-')
        start = int(start_str) if start_str else 0
        end = int(end_str) if end_str else file_size - 1
        
        # Validar rangos
        if start < 0 or end >= file_size or start > end:
            raise ValueError
        
        return start, end
        
    except:
        # Si hay error, devolver archivo completo
        return 0, file_size - 1

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Recurso no encontrado'}), 404

@app.errorhandler(500)
def internal_error(error):
    import traceback
    logger.error(f"Error interno: {error}\n{traceback.format_exc()}")
    return jsonify({'success': False, 'error': 'Error interno del servidor'}), 500

@app.errorhandler(413)
def too_large(error):
    return jsonify({'success': False, 'error': 'Archivo muy grande'}), 413

if __name__ == '__main__':
    # Crear directorios necesarios
    os.makedirs('logs', exist_ok=True)
    os.makedirs(Config.DATA_DIR, exist_ok=True)
    
    # Iniciar servidor Flask
    logger.info("Iniciando Audio Flask Player...")
    logger.info(f"Cache directory: {Config.ABS_CACHE_DIR}")
    logger.info(f"FFmpeg disponible: {audio_processor.is_ffmpeg_available()}")
    
    app.run(
        host='0.0.0.0',
        port=8080,
        debug=Config.DEBUG,
        threaded=True
    )