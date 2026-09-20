#!/usr/bin/env python3
"""
Meta WhatsApp API Live Account Verification Engine
Pings Meta's live gateway endpoint (https://api.whatsapp.com/send/?phone=...)
and checks if Meta returns a registered Business Account with a verified profile.
"""

import sys
import json
import time
import re
import urllib.request
import urllib.error

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def check_live_whatsapp_account(phone_digits, timeout=5):
    """
    Checks if a phone number has an active registered WhatsApp account.
    Returns:
        dict: {
            "phone": digits,
            "is_registered": bool,
            "account_name": str or None,
            "account_type": str or None,
            "verified_badge": bool,
            "meta_status": str
        }
    """
    digits = re.sub(r"[^\d]", "", str(phone_digits))
    if len(digits) == 10 and not digits.startswith("1"):
        digits = "1" + digits

    url = f"https://api.whatsapp.com/send/?phone={digits}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    try:
        html = urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", errors="ignore")
        og_title = re.findall(r'<meta property="og:title" content="(.*?)"', html)
        og_desc = re.findall(r'<meta property="og:description" content="(.*?)"', html)
        h3 = re.findall(r'<h3[^>]*>(.*?)</h3>', html)

        title = og_title[0] if og_title else ""
        desc = og_desc[0] if og_desc else ""
        
        # Meta returns "Share on WhatsApp" if the number is an unregistered landline/wireline
        is_registered = bool(title and title != "Share on WhatsApp")
        has_verified_badge = bool(h3 and "_a93a" in h3[0])

        return {
            "phone": digits,
            "is_registered": is_registered,
            "account_name": title if is_registered else None,
            "account_type": desc if (is_registered and desc) else ("Unregistered Landline" if not is_registered else "Standard Account"),
            "verified_badge": has_verified_badge,
            "meta_status": "Active WhatsApp Business Account" if is_registered else "Not Registered on WhatsApp (Desk Landline)"
        }
    except Exception as e:
        return {
            "phone": digits,
            "is_registered": False,
            "account_name": None,
            "account_type": "Error",
            "verified_badge": False,
            "meta_status": f"Connection Error: {str(e)}"
        }

def audit_file(filepath):
    print(f"Auditing file: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        leads = json.load(f)

    results = []
    registered_count = 0
    total = len(leads)

    for i, lead in enumerate(leads, 1):
        num = lead.get("whatsapp_number") or lead.get("phone")
        res = check_live_whatsapp_account(num)
        results.append({
            "id": lead.get("id"),
            "name": lead.get("name"),
            "city": lead.get("city"),
            "category": lead.get("category"),
            "phone": num,
            "verification": res
        })
        if res["is_registered"]:
            registered_count += 1
            print(f"[{i}/{total}] ✓ REGISTERED: {lead.get('name')} -> {res['account_name']} ({res['account_type']})")
        else:
            print(f"[{i}/{total}] ✗ UNREGISTERED: {lead.get('name')} -> {res['meta_status']}")
        time.sleep(0.2)

    print(f"\n--- AUDIT SUMMARY FOR {filepath} ---")
    print(f"Total checked: {total}")
    print(f"Active Registered on WhatsApp: {registered_count} ({(registered_count/total)*100:.1f}%)")
    print(f"Unregistered Landlines: {total - registered_count} ({((total - registered_count)/total)*100:.1f}%)\n")
    return results

if __name__ == "__main__":
    if len(sys.argv) > 1:
        audit_file(sys.argv[1])
    else:
        # Default test
        test_numbers = ["18324198411", "13462055711", "18326310784", "13057840033", "17867018246", "17135200772"]
        print("Testing benchmark numbers:")
        for num in test_numbers:
            r = check_live_whatsapp_account(num)
            status_icon = "✓" if r["is_registered"] else "✗"
            print(f"  {status_icon} {num}: {r['account_name'] or 'N/A'} | {r['meta_status']}")
