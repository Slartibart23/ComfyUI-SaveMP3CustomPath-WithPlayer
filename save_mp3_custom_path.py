"""
ComfyUI Custom Node: Save Audio as MP3 to Custom Path
-----------------------------------------------------
Speichert ein generiertes AUDIO als MP3 an einem frei waehlbaren
absoluten Pfad (z.B. D:\\omnivoice\\person1 oder E:\\luca\\proj01)
mit einstellbarer Bitrate (128k / 256k) und blendet zusaetzlich
einen Audio-Player im Node ein. Optional wird der komplette Workflow
als .json mit gleichem Dateinamen im selben Ordner mitgespeichert.

Zusaetzlich gibt es einen optionalen Text-Input (z.B. vom Prompt
oder einer beliebigen Text-Node). Ist dieser verbunden, wird der
Text als <dateiname>.txt (UTF-8) mit exakt demselben Dateinamen
wie die MP3 im selben Ordner abgelegt (inkl. Counter-Logik).

Encoding-Strategie:
1. Audio-Tensor wird als float32-PCM in numpy konvertiert.
2. Rohdaten gehen direkt via stdin-Pipe an ffmpeg (libmp3lame).
   Damit ist die Node unabhaengig von torchaudio.save() bzw.
   torchcodec, was bei einigen ComfyUI-Builds fehlt.
3. Fuer die Vorschau im Node wird eine Kopie ins ComfyUI temp-
   Verzeichnis gelegt und ueber das Standard-Audio-Preview-Widget
   angezeigt.
4. Workflow wird via hidden 'extra_pnginfo' aus ComfyUI uebernommen
   und als <dateiname>.json gespeichert (im UI-Format, ladbar via
   'Load' in ComfyUI).
"""

import json
import os
import shutil
import subprocess

import numpy as np
import torch
import torchaudio  # nur fuer Typ-Hinweise / Kompatibilitaet

import folder_paths


def _find_ffmpeg():
    """Sucht ffmpeg im PATH oder ueber imageio-ffmpeg."""
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def _sanitize_filename(name: str) -> str:
    name = name.strip()
    if not name:
        name = "audio"
    if name.lower().endswith(".mp3"):
        name = name[:-4]
    for ch in '<>:"/\\|?*':
        name = name.replace(ch, "_")
    return name


