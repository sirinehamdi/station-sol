
from flask import Flask, request, jsonify, render_template, send_file, redirect, url_for
from datetime import datetime
import base64
import imghdr
import os
import requests

app = Flask(__name__)

# ==================================================
# STOCKAGE DONNEES ESP32
# ==================================================

data_store = {
    "time": [],
}
file_path = "data.txt"

# Créer un nouveau fichier data.txt vide
if os.path.exists(file_path):
    os.remove(file_path)
with open(file_path, "w") as f:
    pass

IMAGE_SAVE_DIR = os.path.join("static", "img", "esp32")
os.makedirs(IMAGE_SAVE_DIR, exist_ok=True)
os.makedirs('static', exist_ok=True)

# ==================================================
# IP ESP32 (IMPORTANT)
# ==================================================
# ESP32_IP = os.environ.get("ESP32_IP", "192.168.4.1").strip()
# if not ESP32_IP:
#     ESP32_IP = "192.168.4.1"
ESP32_IP = "172.20.10.2"


# ==================================================
# RECEPTION DONNEES ESP32 (WiFi POST JSON)
# ==================================================
@app.route("/data", methods=["POST"])
def receive_data():
    print("Raw data :")
    print(request.data)
    data = request.json
    print("date ", data)
    
    now_time = datetime.now().strftime("%H:%M:%S")
    now_date = datetime.now().strftime("%d-%m-%Y")

    # Ajouter "time" au data_store si pas déjà présent
    if "time" not in data_store:
        data_store["time"] = []
    
    # Stocker le timestamp
    data_store["time"].append(now_time)
    
    # === CRÉATION AUTOMATIQUE DES PARAMÈTRES ===
    # Itérer sur tous les paramètres reçus du JSON
    for key, value in data.items():
        # Créer la liste pour ce paramètre s'il n'existe pas
        if key not in data_store:
            data_store[key] = []
            print(f"[+] Nouveau parametre cree: {key}")
        
        # Ajouter la valeur
        data_store[key].append(value)
    
    # Stocker le status
    data_store2["status"] = data.get("status", 0)

    # === ÉCRITURE FICHIER data.txt (FORMAT SIMPLE) ===
    # Format: HH:MM:SS param:value param:value ...
    with open(file_path, "a") as f:
        line_parts = [now_time]
        
        # Ajouter tous les paramètres avec leurs noms
        for key in sorted(data.keys()):
            line_parts.append(f"{key}:{data[key]}")
        
        line = " ".join(line_parts)
        f.write(line + "\n")

    print("Reçu ESP32:", data)

    return jsonify({"status": "ok"})


# ==================================================
# GET DATA (dashboard Angular / web)
# ==================================================
@app.route("/data", methods=["GET"])
def get_data():
    return jsonify(data_store)


# ==================================================
# PAGE WEB
# ==================================================
@app.route("/")
def index():
    return render_template("index.html")


# ==================================================
# CAM ON (HTTP → ESP32)
# ==================================================
def save_esp32_image(response, prefix="esp32"):
    content_type = response.headers.get("Content-Type", "").lower()
    image_bytes = None
    extension = "jpg"

    if "application/json" in content_type:
        payload = response.json()
        image_data = payload.get("image") or payload.get("data")
        if not image_data:
            raise ValueError("No image data found in JSON response")

        image_bytes = base64.b64decode(image_data)
        extension = payload.get("extension", "jpg").lower()
    else:
        image_bytes = response.content
        if not image_bytes:
            raise ValueError("No image bytes found in response")

        if "jpeg" in content_type or "jpg" in content_type:
            extension = "jpg"
        elif "png" in content_type:
            extension = "png"
        elif "gif" in content_type:
            extension = "gif"
        elif "bmp" in content_type:
            extension = "bmp"
        elif "webp" in content_type:
            extension = "webp"

    if not image_bytes:
        raise ValueError("Image data is empty or invalid")

    detected = imghdr.what(None, h=image_bytes)
    if detected:
        if detected == "jpeg":
            detected = "jpg"
        extension = detected
    elif extension not in ("jpg", "jpeg", "png", "gif", "bmp", "webp"):
        raise ValueError("Unable to determine valid image format")

    filename = datetime.now().strftime(f"{prefix}_%Y%m%d_%H%M%S.") + extension
    save_path = os.path.join(IMAGE_SAVE_DIR, filename)

    with open(save_path, "wb") as f:
        f.write(image_bytes)

    return filename, image_bytes


@app.route("/cam_on")
def cam_on():
    try:
        url = f"http://{ESP32_IP}/cam_on"
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        return jsonify({"message": "CAM ON OK", "ip": ESP32_IP, "attempted_url": url})
    except Exception as e:
        print("cam_on error:", e)
        return jsonify({"message": "ERROR ESP32", "error": str(e)}), 500




