# Guía de Despliegue (Deployment) 🚀

Esta guía te explicará cómo llevar tu Audio Flask Player a internet para que cualquiera pueda usarlo.

## Opción Recomendada: Render (Gratis)

Recomendamos usar **Render** porque ofrece un plan gratuito generoso y es muy fácil de usar con proyectos Python.

### Prerrequisitos

1.  Tener tu código en **GitHub** (o GitLab).
2.  Crear una cuenta en [render.com](https://render.com).

### Pasos para Desplegar

#### Método 1: Despliegue con Docker (El más robusto)

Este es el mejor método porque asegura que **FFmpeg** esté instalado correctamente (lo cual es vital para este proyecto).

1.  Sube tu código a GitHub.
2.  En Render, haz clic en **"New +"** y selecciona **"Web Service"**.
3.  Conecta tu repositorio de GitHub.
4.  Llena el formulario:
    - **Name**: `mi-audio-player` (o lo que quieras).
    - **Region**: La más cercana a ti (ej. Ohio).
    - **Branch**: `main` (o master).
    - **Runtime**: Selecciona **Docker**.
5.  Render detectará automáticamente el archivo `Dockerfile` que hemos creado.
6.  Selecciona el **Plan Free**.
7.  Haz clic en **"Create Web Service"**.

¡Listo! Render construirá tu imagen de Docker (esto puede tardar unos minutos la primera vez) y te dará una URL (ej. `https://mi-audio-player.onrender.com`).

#### Método 2: Despliegue Python Nativo (Alternativa)

Si prefieres no usar Docker, puedes intentar el entorno nativo de Python, pero **Render no instala FFmpeg por defecto en el entorno Python**, por lo que el Método 1 es superior. Si usas este método, es posible que la conversión de audio falle.

### Variables de Entorno

Si tu aplicación usa claves secretas (API Keys) o configuraciones sensibles:

1.  Ve a la pestaña **"Environment"** en tu servicio de Render.
2.  Agrega las variables necesarias (ej. `SECRET_KEY`, etc.).

---

## Opción 2: Railway (Alternativa)

Railway también es excelente y detecta automáticamente el `Procfile` y `requirements.txt`.

1.  Crea cuenta en [railway.app](https://railway.app).
2.  Haz clic en **"New Project"** -> **"Deploy from GitHub repo"**.
3.  Selecciona tu repositorio.
4.  Railway usará `requirements.txt` y `Procfile`.
5.  Para instalar FFmpeg, crea un archivo llamado `nixpacks.toml` (o confía en que su builder lo detecte, pero Docker sigue siendo más seguro).

---

## Archivos Críticos Creados

Hemos preparado tu proyecto con los siguientes archivos para facilitar el despliegue:

- `Procfile`: Le dice a la plataforma cómo iniciar el servidor (`gunicorn`).
- `Dockerfile`: Define un entorno completo con Python y **FFmpeg** instalado.
- `requirements.txt`: Lista todas las librerías necesarias.
