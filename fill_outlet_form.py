"""
Playwright script to fill the NSR Outlet Onboarding Form
at https://nsronboarding.techjays.com/outlet.html with sample data.

Usage:
    pip install playwright
    python -m playwright install chromium
    python fill_outlet_form.py
"""

import asyncio
from playwright.async_api import async_playwright

URL = "https://nsronboarding.techjays.com/outlet.html"

SAMPLE_DATA = {
    # Corporate / Parent Company Information
    "company_name": "Acme Corporation",
    "billing_street": "123 Main Street",
    "billing_city": "Chicago",
    "billing_state": "Illinois",
    "billing_postal": "60601",
    "billing_email": "billing@acmecorp.com",
    "billing_same_for_all": "Yes",
    "remit_to": "Acme Corp Payments, PO Box 999, Chicago IL 60601",

    # Accounts Payable Contact
    "ap_name": "John Smith",
    "ap_phone": "312-555-0101",
    "ap_email": "ap@acmecorp.com",

    # Bank Information
    "bank_name": "First National Bank",
    "bank_address": "456 Bank Avenue, Chicago, IL 60602",
    "bank_account": "123456789",
    "bank_routing": "021000021",
    "bank_swift": "FNBAUS33",

    # Customer Service Contact
    "cs_name": "Jane Doe",
    "cs_phone": "312-555-0202",
    "cs_email": "support@acmecorp.com",

    # Corporate Contact
    "corp_name": "Michael Johnson",
    "corp_phone": "312-555-0303",
    "corp_email": "michael.johnson@acmecorp.com",

    # Corporate Contact (additional)
    "corp2_name": "Sarah Williams",
    "corp2_phone": "312-555-0404",
    "corp2_email": "sarah.williams@acmecorp.com",

    # Emergency Contact
    "emergency_name": "Robert Davis",
    "emergency_phone": "312-555-0505",
    "emergency_email": "emergency@acmecorp.com",

    # Location Contact
    "loc_contact_name": "Emily Brown",
    "loc_contact_phone": "312-555-0606",
    "loc_contact_email": "emily.brown@acmecorp.com",

    # Location 1
    "loc_name": "Chicago Main Warehouse",
    "loc_street": "789 Industrial Blvd",
    "loc_city": "Chicago",
    "loc_state": "Illinois",
    "loc_postal": "60609",
    "loc_hours": "8:00 AM - 5:00 PM",
    "loc_days": "Monday - Friday",
    "loc_gate_code": "4321",
    "loc_special_instructions": "Use rear entrance. Call 30 minutes before arrival.",
}


async def fill_field(page, selector, value, method="fill"):
    """Helper to fill a field, ignoring errors if field not found."""
    try:
        if method == "fill":
            await page.fill(selector, value)
        elif method == "select":
            await page.select_option(selector, label=value)
        elif method == "check":
            await page.check(selector)
        print(f"  Filled: {selector}")
    except Exception as e:
        print(f"  Skipped ({selector}): {e}")


