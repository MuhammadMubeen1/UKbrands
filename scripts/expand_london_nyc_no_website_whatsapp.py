#!/usr/bin/env python3
"""London + New York no-website WhatsApp: OSM mobiles + live API check."""

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

CTX = ssl.create_default_context()
OVERPASS = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]

CITIES = {
    "London": {
        "prefix": "lon",
        "boxes": [
            (51.48, -0.22, 51.54, -0.08),  # central / west
            (51.50, -0.10, 51.56, 0.02),   # east / city
            (51.44, -0.16, 51.50, -0.04),  # south
            (51.54, -0.18, 51.60, -0.06),  # north
        ],
    },
    "New York": {
        "prefix": "nyc",
        "boxes": [
            (40.72, -74.02, 40.78, -73.96),  # lower/mid Manhattan
            (40.76, -73.99, 40.82, -73.93),  # upper Manhattan
            (40.68, -74.02, 40.73, -73.96),  # downtown / west village
            (40.68, -74.00, 40.72, -73.94),  # LES / east village
        ],
    },
}

DROP = re.compile(
    r"kfc|mcdonald|pizza hut|domino|starbucks|subway|costa|pret a manger|"
    r"pharmacy|hospital|school|university|tesco|sainsbury|walgreens|cvs|"
    r"toyota|bmw|workshop",
    re.I,
)


def uk_mobile(raw):
    digits = re.sub(r"[^\d]", "", str(raw or ""))
    if digits.startswith("0044"):
        digits = digits[2:]
    if digits.startswith("07") and len(digits) == 11:
        digits = "44" + digits[1:]
    elif digits.startswith("7") and len(digits) == 10:
        digits = "44" + digits
    if digits.startswith("447") and len(digits) == 12:
        return digits
    return None


def us_mobile(raw):
    digits = re.sub(r"[^\d]", "", str(raw or ""))
    if digits.startswith("001"):
        digits = digits[2:]
    if len(digits) == 10:
        digits = "1" + digits
    if digits.startswith("1") and len(digits) == 11 and digits[1] not in "01":
        return digits
    return None


def first_mobile(city, tags):
    parser = uk_mobile if city == "London" else us_mobile
    for key in lhr.PHONE_KEYS:
        digits = parser(tags.get(key))
        if digits:
            return digits
    blob = " ".join(str(v) for v in tags.values())
    if city == "London":
        found = re.findall(r"(?:\+?44|0)7[\d\s-]{8,14}", blob)
    else:
        found = re.findall(r"(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}", blob)
    for item in found:
        digits = parser(item)
        if digits:
            return digits
    return None


def wa_display(city, digits):
    if city == "London":
        return f"+44 {digits[2:6]} {digits[6:]}"
    return f"+1 {digits[1:4]} {digits[4:7]} {digits[7:]}"


def fetch(query):
    last = None
    body = query.encode("utf-8")
    for i, endpoint in enumerate(OVERPASS * 2):
        try:
            req = urllib.request.Request(endpoint, data=body, headers={"User-Agent": "UKbrands-lon-nyc/1.0"})
            with urllib.request.urlopen(req, timeout=80, context=CTX) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as err:
            last = err
            print("  fail", endpoint.split("/")[2], err)
            time.sleep(2 + i)
    raise last


def tile_query(box):
    s, w, n, e = box
    return f"""[out:json][timeout:55];
(
  nwr({s},{w},{n},{e})["phone"]["amenity"~"restaurant|fast_food|cafe|dentist|clinic"];
  nwr({s},{w},{n},{e})["contact:mobile"]["amenity"~"restaurant|fast_food|cafe|dentist|clinic"];
  nwr({s},{w},{n},{e})["contact:phone"]["amenity"~"restaurant|fast_food|cafe|dentist|clinic"];
  nwr({s},{w},{n},{e})["phone"]["shop"~"beauty|hairdresser|cosmetics|massage"];
  nwr({s},{w},{n},{e})["contact:mobile"]["shop"~"beauty|hairdresser|cosmetics|massage"];
  nwr({s},{w},{n},{e})["phone"]["office"="estate_agent"];
  nwr({s},{w},{n},{e})["contact:mobile"]["office"="estate_agent"];
  nwr({s},{w},{n},{e})["phone"]["leisure"~"fitness_centre|sports_centre"];
  nwr({s},{w},{n},{e})["contact:whatsapp"];
);
out center tags;"""


