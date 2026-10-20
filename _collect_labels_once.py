import csv
import json
import ssl
import time
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import certifi


ROOT_ID = 50151036
TARGET = 200
API = "https://hacker-news.firebaseio.com/v0/item/{}.json"
SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())


class PostText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag in {"p", "br", "li", "blockquote"}:
            self.parts.append("\n")
        if tag == "a":
            self.links.append(dict(attrs).get("href", ""))

    def handle_endtag(self, tag):
        if tag == "a" and self.links:
            href = self.links.pop()
            if href:
                self.parts.append(f" ({href})")
        if tag in {"p", "li", "blockquote"}:
            self.parts.append("\n")

    def handle_data(self, data):
        self.parts.append(data)


def get_item(item_id):
    request = Request(API.format(item_id), headers={"User-Agent": "community-label-course/1.0"})
    for attempt in range(4):
        try:
            with urlopen(request, timeout=20, context=SSL_CONTEXT) as response:
                return item_id, json.load(response)
        except (HTTPError, URLError, TimeoutError):
            if attempt == 3:
                return item_id, None
            time.sleep(attempt + 1)


def plain_text(source):
    parser = PostText()
    parser.feed(source)
    return " ".join(" ".join(parser.parts).split())


def main():
    _, root = get_item(ROOT_ID)
    if not root:
        raise RuntimeError("Could not load the public HN discussion")

    pending = list(root.get("kids", []))
    seen = {ROOT_ID}
    rows = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        while pending and len(rows) < TARGET:
            batch = []
            while pending and len(batch) < 18:
                item_id = pending.pop(0)
                if item_id not in seen:
                    seen.add(item_id)
                    batch.append(item_id)
            for item_id, item in pool.map(get_item, batch):
                if not item:
                    continue
                pending.extend(item.get("kids", []))
                text = plain_text(item.get("text", ""))
                if item.get("type") == "comment" and text:
                    url = f"https://news.ycombinator.com/item?id={item_id}"
                    note = "cold" if len(rows) < 20 else "ai-pending"
                    rows.append({"text": text, "label": "", "note": f"{note}; {url}"})
                    if len(rows) == TARGET:
                        break

    if len(rows) < TARGET:
        raise RuntimeError(f"Found only {len(rows)} public comments, need {TARGET}")

    with open("labels.csv", "w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=("text", "label", "note"))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Collected {len(rows)} full comments; first 20 marked cold; remaining labels left blank for AI-assisted review.")


if __name__ == "__main__":
    main()