@app.route("/status")
def status():
    return jsonify({"status": data_store2["status"]})

# ==================================================
# CAM OFF (HTTP → ESP32)
# ==================================================
@app.route("/cam_off")
def cam_off():
    try:
        url = f"http://{ESP32_IP}/cam_off"
        r = requests.get(url)
        return jsonify({"message": "CAM OFF OK"})
    except Exception as e:
        return jsonify({"message": "ERROR ESP32", "error": str(e)}), 500


@app.route('/esp32_ip', methods=['GET', 'POST'])
def esp32_ip():
    global ESP32_IP
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        new_ip = data.get('ip') if isinstance(data, dict) else None
        if not new_ip:
            return jsonify({"message": "No IP provided."}), 400
        ESP32_IP = new_ip.strip()
        return jsonify({"message": "ESP32 IP updated.", "ip": ESP32_IP})
    return jsonify({"ip": ESP32_IP})


# ==================================================
# Capture endpoints (upload from ESP32 / trigger capture)
# ==================================================


@app.route('/capture', methods=['POST', 'GET'])
def capture():
    """Trigger the ESP32 to take a picture (GET/POST) and return capture metadata."""
    url = f"http://{ESP32_IP}/capture"
    attempted_urls = [url]
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()

        if not r.content:
            raise ValueError("No image content returned from ESP32.")

        saved_file, image_bytes = save_esp32_image(r, prefix="Capture")
        latest_path = os.path.join('static', 'Derniere_Capture.jpg')

        with open(latest_path, 'wb') as f:
            f.write(image_bytes)

        return jsonify({
            "message": "Capture saved",
            "saved_image": saved_file,
            "image_url": url_for('static', filename=f'img/esp32/{saved_file}'),
            "ip": ESP32_IP,
            "attempted_url": url
        })
    except requests.exceptions.RequestException as e:
        error_msg = f"{type(e).__name__}: {e}"
        print(f"capture attempt failed for {url}:", error_msg)
        return jsonify({
            "message": "ERROR ESP32",
            "error": error_msg,
            "ip": ESP32_IP,
            "attempted_urls": attempted_urls
        }), 500
    except Exception as e:
        error_msg = f"{type(e).__name__}: {e}"
        print(f"capture processing failed for {url}:", error_msg)
        return jsonify({
            "message": "ERROR ESP32",
            "error": error_msg,
            "ip": ESP32_IP,
            "attempted_urls": attempted_urls
        }), 500


@app.route('/upload', methods=['POST'])
def upload():
    """Endpoint for ESP32 to POST raw image bytes. Saves archive and latest file."""
    data = request.data
    if not data:
        return "No data received", 400

    detected = imghdr.what(None, h=data)
    if not detected:
        return "Invalid image data", 400
    if detected == "jpeg":
        detected = "jpg"

    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"Capture_{timestamp}.{detected}"
        archive_path = os.path.join(IMAGE_SAVE_DIR, filename)
        with open(archive_path, 'wb') as f:
            f.write(data)

        latest_path = os.path.join('static', 'Derniere_Capture.jpg')
        with open(latest_path, 'wb') as f:
            f.write(data)

        print(f"{filename} is saved.")
        return "Capture received successfully", 200
    except Exception as e:
        print(f"Error: {e}. Saving has failed.")
        return "Writing Error.", 500


@app.route('/image')
def image():
    latest_path = os.path.join('static', 'Derniere_Capture.jpg')
    if os.path.exists(latest_path):
        return send_file(latest_path, mimetype='image/jpeg')
    return "No image available", 404


@app.route('/historique')
def historique():
    files = []
    try:
        for fichier in os.listdir(IMAGE_SAVE_DIR):
            if not fichier.lower().startswith('capture_'):
                continue
            path = os.path.join(IMAGE_SAVE_DIR, fichier)
            if not os.path.isfile(path) or os.path.getsize(path) < 200:
                continue
            if not imghdr.what(path):
                continue
            files.append(fichier)
    except Exception:
        files = []

    files.sort(reverse=True)

    page = """
    <h3>Historique des captures</h3>
    <p><a href='/'>Retour</a></p>
    <div>
    """

    for image_file in files:
        url = url_for('static', filename=f'img/esp32/{image_file}')
        page += f"<div><h5>{image_file}</h5><img src=\"{url}\" style=\"max-width:300px;\"></div><hr>"

    page += "</div>"
    return page


data_store2 = {

    "latitude": 48.8566,
    "longitude": 2.3522,
    "status": 0
}

@app.route("/position")
def position():
    return jsonify({
        "latitude": data_store2["latitude"],
        "longitude": data_store2["longitude"]
    })

# ==================================================
# RUN SERVER
# ==================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)





