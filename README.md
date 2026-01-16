# Audio Flask Player 🎵

Un reproductor de música moderno basado en web, construido con **Flask**, que permite reproducir y gestionar audio desde múltiples plataformas como **YouTube**, **Vimeo**, **SoundCloud** y **Facebook**.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.x-green.svg)
![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.x-38bdf8.svg)

## ✨ Características

- **Multi-Plataforma**: Soporte para extraer y reproducir audio de YouTube, Vimeo, Facebook, SoundCloud y más (gracias a `yt-dlp`).
- **Interfaz Moderna**: Diseño responsivo y elegante con **Tailwind CSS**, modo oscuro y efectos de vidrio (Glassmorphism).
- **Reproductor Completo**:
  - Controles de reproducción (Play/Pause, Anterior, Siguiente).
  - Control de volumen y barra de progreso interactiva.
  - Modos de reproducción: Aleatorio (Shuffle) y Repetición.
- **Gestión de Playlist**:
  - Agregar canciones mediante URL.
  - Cola de reproducción dinámica.
  - Opción de "Agregar y Reproducir automáticamente".
  - Persistencia de playlist.
- **Caché Inteligente**: Descarga y almacena audio localmente para una reproducción fluida y sin interrupciones.
- **Configuración Avanzada**:
  - Selección de calidad de audio (128kbps, 192kbps, 320kbps, FLAC).
  - Temas visuales.
  - Gestión de caché.

## 📱 Demo
Para probar el demo, puedes visitar el siguiente enlace: [Demo](https://flask-audio-player-lrrq.onrender.com)



## 🚀 Instalación y Configuración

### Prerrequisitos

- **Python 3.8+**
- **FFmpeg** (Necesario para el procesamiento de audio).
  - _Ubuntu/Debian_: `sudo apt install ffmpeg`
  - _Windows_: Descargar y agregar al PATH.
  - _macOS_: `brew install ffmpeg`

### Pasos de Instalación

1.  **Clonar el repositorio**

    ```bash
    git clone https://github.com/Marbinseca/flask_audio_player.git
    cd flask_audio_player
    ```

2.  **Crear un entorno virtual**

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # En Windows: venv\Scripts\activate
    ```

3.  **Instalar dependencias**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Ejecutar la aplicación**

    ```bash
    python3 app.py
    ```

5.  **Abrir en el navegador**
    Visita `http://127.0.0.1:8080` en tu navegador favorito.

## 📖 Uso

1.  **Agregar Música**:

    - Haz clic en el botón **"+"** o usa la tarjeta de "Agregar Rápido".
    - Pega una URL de YouTube (o cualquier plataforma soportada).
    - Haz clic en "Agregar a la Lista".
    - _Tip_: Si marcas "Reproducir automáticamente", la canción comenzará de inmediato.

2.  **Controlar Reproducción**:

    - Usa los controles grandes a la izquierda para Pausar, Cambiar canción o Ajustar volumen.
    - También puedes controlar la reproducción desde la tarjeta "Now Playing" en la lista de reproducción.

3.  **Ajustes**:
    - Accede al menú de configuración (icono de engranaje) para cambiar la calidad de audio o limpiar la caché si el disco se llena.

## 🛠️ Estructura del Proyecto

```
flask_audio_player/
├── app.py                  # Aplicación principal Flask
├── config.py               # Configuraciones (Clave secreta, directorios)
├── youtube_dl_helper.py    # Wrapper para yt-dlp (extracción de audio)
├── audio_cache/            # Directorio donde se guardan los archivos de audio
├── data/                   # Almacenamiento de datos (playlist.json, settings.json)
├── static/
│   ├── css/                # Estilos personalizados (custom.css)
│   ├── js/                 # Lógica del cliente (player.js, playlist.js)
│   └── icons/              # Favicons e imágenes por defecto
└── templates/
    ├── base.html           # Plantilla base
    ├── index.html          # Página principal (Dashboard)
    ├── settings_modal.html # Modal de configuración
    └── add_url_modal.html  # Modal para agregar URL
```

## 🤝 Contribución

¡Las contribuciones son bienvenidas! Si encuentras un bug o quieres mejorar una característica:

1.  Haz un Fork del proyecto.
2.  Crea una rama (`git checkout -b feature/AmazingFeature`).
3.  Commit tus cambios (`git commit -m 'Add some AmazingFeature'`).
4.  Push a la rama (`git push origin feature/AmazingFeature`).
5.  Abre un Pull Request.

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Consulta el archivo `LICENSE` para más detalles.
