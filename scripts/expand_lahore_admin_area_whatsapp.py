#!/usr/bin/env python3
"""Lahore admin-area Overpass: all contact mobiles inside the city polygon."""

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

QUERY = """[out:json][timeout:90];
area["name"="Lahore"]["boundary"="administrative"]->.a;
(
  nwr(area.a)["contact:mobile"];
  nwr(area.a)["contact:whatsapp"];
  nwr(area.a)["whatsapp"];
);
out center tags;"""

DROP = re.compile(
    r"ufone|mobilink|e-commerce|mart\b|general store|pet clinic|veterinary|"
    r"paint house|law associate|plastic store|super store|franchise|kfc|"
    r"mcdonald|pizza hut|domino|jalal sons|madni traders",
    re.I,
)


def fetch():
    last = None
    body = QUERY.encode("utf-8")
    for i, endpoint in enumerate(OVERPASS * 2):
        try:
            req = urllib.request.Request(endpoint, data=body, headers={"User-Agent": "UKbrands-lhr-area/1.0"})
            with urllib.request.urlopen(req, timeout=100, context=CTX) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as err:
            last = err
            print("fail", endpoint.split("/")[2], err)
            time.sleep(3 + i)
    raise last


def main():
    os.chdir(ROOT)
    existing = json.load(open("data/pakistan_no_website_leads.json", encoding="utf-8"))
    seen_phones = {l.get("whatsapp_number") for l in existing}
    seen_names = {
        (l.get("city"), re.sub(r"[^a-z0-9\u0600-\u06FF]+", "", (l.get("name") or "").lower()))
        for l in existing
    }
    print("Fetching Lahore administrative-area mobiles...")
    data = fetch()
    els = data.get("elements") or []
    print("elements", len(els))
    candidates = []
    n = 900
    for el in els:
        tags = el.get("tags") or {}
        name = (tags.get("name:en") or tags.get("name") or "").strip()
        if not name or len(name) < 2:
            continue
        if DROP.search(name):
            continue
        if lhr.has_website_or_app(tags):
            continue
        digits = lhr.first_pk_mobile(tags)
        if not digits or digits in seen_phones:
            continue
        cat = lhr.map_category(tags, name)
        if not cat:
            continue
        nkey = ("Lahore", re.sub(r"[^a-z0-9\u0600-\u06FF]+", "", name.lower()))
        if nkey in seen_names:
            continue
        seen_phones.add(digits)
        seen_names.add(nkey)
        lead = lhr.make_lead(cat, name, tags, digits, n)
        lead["source"] = "google_maps_osm_lahore_admin_area"
        candidates.append(lead)
        n += 1
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
                    check = {"is_registered": False, "digits": lead["whatsapp_number"]}
                mark = "LIVE" if check.get("is_registered") else "SKIP"
                print(
                    f"[{done:03d}/{len(candidates):03d}] {mark} {lead['name'][:32]:32} "
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
