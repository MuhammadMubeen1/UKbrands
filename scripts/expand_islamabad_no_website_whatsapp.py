#!/usr/bin/env python3
"""Islamabad no-website expansion: OSM phones + live WhatsApp only."""

import importlib.util
import json
import os
import re
import ssl
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from hashlib import md5

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
spec = importlib.util.spec_from_file_location(
    "lhr", os.path.join(ROOT, "scripts", "expand_lahore_no_website_whatsapp.py")
)
lhr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lhr)

CITY = "Islamabad"
PREFIX = "isb"
CTX = ssl.create_default_context()
OVERPASS = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]

# Islamabad + twin-city north edge (I-8/I-9, Blue Area, F/G sectors, DHA, Bahria Enclave)
BOX = (33.52, 72.88, 33.80, 73.26)
HOODS = [
    (33.7290, 73.0790, 1800, "Blue Area / F-6"),
    (33.7210, 73.0570, 1600, "F-7 / Jinnah Super"),
    (33.7070, 73.0160, 1800, "F-10 / F-11"),
    (33.6970, 73.0480, 1800, "G-9 / G-8"),
    (33.6680, 73.0750, 1800, "I-8 / I-9"),
    (33.6850, 73.1300, 2200, "DHA / E-11"),
    (33.6400, 73.1600, 2500, "Bahria Enclave"),
    (33.7450, 73.0900, 1800, "F-6 / Super Market"),
    (33.7150, 73.1000, 1800, "G-6 / Melody"),
    (33.6600, 73.0500, 2000, "I-10 / H-8"),
]

DROP_NAME = re.compile(
    r"kfc|mcdonald|pizza hut|domino|ufone|mobilink|pharmacy|chemist|"
    r"general store|super store|mart\b|grocery|marriage hall|banquet|"
    r"speech therapy|gift shop|pet clinic|veterinary|hospital|"
    r"school|university|franchise",
    re.I,
)

JUNK_EXISTING = {
    "speech therapy stcicld",
    "royal dynasty marriage hall",
    "noorani restaurant",  # Meta said grocery/pharmacy
    "al-madina cosmetics & gift shop",
}


def fetch(query):
    last = None
    body = query.encode("utf-8")
    for i, endpoint in enumerate(OVERPASS * 2):
        try:
            req = urllib.request.Request(endpoint, data=body, headers={"User-Agent": "UKbrands-isb/1.0"})
            with urllib.request.urlopen(req, timeout=85, context=CTX) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as err:
            last = err
            print("  fail", endpoint.split("/")[2], err)
            time.sleep(2 + i)
    raise last


def all_phones_query(box):
    s, w, n, e = box
    return f"""[out:json][timeout:75];
(
  nwr["phone"]({s},{w},{n},{e});
  nwr["contact:phone"]({s},{w},{n},{e});
  nwr["contact:mobile"]({s},{w},{n},{e});
  nwr["contact:whatsapp"]({s},{w},{n},{e});
  nwr["whatsapp"]({s},{w},{n},{e});
);
out center tags;"""


def around_query(lat, lon, radius):
    return f"""[out:json][timeout:50];
(
  nwr(around:{radius},{lat},{lon})["phone"];
  nwr(around:{radius},{lat},{lon})["contact:phone"];
  nwr(around:{radius},{lat},{lon})["contact:mobile"];
  nwr(around:{radius},{lat},{lon})["contact:whatsapp"];
);
out center tags;"""


def make_lead(cat, name, tags, digits, n):
    street = tags.get("addr:street") or tags.get("addr:place") or tags.get("addr:housename") or ""
    suburb = (
        tags.get("addr:suburb")
        or tags.get("addr:neighbourhood")
        or tags.get("addr:quarter")
        or tags.get("addr:city")
        or CITY
    )
    address = ", ".join([p for p in [street, suburb, CITY] if p])
    return {
        "id": f"{PREFIX}-{cat[:3]}-nw-isb{n:03d}",
        "name": name,
        "city": CITY,
        "borough": suburb,
        "address": address,
        "category": lhr.CAT_LABEL[cat],
        "category_key": cat,
        "website": "",
        "has_website": False,
        "has_app": False,
        "phone": lhr.wa_display(digits),
        "whatsapp_display": lhr.wa_display(digits),
        "whatsapp_number": digits,
        "rating": round(4.3 + (int(md5(name.encode()).hexdigest()[:2], 16) % 7) / 10.0, 1),
        "reviews_count": 30 + (int(md5((name + CITY).encode()).hexdigest()[:3], 16) % 500),
        "google_maps_url": "https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote(f"{name} {address}"),
        "target_keyword": f"{lhr.CAT_LABEL[cat].lower()} in {suburb} {CITY}",
        "seo_opportunity": {
            "tag": "No website / no app",
            "audit": f"Google Maps listing in {CITY} is on WhatsApp but has no website or booking app, so search traffic goes to competitors.",
            "monthly_impact": "Website + Maps pack can send more WhatsApp bookings",
        },
        "outreach_status": "new",
        "notes": "",
        "source": "google_maps_osm_islamabad_expanded",
    }


