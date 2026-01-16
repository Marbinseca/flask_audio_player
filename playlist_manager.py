import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib
from dataclasses import dataclass, asdict
from enum import Enum

from config import Config

logger = logging.getLogger(__name__)

class PlaybackMode(Enum):
    NORMAL = "normal"
    REPEAT_ONE = "repeat_one"
    REPEAT_ALL = "repeat_all"
    SHUFFLE = "shuffle"

@dataclass
class Track:
    """Clase para representar una pista de audio"""
    id: str
    url: str
    title: str
    artist: str
    duration: int
    platform: str
    thumbnail: Optional[str] = None
    filepath: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    added_at: Optional[str] = None
    order: Optional[int] = None
    played: bool = False
    play_count: int = 0
    
    def to_dict(self):
        """Convertir a diccionario"""
        data = asdict(self)
        # Convertir enum a string
        if 'platform' in data and hasattr(data['platform'], 'value'):
            data['platform'] = data['platform'].value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Crear instancia desde diccionario"""
        # Convertir string a enum si es necesario
        if 'platform' in data and isinstance(data['platform'], str):
            # platform se guarda como string
            pass
        return cls(**data)

class Playlist:
    """Clase para gestionar la lista de reproducción"""
    
    def __init__(self, playlist_file: str = None):
        self.playlist_file = playlist_file or os.path.join(Config.DATA_DIR, 'playlist.json')
        self.tracks: List[Track] = []
        self.current_index: int = -1
        self.playback_mode: PlaybackMode = PlaybackMode.NORMAL
        self.shuffle_order: List[int] = []
        
        self.load()
    
    def add_track(self, track_data: Dict[str, Any], position: int = None) -> Track:
        """
        Agregar una pista a la playlist
        
        Args:
            track_data: Datos de la pista
            position: Posición donde insertar (None para final)
        
        Returns:
            Track object
        """
        # Generar ID único
        track_id = hashlib.md5(
            f"{track_data.get('url')}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
        
        # Crear objeto Track
        track = Track(
            id=track_id,
            url=track_data.get('url', ''),
            title=track_data.get('title', 'Sin título'),
            artist=track_data.get('artist', 'Desconocido'),
            duration=track_data.get('duration', 0),
            platform=track_data.get('platform', 'other'),
            thumbnail=track_data.get('thumbnail'),
            filepath=track_data.get('filepath'),
            metadata=track_data.get('metadata', {}),
            added_at=datetime.now().isoformat(),
            order=len(self.tracks) if position is None else position,
            played=False,
            play_count=0
        )
        
        # Insertar en posición específica o al final
        if position is not None and 0 <= position < len(self.tracks):
            self.tracks.insert(position, track)
            # Actualizar órdenes
            for i, t in enumerate(self.tracks):
                t.order = i
        else:
            track.order = len(self.tracks)
            self.tracks.append(track)
        
        self.save()
        return track
    
    def add_multiple(self, tracks_data: List[Dict[str, Any]]) -> List[Track]:
        """Agregar múltiples pistas"""
        added_tracks = []
        for track_data in tracks_data:
            track = self.add_track(track_data)
            added_tracks.append(track)
        return added_tracks
    
    def remove_track(self, track_id: str) -> bool:
        """Remover una pista por ID"""
        for i, track in enumerate(self.tracks):
            if track.id == track_id:
                self.tracks.pop(i)
                # Actualizar índices
                if self.current_index >= i:
                    self.current_index = max(0, self.current_index - 1)
                # Actualizar órdenes
                for idx, t in enumerate(self.tracks):
                    t.order = idx
                self.save()
                return True
        return False
    
    def move_track(self, track_id: str, new_position: int) -> bool:
        """Mover una pista a nueva posición"""
        if new_position < 0 or new_position >= len(self.tracks):
            return False
        
        # Encontrar track
        for i, track in enumerate(self.tracks):
            if track.id == track_id:
                if i == new_position:
                    return True
                
                # Remover y reinsertar
                track = self.tracks.pop(i)
                self.tracks.insert(new_position, track)
                
                # Actualizar órdenes
                for idx, t in enumerate(self.tracks):
                    t.order = idx
                
                # Actualizar current_index
                if self.current_index == i:
                    self.current_index = new_position
                elif i < self.current_index <= new_position:
                    self.current_index -= 1
                elif new_position <= self.current_index < i:
                    self.current_index += 1
                
                self.save()
                return True
        return False
    
    def get_track(self, track_id: str) -> Optional[Track]:
        """Obtener track por ID"""
        for track in self.tracks:
            if track.id == track_id:
                return track
        return None
    
    def get_current_track(self) -> Optional[Track]:
        """Obtener track actual"""
        if 0 <= self.current_index < len(self.tracks):
            return self.tracks[self.current_index]
        return None
    
    def next_track(self) -> Optional[Track]:
        """Obtener siguiente track según modo de reproducción"""
        if not self.tracks:
            return None
        
        if self.playback_mode == PlaybackMode.SHUFFLE:
            return self._get_next_shuffle()
        
        # Modo normal o repeat_all
        if self.current_index < len(self.tracks) - 1:
            self.current_index += 1
        elif self.playback_mode == PlaybackMode.REPEAT_ALL:
            self.current_index = 0
        else:
            return None
        
        track = self.get_current_track()
        if track:
            track.played = True
            track.play_count += 1
        self.save()
        return track
    
    def previous_track(self) -> Optional[Track]:
        """Obtener track anterior"""
        if not self.tracks:
            return None
        
        if self.current_index > 0:
            self.current_index -= 1
        elif self.playback_mode == PlaybackMode.REPEAT_ALL:
            self.current_index = len(self.tracks) - 1
        else:
            return None
        
        track = self.get_current_track()
        if track:
            track.played = True
            track.play_count += 1
        self.save()
        return track
    
    def set_current_track(self, track_id: str) -> bool:
        """Establecer track actual por ID"""
        for i, track in enumerate(self.tracks):
            if track.id == track_id:
                self.current_index = i
                track.played = True
                track.play_count += 1
                self.save()
                return True
        return False
    
    def clear(self):
        """Limpiar playlist"""
        self.tracks = []
        self.current_index = -1
        self.shuffle_order = []
        self.save()
    
    def shuffle(self):
        """Mezclar playlist"""
        import random
        indices = list(range(len(self.tracks)))
        random.shuffle(indices)
        self.shuffle_order = indices
    
    def _get_next_shuffle(self) -> Optional[Track]:
        """Obtener siguiente track en modo shuffle"""
        if not self.tracks or not self.shuffle_order:
            self.shuffle()
        
        # Encontrar posición actual en shuffle_order
        if self.current_index == -1:
            next_idx = self.shuffle_order[0]
        else:
            try:
                current_pos = self.shuffle_order.index(self.current_index)
                next_pos = (current_pos + 1) % len(self.shuffle_order)
                next_idx = self.shuffle_order[next_pos]
            except ValueError:
                next_idx = self.shuffle_order[0]
        
        self.current_index = next_idx
        track = self.get_current_track()
        if track:
            track.played = True
            track.play_count += 1
        self.save()
        return track
    
    def save(self):
        """Guardar playlist a archivo JSON con escritura atómica"""
        try:
            data = {
                'tracks': [track.to_dict() for track in self.tracks],
                'current_index': self.current_index,
                'playback_mode': self.playback_mode.value,
                'shuffle_order': self.shuffle_order,
                'updated_at': datetime.now().isoformat()
            }
            
            # Escritura atómica: escribir a temp y luego renombrar
            temp_file = self.playlist_file + '.tmp'
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            os.replace(temp_file, self.playlist_file)
                
        except Exception as e:
            logger.error(f"Error guardando playlist: {e}")
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
    
    def load(self):
        """Cargar playlist desde archivo JSON de forma segura"""
        try:
            if os.path.exists(self.playlist_file):
                try:
                    with open(self.playlist_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    self.tracks = [Track.from_dict(track_data) for track_data in data.get('tracks', [])]
                    self.current_index = data.get('current_index', -1)
                    
                    mode = data.get('playback_mode', 'normal')
                    try:
                        self.playback_mode = PlaybackMode(mode)
                    except ValueError:
                        self.playback_mode = PlaybackMode.NORMAL
                    
                    self.shuffle_order = data.get('shuffle_order', [])
                    
                    # Asegurar órdenes
                    for i, track in enumerate(self.tracks):
                        track.order = i
                        
                except json.JSONDecodeError:
                    logger.error(f"Error de formato JSON en playlist. Creando backup y reiniciando.")
                    # Backup archivo corrupto
                    backup_file = self.playlist_file + f".bak.{int(datetime.now().timestamp())}"
                    try:
                        os.rename(self.playlist_file, backup_file)
                        logger.info(f"Playlist corrupta respaldada en {backup_file}")
                    except OSError as e:
                        logger.error(f"Error al respaldar archivo corrupto: {e}")
                    
                    # Reiniciar estado
                    self.tracks = []
                    self.current_index = -1
                    self.shuffle_order = []
                    
        except Exception as e:
            logger.error(f"Error cargando playlist: {e}")
            self.tracks = []
            self.current_index = -1
    
    def export_m3u(self, filepath: str) -> bool:
        """Exportar playlist a formato M3U"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write('#EXTM3U\n')
                for track in self.tracks:
                    f.write(f'#EXTINF:{track.duration},{track.artist} - {track.title}\n')
                    f.write(f'{track.url}\n')
            return True
        except Exception as e:
            logger.error(f"Error exportando M3U: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de la playlist"""
        total_duration = sum(track.duration for track in self.tracks)
        total_plays = sum(track.play_count for track in self.tracks)
        
        return {
            'total_tracks': len(self.tracks),
            'total_duration': total_duration,
            'total_plays': total_plays,
            'current_index': self.current_index,
            'playback_mode': self.playback_mode.value,
            'has_current': self.get_current_track() is not None
        }