class SaveAudioMP3CustomPath:
    """
    Speichert AUDIO als MP3 an einem absoluten Pfad.
    Zeigt einen Audio-Player im Node zur Vorschau / Wiedergabe.
    Speichert optional einen verbundenen Text als .txt mit
    identischem Dateinamen.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "audio": ("AUDIO",),
                "output_path": (
                    "STRING",
                    {
                        "default": "D:\\omnivoice\\person1",
                        "multiline": False,
                        "tooltip": "Zielordner (wird automatisch angelegt, falls nicht vorhanden)",
                    },
                ),
                "filename": (
                    "STRING",
                    {
                        "default": "audio",
                        "multiline": False,
                        "tooltip": "Dateiname ohne Endung (.mp3 wird automatisch angehaengt)",
                    },
                ),
                "quality": (
                    ["128k", "256k"],
                    {"default": "256k", "tooltip": "MP3 Bitrate"},
                ),
                "overwrite": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "True = vorhandene Datei ueberschreiben. False = an Dateinamen wird _00001, _00002 ... angehaengt.",
                    },
                ),
                "save_workflow": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "tooltip": "Workflow als JSON mit gleichem Dateinamen im selben Ordner speichern.",
                    },
                ),
            },
            "optional": {
                "text": (
                    "STRING",
                    {
                        "forceInput": True,
                        "multiline": True,
                        "tooltip": "Optionaler Text-Input (z.B. Prompt). Wird als <dateiname>.txt mit identischem Dateinamen gespeichert.",
                    },
                ),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    RETURN_TYPES = ()
    OUTPUT_NODE = True
    FUNCTION = "save_mp3"
    CATEGORY = "audio/save"

    # ------------------------------------------------------------------ #
    def _encode_mp3(self, waveform: torch.Tensor, sample_rate: int,
                    target_path: str, bitrate: str) -> None:
        """
        Encodiert das Audio direkt via ffmpeg stdin-Pipe zu MP3.

        Vorteil: Keine WAV-Zwischendatei und keine torchaudio.save()-
        Abhaengigkeit (das schlaegt bei neueren torchaudio-Versionen
        fehl, wenn torchcodec nicht installiert ist).

        waveform: Tensor der Form [channels, time], float
        """
        ffmpeg_exe = _find_ffmpeg()
        if ffmpeg_exe is None:
            raise RuntimeError(
                "ffmpeg wurde nicht gefunden. Bitte ffmpeg installieren "
                "und in den PATH legen, oder ausfuehren: "
                "pip install imageio-ffmpeg"
            )

        # Nach numpy float32 konvertieren ([channels, time])
        waveform_np = waveform.detach().cpu().to(torch.float32).numpy()
        if waveform_np.ndim == 1:
            waveform_np = waveform_np[np.newaxis, :]

        num_channels = waveform_np.shape[0]

        # ffmpeg erwartet interleaved samples: [t0c0, t0c1, t1c0, t1c1, ...]
        # also [channels, time] -> [time, channels] -> bytes
        interleaved = np.ascontiguousarray(waveform_np.T).tobytes()

        cmd = [
            ffmpeg_exe, "-y", "-loglevel", "error",
            "-f", "f32le",
            "-ar", str(sample_rate),
            "-ac", str(num_channels),
            "-i", "-",
            "-codec:a", "libmp3lame",
            "-b:a", bitrate,
            target_path,
        ]

        result = subprocess.run(cmd, input=interleaved, capture_output=True)
        if result.returncode != 0:
            err = result.stderr.decode("utf-8", errors="replace")
            raise RuntimeError(f"ffmpeg-Encoding fehlgeschlagen:\n{err}")

    # ------------------------------------------------------------------ #
    def save_mp3(self, audio, output_path, filename, quality, overwrite,
                 save_workflow, text=None, prompt=None, extra_pnginfo=None):

        # --- Pfad / Dateiname vorbereiten -------------------------------
        output_path = os.path.normpath(output_path.strip())
        os.makedirs(output_path, exist_ok=True)

        filename = _sanitize_filename(filename)
        base_full = os.path.join(output_path, filename + ".mp3")

        if overwrite or not os.path.exists(base_full):
            full_path = base_full
        else:
            counter = 1
            while True:
                candidate = os.path.join(
                    output_path, f"{filename}_{counter:05d}.mp3"
                )
                if not os.path.exists(candidate):
                    full_path = candidate
                    break
                counter += 1

        # --- Waveform vorbereiten ---------------------------------------
        waveform = audio["waveform"]
        sample_rate = int(audio["sample_rate"])

        # [Batch, Channels, Time] -> [Channels, Time]
        if waveform.dim() == 3:
            waveform = waveform[0]

        if waveform.is_cuda:
            waveform = waveform.cpu()
        waveform = waveform.to(torch.float32)

        # --- MP3 encoden ------------------------------------------------
        self._encode_mp3(waveform, sample_rate, full_path, quality)
        print(f"[SaveAudioMP3CustomPath] gespeichert: {full_path}")

        # --- Text als TXT speichern (falls Input verbunden) -------------
        if text is not None:
            txt_path = os.path.splitext(full_path)[0] + ".txt"
            try:
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(text)
                print(f"[SaveAudioMP3CustomPath] Text gespeichert: {txt_path}")
            except Exception as e:
                print(f"[SaveAudioMP3CustomPath] Text-Speicherung fehlgeschlagen: {e}")

        # --- Workflow als JSON speichern -------------------------------
        if save_workflow:
            json_path = os.path.splitext(full_path)[0] + ".json"
            try:
                # Bevorzugt: kompletter Workflow aus extra_pnginfo
                # (entspricht dem, was beim "Save"-Knopf in ComfyUI rauskommt)
                workflow_obj = None
                if extra_pnginfo and isinstance(extra_pnginfo, dict):
                    workflow_obj = extra_pnginfo.get("workflow")

                if workflow_obj is not None:
                    payload = workflow_obj
                else:
                    # Fallback: API-Format (prompt graph)
                    payload = prompt if prompt is not None else {}

                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(payload, f, indent=2, ensure_ascii=False)
                print(f"[SaveAudioMP3CustomPath] Workflow gespeichert: {json_path}")
            except Exception as e:
                print(f"[SaveAudioMP3CustomPath] Workflow-Speicherung fehlgeschlagen: {e}")

        # --- Kopie fuer Player im Node ----------------------------------
        # ComfyUI darf nur Dateien aus seinen eigenen Ordnern ueber den
        # /view-Endpoint ausliefern, daher legen wir eine Kopie ins temp-
        # Verzeichnis.
        ui_audio = []
        try:
            temp_dir = folder_paths.get_temp_directory()
            os.makedirs(temp_dir, exist_ok=True)
            preview_name = os.path.basename(full_path)
            preview_path = os.path.join(temp_dir, preview_name)
            shutil.copy2(full_path, preview_path)
            ui_audio.append(
                {
                    "filename": preview_name,
                    "subfolder": "",
                    "type": "temp",
                }
            )
        except Exception as e:
            print(f"[SaveAudioMP3CustomPath] Preview-Kopie fehlgeschlagen: {e}")

        return {"ui": {"audio": ui_audio}}


# ---------------------------------------------------------------------- #
# ComfyUI Registrierung
# ---------------------------------------------------------------------- #
NODE_CLASS_MAPPINGS = {
    "SaveAudioMP3CustomPath": SaveAudioMP3CustomPath,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SaveAudioMP3CustomPath": "💾 Save MP3 (Custom Path)",
}