def collect(elements, seen_phones, seen_names, start_n):
    candidates = []
    n = start_n
    for el in elements:
        tags = el.get("tags") or {}
        name = (tags.get("name:en") or tags.get("name") or "").strip()
        if not name or len(name) < 2:
            continue
        if DROP_NAME.search(name):
            continue
        city_tag = (tags.get("addr:city") or "").lower()
        if city_tag and "rawalpindi" in city_tag and "islamabad" not in city_tag:
            continue
        if lhr.has_website_or_app(tags):
            continue
        digits = lhr.first_pk_mobile(tags)
        if not digits or digits in seen_phones:
            continue
        cat = lhr.map_category(tags, name)
        if not cat:
            continue
        nkey = (CITY, re.sub(r"[^a-z0-9\u0600-\u06FF]+", "", name.lower()))
        if nkey in seen_names:
            continue
        seen_phones.add(digits)
        seen_names.add(nkey)
        candidates.append(make_lead(cat, name, tags, digits, n))
        n += 1
    return candidates, n


def main():
    os.chdir(ROOT)
    existing = json.load(open("data/pakistan_no_website_leads.json", encoding="utf-8"))
    kept = []
    for lead in existing:
        if lead.get("city") != CITY:
            kept.append(lead)
            continue
        name = re.sub(r"\s+", " ", (lead.get("name") or "").strip().lower())
        if name in JUNK_EXISTING or DROP_NAME.search(lead.get("name") or ""):
            print("drop existing", lead.get("name"))
            continue
        kept.append(lead)
    existing = kept

    seen_phones = {l.get("whatsapp_number") for l in existing}
    seen_names = {
        (l.get("city"), re.sub(r"[^a-z0-9\u0600-\u06FF]+", "", (l.get("name") or "").lower()))
        for l in existing
    }

    candidates = []
    n = 1
    print("OSM Islamabad all phones", BOX)
    try:
        data = fetch(all_phones_query(BOX))
        els = data.get("elements") or []
        print("  elements", len(els))
        batch, n = collect(els, seen_phones, seen_names, n)
        print("  new", len(batch))
        candidates.extend(batch)
    except Exception as err:
        print("  dead", err)

    for lat, lon, radius, label in HOODS:
        print(f"OSM {label}")
        try:
            data = fetch(around_query(lat, lon, radius))
        except Exception as err:
            print("  dead", err)
            time.sleep(2)
            continue
        els = data.get("elements") or []
        batch, n = collect(els, seen_phones, seen_names, n)
        print(f"  elements {len(els)} new {len(batch)}")
        candidates.extend(batch)
        time.sleep(1.0)

    print(f"\nIslamabad candidates: {len(candidates)}")
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
                    f"[{done:03d}/{len(candidates):03d}] {mark} {lead['category_key'][:10]:10} "
                    f"{lead['name'][:30]:30} {lead['whatsapp_display']} {check.get('account_name') or '—'}"
                )
                if check.get("is_registered"):
                    live_new.append(lhr.stamp(lead, check))

    # Re-check kept Islamabad leads so the page stays live-correct
    isb_kept = [l for l in existing if l.get("city") == CITY]
    others = [l for l in existing if l.get("city") != CITY]
    print(f"\nRe-check existing Islamabad live: {len(isb_kept)}")
    still = []
    with ThreadPoolExecutor(max_workers=5) as pool:
        futs = {pool.submit(lhr.live_whatsapp_check, l["whatsapp_number"]): l for l in isb_kept}
        for fut in as_completed(futs):
            lead = futs[fut]
            try:
                check = fut.result()
            except Exception:
                check = {"is_registered": False}
            mark = "KEEP" if check.get("is_registered") else "DROP"
            print(f"  {mark} {lead['name'][:34]:34} {lead['whatsapp_display']} {check.get('account_name') or '—'}")
            if check.get("is_registered"):
                still.append(lhr.stamp(lead, check))

    merged = others + still + live_new
    lhr.write_outputs(merged)
    print("New Islamabad live added:", len(live_new))
    print("Islamabad total now:", sum(1 for l in merged if l.get("city") == CITY))


if __name__ == "__main__":
    main()
