# ComfyUI – Save MP3 (Custom Path) with Player

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)
![ComfyUI](https://img.shields.io/badge/ComfyUI-custom%20node-purple)

Ein ComfyUI Custom Node, der **generiertes Audio als MP3** an einem **frei wählbaren absoluten Pfad** speichert (z. B. `D:\omnivoice\person1` oder `E:\luca\proj01`), einen **Audio-Player direkt im Node** einblendet und auf Wunsch den kompletten **Workflow als JSON** mit identischem Dateinamen daneben ablegt.

---

## Inhalt

- [Features](#features)
- [Installation](#installation)
- [Benutzung](#benutzung)
- [Parameter](#parameter)
- [Workflow-JSON](#workflow-json)
- [Troubleshooting](#troubleshooting)
- [Lizenz](#lizenz)

---

## Features

- 💾 **Frei wählbarer Speicherort** — jedes Laufwerk, jede Ordnerstruktur, Ordner wird automatisch angelegt
- ✏️ **Frei wählbarer Dateiname** — ohne Endung, `.mp3` wird automatisch angehängt
- 🎚️ **Bitrate wählbar** — `128k` oder `256k`
- 🔢 **Automatischer Counter** — `audio_00001.mp3`, `audio_00002.mp3`, … (oder Überschreiben)
- 🎧 **Audio-Player direkt im Node** — anhören ohne Datei extern zu öffnen
- 🧩 **Workflow-JSON** — speichert den kompletten Workflow als `<dateiname>.json` im selben Ordner
- ⚡ **Robust** — Encoding direkt über ffmpeg-stdin-Pipe, keine Abhängigkeit von torchaudio/torchcodec

---

## Installation

### Variante 1: Über ComfyUI Manager

`Manager → Install via Git URL` → URL des Repos einfügen → Install. ComfyUI neu starten.

### Variante 2: Manuell mit GitHub Desktop / git clone

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/YOUR_GITHUB_USER/ComfyUI-SaveMP3CustomPath-WithPlayer.git
```

Anschließend ComfyUI neu starten.

### Variante 3: ZIP-Download

1. Repository als ZIP herunterladen (grüner `Code`-Button → `Download ZIP`)
2. ZIP nach `ComfyUI/custom_nodes/` entpacken
3. Ordner heißt am Ende `ComfyUI/custom_nodes/ComfyUI-SaveMP3CustomPath-WithPlayer/`
4. ComfyUI neu starten

### ffmpeg-Voraussetzung

Der Node nutzt **ffmpeg** zum MP3-Encoding. Wähle einen der beiden Wege:

**A) ffmpeg im System-PATH (empfohlen)**

- Windows: Build von <https://www.gyan.dev/ffmpeg/builds/> herunterladen, entpacken, den `bin`-Ordner zum PATH hinzufügen
- macOS: `brew install ffmpeg`
- Linux: `sudo apt install ffmpeg` o. ä.
- Prüfen mit `ffmpeg -version`

**B) Über pip (im ComfyUI-Python-Environment)**

```bash
pip install imageio-ffmpeg
```

Bei einer portablen Windows-Installation:

```bash
python_embeded\python.exe -m pip install imageio-ffmpeg
```

---

## Benutzung

Node-Menü:

```
Add Node  →  audio  →  save  →  💾 Save MP3 (Custom Path)
```

Oder per Doppelklick auf den Canvas → `Save MP3` eintippen.

Den `audio`-Output deines TTS- / Audio-Generator-Nodes mit dem `audio`-Input dieses Nodes verbinden, Pfad und Dateinamen eintragen, Workflow ausführen — fertig. Im Node erscheint anschließend der Audio-Player zum direkten Anhören.

---

## Parameter

| Parameter | Typ | Beschreibung |
|---|---|---|
| `audio` | AUDIO | Audio-Input vom vorherigen Node |
| `output_path` | STRING | Zielordner, z. B. `D:\omnivoice\person1` — wird angelegt, falls nicht vorhanden |
| `filename` | STRING | Dateiname ohne Endung, z. B. `voice_take` → wird zu `voice_take.mp3` |
| `quality` | `128k` / `256k` | MP3 Bitrate |
| `overwrite` | BOOLEAN | `True` = vorhandene Datei überschreiben. `False` = Counter anhängen |
| `save_workflow` | BOOLEAN | `True` = Workflow zusätzlich als `<dateiname>.json` im selben Ordner ablegen |

---

## Workflow-JSON

Mit `save_workflow = True` wird der aktuelle Workflow im **UI-Format** gespeichert — exakt das, was ComfyUI beim "Save" / "Export"-Button produziert.

- Datei kann per **Drag & Drop in den Canvas** gezogen oder über "Load" geladen werden → kompletter Graph wird wiederhergestellt
- Bei aktivem Counter bleibt das Namens-Paar erhalten: `voice_take_00003.mp3` ↔ `voice_take_00003.json`
- Speichert also bei jedem Run automatisch das passende Rezept zum Audio dazu

---

## Troubleshooting

**`ffmpeg wurde nicht gefunden`**
→ Siehe Installation, Abschnitt *ffmpeg-Voraussetzung*. Entweder ffmpeg in den PATH legen, oder `pip install imageio-ffmpeg` im ComfyUI-Environment ausführen.

**Datei wird gespeichert, aber Player erscheint nicht**
→ Browser-Cache leeren (Strg+F5). Das Audio liegt in jedem Fall am Zielort. Falls weiterhin kein Player erscheint: Node aus dem Workflow entfernen und neu hinzufügen.

**Backslashes in Pfaden**
→ Müssen im Node-Feld **nicht** verdoppelt werden — `D:\omnivoice\person1` reicht.

**Stereo / Mehrkanal**
→ Bei `[Batch, Channels, Time]`-Tensor wird das erste Batch-Element genommen, Kanäle bleiben erhalten.

---

## Lizenz

MIT — siehe [LICENSE](LICENSE).
