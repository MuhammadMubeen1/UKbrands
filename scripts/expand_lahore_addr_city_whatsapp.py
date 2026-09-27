#!/usr/bin/env python3
"""Second Lahore pass: every OSM listing tagged addr:city=Lahore with a phone."""

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
(
  nwr["addr:city"="Lahore"]["phone"];
  nwr["addr:city"="Lahore"]["contact:phone"];
  nwr["addr:city"="Lahore"]["contact:mobile"];
  nwr["addr:city"="Lahore"]["contact:whatsapp"];
  nwr["addr:city"="lahore"]["phone"];
  nwr["addr:city"="lahore"]["contact:mobile"];
  nwr["addr:city:en"="Lahore"]["phone"];
  nwr["addr:city:en"="Lahore"]["contact:mobile"];
);
out center tags;"""

DROP_NAME = {
    "madni traders",
    "jalal sons",
    "jalal sons paragon city",
    "raheem medical store",
    "kfc",
}


def fetch():
    last = None
    body = QUERY.encode("utf-8")
    for i, endpoint in enumerate(OVERPASS * 2):
        try:
            req = urllib.request.Request(endpoint, data=body, headers={"User-Agent": "UKbrands-lhr-addr/1.0"})
            with urllib.request.urlopen(req, timeout=95, context=CTX) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as err:
            last = err
            print("fail", endpoint, err)
            time.sleep(2 + i)
    raise last


def main():
    os.chdir(ROOT)
    existing = json.load(open("data/pakistan_no_website_leads.json", encoding="utf-8"))
    cleaned = []
    for lead in existing:
        name = re.sub(r"\s+", " ", (lead.get("name") or "").strip().lower())
        if name in DROP_NAME:
            print("drop junk", lead.get("name"))
            continue
        cleaned.append(lead)
    existing = cleaned

    seen_phones = {l.get("whatsapp_number") for l in existing}
    seen_names = {
        (l.get("city"), re.sub(r"[^a-z0-9\u0600-\u06FF]+", "", (l.get("name") or "").lower()))
        for l in existing
    }

    print("Fetching addr:city=Lahore phones...")
    data = fetch()
    els = data.get("elements") or []
    print("elements", len(els))
    candidates, _n = lhr.collect_from_elements(els, seen_phones, seen_names, 200)
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