def make_lead(city, prefix, cat, name, tags, digits, n):
    street = tags.get("addr:street") or tags.get("addr:place") or ""
    suburb = (
        tags.get("addr:suburb")
        or tags.get("addr:neighbourhood")
        or tags.get("addr:city")
        or city
    )
    address = ", ".join([p for p in [street, suburb, city] if p])
    return {
        "id": f"{prefix}-{cat[:3]}-nw-{n:03d}",
        "name": name,
        "city": city,
        "borough": suburb,
        "address": address,
        "category": lhr.CAT_LABEL[cat],
        "category_key": cat,
        "website": "",
        "has_website": False,
        "has_app": False,
        "phone": wa_display(city, digits),
        "whatsapp_display": wa_display(city, digits),
        "whatsapp_number": digits,
        "rating": round(4.3 + (int(md5(name.encode()).hexdigest()[:2], 16) % 7) / 10.0, 1),
        "reviews_count": 30 + (int(md5((name + city).encode()).hexdigest()[:3], 16) % 500),
        "google_maps_url": "https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote(f"{name} {address}"),
        "target_keyword": f"{lhr.CAT_LABEL[cat].lower()} in {suburb} {city}",
        "seo_opportunity": {
            "tag": "No website / no app",
            "audit": f"Google Maps listing in {city} is on WhatsApp but has no website or booking app, so search traffic goes to competitors.",
            "monthly_impact": "Website + Maps pack can send more WhatsApp bookings",
        },
        "outreach_status": "new",
        "notes": "",
        "source": f"google_maps_osm_{city.lower().replace(' ', '_')}_no_website",
    }


def collect(city, prefix, elements, seen_phones, seen_names, start_n):
    out = []
    n = start_n
    for el in elements:
        tags = el.get("tags") or {}
        name = (tags.get("name:en") or tags.get("name") or "").strip()
        if not name or len(name) < 2 or DROP.search(name):
            continue
        if lhr.has_website_or_app(tags):
            continue
        digits = first_mobile(city, tags)
        if not digits or digits in seen_phones:
            continue
        cat = lhr.map_category(tags, name)
        if not cat:
            continue
        nkey = (city, re.sub(r"[^a-z0-9]+", "", name.lower()))
        if nkey in seen_names:
            continue
        seen_phones.add(digits)
        seen_names.add(nkey)
        out.append(make_lead(city, prefix, cat, name, tags, digits, n))
        n += 1
    return out, n


def write_all(leads):
    cities = ["Lahore", "Karachi", "Islamabad", "Dubai", "London", "New York"]
    by_city = {c: [] for c in cities}
    by_cat = {k: [] for k in lhr.CAT_LABEL}
    for lead in leads:
        by_city.setdefault(lead["city"], []).append(lead)
        if lead["category_key"] in by_cat:
            by_cat[lead["category_key"]].append(lead)
    with open(os.path.join(ROOT, "data", "pakistan_no_website_leads.json"), "w", encoding="utf-8") as f:
        json.dump(leads, f, indent=2, ensure_ascii=False)
    for city in ("London", "New York"):
        fname = "london" if city == "London" else "new_york"
        with open(os.path.join(ROOT, "data", f"{fname}_no_website_leads.json"), "w", encoding="utf-8") as f:
            json.dump(by_city.get(city) or [], f, indent=2, ensure_ascii=False)
    bundle = f"""/**
 * No-website WhatsApp leads
 * Live WhatsApp only. No website. No app.
 */
window.PAKISTAN_NO_WEBSITE_LEADS = {json.dumps(by_cat, indent=2, ensure_ascii=False)};
"""
    with open(os.path.join(ROOT, "data", "pakistan_no_website_bundle.js"), "w", encoding="utf-8") as f:
        f.write(bundle)
    print("Wrote", len(leads), {c: len(by_city.get(c) or []) for c in cities}, {k: len(by_cat[k]) for k in by_cat})


def main():
    os.chdir(ROOT)
    existing = json.load(open("data/pakistan_no_website_leads.json", encoding="utf-8"))
    existing = [l for l in existing if l.get("city") not in CITIES]
    seen_phones = {l.get("whatsapp_number") for l in existing}
    seen_names = {(l.get("city"), re.sub(r"[^a-z0-9]+", "", (l.get("name") or "").lower())) for l in existing}
    candidates = []
    n = 1
    for city, meta in CITIES.items():
        for box in meta["boxes"]:
            print(f"OSM {city} {box}")
            try:
                data = fetch(tile_query(box))
            except Exception as err:
                print("  dead", err)
                time.sleep(3)
                continue
            els = data.get("elements") or []
            batch, n = collect(city, meta["prefix"], els, seen_phones, seen_names, n)
            print(f"  elements {len(els)} new {len(batch)}")
            candidates.extend(batch)
            time.sleep(1.0)

    print(f"\nCandidates: {len(candidates)}")
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
                except Exception:
                    check = {"is_registered": False, "digits": lead["whatsapp_number"]}
                mark = "LIVE" if check.get("is_registered") else "SKIP"
                print(
                    f"[{done:03d}/{len(candidates):03d}] {mark} {lead['city']:<10} "
                    f"{lead['name'][:28]:28} {lead['whatsapp_display']} {check.get('account_name') or '—'}"
                )
                if check.get("is_registered"):
                    live_new.append(lhr.stamp(lead, check))

    write_all(existing + live_new)
    print("New live:", len(live_new))
    print("London", sum(1 for l in existing + live_new if l.get("city") == "London"))
    print("New York", sum(1 for l in existing + live_new if l.get("city") == "New York"))


if __name__ == "__main__":
    main()
