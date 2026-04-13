# 🎵 MusicBot Discord - Dx Edition

Un bot Discord simple et puissant pour jouer de la musique depuis **YouTube**, **Spotify** et **SoundCloud**.

## ✨ Fonctionnalités
- Support YouTube, Spotify (conversion automatique) et SoundCloud
- Commandes Slash modernes (`/play`, `/dashboard`, etc.)
- Contrôles : Pause, Reprendre, Skip, Volume (+ / -)
- Dashboard HTML beau et facile à utiliser (ouvre-le dans ton navigateur)
- File d'attente basique
- Lecture automatique de la musique suivante

## 📋 Installation rapide

### 1. Prérequis
- Python 3.10 ou supérieur
- FFmpeg installé et ajouté au PATH (obligatoire pour le son)
  - Télécharge-le ici : https://ffmpeg.org/download.html
  - Ou avec winget (Windows) : `winget install ffmpeg`

### 2. Installation des packages
Ouvre un terminal dans le dossier du bot et tape :
```bash
pip install discord.py[voice] yt-dlp spotipy python-dotenv
