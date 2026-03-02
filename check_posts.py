import json
import os
import hashlib
import requests
from playwright.sync_api import sync_playwright

SLACK_WEBHOOK = os.environ['SLACK_WEBHOOK']
LINKEDIN_LI_AT = os.environ['LINKEDIN_LI_AT']
X_AUTH_TOKEN = os.environ['X_AUTH_TOKEN']
X_CT0 = os.environ['X_CT0']
SEEN_FILE = 'seen_posts.json'

ACCOUNTS = [
    {
        'name': 'Web3Finance Club LinkedIn',
        'type': 'linkedin',
        'url': 'https://www.linkedin.com/company/web3financeclub/posts/?feedView=all',
        'emoji': '🔵'
    },
    {
        'name': 'Request Finance LinkedIn',
        'url': 'https://www.linkedin.com/company/request-finance/posts/?feedView=all',
        'type': 'linkedin',
        'emoji': '🔵'
    },
    {
        'name': 'Web3Finance Club X',
        'type': 'x',
        'url': 'https://x.com/web3financeclub',
        'emoji': '🐦'
    },
    {
        'name': 'Request Finance X',
        'type': 'x',
        'url': 'https://x.com/RequestFinance',
        'emoji': '🐦'
    },
]

def load_seen():
    try:
        with open(SEEN_FILE) as f:
            return json.load(f)
    except:
        return []

def save_seen(seen):
    with open(SEEN_FILE, 'w') as f:
        json.dump(seen[-200:], f)

def post_to_slack(message):
    requests.post(SLACK_WEBHOOK, json={'text': message})

def main():
    seen = load_seen()
    new_seen = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for account in ACCOUNTS:
            print(f"Checking {account['name']}...")
            try:
                if account['type'] == 'linkedin':
                    context = browser.new_context()
                    context.add_cookies([{
                        'name': 'li_at',
                        'value': LINKEDIN_LI_AT,
                        'domain': '.linkedin.com',
                        'path': '/'
                    }])
                    page = context.new_page()
                    page.goto(account['url'])
                    page.wait_for_timeout(5000)
                    print(f"  Title: {page.title()}")

                    posts = page.query_selector_all('a[href*="feed/update"]')
                    seen_links = set()
                    for post in posts[:5]:
                        link = post.get_attribute('href') or ''
                        if 'feed/update' not in link:
                            continue
                        link = link.split('?')[0]
                        if not link.startswith('http'):
                            link = 'https://www.linkedin.com' + link
                        if link in seen_links:
                            continue
                        seen_links.add(link)
                        uid = hashlib.md5(link.encode()).hexdigest()
                        if uid not in seen:
                            new_seen.append(uid)
                            message = f"{account['emoji']} *New post on {account['name']}!*\n\n🔗 {link}\n\nGo engage 👇"
                            post_to_slack(message)
                            print(f"  Sent: {link}")

                elif account['type'] == 'x':
                    context = browser.new_context()
                    context.add_cookies([
                        {'name': 'auth_token', 'value': X_AUTH_TOKEN, 'domain': '.x.com', 'path': '/'},
                        {'name': 'ct0', 'value': X_CT0, 'domain': '.x.com', 'path': '/'}
                    ])
                    page = context.new_page()
                    page.goto(account['url'])
                    page.wait_for_timeout(5000)
                    print(f"  Title: {page.title()}")

                    posts = page.query_selector_all('a[href*="/status/"]')
                    seen_links = set()
                    for post in posts[:5]:
                        link = post.get_attribute('href') or ''
                        if '/status/' not in link:
                            continue
                        if not link.startswith('http'):
                            link = 'https://x.com' + link
                        link = link.split('?')[0]
                        if link in seen_links:
                            continue
                        seen_links.add(link)
                        uid = hashlib.md5(link.encode()).hexdigest()
                        if uid not in seen:
                            new_seen.append(uid)
                            message = f"{account['emoji']} *New post on {account['name']}!*\n\n🔗 {link}\n\nGo engage 👇"
                            post_to_slack(message)
                            print(f"  Sent: {link}")

                context.close()

            except Exception as e:
                print(f"  Error: {e}")

        browser.close()

    save_seen(seen + new_seen)
    print("Done.")

if __name__ == '__main__':
    main()
