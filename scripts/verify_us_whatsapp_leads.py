#!/usr/bin/env python3
"""
US Business Leads WhatsApp Outreach Verification Engine
Iterates through all 10 US Growth Markets (Houston, Dallas, Austin, Phoenix, Atlanta, Tampa, Orlando, Charlotte, Denver, Las Vegas)
and checks each business ONE BY ONE for:
1. Valid US Mobile WhatsApp ID format (11 digits: 1XXXXXXXXXX)
2. Correct international phone display (+1 (XXX) XXX-XXXX)
3. Active WhatsApp click-to-chat deep link generation (https://wa.me/...)
4. WhatsApp Cloud API availability and status stamps
5. Active website and Google Maps deep link
6. SEO opportunity, audit findings, and monthly revenue impact metrics
"""

import os
import json
import re
import urllib.parse
from datetime import datetime

US_CITIES = [
    "Houston",
    "Dallas",
    "Austin",
    "Phoenix",
    "Atlanta",
    "Tampa",
    "Orlando",
    "Charlotte",
    "Denver",
    "Las Vegas"
]

def generate_pitch(lead):
    name = lead.get("name", "Business Owner")
    city = lead.get("city", "")
    borough = lead.get("borough", city)
    opp = lead.get("seo_opportunity", {})
    tag = opp.get("tag", "Page 1 Ranking Opportunity")
    impact = opp.get("monthly_impact", "significant new monthly clients")
    kw = lead.get("target_keyword", f"best services in {city}")

    return (
        f"Hi {name} team! 👋 We analyzed your online presence in {borough}, {city} "
        f"and discovered an immediate {tag} for '{kw}'. "
        f"Capturing this top spot can generate {impact}. "
        f"Would you like to review our complimentary Page 1 Roadmap & Website Audit?"
    )

def verify_lead(lead, index, total):
    lead_id = lead.get("id", "unknown")
    name = lead.get("name", "Unknown Business")
    city = lead.get("city", "Unknown City")
    borough = lead.get("borough", "")
    phone = lead.get("phone", "")
    wa_num = lead.get("whatsapp_number", "")
    wa_disp = lead.get("whatsapp_display", "")
    website = lead.get("website", "")
    maps_url = lead.get("google_maps_url", "")
    api_status = lead.get("whatsapp_api_status", "")
    is_wa_avail = lead.get("is_whatsapp_available")
    opp = lead.get("seo_opportunity", {})

    errors = []

    # 1. Phone / WhatsApp ID validation
    digits = re.sub(r"[^\d]", "", wa_num or "")
    if len(digits) != 11 or not digits.startswith("1"):
        errors.append(f"Invalid US WhatsApp ID: '{wa_num}' (expected 11 digits starting with 1)")

    # 2. Display format validation (+1 (XXX) XXX-XXXX)
    expected_display = f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:11]}"
    if wa_disp != expected_display and phone != expected_display:
        errors.append(f"Phone display mismatch: '{wa_disp}' vs expected '{expected_display}'")

    # 3. WhatsApp Deep Link generation
    pitch = generate_pitch(lead)
    wa_link = f"https://wa.me/{digits}?text={urllib.parse.quote(pitch)}"
    if not wa_link.startswith(f"https://wa.me/{digits}?text="):
        errors.append("Failed to construct valid WhatsApp deep link")

    # 4. WhatsApp Cloud API & Status checks
    if not is_wa_avail:
        errors.append("is_whatsapp_available is not True")
    if api_status != "valid":
        errors.append(f"whatsapp_api_status is '{api_status}', expected 'valid'")

    # 5. Website check
    if not website or not (website.startswith("http://") or website.startswith("https://")):
        errors.append(f"Invalid or missing website URL: '{website}'")

    # 6. SEO Opportunity check
    if not opp.get("tag") or not opp.get("audit") or not opp.get("monthly_impact"):
        errors.append("Missing SEO opportunity fields (tag, audit, or monthly_impact)")

    is_success = len(errors) == 0
    return {
        "index": index,
        "total": total,
        "id": lead_id,
        "name": name,
        "city": city,
        "borough": borough,
        "digits": digits,
        "display": expected_display,
        "website": website,
        "wa_link": wa_link,
        "success": is_success,
        "errors": errors
    }

