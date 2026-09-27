#!/usr/bin/env python3
"""
Live WhatsApp API audit for every Pakistani business (Lahore, Karachi, Islamabad).

Does NOT trust existing flags. For each business, one-by-one:
1. GET https://api.whatsapp.com/send/?phone=923...
2. Parse Meta og:title / og:description
   - "Share on WhatsApp" => number is NOT registered on WhatsApp
   - any other title => live registered account
3. If unregistered, look on the business website for a wa.me / send?phone= number and re-check.
4. Keep only live-registered accounts in the Pakistan datasets + leads_bundle.js.
"""

import json
import os
import re
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html import unescape

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
CTX = ssl.create_default_context()
PK_CITIES = {"Lahore", "Karachi", "Islamabad"}


def http_get(url, timeout=12):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout, context=CTX) as resp:
        return resp.status, resp.read().decode("utf-8", errors="ignore"), resp.geturl()


def normalize_pk_mobile(raw):
    digits = re.sub(r"[^\d]", "", str(raw or ""))
    if digits.startswith("0092"):
        digits = digits[2:]
    if digits.startswith("03"):
        digits = "92" + digits[1:]
    elif digits.startswith("3") and len(digits) == 10:
        digits = "92" + digits
    if digits.startswith("923") and len(digits) == 12:
        return digits
    return None


def live_whatsapp_check(digits):
    """Ping Meta WhatsApp send API and detect a live registered account."""
    url = f"https://api.whatsapp.com/send/?phone={digits}"
    try:
        status, html, final = http_get(url, timeout=15)
    except Exception as err:
        return {
            "digits": digits,
            "http_status": None,
            "final_url": url,
            "is_registered": False,
            "account_name": None,
            "account_type": None,
            "meta_status": f"connection_error: {err}",
            "api_endpoint": url,
        }

    titles = re.findall(r'<meta property="og:title" content="(.*?)"', html, flags=re.I)
    descs = re.findall(r'<meta property="og:description" content="(.*?)"', html, flags=re.I)
    title = unescape(titles[0]).strip() if titles else ""
    desc = unescape(descs[0]).strip() if descs else ""

    is_registered = bool(title) and title.lower() not in {
        "share on whatsapp",
        "whatsapp",
        "whatsapp messenger",
    }

    return {
        "digits": digits,
        "http_status": status,
        "final_url": final,
        "is_registered": is_registered,
        "account_name": title if is_registered else None,
        "account_type": desc if is_registered else None,
        "meta_status": (
            f"Live registered WhatsApp account ({title})"
            if is_registered
            else "Not registered on WhatsApp (Meta returned Share on WhatsApp)"
        ),
        "api_endpoint": url,
        "og_title": title,
        "og_description": desc,
    }


def find_whatsapp_on_website(website):
    if not website:
        return []
    try:
        _, html, _ = http_get(website, timeout=10)
    except Exception:
        return []
    found = []
    for match in re.findall(
        r"(?:wa\.me/|api\.whatsapp\.com/send/\?phone=|api\.whatsapp\.com/send\?phone=|whatsapp\.com/send/\?phone=)(\+?[\d]+)",
        html,
        flags=re.I,
    ):
        digits = normalize_pk_mobile(match)
        if digits and digits not in found:
            found.append(digits)
    return found


def wa_display(digits):
    return f"+92 {digits[2:5]} {digits[5:8]} {digits[8:]}"


def stamp_live(lead, check):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    digits = check["digits"]
    lead["whatsapp_number"] = digits
    lead["whatsapp_wa_id"] = digits
    lead["phone"] = wa_display(digits)
    lead["whatsapp_display"] = wa_display(digits)
    lead["whatsapp_api_checked"] = True
    lead["whatsapp_api_verified_at"] = now
    lead["whatsapp_live_verified"] = True
    lead["is_whatsapp_available"] = True
    lead["whatsapp_verified"] = True
    lead["whatsapp_account_name"] = check["account_name"]
    lead["whatsapp_account_type"] = check["account_type"] or "Business Account"
    lead["whatsapp_api_status"] = "meta_live_verified"
    lead["whatsapp_verified_source"] = f"Live WhatsApp API ({check['account_name']})"
    lead["whatsapp_api_response"] = check["meta_status"]
    return lead


def stamp_not_on_whatsapp(lead, check):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lead["whatsapp_live_verified"] = False
    lead["is_whatsapp_available"] = False
    lead["whatsapp_verified"] = False
    lead["whatsapp_api_checked"] = True
    lead["whatsapp_api_verified_at"] = now
    lead["whatsapp_api_status"] = "not_on_whatsapp"
    lead["whatsapp_account_name"] = None
    lead["whatsapp_account_type"] = None
    lead["whatsapp_verified_source"] = "Not registered on WhatsApp (live API)"
    lead["whatsapp_api_response"] = check["meta_status"]
    return lead


def load_pakistan_from_bundle():
    path = os.path.join(ROOT, "data", "leads_bundle.js")
    with open(path, encoding="utf-8") as f:
        text = f.read()
    m = re.search(r"window\.LONDON_LEADS_DATA\s*=\s*(\{[\s\S]*?\});\s*(?:window\.|$)", text)
    if not m:
        raise ValueError("Could not parse leads_bundle.js")
    bundle = json.loads(m.group(1))
    leads = []
    for cat, items in bundle.items():
        for lead in items:
            if lead.get("city") in PK_CITIES:
                lead["category_key"] = lead.get("category_key") or cat
                leads.append(lead)
    return bundle, leads


