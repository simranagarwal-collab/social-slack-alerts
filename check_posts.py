import json
import os
import hashlib
import requests
from playwright.sync_api import sync_playwright

SLACK_WEBHOOK = os.environ['SLACK_WEBHOOK']
LINKEDIN_EMAIL = os.environ['LINKEDIN_EMAIL']
LINKEDIN_PASSWORD = os.environ['LINKEDIN_PASSWORD']
SEEN_FILE = 'seen_posts.json'

LINKEDIN_PAGES = [
    {'name': 'Web3Finance Club LinkedIn', 'slug': 'web3financeclub'},
    {'name': 'Request Finance LinkedIn', 'slug': 'request-finance'},
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

def check_linkedin(page, seen):
    new_seen = []
    print("Logging into LinkedIn...")
    page.goto('https://www.linkedin.com/login')
    page.fill('#username', LINKEDIN_EMAIL)
    page.fill('#password', LINKEDIN_PASSWORD)
    page.click('button[type=submit]')
    page.wait_for_timeout(5000)
    print(f"Page title after login: {page.title()}")

    for account in LINKEDIN_PAGES:
        print(f"Checking {account['name']}...")
        page.goto(f"https://www.linkedin.com/company/{account['slug']}/posts/?feedView=all")
        page.wait_for_timeout(5000)
        print(f"Page title: {page.title()}")

        posts = page.query_selector_all('a[href*="feed/update"]')
        print(f"  Found {len(posts)} posts")

        seen_links = set()
        for post in posts[:5]:
            try:
                link = post.get_attribute('href') or ''
                if 'feed/update' not in link:
                    continue
                link = link.split('?')[0]
                if link in seen_links:
                    continue
                seen_links.add(link)
                if not link.startswith('http'):
                    link = 'https://www.linkedin.com' + link
                uid = hashlib.md5(link.encode()).hexdigest()
                if uid not in seen:
                    new_seen.append(uid)
                    message = f"🔵 *New post on {account['name']}!*\n\n🔗 {link}\n\nGo engage 👇"
                    post_to_slack(message)
                    print(f"  Sent to Slack: {link}")
            except Exception as e:
                print(f"  Error: {e}")

    return new_seen


def main():
    seen = load_seen()
    new_seen = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            new_seen = check_linkedin(page, seen)
        except Exception as e:
            print(f"LinkedIn error: {e}")
        finally:
            browser.close()

    save_seen(seen + new_seen)
    print("Done.")

if __name__ == '__main__':
    main()
