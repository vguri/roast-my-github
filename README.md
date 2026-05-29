# Roast My GitHub

A web app that fetches your public GitHub profile and repos, then uses Claude AI to roast you. Six roast styles. No mercy.

**Live demo:** [Replit URL — add after deploy]

---

## What it does

- Fetches public repos and profile data via the GitHub REST API
- Sends the data to Claude AI with a style-specific prompt and streams the response word by word
- Profile appears instantly (~0.8s). Roast streams in as it generates (~3s)
- Detects Albanian/Kosovar users by location and roasts them in Kosovo Albanian dialect
- Handles missing users, private profiles, rate limits, and empty inputs gracefully

## Roast styles

| Style | What it does |
|-------|-------------|
| Savage | Sharp, specific, dry — every joke anchored to real data |
| Pirate | Nautical metaphors, theatrical outrage, actual pirate vocabulary |
| Corporate | Passive-aggressive performance review, weaponized HR speak |
| Haiku | Two limericks (AABBA rhyme) with a punchline on line 5 |
| Shakespeare | Elizabethan English, dramatic, personally offended |
| Albanian | Kosovo Albanian dialect — everyday language, English tech words mixed in |

---

## How to run locally

### 1. Clone

```bash
git clone https://github.com/YOUR_USERNAME/roast-my-github.git
cd roast-my-github
```

### 2. Install dependencies

```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Add API keys

```bash
cp .env.example .env
```

Edit `.env`:
```
ANTHROPIC_API_KEY=your_key_here
GITHUB_TOKEN=your_github_token_here
```

- Anthropic key: [console.anthropic.com](https://console.anthropic.com)
- GitHub token: GitHub → Settings → Developer settings → Personal access tokens → no scopes needed. Raises rate limit from 60 → 5000 req/hour.

### 4. Run

```bash
python app.py
```

Open [http://localhost:8080](http://localhost:8080).

---

## How to run on Replit

1. Fork this repo on GitHub
2. Go to [replit.com](https://replit.com) → Create Repl → Import from GitHub
3. In the Replit Secrets tab, add `ANTHROPIC_API_KEY` and `GITHUB_TOKEN`
4. Click Run — dependencies install automatically
5. Public URL appears at the top of the Replit window

---

## The prompts I used

Each roast style has its own system prompt. The core structure:

```
System: [style-specific persona and rules — tone, format, what to reference]

User: GitHub Developer Profile:
- Name, bio, location, followers, following, public repos, member since, total stars, languages

Their repositories:
- repo-name (language, N stars): description
...

Roast this developer now. [random angle — stats / repos / bio / languages / account age].
Under 140 words.
```

**What I tried first:**
My first prompt was just "roast this GitHub user." The output was generic — nothing specific to the person. The fix was feeding in exact repo names, star counts, and languages, then requiring every joke to reference real data. Vague insults that could apply to anyone got rewritten.

**Two-step loading:**
The first version called GitHub + Claude sequentially, so nothing appeared for ~11 seconds. I split it into `/profile` (GitHub only, ~0.8s) and `/roast` (Claude streaming). Profile card appears immediately, roast streams in word by word. The loading state says "Claude is cooking something brutal..." while you wait.

**Speed:**
Started with `claude-sonnet-4-6` (~10s). Switched to `claude-haiku-4-5-20251001` (~3s) — fast enough that streaming feels instant.

**Albanian style:**
Detects location field from GitHub API for Albanian/Kosovar cities. Uses a separate prompt written in Kosovo Albanian dialect with everyday language, English tech terms mixed in naturally (followers, stars, repos, commits), and real example roasts embedded so the model has patterns to follow rather than rules to interpret.

---

## What I'd do with more time

1. Cache GitHub data per username for 5 minutes — avoid re-fetching on style switches
2. Per-IP rate limiting on `/roast` to prevent abuse
3. Share card — generate a styled PNG of the roast to post on social
4. More Albanian examples embedded to improve dialect accuracy
5. Roast history in localStorage — see your last 5 victims
6. README deep-dive — fetch repo READMEs for even more specific jokes

---

## Stack

- Backend: Python / Flask
- Frontend: HTML + Tailwind CSS (CDN) + Vanilla JS
- AI: Anthropic Claude Haiku via Python SDK (streaming)
- Data: GitHub REST API v3
- Deploy: Replit

---

## Project structure

```
roast-my-github/
├── app.py              # Flask backend, GitHub fetch, Claude streaming
├── requirements.txt
├── .env.example
├── .replit
├── .gitignore
├── README.md
└── templates/
    └── index.html      # Full frontend — Tailwind, streaming JS, all UI
```
