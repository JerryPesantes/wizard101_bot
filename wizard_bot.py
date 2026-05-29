import os
import requests
from bs4 import BeautifulSoup
# Try to import dotenv for local testing, fail silently on GitHub Actions
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

URL = "https://www.console.wizard101.com/news"
# This reads from GitHub Secrets in production, or your .env file locally
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
CACHE_FILE = "last_news_title.txt"

def get_latest_news():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(URL, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching page: {e}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    first_article = soup.find('h3') or soup.find('h2')
    if not first_article:
        print("Could not find news elements.")
        return None
        
    title = first_article.get_text(strip=True)
    link_element = first_article.find('a') if first_article.name != 'a' else first_article
    if not link_element:
        link_element = first_article.find_parent('a')
        
    link = link_element['href'] if link_element and 'href' in link_element.attrs else URL
    if link.startswith('/'):
        link = "https://www.console.wizard101.com" + link

    return {"title": title, "link": link}

def send_to_discord(title, link):
    if not DISCORD_WEBHOOK_URL:
        print("🚨 Discord Webhook environment variable is missing!")
        print(" -> If running locally: Set up your .env file or terminal environment variable.")
        print(" -> If running on GitHub: Ensure you added 'DISCORD_WEBHOOK_URL' to Settings > Secrets > Actions.")
        return

    payload = {
        "username": "Wizard101 Console News Tracker",
        "avatar_url": "https://www.wizard101.com/shared/images/icons/w101_icon_50.png",
        "embeds": [{
            "title": "📜 New Wizard101 Console Update Found!",
            "description": f"**Headline:** {title}",
            "url": link,
            "color": 5763719,
            "footer": {"text": "Automated Update Checker"}
        }]
    }
    try:
        res = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        res.raise_for_status()
        print("🚀 Sent to Discord successfully!")
    except requests.exceptions.RequestException as e:
        print(f"Discord API Error: {e}")

def check_for_updates():
    current_news = get_latest_news()
    if not current_news:
        return

    last_saved_title = ""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            last_saved_title = f.read().strip()

    if current_news["title"] != last_saved_title:
        print(f"New Update Detected: {current_news['title']}.")
        send_to_discord(current_news["title"], current_news["link"])
        
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            f.write(current_news["title"])
    else:
        print("No new updates found.")

if __name__ == "__main__":
    check_for_updates()