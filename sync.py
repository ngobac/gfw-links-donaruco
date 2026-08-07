import datetime, os, time
from common import (agol_token, build_url, canonical, choose_features,
                    fetch_features, get_id, geom_hash, load_links, notify,
                    post_geostore, save_links)

TEMPLATE = open("map_template.txt", encoding="utf-8").read().strip()
WHERE = os.environ.get("WHERE_CLAUSE", "1=1")   # pilot: "IDlomoi IN ('LT01',...)"

def now():
    return datetime.datetime.now(datetime.timezone(
        datetime.timedelta(hours=7))).isoformat(timespec="seconds")

def main():
    data = load_links()
    old = {p["id_lo"]: p for p in data["plots"]}
    feats = fetch_features(agol_token(), WHERE)
    print(f"AGOL tra ve {len(feats)} ban ghi")
    feats, dup_warns = choose_features(feats)
    print(f"Con {len(feats)} lo sau khi gop trung lap")

    plots, changes = [], list(dup_warns)
    for f in feats:
        id_lo = get_id(f["properties"])
        cg = canonical(f["geometry"])
        h = geom_hash(cg)
        rec = old.get(id_lo)

        if rec and rec["geom_hash"] == h:          # không đổi
            plots.append(rec)
            continue

        gid = post_geostore(cg)                     # lô mới hoặc đổi ranh
        time.sleep(0.3)
        plots.append({
            "id_lo": id_lo,
            "long_url": build_url(gid, TEMPLATE),
            "geostore_id": gid,
            "geom_hash": h,
            "status": "alive",
            "last_checked": now(),
            "geom_updated_at": now(),
        })
        changes.append(f"{'DOI RANH' if rec else 'LO MOI'}: {id_lo}")

    removed = set(old) - {p["id_lo"] for p in plots}
    for r_ in removed:
        changes.append(f"LO BI XOA khoi AGOL: {r_}")

    data.update({"generated_at": now(), "count": len(plots), "plots": plots})
    save_links(data)

    if changes:
        notify("SYNC GFW co bien dong:\n" + "\n".join(changes[:50]))
    print(f"Xong. {len(changes)} bien dong.")

if __name__ == "__main__":
    main()
