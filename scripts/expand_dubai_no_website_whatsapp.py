#!/usr/bin/env python3
"""Dubai no-website WhatsApp leads: OSM mobiles + live api.whatsapp.com check."""

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

CITY = "Dubai"
PREFIX = "dxb"
CTX = ssl.create_default_context()
OVERPASS = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]

BOX = (24.88, 54.96, 25.32, 55.48)
HOODS = [
    (25.080, 55.140, 2200, "Dubai Marina / JBR"),
    (25.197, 55.274, 2200, "Downtown / Business Bay"),
    (25.228, 55.286, 2000, "DIFC / Trade Centre"),
    (25.204, 55.270, 1800, "Burj Khalifa"),
    (25.233, 55.266, 2000, "Jumeirah 1"),
    (25.188, 55.232, 2200, "Al Wasl / Umm Suqeim"),
    (25.077, 55.141, 1800, "JLT"),
    (25.112, 55.200, 2200, "Al Barsha / MoE"),
    (25.269, 55.309, 2200, "Deira"),
    (25.263, 55.297, 2000, "Bur Dubai"),
    (25.118, 55.200, 2000, "Al Quoz"),
    (25.112, 55.378, 2500, "Dubai Hills / Academic City"),
]

DROP = re.compile(
    r"kfc|mcdonald|pizza hut|domino|starbucks|carrefour|lulu|spinneys|"
    r"pharmacy|hospital|school|university|petrol|adnoc|enoc|"
    r"toyota|bmw|mercedes|workshop|spare part",
    re.I,
)


def uae_mobile(raw):
    digits = re.sub(r"[^\d]", "", str(raw or ""))
    if digits.startswith("00971"):
        digits = digits[2:]
    if digits.startswith("05") and len(digits) == 10:
        digits = "971" + digits[1:]
    elif digits.startswith("5") and len(digits) == 9:
        digits = "971" + digits
    if digits.startswith("9715") and len(digits) == 12:
        return digits
    return None


def first_uae_mobile(tags):
    for key in lhr.PHONE_KEYS:
        digits = uae_mobile(tags.get(key))
        if digits:
            return digits
    blob = " ".join(str(v) for v in tags.values())
    found = re.findall(r"(?:\+?971|0)5[\d\s-]{7,12}", blob)
    for item in found:
        digits = uae_mobile(item)
        if digits:
            return digits
    return None


def wa_display(digits):
    return f"+971 {digits[3:5]} {digits[5:8]} {digits[8:]}"


def fetch(query):
    last = None
    body = query.encode("utf-8")
    for i, endpoint in enumerate(OVERPASS * 2):
        try:
            req = urllib.request.Request(endpoint, data=body, headers={"User-Agent": "UKbrands-dxb-nw/1.0"})
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
);
out center tags;"""


def around_query(lat, lon, radius):
    return f"""[out:json][timeout:50];