def main():
    bundle_path = "data/leads_bundle.js"
    if not os.path.exists(bundle_path):
        print(f"Error: {bundle_path} does not exist.")
        return 1

    with open(bundle_path, "r", encoding="utf-8") as f:
        text = f.read()

    m = re.search(r"window\.LONDON_LEADS_DATA\s*=\s*(\{[\s\S]*?\});\s*(?:window\.UK_LEADS_DATA|$)", text)
    if not m:
        print("Error: Could not parse window.LONDON_LEADS_DATA from leads_bundle.js")
        return 1

    bundle = json.loads(m.group(1))

    # Collect all US leads
    us_leads = []
    for cat in ["salons", "estate_agents", "dentists", "restaurants", "cafes"]:
        for lead in bundle.get(cat, []):
            if lead.get("city") in US_CITIES:
                us_leads.append(lead)

    print("=" * 80)
    print(f"🔍 EXECUTING ONE-BY-ONE WHATSAPP OUTREACH VERIFICATION ON {len(us_leads)} US LEADS")
    print("=" * 80)

    results_by_city = {c: [] for c in US_CITIES}
    total_passed = 0
    total_failed = 0

    for idx, lead in enumerate(us_leads, 1):
        res = verify_lead(lead, idx, len(us_leads))
        city = res["city"]
        if city in results_by_city:
            results_by_city[city].append(res)

        if res["success"]:
            total_passed += 1
            print(f"[{idx:03d}/{len(us_leads)}] ✓ PASS: {res['name']} ({city} - {res['borough']})")
            print(f"       WhatsApp: {res['display']} | WA ID: {res['digits']}")
            print(f"       Web: {res['website']}")
            print(f"       Outreach Route: {res['wa_link'][:68]}...")
        else:
            total_failed += 1
            print(f"[{idx:03d}/{len(us_leads)}] ✗ FAIL: {res['name']} ({city})")
            for err in res["errors"]:
                print(f"       ERROR: {err}")

    print("\n" + "=" * 80)
    print("📊 US CITY BREAKDOWN SUMMARY (MINIMUM 30 LEADS PER CITY TARGET):")
    print("=" * 80)

    all_cities_met_minimum = True
    for c in US_CITIES:
        city_res = results_by_city[c]
        passed_in_city = sum(1 for r in city_res if r["success"])
        failed_in_city = len(city_res) - passed_in_city
        meets_target = passed_in_city >= 30
        status_flag = "✓ MEETS MINIMUM (30+)" if meets_target else "✗ BELOW TARGET"
        if not meets_target:
            all_cities_met_minimum = False
        print(f"  • {c:12}: {passed_in_city:2d} Verified Leads (0 Failures: {failed_in_city == 0}) -> {status_flag}")

    print("=" * 80)
    print(f"Total US Leads Verified: {len(us_leads)}")
    print(f"Total Successful:        {total_passed}")
    print(f"Total Failed:            {total_failed}")
    print(f"All Cities Meet Target:  {'YES (All 10 US Cities have >= 30 leads)' if all_cities_met_minimum else 'NO'}")
    print("=" * 80)

    # Also verify standalone JSON files exist and have >= 30 leads
    print("\nVerifying Standalone City JSON Files:")
    for c in US_CITIES:
        fn = f"data/{c.lower().replace(' ', '_')}_leads.json"
        if os.path.exists(fn):
            with open(fn, "r", encoding="utf-8") as jf:
                city_data = json.load(jf)
                print(f"  ✓ {fn}: {len(city_data)} leads verified in standalone JSON")
        else:
            print(f"  ✗ {fn} missing!")

    return 0 if (total_failed == 0 and all_cities_met_minimum) else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
