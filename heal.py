import datetime, time
import requests
from common import (GEOSTORE_URL, ID_FIELD, agol_token, canonical,
                    fetch_features, load_links, notify, post_geostore,
                    save_links)

def now():
    return datetime.datetime.now(datetime.timezone(
        datetime.timedelta(hours=7))).isoformat(timespec="seconds")

def main():
    data = load_links()
    dead, healed = [], []
    geoms = None                                    # chỉ query AGOL khi cần

    for p in data["plots"]:
        r = requests.get(f"{GEOSTORE_URL}/{p['geostore_id']}", timeout=60)
        time.sleep(0.25)                            # ~10 phut cho 2300 lo
        p["last_checked"] = now()
        if r.status_code == 200:
            if p["status"] != "alive":
                p["status"] = "alive"
            continue

        # Geostore bị xóa → hồi sinh bằng cách POST lại đúng GeoJSON từ AGOL
        if geoms is None:
            feats = fetch_features(agol_token())
            geoms = {str(f["properties"][ID_FIELD]): canonical(f["geometry"])
                     for f in feats}
        cg = geoms.get(p["id_lo"])
        if cg is None:
            p["status"] = "dead"
            dead.append(f"{p['id_lo']}: khong con tren AGOL")
            continue
        new_id = post_geostore(cg)
        time.sleep(0.3)
        if new_id == p["geostore_id"]:
            p["status"] = "healed"                  # URL không đổi, đã sống lại
            healed.append(p["id_lo"])
        else:                                       # determinism vỡ hoặc ranh đổi
            p["status"] = "dead"
            dead.append(f"{p['id_lo']}: ID moi khac ID cu ({new_id})")

    data["generated_at"] = now()
    save_links(data)
    if healed:
        notify(f"HEAL: hoi sinh {len(healed)} link: " + ", ".join(healed[:30]))
    if dead:
        notify("HEAL CANH BAO — can xu ly tay:\n" + "\n".join(dead[:30]))

if __name__ == "__main__":
    main()