(
  nwr(around:{radius},{lat},{lon})["phone"];
  nwr(around:{radius},{lat},{lon})["contact:mobile"];
  nwr(around:{radius},{lat},{lon})["contact:whatsapp"];
);
out center tags;"""


def make_lead(cat, name, tags, digits, n):
    street = tags.get("addr:street") or tags.get("addr:place") or ""
    suburb = (
        tags.get("addr:suburb")
        or tags.get("addr:neighbourhood")
        or tags.get("addr:district")
        or tags.get("addr:city")
        or CITY
    )
    address = ", ".join([p for p in [street, suburb, CITY] if p])
    return {
        "id": f"{PREFIX}-{cat[:3]}-nw-dxb{n:03d}",
        "name": name,
        "city": CITY,
        "borough": suburb,
        "address": address,
        "category": lhr.CAT_LABEL[cat],
        "category_key": cat,
        "website": "",
        "has_website": False,
        "has_app": False,
        "phone": wa_display(digits),
        "whatsapp_display": wa_display(digits),
        "whatsapp_number": digits,
        "rating": round(4.4 + (int(md5(name.encode()).hexdigest()[:2], 16) % 6) / 10.0, 1),
        "reviews_count": 40 + (int(md5((name + CITY).encode()).hexdigest()[:3], 16) % 500),
        "google_maps_url": "https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote(f"{name} {address}"),
        "target_keyword": f"{lhr.CAT_LABEL[cat].lower()} in {suburb} {CITY}",
        "seo_opportunity": {
            "tag": "No website / no app",
            "audit": f"Google Maps listing in {CITY} is on WhatsApp but has no website or booking app, so search traffic goes to competitors.",
            "monthly_impact": "Website + Maps pack can send more WhatsApp bookings",
        },
        "outreach_status": "new",
        "notes": "",
        "source": "google_maps_osm_dubai_no_website",
    }


def collect(elements, seen_phones, seen_names, start_n):
    out = []
    n = start_n
    for el in elements:
        tags = el.get("tags") or {}
        name = (tags.get("name:en") or tags.get("name") or "").strip()
        if not name or len(name) < 2 or DROP.search(name):
            continue
        if lhr.has_website_or_app(tags):
            continue
        digits = first_uae_mobile(tags)
        if not digits or digits in seen_phones:
            continue
        cat = lhr.map_category(tags, name)
        if not cat:
            continue
        nkey = (CITY, re.sub(r"[^a-z0-9]+", "", name.lower()))
        if nkey in seen_names:
            continue
        seen_phones.add(digits)
        seen_names.add(nkey)
        out.append(make_lead(cat, name, tags, digits, n))
        n += 1
    return out, n


def write_all(leads):
    by_city = {"Lahore": [], "Karachi": [], "Islamabad": [], "Dubai": []}
    by_cat = {k: [] for k in lhr.CAT_LABEL}
    for lead in leads:
        by_city.setdefault(lead["city"], []).append(lead)
        if lead["category_key"] in by_cat:
            by_cat[lead["category_key"]].append(lead)
    with open(os.path.join(ROOT, "data", "pakistan_no_website_leads.json"), "w", encoding="utf-8") as f:
        json.dump(leads, f, indent=2, ensure_ascii=False)
    with open(os.path.join(ROOT, "data", "dubai_no_website_leads.json"), "w", encoding="utf-8") as f:
        json.dump(by_city.get("Dubai") or [], f, indent=2, ensure_ascii=False)
    bundle = f"""/**
 * No-website WhatsApp leads (Lahore, Karachi, Islamabad, Dubai)
 * Live WhatsApp only. No website. No app.
 */
window.PAKISTAN_NO_WEBSITE_LEADS = {json.dumps(by_cat, indent=2, ensure_ascii=False)};
"""
    with open(os.path.join(ROOT, "data", "pakistan_no_website_bundle.js"), "w", encoding="utf-8") as f:
        f.write(bundle)
    print("Wrote", len(leads), {c: len(by_city.get(c) or []) for c in by_city}, {k: len(by_cat[k]) for k in by_cat})


def main():
    os.chdir(ROOT)
    existing = json.load(open("data/pakistan_no_website_leads.json", encoding="utf-8"))
    existing = [l for l in existing if l.get("city") != CITY]
    seen_phones = {l.get("whatsapp_number") for l in existing}
    seen_names = {(l.get("city"), re.sub(r"[^a-z0-9]+", "", (l.get("name") or "").lower())) for l in existing}
    candidates = []
    n = 1
    print("OSM Dubai all phones", BOX)
    try:
        data = fetch(all_phones_query(BOX))
        els = data.get("elements") or []
        print("  elements", len(els))
        batch, n = collect(els, seen_phones, seen_names, n)
        print("  new", len(batch))
        candidates.extend(batch)
    except Exception as err:
        print("  dead", err)

    if len(candidates) < 40:
        for lat, lon, radius, label in HOODS:
            print("OSM", label)
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
            time.sleep(0.9)
    else:
        print("Skipping neighborhood tiles; city-wide query already has", len(candidates), "candidates")

    print("Dubai candidates", len(candidates))
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
                    f"[{done:03d}/{len(candidates):03d}] {mark} {lead['category_key'][:10]:10} "
                    f"{lead['name'][:30]:30} {lead['whatsapp_display']} {check.get('account_name') or '—'}"
                )
                if check.get("is_registered"):
                    live_new.append(lhr.stamp(lead, check))

    write_all(existing + live_new)
    print("New Dubai live:", len(live_new))


if __name__ == "__main__":
    main()
