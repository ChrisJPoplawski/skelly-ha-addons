import os, json, pathlib
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, abort
import vlc

BASE_DIR = pathlib.Path(__file__).parent.resolve()
DATA_DIR  = pathlib.Path(os.getenv("SKELLY_DATA_DIR", "/data/skelly/data"))
MUSIC_DIR = pathlib.Path(os.getenv("SKELLY_MUSIC_DIR", "/data/skelly/music"))
BLE_DIR = BASE_DIR / "ble-ui"
QUEUE_JSON = DATA_DIR / "queue.json"
STATE_JSON = DATA_DIR / "state.json"

app = Flask(__name__)

def load_queue():
    if QUEUE_JSON.exists():
        return json.loads(QUEUE_JSON.read_text())
    return []

def save_queue(q):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    QUEUE_JSON.write_text(json.dumps(q, indent=2))

def load_state():
    if STATE_JSON.exists():
        return json.loads(STATE_JSON.read_text())
    return {"volume": 80}

def save_state(s):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STATE_JSON.write_text(json.dumps(s, indent=2))

class Player:
    def __init__(self):
        self.instance = vlc.Instance()
        self.list_player = self.instance.media_list_player_new()
        self.media_list = self.instance.media_list_new()
        self.list_player.set_media_list(self.media_list)
        self.player = self.list_player.get_media_player()
        self.queue = load_queue()
        self.current_index = -1
        self.playing = False
        self.volume = load_state().get("volume", 80)
        self.player.audio_set_volume(self.volume)
        em = self.player.event_manager()
        em.event_attach(vlc.EventType.MediaPlayerEndReached, self._track_ended)

    def library(self):
        files = []
        for p in MUSIC_DIR.rglob("*"):
            if p.is_file() and p.suffix.lower() in [".mp3",".wav",".flac",".m4a",".aac",".ogg"]:
                files.append({"name": p.name, "relpath": str(p.relative_to(MUSIC_DIR))})
        files.sort(key=lambda x: x["name"].lower())
        return files

    def _set_media_list_from_queue(self):
        self.media_list = self.instance.media_list_new()
        for item in self.queue:
            abs_path = str(MUSIC_DIR / item["relpath"])
            self.media_list.add_media(self.instance.media_new_path(abs_path))
        self.list_player.set_media_list(self.media_list)

    def _current_title(self):
        if 0 <= self.current_index < len(self.queue):
            return self.queue[self.current_index]["name"]
        return None

    def _track_ended(self, event):
        self.current_index += 1
        if self.current_index >= len(self.queue):
            self.playing = False

    def play(self):
        if not self.queue:
            return
        self._set_media_list_from_queue()
        start_index = max(self.current_index, 0)
        self.list_player.play_item_at_index(start_index)
        self.playing = True

    def pause(self):
        self.list_player.pause(); self.playing = False

    def stop(self):
        self.list_player.stop(); self.playing = False

    def next(self):
        if self.current_index + 1 < len(self.queue):
            self.current_index += 1
            self.list_player.play_item_at_index(self.current_index)
            self.playing = True

    def prev(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.list_player.play_item_at_index(self.current_index)
            self.playing = True

    def set_volume(self, v:int):
        v = max(0, min(100, int(v)))
        self.player.audio_set_volume(v)
        self.volume = v
        s = load_state(); s["volume"] = v; save_state(s)

    def add_to_queue(self, relpath, name):
        self.queue.append({"relpath": relpath, "name": name})
        save_queue(self.queue)
        if self.current_index == -1: self.current_index = 0

    def remove_from_queue(self, idx):
        if 0 <= idx < len(self.queue):
            del self.queue[idx]
            if idx <= self.current_index:
                self.current_index = max(-1, self.current_index-1)
            save_queue(self.queue)

    def move(self, idx, dir):
        if 0 <= idx < len(self.queue):
            new_idx = idx-1 if dir=='up' else idx+1
            if 0 <= new_idx < len(self.queue):
                self.queue[idx], self.queue[new_idx] = self.queue[new_idx], self.queue[idx]
                if self.current_index == idx:
                    self.current_index = new_idx
                elif self.current_index == new_idx:
                    self.current_index = idx
                save_queue(self.queue)

    def clear(self):
        self.queue = []; self.current_index = -1; save_queue(self.queue)

player = Player()

@app.route("/")
def index():
    state = {"current_title": player._current_title(), "playing": player.playing, "volume": player.volume, "queue_len": len(player.queue)}
    return render_template("index.html", library=player.library(), queue=player.queue, state=state, enumerate=enumerate)

@app.post("/upload")
def upload():
    MUSIC_DIR.mkdir(parents=True, exist_ok=True)
    files = request.files.getlist("files")
    for f in files:
        if not f.filename: continue
        ext = os.path.splitext(f.filename)[1].lower()
        if ext not in [".mp3",".wav",".flac",".m4a",".aac",".ogg"]: continue
        dest = MUSIC_DIR / os.path.basename(f.filename)
        i=1
        while dest.exists():
            dest = MUSIC_DIR / f"{os.path.splitext(os.path.basename(f.filename))[0]}_{i}{ext}"; i+=1
        f.save(dest)
    return redirect(url_for('index'))

@app.post("/control")
def control():
    action = request.form.get("action"); vol = request.form.get("volume")
    if vol is not None: player.set_volume(vol)
    if action == "play": player.play()
    elif action == "pause": player.pause()
    elif action == "stop": player.stop()
    elif action == "next": player.next()
    elif action == "prev": player.prev()
    return redirect(url_for('index'))

@app.post("/queue/add")
def queue_add():
    relpath = request.form.get("path"); name = os.path.basename(relpath)
    player.add_to_queue(relpath, name); return redirect(url_for('index'))

@app.post("/queue/remove")
def queue_remove():
    idx = int(request.form.get("index", "-1")); player.remove_from_queue(idx); return redirect(url_for('index'))

@app.post("/queue/move")
def queue_move():
    idx = int(request.form.get("index", "-1")); dir = request.form.get("dir")
    player.move(idx, dir); return redirect(url_for('index'))

@app.post("/queue/clear")
def queue_clear():
    player.clear(); return redirect(url_for('index'))

@app.post("/queue/save")
def queue_save():
    return redirect(url_for('index'))

@app.post("/queue/load")
def queue_load():
    player.queue = load_queue(); return redirect(url_for('index'))

@app.route("/ble")
def ble_home():
    index_path = BLE_DIR / "index.html"
    if not index_path.exists(): return render_template("ble_missing.html")
    return render_template("ble_embed.html")

@app.route("/ble/static/<path:subpath>")
def ble_static(subpath):
    if not BLE_DIR.exists(): abort(404)
    return send_from_directory(BLE_DIR, subpath)

@app.route("/ble/index.html")
def ble_index_direct():
    if not (BLE_DIR / "index.html").exists(): abort(404)
    return send_from_directory(BLE_DIR, "index.html")

@app.route("/controls")
def controls():
    return render_template("controls.html")

@app.post("/controls/center")
def center_controls():
    return redirect(url_for('controls'))

@app.post("/controls/leds")
def led_controls():
    return redirect(url_for('controls'))

if __name__ == "__main__":
    from waitress import serve
    host = os.getenv("SKELLY_BIND_HOST", "0.0.0.0")
    port = int(os.getenv("SKELLY_PORT", "8099"))
    serve(app, host=host, port=port)
