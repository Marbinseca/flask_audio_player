import os
import logging
import tempfile
import subprocess
from typing import Optional, Tuple, Dict, Any
from pathlib import Path

from config import Config

logger = logging.getLogger(__name__)

class AudioProcessor:
    """Clase para procesamiento de archivos de audio"""
    
    def __init__(self):
        self.supported_formats = ['mp3', 'm4a', 'wav', 'flac', 'ogg', 'opus']
        self.ffmpeg_path = self._find_ffmpeg()
    
    def _find_ffmpeg(self) -> Optional[str]:
        """Buscar ruta de FFmpeg"""
        # Verificar en PATH
        import shutil
        ffmpeg_path = shutil.which('ffmpeg')
        if ffmpeg_path:
            return ffmpeg_path
        
        # Verificar rutas comunes
        common_paths = [
            '/usr/bin/ffmpeg',
            '/usr/local/bin/ffmpeg',
            '/opt/homebrew/bin/ffmpeg',
            'C:\\ffmpeg\\bin\\ffmpeg.exe'
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                return path
        
        logger.warning("FFmpeg no encontrado. Algunas funcionalidades estarán limitadas.")
        return None
    
    def convert_audio(
        self, 
        input_file: str, 
        output_format: str = 'mp3',
        bitrate: str = '192k',
        sample_rate: int = 44100,
        channels: int = 2
    ) -> Optional[str]:
        """
        Convertir archivo de audio a formato específico
        
        Args:
            input_file: Ruta del archivo de entrada
            output_format: Formato de salida (mp3, wav, flac, etc.)
            bitrate: Bitrate de salida (para formatos con pérdida)
            sample_rate: Tasa de muestreo
            channels: Número de canales (1=mono, 2=estéreo)
        
        Returns:
            Ruta del archivo convertido o None si hay error
        """
        if not self.ffmpeg_path:
            logger.error("FFmpeg no está disponible")
            return None
        
        if not os.path.exists(input_file):
            logger.error(f"Archivo de entrada no existe: {input_file}")
            return None
        
        # Crear archivo temporal para salida
        output_ext = output_format.lower()
        with tempfile.NamedTemporaryFile(
            suffix=f'.{output_ext}', 
            delete=False,
            dir=Config.ABS_CACHE_DIR
        ) as tmp_file:
            output_file = tmp_file.name
        
        try:
            # Construir comando FFmpeg
            cmd = [
                self.ffmpeg_path,
                '-i', input_file,
                '-vn',  # No video
                '-ar', str(sample_rate),
                '-ac', str(channels),
                '-y'  # Sobrescribir sin preguntar
            ]
            
            # Añadir parámetros según formato
            if output_ext in ['mp3', 'aac', 'opus']:
                cmd.extend(['-b:a', bitrate])
            elif output_ext == 'flac':
                cmd.append('-compression_level', '5')
            
            cmd.append(output_file)
            
            # Ejecutar conversión
            logger.info(f"Ejecutando: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutos timeout
            )
            
            if result.returncode != 0:
                logger.error(f"Error en conversión: {result.stderr}")
                os.unlink(output_file)
                return None
            
            # Verificar que el archivo existe y tiene tamaño
            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                logger.info(f"Conversión exitosa: {output_file}")
                return output_file
            else:
                logger.error("Archivo de salida vacío o no creado")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error("Timeout en conversión de audio")
            if os.path.exists(output_file):
                os.unlink(output_file)
            return None
        except Exception as e:
            logger.error(f"Error en procesamiento de audio: {e}")
            if os.path.exists(output_file):
                os.unlink(output_file)
            return None
    
    def extract_audio_from_video(self, video_file: str, **kwargs) -> Optional[str]:
        """Extraer audio de archivo de video"""
        return self.convert_audio(video_file, **kwargs)
    
    def normalize_audio(self, input_file: str, target_lufs: float = -14.0) -> Optional[str]:
        """
        Normalizar audio usando Loudness Units Full Scale (LUFS)
        
        Args:
            input_file: Ruta del archivo de entrada
            target_lufs: Nivel LUFS objetivo (ej: -14.0 para streaming)
        
        Returns:
            Ruta del archivo normalizado
        """
        if not self.ffmpeg_path:
            logger.error("FFmpeg no está disponible")
            return None
        
        # Crear archivo temporal para salida
        input_ext = Path(input_file).suffix
        with tempfile.NamedTemporaryFile(
            suffix=f'_normalized{input_ext}', 
            delete=False,
            dir=Config.ABS_CACHE_DIR
        ) as tmp_file:
            output_file = tmp_file.name
        
        try:
            # Normalizar usando ebur128 filter de FFmpeg
            cmd = [
                self.ffmpeg_path,
                '-i', input_file,
                '-filter_complex', f'loudnorm=I={target_lufs}:TP=-1.5:LRA=11:print_format=json',
                '-f', 'null', '-'
            ]
            
            # Primero medir el loudness actual
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                logger.error(f"Error midiendo loudness: {result.stderr}")
                return None
            
            # Extraer mediciones del output (simplificado)
            # En implementación real, parsear JSON del output
            
            # Aplicar normalización
            cmd = [
                self.ffmpeg_path,
                '-i', input_file,
                '-af', f'loudnorm=I={target_lufs}:TP=-1.5:LRA=11',
                '-y',
                output_file
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                logger.error(f"Error normalizando audio: {result.stderr}")
                os.unlink(output_file)
                return None
            
            return output_file
            
        except Exception as e:
            logger.error(f"Error en normalización: {e}")
            if os.path.exists(output_file):
                os.unlink(output_file)
            return None
    
    def get_audio_info(self, filepath: str) -> Optional[Dict[str, Any]]:
        """
        Obtener información técnica del archivo de audio
        
        Args:
            filepath: Ruta del archivo
        
        Returns:
            Diccionario con información del audio
        """
        if not self.ffmpeg_path:
            return None
        
        try:
            cmd = [
                self.ffmpeg_path,
                '-i', filepath,
                '-hide_banner',
                '-f', 'null', '-'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            # Parsear output de FFmpeg para extraer información
            import re
            
            info = {
                'filepath': filepath,
                'filesize': os.path.getsize(filepath),
                'duration': 0,
                'bitrate': 0,
                'sample_rate': 0,
                'channels': 0,
                'format': Path(filepath).suffix[1:].lower()
            }
            
            # Buscar duración
            duration_match = re.search(r'Duration:\s*(\d{2}):(\d{2}):(\d{2}\.\d+)', result.stderr)
            if duration_match:
                hours, minutes, seconds = duration_match.groups()
                info['duration'] = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
            
            # Buscar información de audio stream
            audio_match = re.search(r'Stream.*Audio:.*?(\d+)\s*Hz.*?(\d+)\s*ch', result.stderr)
            if audio_match:
                info['sample_rate'] = int(audio_match.group(1))
                info['channels'] = int(audio_match.group(2))
            
            # Buscar bitrate
            bitrate_match = re.search(r'bitrate:\s*(\d+)\s*kb/s', result.stderr)
            if bitrate_match:
                info['bitrate'] = int(bitrate_match.group(1))
            
            return info
            
        except Exception as e:
            logger.error(f"Error obteniendo info de audio: {e}")
            return None
    
    def trim_audio(self, input_file: str, start_time: float, end_time: float) -> Optional[str]:
        """
        Recortar segmento de audio
        
        Args:
            input_file: Ruta del archivo de entrada
            start_time: Tiempo de inicio en segundos
            end_time: Tiempo de fin en segundos
        
        Returns:
            Ruta del archivo recortado
        """
        if not self.ffmpeg_path:
            return None
        
        duration = end_time - start_time
        
        # Crear archivo temporal para salida
        input_ext = Path(input_file).suffix
        with tempfile.NamedTemporaryFile(
            suffix=f'_trimmed{input_ext}', 
            delete=False,
            dir=Config.ABS_CACHE_DIR
        ) as tmp_file:
            output_file = tmp_file.name
        
        try:
            cmd = [
                self.ffmpeg_path,
                '-i', input_file,
                '-ss', str(start_time),
                '-t', str(duration),
                '-y',
                output_file
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                logger.error(f"Error recortando audio: {result.stderr}")
                os.unlink(output_file)
                return None
            
            return output_file
            
        except Exception as e:
            logger.error(f"Error en trim de audio: {e}")
            if os.path.exists(output_file):
                os.unlink(output_file)
            return None
    
    def merge_audio_files(self, file_list: list, output_format: str = 'mp3') -> Optional[str]:
        """
        Combinar múltiples archivos de audio en uno
        
        Args:
            file_list: Lista de rutas de archivos
            output_format: Formato de salida
        
        Returns:
            Ruta del archivo combinado
        """
        if not self.ffmpeg_path or len(file_list) < 2:
            return None
        
        # Crear lista de archivos temporal
        import tempfile
        list_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
        for filepath in file_list:
            list_file.write(f"file '{os.path.abspath(filepath)}'\n")
        list_file.close()
        
        # Crear archivo de salida
        with tempfile.NamedTemporaryFile(
            suffix=f'.{output_format}', 
            delete=False,
            dir=Config.ABS_CACHE_DIR
        ) as tmp_file:
            output_file = tmp_file.name
        
        try:
            cmd = [
                self.ffmpeg_path,
                '-f', 'concat',
                '-safe', '0',
                '-i', list_file.name,
                '-c', 'copy',
                '-y',
                output_file
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutos timeout
            )
            
            # Limpiar archivo de lista
            os.unlink(list_file.name)
            
            if result.returncode != 0:
                logger.error(f"Error combinando audio: {result.stderr}")
                if os.path.exists(output_file):
                    os.unlink(output_file)
                return None
            
            return output_file
            
        except Exception as e:
            logger.error(f"Error combinando archivos: {e}")
            if os.path.exists(list_file.name):
                os.unlink(list_file.name)
            if os.path.exists(output_file):
                os.unlink(output_file)
            return None
    
    def is_ffmpeg_available(self) -> bool:
        """Verificar si FFmpeg está disponible"""
        return self.ffmpeg_path is not None