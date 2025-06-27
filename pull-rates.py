from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from bs4 import BeautifulSoup
import re
from datetime import datetime
import time

import os
import re
from pathlib import Path

url = "https://www.mariages.net/musique-mariage/resch--e316860/avis"
rate_path = Path("content/footer/rates")

### Read current rates ###

# List to store results
current_rates = []

# Iterate through all .md files
for file in rate_path.glob("*.md"):
    with file.open(encoding="utf-8") as f:
        content = f.read()

        # Match the frontmatter block
        match = re.search(r'^---\s*(.*?)\s*---', content, re.DOTALL | re.MULTILINE)
        if match:
            frontmatter = match.group(1)

            # AUTHOR
            author_match = re.search(r'author:\s*["\']?(.*?)["\']?\s*$', frontmatter, re.MULTILINE)
            author = author_match.group(1).strip()

            # DATE
            date_match = re.search(r'date:\s*["\']?(.*?)["\']?\s*$', frontmatter, re.MULTILINE)
            date_text = date_match.group(1).strip()
            date = datetime.strptime(date_text, "%Y-%m-%d")

            if author_match and date_match:
                current_rates.append({'author': author, 'date': date})

# Print results
print("=== Current Rates: ===")
for r in current_rates:
    print(f"Date: {r['date'].strftime('%Y-%m-%d')}")
    print(f"Author: {r['author']}\n")

### Fetch remote rates ###

# Set up Chrome headless browser
options = Options()
options.add_argument('--headless')
# options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
options.add_argument("--lang=fr-FR")
options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(options=options)

# Load the page
url = "https://www.mariages.net/musique-mariage/resch--e316860/avis"
driver.get(url)

# Wait for page content to load
time.sleep(5)

html = driver.page_source

# Parse HTML with BeautifulSoup
soup = BeautifulSoup(html, 'html.parser')

# Extract review blocks
reviews = soup.find_all('li', class_='storefrontReviewsTileSubpage')

remote_rates = []

for review in reviews:
    try:
        print(review)

        # AUTHOR
        author_div = review.find('div', class_='storefrontReviewsTileInfo')
        author = author_div.get_text(strip=True).split('Envoyé le')[0].strip()
        print(author)

        # DATE
        date_span = review.find('span', class_='storefrontReviewsTileInfo__date')
        date_text = date_span.get_text(strip=True).replace('Envoyé le ', '')
        date = datetime.strptime(date_text, "%d/%m/%Y")
        print(date)

        # NOTE
        note_div = review.find('div', class_='srOnly')
        note_match = re.search(r'Note globale (\d(?:,\d)?) sur 5', note_div.get_text())
        note = float(note_match.group(1).replace(',', '.')) if note_match else None
        print(note)

        # TITLE
        title = review.find('p', class_='storefrontReviewsTileContent__title').get_text(strip=True)

        # DESCRIPTION
        description_div = review.find('div', class_='app-full-description')
        description = description_div.get_text(strip=True)

        remote_rates.append({
            'author': author,
            'date': date,
            'note': note,
            'title': title,
            'description': description
        })
    except Exception as e:
        print(f"Skip review: {e}")
        continue

# Sort by date
remote_rates.sort(key=lambda x: x['date'])

print("=== Remote Rates: ===")
for r in remote_rates:
    print(f"Date: {r['date'].strftime('%Y-%m-%d')}")
    print(f"Author: {r['author']}")
    print(f"Note: {r['note']}")
    print(f"Title: {r['title']}")
    print(f"Description: {r['description']}\n")


### Check new rates

new_rates = []
for remote_rate in remote_rates:
  # current_rates.find
  if len(list(filter(lambda rate: rate['author'] == remote_rate['author'], current_rates))) == 0:
    new_rates.append(remote_rate)
  # li = list(filter(lambda x: x % 2 == 0, arr))

# Print results
if len(new_rates) != 0:
  print("=== New Rates: ===")
  for new_rate in new_rates:
      print(f"Date: {r['date'].strftime('%Y-%m-%d')}")
      print(f"Author: {r['author']}")
      print(f"Note: {r['note']}")
      print(f"Title: {r['title']}")
      print(f"Description: {r['description']}\n")

if len(new_rates) == 0:
  print("No new rate found")
  exit()

### Check new rates

def write_rate(rate):
    date = rate['date'].strftime('%Y-%m-%d')
    author = rate['author']
    note = rate['note']
    title = rate['title']
    description = rate['description']

    safe_author = "".join(c for c in author if c.isalnum() or c in ('-', '_')).lower()

    # Build file path
    filename = f"rate-{safe_author}-{date}.md"
    file_path = rate_path / filename

    # Markdown content
    content = f"""---
title: "{author}"
author: "{author}"
date:  {date}
rate: {note}
---

**{title}**

{description}
"""
    # Ensure target directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Write file
    file_path.write_text(content, encoding='utf-8')
    print(f"Write {file_path}")

for new_rate in new_rates:
    write_rate(new_rate)

Path("new_rate.txt").write_text("1", encoding='utf-8')


