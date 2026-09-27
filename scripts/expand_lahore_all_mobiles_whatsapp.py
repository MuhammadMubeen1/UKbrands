#!/usr/bin/env python3
"""Live-check every Lahore OSM Pakistani mobile with no real website."""

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
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter",
]

QUERY = """[out:json][timeout:80];
(
  nwr["phone"](31.32,74.12,31.68,74.52);
  nwr["contact:phone"](31.32,74.12,31.68,74.52);
  nwr["contact:mobile"](31.32,74.12,31.68,74.52);
  nwr["contact:whatsapp"](31.32,74.12,31.68,74.52);
  nwr["whatsapp"](31.32,74.12,31.68,74.52);
);
out center tags;"""

DROP = {
    "madni traders",
    "jalal sons",
    "kfc",
    "raheem medical store",
    "mcdonald",
    "pizza hut",
    "domino",
}


def loose_category(tags, name):
    cat = lhr.map_category(tags, name)
    if cat:
        return cat
    amenity = (tags.get("amenity") or "").lower()
    shop = (tags.get("shop") or "").lower()
    office = (tags.get("office") or "").lower()
    leisure = (tags.get("leisure") or "").lower()
    health = (tags.get("healthcare") or "").lower()
    blob = f"{name} {amenity} {shop} {office} {leisure} {health}".lower()
    if any(w in blob for w in ("dental", "dentist", "orthodont")):
        return "dentists"
    if office or any(w in blob for w in ("estate", "property", "realtor", "plot", "builder", "housing")):
        return "estate_agents"
    if leisure or any(w in blob for w in ("gym", "fitness", "yoga")):
        return "fitness"
    if amenity in ("clinic", "doctors", "hospital") or health or any(w in blob for w in ("clinic", "dr ", "doctor", "hijama", "skin")):
        return "aesthetic"
    if shop in ("beauty", "hairdresser", "cosmetics", "massage", "chemist") or any(
        w in blob for w in ("salon", "parlour", "parlor", "spa", "makeup", "barber")
    ):
        return "salons"
    if amenity in ("restaurant", "fast_food", "cafe", "food_court", "ice_cream", "bar", "pub") or shop in (
        "bakery", "pastry", "coffee", "confectionery", "convenience"
    ):
        return "restaurants"
    return None


def fetch():
    last = None
    body = QUERY.encode("utf-8")
    for i, endpoint in enumerate(OVERPASS * 2):
        try:
            req = urllib.request.Request(endpoint, data=body, headers={"User-Agent": "UKbrands-lhr-all/1.0"})
            with urllib.request.urlopen(req, timeout=95, context=CTX) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as err:
            last = err
            print("fail", endpoint.split("/")[2], err)
            time.sleep(2 + i)
    raise last


def main():
    os.chdir(ROOT)
    existing = json.load(open("data/pakistan_no_website_leads.json", encoding="utf-8"))
    existing = [
        l for l in existing if re.sub(r"\s+", " ", (l.get("name") or "").strip().lower()) not in DROP
    ]
    seen_phones = {l.get("whatsapp_number") for l in existing}
    seen_names = {
        (l.get("city"), re.sub(r"[^a-z0-9\u0600-\u06FF]+", "", (l.get("name") or "").lower()))
        for l in existing
    }

    print("Fetching all Lahore OSM phones...")
    data = fetch()
    els = data.get("elements") or []
    print("elements", len(els))

    candidates = []
    n = 800
    skipped = {"no_name": 0, "has_site": 0, "no_mobile": 0, "dup": 0, "no_cat": 0, "drop": 0}
    for el in els:
        tags = el.get("tags") or {}
        name = (tags.get("name:en") or tags.get("name") or "").strip()
        if not name or len(name) < 2:
            skipped["no_name"] += 1
            continue
        if re.sub(r"\s+", " ", name.lower()) in DROP:
            skipped["drop"] += 1
            continue
        if lhr.has_website_or_app(tags):
            skipped["has_site"] += 1
            continue
        digits = lhr.first_pk_mobile(tags)
        if not digits:
            skipped["no_mobile"] += 1
            continue
        if digits in seen_phones:
            skipped["dup"] += 1
            continue
        cat = loose_category(tags, name)
        if not cat:
            skipped["no_cat"] += 1
            continue
        nkey = ("Lahore", re.sub(r"[^a-z0-9\u0600-\u06FF]+", "", name.lower()))
        if nkey in seen_names:
            skipped["dup"] += 1
            continue
        seen_phones.add(digits)
        seen_names.add(nkey)
        lead = lhr.make_lead(cat, name, tags, digits, n)
        lead["source"] = "google_maps_osm_lahore_all_mobiles"
        candidates.append(lead)
        n += 1

    print("skip", skipped)
    print("new candidates", len(candidates))

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
                    f"[{done:03d}/{len(candidates):03d}] {mark} {lead['category_key'][:8]:8} "
                    f"{lead['name'][:30]:30} {lead['whatsapp_display']} {check.get('account_name') or '—'}"
                )
                if check.get("is_registered"):
                    live_new.append(lhr.stamp(lead, check))

    merged = existing + live_new
    lhr.write_outputs(merged)
    print("New Lahore live added:", len(live_new))
    print("Lahore total now:", sum(1 for l in merged if l.get("city") == "Lahore"))


if __name__ == "__main__":
    main()
