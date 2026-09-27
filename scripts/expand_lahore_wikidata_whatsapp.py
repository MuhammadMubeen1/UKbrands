#!/usr/bin/env python3
"""Lahore no-website leads from Wikidata phones + live WhatsApp API."""

import importlib.util
import json
import os
import re
import ssl
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
spec = importlib.util.spec_from_file_location(
    "lhr", os.path.join(ROOT, "scripts", "expand_lahore_no_website_whatsapp.py")
)
lhr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lhr)

CTX = ssl.create_default_context()
SPARQL = "https://query.wikidata.org/sparql"

QUERY = """
SELECT ?item ?itemLabel ?phone ?website ?typeLabel ?addr WHERE {
  VALUES ?place { wd:Q11739 wd:Q2093 }
  ?item wdt:P131 ?place .
  ?item wdt:P1329 ?phone .
  OPTIONAL { ?item wdt:P856 ?website . }
  OPTIONAL { ?item wdt:P31 ?type . }
  OPTIONAL { ?item wdt:P6375 ?addr . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en,ur". }
}
"""

DROP_NAME = {
    "madni traders",
    "jalal sons",
    "kfc",
    "raheem medical store",
}

TYPE_TO_CAT = (
    (("dental", "dentist"), "dentists"),
    (("estate", "real estate", "realtor", "property"), "estate_agents"),
    (("gym", "fitness", "sports club"), "fitness"),
    (("aesthetic", "dermatolog", "skin", "beauty salon", "hairdress", "spa", "barber"), "salons"),
    (("restaurant", "cafe", "fast food", "bakery", "eatery", "dhaba"), "restaurants"),
    (("clinic", "hospital"), "aesthetic"),
)


def sparql():
    url = SPARQL + "?" + urllib.parse.urlencode({"query": QUERY, "format": "json"})
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "UKbrands-lhr-wikidata/1.0", "Accept": "application/sparql-results+json"},
    )
    with urllib.request.urlopen(req, timeout=90, context=CTX) as resp:
        return json.loads(resp.read().decode("utf-8"))


def map_type(name, type_label):
    blob = f"{name} {type_label}".lower()
    if any(w in blob for w in ("pharmacy", "supermarket", "grocery", "bank", "school", "university", "mosque", "hospital", "government")):
        if "clinic" not in blob and "dental" not in blob:
            return None
    for keys, cat in TYPE_TO_CAT:
        if any(k in blob for k in keys):
            return cat
    return None


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

    print("Wikidata SPARQL Lahore phones...")
    data = sparql()
    rows = data.get("results", {}).get("bindings", [])
    print("rows", len(rows))

    candidates = []
    n = 400
    for row in rows:
        name = (row.get("itemLabel") or {}).get("value") or ""
        if not name or name.startswith("Q") and name[1:].isdigit():
            continue
        website = (row.get("website") or {}).get("value") or ""
        if website and not any(h in website.lower() for h in ("facebook.com", "instagram.com", "tiktok.com")):
            continue
        digits = lhr.pk_mobile((row.get("phone") or {}).get("value"))
        if not digits or digits in seen_phones:
            continue
        typ = (row.get("typeLabel") or {}).get("value") or ""
        cat = map_type(name, typ)
        if not cat:
            continue
        nkey = ("Lahore", re.sub(r"[^a-z0-9\u0600-\u06FF]+", "", name.lower()))
        if nkey in seen_names:
            continue
        tags = {"addr:street": (row.get("addr") or {}).get("value") or "", "addr:city": "Lahore"}
        seen_phones.add(digits)
        seen_names.add(nkey)
        lead = lhr.make_lead(cat, name, tags, digits, n)
        lead["source"] = "wikidata_lahore_no_website"
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
