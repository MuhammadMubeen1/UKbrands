#!/usr/bin/env python3
"""Dense Lahore neighborhood Overpass (all phones) + live WhatsApp."""

import importlib.util
import json
import os
import re
import ssl
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
spec = importlib.util.spec_from_file_location(
    "lhr", os.path.join(ROOT, "scripts", "expand_lahore_no_website_whatsapp.py")
)
lhr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lhr)

CTX = ssl.create_default_context()
OVERPASS = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]

# lat, lon, radius_m, label
HOODS = [
    (31.5204, 74.3510, 2800, "Gulberg"),
    (31.5108, 74.3280, 2200, "MM Alam / Garden Town"),
    (31.4697, 74.4130, 3200, "DHA"),
    (31.4692, 74.2728, 2800, "Johar Town"),
    (31.4820, 74.3230, 2200, "Model Town"),
    (31.5100, 74.2700, 2800, "Iqbal Town"),
    (31.5650, 74.3460, 2500, "Mall / Cantt"),
    (31.5490, 74.3060, 2200, "Data Darbar / Old City"),
    (31.4500, 74.3100, 2500, "Faisal Town / Township"),
    (31.4010, 74.2150, 3500, "Bahria Town"),
    (31.5320, 74.3800, 2500, "Cavalry / Walton"),
    (31.4950, 74.2400, 2500, "Sabzazar / Allama Iqbal"),
    (31.5800, 74.3050, 2200, "Shalimar / Baghbanpura"),
    (31.4300, 74.3600, 2500, "Valencia / Defence"),
]

DROP_NAME = {
    "madni traders",
    "jalal sons",
    "kfc",
    "raheem medical store",
}


def fetch(query):
    last = None
    body = query.encode("utf-8")
    for i, endpoint in enumerate(OVERPASS * 2):
        try:
            req = urllib.request.Request(endpoint, data=body, headers={"User-Agent": "UKbrands-lhr-hoods/1.0"})
            with urllib.request.urlopen(req, timeout=80, context=CTX) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as err:
            last = err
            print("  fail", endpoint.split("/")[2], err)
            time.sleep(2 + i)
    raise last


def hood_query(lat, lon, radius):
    return f"""[out:json][timeout:50];
(
  nwr(around:{radius},{lat},{lon})["phone"];
  nwr(around:{radius},{lat},{lon})["contact:phone"];
  nwr(around:{radius},{lat},{lon})["contact:mobile"];
  nwr(around:{radius},{lat},{lon})["contact:whatsapp"];
);
out center tags;"""


def main():
    os.chdir(ROOT)
    existing = json.load(open("data/pakistan_no_website_leads.json", encoding="utf-8"))
    existing = [
        l
        for l in existing
        if re.sub(r"\s+", " ", (l.get("name") or "").strip().lower()) not in DROP_NAME
    ]
    seen_phones = {l.get("whatsapp_number") for l in existing}
    seen_names = {
        (l.get("city"), re.sub(r"[^a-z0-9\u0600-\u06FF]+", "", (l.get("name") or "").lower()))
        for l in existing
    }
    candidates = []
    n = 500
    for lat, lon, radius, label in HOODS:
        print(f"OSM {label} around {lat},{lon} r={radius}")
        try:
            data = fetch(hood_query(lat, lon, radius))
        except Exception as err:
            print("  dead", err)
            time.sleep(3)
            continue
        els = data.get("elements") or []
        batch, n = lhr.collect_from_elements(els, seen_phones, seen_names, n)
        print(f"  elements {len(els)} new {len(batch)}")
        candidates.extend(batch)
        time.sleep(1.1)

    print(f"\nNeighborhood candidates: {len(candidates)}")
    live_new = []
    if candidates:
        with ThreadPoolExecutor(max_workers=6) as pool:
            futs = {pool.submit(lhr.live_whatsapp_check, c["whatsapp_number"]): c for c in candidates}
            done = 0
            for fut in as_completed(futs):
                lead = futs[fut]
                done += 1
                try:
                    check = fut.result()
                except Exception as err:
                    check = {"is_registered": False, "digits": lead["whatsapp_number"], "account_name": None}
                mark = "LIVE" if check.get("is_registered") else "SKIP"
                print(
                    f"[{done:03d}/{len(candidates):03d}] {mark} {lead['name'][:34]:34} "
                    f"{lead['whatsapp_display']} {check.get('account_name') or '—'}"
                )
                if check.get("is_registered"):
                    live_new.append(lhr.stamp(lead, check))

    merged = existing + live_new
    lhr.write_outputs(merged)
    print("New Lahore live added:", len(live_new))
    print("Lahore total now:", sum(1 for l in merged if l.get("city") == "Lahore"))


if __name__ == "__main__":
    main()
