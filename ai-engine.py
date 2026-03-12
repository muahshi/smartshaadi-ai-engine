import json
import requests

API_KEY="YOUR_GROQ_API_KEY"

template=open("template.html").read()

cities=json.load(open("cities.json"))

urls=[]

for city in cities:

    keyword=f"wedding cost in {city}"

    prompt=f"""
Write a 900 word SEO article about {keyword} in India.

Structure:

Intro story
Average wedding cost
Venue cost
Food cost
Decor cost
Real couple example
Budget saving tips
FAQ

Tone conversational Hinglish.
"""

    r=requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization":f"Bearer {API_KEY}",
            "Content-Type":"application/json"
        },
        json={
            "model":"llama-3.3-70b-versatile",
            "messages":[{"role":"user","content":prompt}]
        }
    )

    content=r.json()["choices"][0]["message"]["content"]

    title=f"{city} Wedding Cost 2026 – Honest Budget Guide"

    page=template.replace("{{content}}",content)
    page=page.replace("{{city}}",city)
    page=page.replace("{{title}}",title)

    filename=f"output/blog-{city.lower()}-wedding-cost-2026.html"

    open(filename,"w").write(page)

    urls.append(f"https://smartshaadi.online/blog-{city.lower()}-wedding-cost-2026.html")

print("Blogs generated!")
