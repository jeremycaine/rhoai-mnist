#!/usr/bin/env python3
import os
import json
import numpy as np
import requests
import flask
from PIL import Image, ImageOps

app = flask.Flask(__name__)

# OVMS REST v2 inference endpoint
OVMS_URL = os.getenv(
    "OVMS_URL",
    "https://mnist-onxx-jeremycaine-dev.apps.rm2.thpm.p1.openshiftapps.com/v2/models/mnist-onxx/infer",
)

SA_TOKEN_PATH = os.getenv(
    "SA_TOKEN_PATH",
    "/var/run/secrets/kubernetes.io/serviceaccount/token"
)

def log(msg): print(f"{msg}\n", flush=True)

def _read_sa_token():
    try:
        with open(SA_TOKEN_PATH, "r") as f:
            return f.read().strip()
    except Exception:
        return None

def preprocess_rgba_bytes_to_28x28_gray_norm(raw_rgba_bytes: bytes, src_size=(200, 200)) -> np.ndarray:
    """
    Convert raw RGBA bytes from the canvas (200x200) into float32 tensor
    shape (1, 28, 28, 1), values in [0,1].
    """
    # 1) Load RGBA
    img = Image.frombytes(mode="RGBA", size=src_size, data=raw_rgba_bytes)

    # 2) Resize drawing area to 20x20
    img = img.resize((20, 20))

    # 3) Put over white background to remove alpha
    bg = Image.new(mode="RGBA", size=(20, 20), color="WHITE")
    bg.paste(img, (0, 0), mask=img)

    # 4) Grayscale
    gray = ImageOps.grayscale(bg)  # "L"

    # 5) Pad to 28x28 with white border (4 pixels each side)
    padded = ImageOps.expand(gray, border=4, fill=255)

    # 6) Invert (your training expected white=0, black=1 style)
    inverted = ImageOps.invert(padded)  # still 28x28

    # 7) To float32 [0,1], shape (1,28,28,1)
    arr = np.asarray(inverted, dtype=np.float32) / 255.0  # (28,28)
    arr = arr.reshape(1, 28, 28, 1)
    return arr

@app.route("/", methods=["GET"])
def index():
    return flask.render_template("mnist.html")

@app.route("/image", methods=["POST"])
def image():
    log(f"OVMS_URL={OVMS_URL}")

    # Raw bytes from the canvas POST (expected RGBA 200x200)
    raw = flask.request.get_data(cache=False)

    # Preprocess to model tensor
    try:
        x = preprocess_rgba_bytes_to_28x28_gray_norm(raw, src_size=(200, 200))  # (1,28,28,1) float32
    except Exception as e:
        log(f"Preprocess error: {e}")
        return flask.Response("Invalid image data", status=400)

    # Build V2 request
    payload = {
        "inputs": [{
            "name": "input",            # input tensor name in your ONNX graph
            "shape": list(x.shape),     # [1,28,28,1]
            "datatype": "FP32",
            "data": x.flatten().tolist()
        }]
        # Optionally: "outputs": [{"name": "probabilities"}]
    }

    headers = {"Content-Type": "application/json"}
    token = _read_sa_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        r = requests.post(OVMS_URL, headers=headers, data=json.dumps(payload), timeout=10)
        r.raise_for_status()
        resp = r.json()
    except requests.HTTPError as e:
        log(f"OVMS HTTP error: {e} body={getattr(e.response, 'text', '')}")
        return flask.Response("Model server error", status=502)
    except Exception as e:
        log(f"OVMS request error: {e}")
        return flask.Response("Inference call failed", status=500)

    # Parse V2 response
    outputs = resp.get("outputs", [])
    if not outputs or "data" not in outputs[0]:
        log(f"Malformed OVMS response: {resp}")
        return flask.Response("Malformed model response", status=502)

    probs = outputs[0]["data"]
    if isinstance(probs, list) and len(probs) == 10:
        pred = int(max(range(10), key=lambda i: probs[i]))
    else:
        # Some models return [[...]] or logits; handle simple cases
        flat = probs[0] if (isinstance(probs, list) and probs and isinstance(probs[0], list)) else probs
        pred = int(np.argmax(flat))
        probs = flat

    result = {"predicted": pred}
    return flask.Response(str(pred), mimetype="application/json", status=200)

# Run
if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    log(f"application ready - Debug is {debug}")
    app.run(host="0.0.0.0", port=port, debug=debug)