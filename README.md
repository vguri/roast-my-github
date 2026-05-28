# 🔥 Roast My GitHub

A web app that fetches your public GitHub profile and repos, then uses Claude AI to roast you in your chosen style. No mercy. No survivors.

**Live demo:** [Replit URL here]

---

## What it does

- Fetches public repos and profile data via the **GitHub REST API**
- Sends the data to **Claude claude-opus-4-5** with a carefully crafted roast prompt
- Returns a hilarious, personalized roast based on your actual repos, languages, star count, and bio
- **Detects Albanian users** (via GitHub location field) and roasts them in Albanian 🇦🇱
- Handles missing users, private profiles, and API errors gracefully

## Roast styles

| Style | Description |
|-------|-------------|
| Savage | Brutally honest comedy roast, no holds barred |
| Pirate | Arr, ye code be cursed, landlubber |
| Corporate | Passive-aggressive "constructive feedback" in full buzzword mode |
| Haiku | 5 devastating haikus (5-7-5) about your coding sins |
| Shakespearean | Elizabethan English, dramatic, poetic, and ruthless |

---

## How to run locally

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/roast-my-github.git
cd roast-my-github
```

### 2. Set up environment

```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Add your API keys

```bash
cp .env.example .env
```

Edit `.env`:
```
ANTHROPIC_API_KEY=your_key_here
GITHUB_TOKEN=optional_but_recommended
```

Get your Anthropic API key at [console.anthropic.com](https://console.anthropic.com).  
`GITHUB_TOKEN` is optional but raises the GitHub API rate limit from 60 → 5000 req/hour.

### 4. Run

```bash
python app.py
```

Open [http://localhost:5000](http://localhost:5000).

---

## How to run on Replit

1. Fork this repo on GitHub
2. Go to [replit.com](https://replit.com) → **Create Repl** → **Import from GitHub**
3. In the Replit **Secrets** tab, add:
   - `ANTHROPIC_API_KEY` → your Anthropic key
   - `GITHUB_TOKEN` → your GitHub token (optional)
4. Click **Run** — Replit will install dependencies and start the server
5. Your public URL will appear at the top of the Replit window

---

## The prompts I settled on

The core roast prompt structure:

```
System: You are a [STYLE] roast master. [style-specific instructions]

User: GitHub Developer Profile:
- Name, bio, location, followers, repos, languages, total stars
- List of up to 15 repos with language, stars, and description

Roast this developer in a funny, specific way based on the data above.
Reference their actual repos, languages, and stats. Keep it under 250 words.
```

**What I tried first:**  
My first prompt was generic — "roast this GitHub user." The output was bland and could have applied to anyone. The breakthrough was feeding in **specific repo data** (names, descriptions, languages, star counts) so Claude could make jokes about actual things like "your 47 abandoned todo-app repos" or "a shell script with 0 stars that you apparently consider your magnum opus."

**Albanian detection:**  
I check the GitHub API's `location` field for Albanian cities and country names (Albania, Kosovo, Tirana, Pristina, etc.). When detected, a separate Albanian-language system prompt fires instead. The model handles Albanian well and the jokes land differently — more personal.

**Style differentiation:**  
Each style has its own system prompt persona. The corporate style was the most fun to craft — the trick is that it never admits it's insulting you while being maximally devastating.

---

## Project structure

```
roast-my-github/
├── app.py              # Flask backend, GitHub API fetch, Claude API call
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── .replit             # Replit configuration
├── .gitignore
├── README.md
└── templates/
    └── index.html      # Single-page frontend (Tailwind CSS via CDN)
```

---

## What I'd do with more time

1. **Caching** — Cache GitHub data for ~5 minutes per username to reduce API calls
2. **Rate limiting** — Per-IP rate limit on the `/roast` endpoint to prevent abuse
3. **Share button** — Generate a shareable link/image of your roast (like a roast card)
4. **More languages** — Detect more languages beyond Albanian (e.g., based on repo README language)
5. **Streak counter** — Track how many users you've roasted in localStorage
6. **Repo deep-dive** — Fetch README content for even more personalized roasts
7. **Export as image** — Download your roast as a styled PNG to post on social

---

## Tech stack

- **Backend:** Python / Flask
- **Frontend:** HTML + Tailwind CSS (CDN) + Vanilla JS
- **AI:** Anthropic Claude claude-opus-4-5 via the official Python SDK
- **Data:** GitHub REST API v3
- **Deploy:** Replit (free tier)

---

*Built with Claude Code and an unhealthy amount of roast energy.*
