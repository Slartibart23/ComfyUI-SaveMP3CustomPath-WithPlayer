/**
 * ComfyUI Frontend Extension: Audio-Player fuer "Save MP3 (Custom Path)".
 *
 * Haengt nach erfolgreicher Ausfuehrung des Nodes ein <audio>-Element
 * an den Node, das die gerade gespeicherte MP3 abspielt. Die MP3 wird
 * dafuer parallel ins ComfyUI temp-Verzeichnis kopiert und ueber den
 * /view-Endpoint ausgeliefert.
 */

import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

app.registerExtension({
    name: "SaveAudioMP3CustomPath.Preview",

    async beforeRegisterNodeDef(nodeType, nodeData, _app) {
        if (nodeData.name !== "SaveAudioMP3CustomPath") return;

        const onExecuted = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = function (message) {
            onExecuted?.apply(this, arguments);

            if (!message?.audio?.length) return;
            const info = message.audio[0];

            const params = new URLSearchParams({
                filename: info.filename,
                type: info.type || "temp",
                subfolder: info.subfolder || "",
                rand: Math.random().toString(36).slice(2),
            });
            const url = api.apiURL(`/view?${params.toString()}`);

            // Vorhandenes Preview-Widget entfernen, falls erneut ausgefuehrt
            if (this.widgets) {
                for (let i = this.widgets.length - 1; i >= 0; i--) {
                    if (this.widgets[i].name === "mp3_preview") {
                        this.widgets[i].onRemove?.();
                        this.widgets.splice(i, 1);
                    }
                }
            }

            // Audio-Element bauen
            const audio = document.createElement("audio");
            audio.controls = true;
            audio.src = url;
            audio.preload = "metadata";
            audio.style.width = "100%";
            audio.style.minWidth = "240px";
            audio.style.marginTop = "4px";

            // Container, damit der DOM-Widget eine vernuenftige Hoehe bekommt
            const container = document.createElement("div");
            container.style.padding = "4px 0";
            container.appendChild(audio);

            this.addDOMWidget("mp3_preview", "audio", container, {
                serialize: false,
                hideOnZoom: false,
            });

            // Node-Hoehe an den Player anpassen
            requestAnimationFrame(() => {
                const size = this.computeSize();
                if (size[1] > this.size[1]) this.size[1] = size[1];
                app.graph.setDirtyCanvas(true, true);
            });
        };
    },
});
