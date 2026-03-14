"""
SmartShaadi AI SEO Blog Generator
Generates static HTML blog pages for Indian wedding planning topics.
Run: python ai_engine.py
Requires: GROQ_API_KEY environment variable
"""

import os
import json
import re
import time
import requests
from datetime import datetime
from xml.etree import ElementTree as ET


# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL   = "llama-3.3-70b-versatile"
BASE_URL      = "https://smartshaadi.online"

CITIES_FILE   = "cities.json"
TEMPLATE_FILE = "template.html"
SITEMAP_FILE  = "sitemap.xml"
OUTPUT_DIR    = "output"

INTERNAL_LINKS_HTML = """
<div class="smartshaadi-tools-cta">
  <h3>🪄 Try SmartShaadi AI Tools – Free!</h3>
  <p>Plan your dream wedding smarter with our free AI-powered tools:</p>
  <ul>
    <li><a href="/ai-budget-calculator.html">💰 AI Wedding Budget Calculator</a> – Get a personalised budget breakdown in seconds</li>
    <li><a href="/ai-invitation-writer.html">✉️ AI Invitation Writer</a> – Create beautiful bilingual wedding invitations</li>
    <li><a href="/ai-planning-timeline.html">📅 AI Planning Timeline</a> – Build your complete wedding countdown checklist</li>
  </ul>
</div>
"""


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def load_api_key() -> str:
    key = os.environ.get("GROQ_API_KEY", "").strip()
    if not key:
        raise EnvironmentError(
            "❌  GROQ_API_KEY environment variable is not set.\n"
            "    Export it first:  export GROQ_API_KEY=your_key_here"
        )
    return key


def load_cities() -> list[str]:
    with open(CITIES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Support both ["Delhi", ...] and {"cities": ["Delhi", ...]}
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("cities", list(data.values())[0])
    raise ValueError("cities.json must be a list or a dict with a 'cities' key.")


def load_template() -> str:
    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        return f.read()


def slugify(city: str) -> str:
    """Convert 'New Delhi' → 'new-delhi'"""
    return re.sub(r"[^a-z0-9]+", "-", city.lower()).strip("-")


def output_filename(city: str) -> str:
    return f"blog-{slugify(city)}-wedding-cost-2026.html"


def page_url(city: str) -> str:
    return f"{BASE_URL}/{output_filename(city)}"


# ─────────────────────────────────────────────
# ARTICLE GENERATION
# ─────────────────────────────────────────────
ARTICLE_PROMPT = """You are a friendly, expert Indian wedding planner writing a detailed blog post for SmartShaadi.online.

Write a comprehensive, human-like SEO blog article about wedding costs in {city}, India.

Title: Wedding Cost in {city} India – Complete Budget Breakdown (2026)

STRICT REQUIREMENTS:
- Length: exactly 900–1200 words of body content (not counting headings)
- Tone: warm conversational Hinglish – mix natural Hindi words/phrases into English sentences (like "yaar", "bilkul", "bas", "shaadi", "lekin", "sach mein", etc.)
- Feel like a real wedding planning guide written by a desi friend who has been there
- Use real, researched-style numbers specific to {city} (not generic)
- Include ALL sections listed below in order

REQUIRED SECTIONS (use <h2> tags for headings):

1. <h2>Introduction – Meet Priya & Rahul 💍</h2>
   A short story (3–4 sentences) about a fictional couple from {city} planning their wedding. Make it relatable and warm.

2. <h2>Average Wedding Cost in {city} (2026) 💰</h2>
   Overall budget range (budget, mid-range, lavish). Mention local context.

3. <h2>Venue Prices in {city} 🏛️</h2>
   Banquet halls, farmhouses, hotels. Give price ranges per day/event.

4. <h2>Catering Cost Per Plate in {city} 🍽️</h2>
   Veg & non-veg rates, typical guest count scenarios.

5. <h2>Decoration & Floral Budget 🌸</h2>
   Mehendi, sangeet, wedding day decor ranges.

6. <h2>Photography & Videography Cost 📸</h2>
   Per-day rates, cinematic vs standard packages.

7. <h2>Real Wedding Budget Example – 300 Guests 📋</h2>
   A realistic itemised table (use HTML <table> with columns: Item | Estimated Cost).

8. <h2>Money-Saving Tips for {city} Weddings 💡</h2>
   5–6 specific, actionable tips relevant to the city.

9. <h2>FAQs – {city} Wedding Cost 2026 ❓</h2>
   3–5 questions in <details>/<summary> HTML accordion format.

FORMATTING RULES:
- Use <p> tags for paragraphs
- Use <ul>/<li> for lists
- Use <strong> for emphasis on numbers/key phrases
- Use <table> for the budget breakdown (with thead/tbody)
- Do NOT include the <html>, <head>, <body> tags – body content only
- Do NOT include any markdown (no ``` or **)
- End the article just before the internal links section (I will inject that separately)

Write the full article now:"""


def generate_article(city: str, api_key: str) -> str:
    prompt = ARTICLE_PROMPT.format(city=city)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.75,
        "max_tokens": 2048,
    }

    response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=90)

    if response.status_code != 200:
        raise RuntimeError(
            f"Groq API error {response.status_code}: {response.text[:300]}"
        )

    data = response.json()
    return data["choices"][0]["message"]["content"].strip()