def write_outputs(bundle, live_leads, audit_rows):
    for cat in bundle:
        bundle[cat] = [l for l in bundle[cat] if l.get("city") not in PK_CITIES]
    for lead in live_leads:
        cat = lead.get("category_key")
        if cat in bundle:
            bundle[cat].append(lead)

    total = sum(len(bundle[c]) for c in bundle)
    new_text = f"""/**
 * Global Multi-City Business Leads Pre-Bundled Dataset
 * Pakistan leads kept only after live WhatsApp API registration check.
 * Total Leads: {total}
 */
window.LONDON_LEADS_DATA = {json.dumps(bundle, indent=2, ensure_ascii=False)};
"""
    with open(os.path.join(ROOT, "data", "leads_bundle.js"), "w", encoding="utf-8") as f:
        f.write(new_text)

    by_city = {"Lahore": [], "Karachi": [], "Islamabad": []}
    for lead in live_leads:
        by_city[lead["city"]].append(lead)
    for city, fname in (
        ("Lahore", "lahore_leads.json"),
        ("Karachi", "karachi_leads.json"),
        ("Islamabad", "islamabad_leads.json"),
    ):
        with open(os.path.join(ROOT, "data", fname), "w", encoding="utf-8") as f:
            json.dump(by_city[city], f, indent=2, ensure_ascii=False)
    with open(os.path.join(ROOT, "data", "pakistan_leads.json"), "w", encoding="utf-8") as f:
        json.dump(live_leads, f, indent=2, ensure_ascii=False)

    live_n = sum(1 for r in audit_rows if r["is_registered"])
    report = {
        "metadata": {
            "title": "Pakistan Live WhatsApp API Registration Audit",
            "method": "GET https://api.whatsapp.com/send/?phone=923... then parse og:title",
            "rule": "og:title == Share on WhatsApp => NOT on WhatsApp; other title => live account",
            "cities": ["Lahore", "Karachi", "Islamabad"],
            "total_checked": len(audit_rows),
            "live_registered": live_n,
            "not_on_whatsapp": len(audit_rows) - live_n,
            "kept_in_app": len(live_leads),
            "audit_executed_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        },
        "city_live_counts": {c: len(by_city[c]) for c in by_city},
        "category_live_counts": {
            k: sum(1 for l in live_leads if l.get("category_key") == k)
            for k in ["salons", "estate_agents", "dentists", "restaurants", "cafes", "fitness"]
        },
        "leads_audit": audit_rows,
    }
    with open(
        os.path.join(ROOT, "data", "pakistan_whatsapp_api_verification_report.json"),
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    return report


def main():
    os.chdir(ROOT)
    bundle, leads = load_pakistan_from_bundle()
    print("=" * 92)
    print(f"LIVE WHATSAPP API AUDIT — {len(leads)} Pakistani businesses, one by one")
    print("Endpoint: https://api.whatsapp.com/send/?phone=923...")
    print("Registered only if Meta og:title is an account name (not 'Share on WhatsApp')")
    print("=" * 92)

    live_leads = []
    audit_rows = []

    for i, lead in enumerate(leads, 1):
        name = lead.get("name")
        city = lead.get("city")
        digits = normalize_pk_mobile(lead.get("whatsapp_number") or lead.get("phone"))
        check = (
            live_whatsapp_check(digits)
            if digits
            else {
                "digits": None,
                "http_status": None,
                "is_registered": False,
                "account_name": None,
                "account_type": None,
                "meta_status": "invalid Pakistani mobile format",
                "api_endpoint": None,
            }
        )
        recovered_from_site = False
        if not check["is_registered"]:
            site_nums = find_whatsapp_on_website(lead.get("website"))
            for alt in site_nums:
                if alt == digits:
                    continue
                alt_check = live_whatsapp_check(alt)
                if alt_check["is_registered"]:
                    check = alt_check
                    recovered_from_site = True
                    break

        row = {
            "id": lead.get("id"),
            "name": name,
            "city": city,
            "category": lead.get("category_key"),
            "website": lead.get("website"),
            "checked_number": check.get("digits"),
            "is_registered": check["is_registered"],
            "account_name": check.get("account_name"),
            "account_type": check.get("account_type"),
            "http_status": check.get("http_status"),
            "api_endpoint": check.get("api_endpoint"),
            "recovered_from_website": recovered_from_site,
            "status": "meta_live_verified" if check["is_registered"] else "not_on_whatsapp",
            "message": check["meta_status"],
        }
        audit_rows.append(row)

        if check["is_registered"]:
            stamp_live(lead, check)
            live_leads.append(lead)
            mark = "LIVE"
        else:
            stamp_not_on_whatsapp(lead, check)
            mark = "NOT ON WA"

        acc = check.get("account_name") or "—"
        print(
            f"[{i:03d}/{len(leads):03d}] {mark:<9} {city:<10} {str(name)[:34]:<34} "
            f"{check.get('digits') or 'n/a':<13} {acc}"
        )
        time.sleep(0.25)

    report = write_outputs(bundle, live_leads, audit_rows)
    print("\n" + "=" * 92)
    print(
        f"Checked {report['metadata']['total_checked']} | "
        f"LIVE on WhatsApp {report['metadata']['live_registered']} | "
        f"NOT on WhatsApp {report['metadata']['not_on_whatsapp']}"
    )
    print("Kept in app:", report["city_live_counts"])
    print("Categories:", report["category_live_counts"])


if __name__ == "__main__":
    main()
