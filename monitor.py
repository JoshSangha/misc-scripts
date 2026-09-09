"""
IWWN "New In" page monitor.

Fetches the New In page, works out which products are new since the
last check, and emails the user if anything new has appeared.

State (the list of products seen so far) is stored in seen_products.json
so that only genuinely new items trigger an email, not every product on
every run.
"""

import json
import os
import re
import smtplib
import sys
from email.mime.text import MIMEText
from pathlib import Path

import requests
from bs4 import BeautifulSoup

URL = "https://www.iwonderwhatsnext.co.uk/new-in/"
STATE_FILE = Path(__file__).parent / "seen_products.json"

HEADERS = {
    # A normal browser user-agent avoids some basic bot-blocking.
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}

PRICE_RE = re.compile(r"£\s?\d+(?:\.\d{2})?")


def fetch_html() -> str:
    resp = requests.get(URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.text


def extract_products(html: str):
    """
    Returns a list of dicts: {"key": unique id, "name": str, "price": str,
    "link": str or None}

    Strategy: find every element containing an "Add to cart" style
    control, then walk up to the nearest ancestor that also contains a
    link — that ancestor is treated as one product tile. This avoids
    depending on exact CSS class names, which can change without notice.
    """
    soup = BeautifulSoup(html, "html.parser")
    products = {}

    # Anything that looks like an "add to cart" affordance (button, link,
    # or input with that text/value).
    candidates = soup.find_all(
        lambda tag: tag.name in ("a", "button", "input")
        and (
            "add to cart" in tag.get_text(strip=True).lower()
            or "add to cart" in (tag.get("value") or "").lower()
        )
    )

    for cand in candidates:
        container = cand
        link_tag = None
        # Walk up a handful of parent levels looking for a container that
        # also has a product link and some visible text (the title).
        for _ in range(6):
            if container.parent is None:
                break
            container = container.parent
            link_tag = container.find("a", href=True)
            if link_tag and link_tag.get_text(strip=True):
                break

        if not link_tag:
            continue

        name = link_tag.get_text(strip=True)
        if not name or len(name) < 3:
            continue

        href = link_tag["href"]
        if href.startswith("/"):
            href = "https://www.iwonderwhatsnext.co.uk" + href

        text_block = container.get_text(" ", strip=True)
        prices = PRICE_RE.findall(text_block)
        price = prices[-1] if prices else ""  # last price = the sale price usually

        key = href if href else name
        # Use the product link as the unique key (falls back to name).
        products[key] = {"key": key, "name": name, "price": price, "link": href}

    return list(products.values())


def load_seen():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def save_seen(seen):
    STATE_FILE.write_text(json.dumps(seen, indent=2))


def send_email(new_products):
    sender_address = os.environ["SENDER_EMAIL"]
    sender_app_password = os.environ["SENDER_APP_PASSWORD"]
    recipient = os.environ["RECIPIENT_EMAIL"]

    lines = ["New products just landed on I Wonder What's Next:\n"]
    for p in new_products:
        lines.append(f"- {p['name']} {p['price']}".rstrip())
        if p["link"]:
            lines.append(f"  {p['link']}")
        lines.append("")

    body = "\n".join(lines)
    msg = MIMEText(body)
    msg["Subject"] = f"{len(new_products)} new product(s) on IWWN New In"
    msg["From"] = sender_address
    msg["To"] = recipient

    # Outlook/Office365 SMTP settings (STARTTLS on port 587).
    with smtplib.SMTP("smtp-mail.outlook.com", 587) as server:
        server.starttls()
        server.login(sender_address, sender_app_password)
        server.sendmail(sender_address, [recipient], msg.as_string())


def main():
    html = fetch_html()
    current_products = extract_products(html)

    if not current_products:
        # Something's probably wrong with parsing rather than the site
        # genuinely having zero products — fail loudly so it shows up in
        # the GitHub Actions run log rather than silently doing nothing.
        print("WARNING: no products parsed from the page. Site structure "
              "may have changed.", file=sys.stderr)
        sys.exit(1)

    seen = load_seen()
    new_ones = [p for p in current_products if p["key"] not in seen]

    if new_ones and seen:
        # Only email if this isn't the very first run (first run just
        # establishes the baseline, otherwise you'd get an email listing
        # all 178 existing products).
        send_email(new_ones)
        print(f"Sent email for {len(new_ones)} new product(s).")
    elif not seen:
        print(f"First run: recorded {len(current_products)} existing products as baseline.")
    else:
        print("No new products found.")

    # Update state with everything currently on the page.
    for p in current_products:
        seen[p["key"]] = {"name": p["name"], "price": p["price"]}
    save_seen(seen)


if __name__ == "__main__":
    main()