# ─────────────────────────────────────────────
# HTML ASSEMBLY
# ─────────────────────────────────────────────
def build_html(template: str, city: str, article_html: str) -> str:
    title = f"Wedding Cost in {city} India – Complete Budget Breakdown (2026)"
    content = article_html + "\n\n" + INTERNAL_LINKS_HTML

    html = template.replace("{{title}}", title)
    html = html.replace("{{city}}", city)
    html = html.replace("{{content}}", content)

    # Also inject year dynamically if template uses {{year}}
    html = html.replace("{{year}}", str(datetime.now().year))

    return html


def save_html(html: str, city: str) -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, output_filename(city))
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    return filepath


# ─────────────────────────────────────────────
# SITEMAP UPDATE
# ─────────────────────────────────────────────
def update_sitemap(cities: list[str]) -> None:
    """Add or update <url> entries for each generated page."""

    # Parse existing sitemap or create fresh
    if os.path.exists(SITEMAP_FILE):
        try:
            ET.register_namespace("", "http://www.sitemaps.org/schemas/sitemap/0.9")
            tree = ET.parse(SITEMAP_FILE)
            root = tree.getroot()
        except ET.ParseError:
            print("⚠️  sitemap.xml could not be parsed – creating a fresh one.")
            root = None
    else:
        root = None

    ns = "http://www.sitemaps.org/schemas/sitemap/0.9"

    if root is None:
        root = ET.Element(f"{{{ns}}}urlset")
        root.set("xmlns", ns)

    # Collect existing locs to avoid duplicates
    existing_locs = {
        loc.text
        for loc in root.iter(f"{{{ns}}}loc")
    }

    today = datetime.now().strftime("%Y-%m-%d")

    for city in cities:
        url = page_url(city)
        if url in existing_locs:
            # Update lastmod
            for url_el in root.iter(f"{{{ns}}}url"):
                loc_el = url_el.find(f"{{{ns}}}loc")
                if loc_el is not None and loc_el.text == url:
                    lastmod_el = url_el.find(f"{{{ns}}}lastmod")
                    if lastmod_el is not None:
                        lastmod_el.text = today
            continue

        url_el = ET.SubElement(root, f"{{{ns}}}url")
        ET.SubElement(url_el, f"{{{ns}}}loc").text = url
        ET.SubElement(url_el, f"{{{ns}}}lastmod").text = today
        ET.SubElement(url_el, f"{{{ns}}}changefreq").text = "monthly"
        ET.SubElement(url_el, f"{{{ns}}}priority").text = "0.8"

    # Pretty-print
    _indent_xml(root)

    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(SITEMAP_FILE, xml_declaration=True, encoding="utf-8")
    print(f"✅  sitemap.xml updated → {len(cities)} pages indexed")


def _indent_xml(elem: ET.Element, level: int = 0) -> None:
    """Recursive indent helper for Python < 3.9."""
    indent = "\n" + "  " * level
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = indent + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = indent
        for child in elem:
            _indent_xml(child, level + 1)
        if not child.tail or not child.tail.strip():
            child.tail = indent
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = indent


# ─────────────────────────────────────────────
# MAIN ORCHESTRATOR
# ─────────────────────────────────────────────
def main() -> None:
    print("\n" + "=" * 60)
    print("  SmartShaadi AI SEO Blog Generator  🪄")
    print("=" * 60 + "\n")

    # 1. Load config
    api_key  = load_api_key()
    cities   = load_cities()
    template = load_template()

    print(f"📍 Cities loaded     : {len(cities)}")
    print(f"🤖 Model             : {GROQ_MODEL}")
    print(f"📁 Output directory  : {OUTPUT_DIR}/\n")
    print("-" * 60)

    generated = []
    failed    = []

    for i, city in enumerate(cities, 1):
        print(f"\n[{i}/{len(cities)}] Generating article for {city}...")

        try:
            article_html = generate_article(city, api_key)
            html         = build_html(template, city, article_html)
            filepath     = save_html(html, city)

            generated.append(city)
            print(f"  ✅  Saved → {filepath}")

        except Exception as exc:
            failed.append(city)
            print(f"  ❌  Failed for {city}: {exc}")

        # Polite rate-limit buffer between requests
        if i < len(cities):
            time.sleep(2)

    # 2. Update sitemap for all successfully generated pages
    if generated:
        print("\n" + "-" * 60)
        update_sitemap(generated)

    # 3. Summary
    print("\n" + "=" * 60)
    print(f"  Done!  ✅ {len(generated)} generated  |  ❌ {len(failed)} failed")
    if failed:
        print(f"  Failed cities: {', '.join(failed)}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
