import json
import os
import re
import hashlib
import requests
from playwright.sync_api import sync_playwright

SLACK_WEBHOOK = os.environ['SLACK_WEBHOOK']
LINKEDIN_LI_AT = os.environ['LINKEDIN_LI_AT']
X_AUTH_TOKEN = os.environ['X_AUTH_TOKEN']
X_CT0 = os.environ['X_CT0']
SEEN_FILE = 'seen_posts.json'

ACCOUNTS = [
    {'name': 'Web3Finance Club LinkedIn', 'type': 'linkedin', 'slug': 'web3financeclub', 'emoji': '🔵'},
    {'name': 'Request Finance LinkedIn', 'type': 'linkedin', 'slug': 'request-finance', 'emoji': '🔵'},
    {'name': 'Web3Finance Club X', 'type': 'x', 'username': 'web3financeclub', 'emoji': '🐦'},
    {'name': 'Request Finance X', 'type': 'x', 'username': 'RequestFinance', 'emoji': '🐦'},
]

def load_seen():
    try:
        with open(SEEN_FILE) as f:
            return set(json.load(f))
    except:
        return set()

def save_seen(seen):
    with open(SEEN_FILE, 'w') as f:
        json.dump(list(seen)[-200:], f)

def post_to_slack(message):
    requests.post(SLACK_WEBHOOK, json={'text': message})

def extract_id(url):
    numbers = re.findall(r'\d{10,}', url)
    return int(numbers[-1]) if numbers else 0

def clean_linkedin_url(href):
    if not href or 'feed/update' not in href:
        return None
    if not href.startswith('http'):
        href = 'https://www.linkedin.com' + href
    return href.split('?')[0].rstrip('/')

def clean_x_url(href):
    if not href or '/status/' not in href:
        return None
    if not href.startswith('http'):
        href = 'https://x.com' + href
    match = re.match(r'(https://x\.com/[^/]+/status/\d+)$', href)
    return match.group(1) if match else None

def main():
    seen = load_seen()
    new_seen = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # One shared LinkedIn context for both accounts
        linkedin_context = browser.new_context()
        linkedin_context.add_cookies([
            {'name': 'li_at', 'value': LINKEDIN_LI_AT, 'domain': '.linkedin.com', 'path': '/'},
        ])
        linkedin_page = linkedin_context.new_page()

        for account in ACCOUNTS:
            print(f"\nChecking {account['name']}...")
            try:
                if account['type'] == 'linkedin':
                    linkedin_page.goto(f"https://www.linkedin.com/company/{account['slug']}/posts/?feedView=all")
                    linkedin_page.wait_for_timeout(5000)
                    print(f"  Title: {linkedin_page.title()}")

                    links = set()
                    for el in linkedin_page.query_selector_all('a[href*="feed/update"]'):
                        url = clean_linkedin_url(el.get_attribute('href'))
                        if url:
                            links.add(url)

                    sorted_links = sorted(links, key=extract_id, reverse=True)
                    print(f"  Unique posts found: {len(sorted_links)}")

                    for link in sorted_links[:5]:
                        uid = hashlib.md5(link.encode()).hexdigest()
                        if uid not in seen and uid not in new_seen:
                            new_seen.add(uid)
                            post_to_slack(f"{account['emoji']} *New post on {account['name']}!*\n\n🔗 {link}\n\nGo engage 👇")
                            print(f"  Sent: {link}")

                elif account['type'] == 'x':
                    context = browser.new_context()
                    context.add_cookies([
                        {'name': 'auth_token', 'value': X_AUTH_TOKEN, 'domain': '.x.com', 'path': '/'},
                        {'name': 'ct0', 'value': X_CT0, 'domain': '.x.com', 'path': '/'}
                    ])
                    page = context.new_page()
                    page.goto(f"https://x.com/{account['username']}")
                    page.wait_for_timeout(5000)
                    print(f"  Title: {page.title()}")

                    links = set()
                    for el in page.query_selector_all('a[href*="/status/"]'):
                        url = clean_x_url(el.get_attribute('href'))
                        if url and account['username'].lower() in url.lower():
                            links.add(url)

                    sorted_links = sorted(links, key=extract_id, reverse=True)
                    print(f"  Unique posts found: {len(sorted_links)}")

                    for link in sorted_links[:5]:
                        uid = hashlib.md5(link.encode()).hexdigest()
                        if uid not in seen and uid not in new_seen:
                            new_seen.add(uid)
                            post_to_slack(f"{account['emoji']} *New post on {account['name']}!*\n\n🔗 {link}\n\nGo engage 👇")
                            print(f"  Sent: {link}")

                    context.close()

            except Exception as e:
                print(f"  Error: {e}")

        linkedin_context.close()
        browser.close()

    save_seen(seen | new_seen)
    print("\nDone.")

if __name__ == '__main__':
    main()
