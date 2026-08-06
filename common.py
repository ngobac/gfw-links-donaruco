import hashlib, json, os, sys, time
import requests

GEOSTORE_URL = "https://production-api.globalforestwatch.org/v1/geostore"
ID_FIELD = "IDlomoi"
LINKS_PATH = "docs/links.json"

def agol_token():
    r = requests.post("https://www.arcgis.com/sharing/rest/generateToken", data={
        "username": os.environ["AGOL_USERNAME"],
        "password": os.environ["AGOL_PASSWORD"],
        "referer": "https://www.arcgis.com",
        "f": "json", "expiration": 120}, timeout=60)
    j = r.json()
    if "token" not in j:
        sys.exit(f"Loi lay token AGOL: {j}")
    return j["token"]

def fetch_features(token, where="1=1"):
    """Query toàn bộ lô từ Feature Layer, phân trang 1000 record/lần."""
    url = os.environ["AGOL_LAYER_URL"] + "/query"
    feats, offset = [], 0
    while True:
        r = requests.get(url, params={
            "where": where, "outFields": ID_FIELD, "returnGeometry": "true",
            "outSR": 4326, "f": "geojson",
            "resultOffset": offset, "resultRecordCount": 1000,
            "token": token}, timeout=120)
        batch = r.json().get("features", [])
        feats += batch
        if len(batch) < 1000:
            return feats
        offset += 1000

def canonical(geom):
    """Làm tròn 6 số lẻ + serialize ổn định để hash không nhảy vì jitter."""
    def rnd(c):
        if isinstance(c[0], (int, float)):
            return [round(c[0], 6), round(c[1], 6)]
        return [rnd(x) for x in c]
    g = {"type": geom["type"], "coordinates": rnd(geom["coordinates"])}
    return g

def geom_hash(canon_geom):
    s = json.dumps(canon_geom, sort_keys=True, separators=(",", ":"))
    return hashlib.md5(s.encode()).hexdigest()

def post_geostore(canon_geom):
    body = {"geojson": {"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {}, "geometry": canon_geom}]}}
    r = requests.post(GEOSTORE_URL, json=body, timeout=60)
    r.raise_for_status()
    return r.json()["data"]["id"]

def build_url(geostore_id, template):
    return (f"https://www.globalforestwatch.org/map/geostore/"
            f"{geostore_id}/?{template}")

def load_links():
    if os.path.exists(LINKS_PATH):
        with open(LINKS_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {"generated_at": None, "count": 0, "plots": []}

def save_links(data):
    os.makedirs("docs", exist_ok=True)
    with open(LINKS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)

def notify(msg):
    tok = os.environ.get("TELEGRAM_BOT_TOKEN")
    cid = os.environ.get("TELEGRAM_CHAT_ID")
    if not tok or not cid:
        print("[notify]", msg)
        return
    requests.post(f"https://api.telegram.org/bot{tok}/sendMessage",
                  json={"chat_id": cid, "text": msg[:4000]}, timeout=30)