async def fill_outlet_form():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=300)
        context = await browser.new_context()
        page = await context.new_page()

        print(f"Opening {URL} ...")
        await page.goto(URL, wait_until="networkidle", timeout=30000)
        print("Page loaded.\n")

        data = SAMPLE_DATA

        # ── Corporate / Parent Company Information ──────────────────────────
        print("Filling Corporate/Parent Company Information...")

        await fill_field(page, "input[name='company_name'], input[placeholder*='Company Name'], #company_name, [data-field='company_name']", data["company_name"])
        await fill_field(page, "input[name='billing_address'], input[placeholder*='Street'], #billing_street", data["billing_street"])
        await fill_field(page, "input[name='billing_city'], input[placeholder*='City'], #billing_city", data["billing_city"])
        await fill_field(page, "input[name='billing_state'], input[placeholder*='State'], #billing_state", data["billing_state"])
        await fill_field(page, "input[name='billing_postal'], input[placeholder*='Postal'], input[placeholder*='ZIP'], #billing_postal", data["billing_postal"])
        await fill_field(page, "input[name='billing_email'], input[placeholder*='Billing Email'], #billing_email", data["billing_email"])
        await fill_field(page, "input[name='remit_to'], #remit_to, textarea[name='remit_to']", data["remit_to"])

        # Use billing address for all locations dropdown
        try:
            await page.select_option(
                "select[name='billing_same'], select[name='same_billing'], #billing_same",
                label=data["billing_same_for_all"]
            )
            print("  Filled: billing_same dropdown")
        except Exception as e:
            print(f"  Skipped billing_same dropdown: {e}")

        # Payment Options checkboxes
        print("\nSelecting payment options...")
        for selector in [
            "input[value='Credit Card']",
            "input[value='credit_card']",
            "input[name='payment'][value*='credit']",
        ]:
            try:
                await page.check(selector)
                print(f"  Checked: Credit Card ({selector})")
                break
            except Exception:
                pass
        for selector in [
            "input[value='USD']",
            "input[name='currency'][value='USD']",
        ]:
            try:
                await page.check(selector)
                print(f"  Checked: USD ({selector})")
                break
            except Exception:
                pass

        # ── Accounts Payable Contact ────────────────────────────────────────
        print("\nFilling Accounts Payable Contact...")
        await fill_field(page, "input[name='ap_name'], input[placeholder*='AP'], #ap_name", data["ap_name"])
        await fill_field(page, "input[name='ap_phone'], #ap_phone", data["ap_phone"])
        await fill_field(page, "input[name='ap_email'], #ap_email", data["ap_email"])

        # ── Bank Information ────────────────────────────────────────────────
        print("\nFilling Bank Information...")
        await fill_field(page, "input[name='bank_name'], #bank_name", data["bank_name"])
        await fill_field(page, "input[name='bank_address'], #bank_address, textarea[name='bank_address']", data["bank_address"])
        await fill_field(page, "input[name='account_number'], input[name='bank_account'], #account_number", data["bank_account"])
        await fill_field(page, "input[name='routing_number'], input[name='bank_routing'], #routing_number", data["bank_routing"])
        await fill_field(page, "input[name='swift_code'], input[name='bank_swift'], #swift_code", data["bank_swift"])

        # ── Customer Service Contact ────────────────────────────────────────
        print("\nFilling Customer Service Contact...")
        await fill_field(page, "input[name='cs_name'], #cs_name", data["cs_name"])
        await fill_field(page, "input[name='cs_phone'], #cs_phone", data["cs_phone"])
        await fill_field(page, "input[name='cs_email'], #cs_email", data["cs_email"])

        # ── Corporate Contact ───────────────────────────────────────────────
        print("\nFilling Corporate Contact...")
        await fill_field(page, "input[name='corp_name'], #corp_name", data["corp_name"])
        await fill_field(page, "input[name='corp_phone'], #corp_phone", data["corp_phone"])
        await fill_field(page, "input[name='corp_email'], #corp_email", data["corp_email"])

        # ── Corporate Contact (additional) ──────────────────────────────────
        print("\nFilling Corporate Contact (additional)...")
        await fill_field(page, "input[name='corp2_name'], #corp2_name", data["corp2_name"])
        await fill_field(page, "input[name='corp2_phone'], #corp2_phone", data["corp2_phone"])
        await fill_field(page, "input[name='corp2_email'], #corp2_email", data["corp2_email"])

        # ── Emergency Contact ───────────────────────────────────────────────
        print("\nFilling Emergency Contact...")
        await fill_field(page, "input[name='emergency_name'], #emergency_name", data["emergency_name"])
        await fill_field(page, "input[name='emergency_phone'], #emergency_phone", data["emergency_phone"])
        await fill_field(page, "input[name='emergency_email'], #emergency_email", data["emergency_email"])

        # ── Location Contact ────────────────────────────────────────────────
        print("\nFilling Location Contact...")
        await fill_field(page, "input[name='loc_contact_name'], #loc_contact_name", data["loc_contact_name"])
        await fill_field(page, "input[name='loc_contact_phone'], #loc_contact_phone", data["loc_contact_phone"])
        await fill_field(page, "input[name='loc_contact_email'], #loc_contact_email", data["loc_contact_email"])

        # ── Location 1 ──────────────────────────────────────────────────────
        print("\nFilling Location 1...")
        await fill_field(page, "input[name='location_name'], input[placeholder*='Location Name'], #location_name", data["loc_name"])
        await fill_field(page, "input[name='location_street'], input[placeholder*='Physical Address'], #location_street", data["loc_street"])
        await fill_field(page, "input[name='location_city'], #location_city", data["loc_city"])
        await fill_field(page, "input[name='location_state'], #location_state", data["loc_state"])
        await fill_field(page, "input[name='location_postal'], #location_postal", data["loc_postal"])
        await fill_field(page, "input[name='location_hours'], input[placeholder*='Hours'], #location_hours", data["loc_hours"])
        await fill_field(page, "input[name='location_days'], input[placeholder*='Days'], #location_days", data["loc_days"])
        await fill_field(page, "input[name='gate_code'], input[name='gate'], input[placeholder*='Gate'], #gate_code", data["loc_gate_code"])
        await fill_field(page, "textarea[name='special_instructions'], input[name='special_instructions'], #special_instructions", data["loc_special_instructions"])

        print("\nForm filled! Review the data in the browser before submitting.")
        print("Press Enter in this terminal to close the browser, or submit the form manually.")
        input()

        await browser.close()
        print("Done.")


if __name__ == "__main__":
    asyncio.run(fill_outlet_form())
