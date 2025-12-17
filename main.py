import os
import time
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime

URL = "https://www.inli.fr/locations/offres/val-doise-departement_d:95"
BUDGET_MAX = 950

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

SEEN_FILE = "seen.json"


# ----------------------------
# PERSISTENCE (load/save JSON)
# ----------------------------
def load_seen():
    if not os.path.exists(SEEN_FILE):
        return set()
    try:
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    except:
        return set()


def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)


SEEN = load_seen()


# ----------------------------
# TELEGRAM
# ----------------------------
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "disable_web_page_preview": True,
    }

    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code != 200:
            print("⚠️ Telegram error:", r.text)
    except Exception as e:
        print("❌ Telegram exception:", e)


# ----------------------------
# SCRAPER
# ----------------------------
def fetch_page():
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(URL, headers=headers, timeout=15)
        r.raise_for_status()
        return BeautifulSoup(r.text, "html.parser")
    except Exception as e:
        print("❌ Error fetching page:", e)
        return None


def scrape():
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🔍 Checking listings…")

    soup = fetch_page()
    if soup is None:
        return

    items = soup.find_all("div", class_="featured-item")
    print("📌 Found:", len(items), "listings")

    new_count = 0

    for item in items:
        try:
            title = item.find("div", class_="featured-details").get_text(strip=True)
            price_txt = item.find("div", class_="featured-price").get_text(strip=True)

            price = int(
                price_txt.lower()
                .replace("€", "")
                .replace(" ", "")
                .replace("cc", "")
                .replace(",", "")
                .strip()
            )

            link = "https://www.inli.fr" + item.find("a")["href"]

            # Filters
            if "2 pièces" not in title.lower() and "t2" not in title.lower():
                continue
            if price > BUDGET_MAX:
                continue
            if link in SEEN:
                continue

            # ALERT MESSAGE
            message = (
                f"🏡 Nouveau T2 détecté !\n\n"
                f"{title}\nPrix : {price}€\n\n🔗 {link}"
            )

            print("✨ NEW:", title, price)
            send_telegram(message)

            SEEN.add(link)
            new_count += 1

        except Exception as e:
            print("❌ Parsing error:", e)

    if new_count > 0:
        save_seen(SEEN)
        print(f"💾 Saved {new_count} new listings.")
    else:
        print("➡️ No new listings.")


# ----------------------------
# MAIN LOOP
# ----------------------------
if __name__ == "__main__":
    print("🚀 INLI BOT — Railway Cloud — Upgraded Version")
    send_telegram("🚀 Bot started on Railway and running every 2 minutes.")

    while True:
        scrape()
        time.sleep(120)  # every 2 minutes
