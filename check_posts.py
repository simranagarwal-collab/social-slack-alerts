import feedparser
import requests
import json
import os
from datetime import datetime, timezone
import hashlib

SLACK_WEBHOOK = os.environ['SLACK_WEBHOOK']
SEEN_FILE = 'seen_posts.json'

FEEDS = [
    {
        'name': 'Web3Finance Club LinkedIn',
        'url': 'https://rsshub.app/linkedin/company/web3financeclub',
        'emoji': '🔵'
    },
    {
        'name': 'Request Finance LinkedIn',
        'url': 'https://rsshub.app/linkedin/company/request-finance',
        'emoji': '🔵'
    },
    {
        'name': 'Web3Finance Club X',
        'url': 'https://rsshub.app/twitter/user/web3financeclub',
        'emoji': '🐦'
    },
    {
        'name': 'Request Finance X',
        'url': 'https://rsshub.app/twitter/user/RequestFinance',
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

    for feed in FEEDS:
        parsed = feedparser.parse(feed['url'])
        for entry in parsed.entries[:3]:
            uid = hashlib.md5((entry.get('link', '') + entry.get('title', '')).encode()).hexdigest()
            if uid not in seen:
                new_seen.append(uid)
                link = entry.get('link', '')
                title = entry.get('title', 'New post')[:200]
                message = f"{feed['emoji']} *New post on {feed['name']}!*\n\n{title}\n\n🔗 {link}\n\nGo engage 👇"
                post_to_slack(message)

    save_seen(seen + new_seen)

if __name__ == '__main__':
    main()
