import os
from dotenv import load_dotenv
load_dotenv()
import requests
from flask import Flask, render_template, request, jsonify
from anthropic import Anthropic

app = Flask(__name__)
client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

ALBANIAN_LOCATION_KEYWORDS = [
    "albania", "shqipëri", "shqiperia", "shqipëria", "tirana", "tiranë",
    "kosovo", "kosovë", "pristina", "prishtina", "shkodër", "shkodra",
    "durrës", "durres", "vlorë", "vlore", "elbasan", "korçë", "korce",
    "north macedonia", "maqedoni", "tetovo", "tetovë", "AL", "XK"
]

STYLE_PROMPTS = {
    "savage": "You are a brutally savage comedy roast master. Hold absolutely nothing back. Be ruthless, cutting, and merciless — but keep it funny, not cruel.",
    "pirate": "You are a pirate captain roasting a fellow sailor. Use pirate slang (arr, blimey, landlubber, davy jones, etc.) throughout. Be dramatic and theatrical.",
    "corporate": "You are a passive-aggressive corporate manager giving 'constructive feedback' in a performance review. Use buzzwords like 'synergy', 'bandwidth', 'circle back', 'low-hanging fruit'. Make it painfully corporate.",
    "haiku": "You are a Zen master who roasts exclusively in haiku format (5-7-5 syllables). Write exactly 5 haikus about this developer. Each haiku should land like a quiet but devastating insult.",
    "shakespearean": "You are William Shakespeare himself, roasting this developer in Elizabethan English. Use 'thee', 'thou', 'dost', 'wherefore', 'forsooth'. Make it dramatic and poetic.",
}

STYLE_PROMPTS_ALBANIAN = {
    "savage": "Je një komedian i egër shqiptar i specializuar në talljet. Mos mbaj asgjë mbrapa. Ji i pamëshirshëm por qesharak — jo mizor. Shkruaj VETËM në shqip.",
    "pirate": "Je një kapiten pirat shqiptar. Përdor shprehje dramatike dhe teatrale. Shkruaj VETËM në shqip.",
    "corporate": "Je një menaxher korporativ pasiv-agresiv duke dhënë 'feedback konstruktiv'. Përdor zhargon korporativ. Shkruaj VETËM në shqip.",
    "haiku": "Je një mjeshtër Zen që talljet vetëm me haiku (5-7-5 rrokje). Shkruaj 5 haiku për këtë zhvillues. Shkruaj VETËM në shqip.",
    "shakespearean": "Je William Shakespeare duke tallur këtë zhvillues në stilin dramatik elizabetan, por në shqip. Shkruaj VETËM në shqip.",
}


def is_albanian(location: str) -> bool:
    if not location:
        return False
    loc = location.lower()
    return any(kw.lower() in loc for kw in ALBANIAN_LOCATION_KEYWORDS)


def fetch_github_data(username: str) -> dict:
    headers = {"Accept": "application/vnd.github.v3+json"}
    gh_token = os.environ.get("GITHUB_TOKEN")
    if gh_token:
        headers["Authorization"] = f"token {gh_token}"

    user_resp = requests.get(
        f"https://api.github.com/users/{username}", headers=headers, timeout=10
    )
    if user_resp.status_code == 404:
        return {"error": "user_not_found"}
    if user_resp.status_code == 403:
        return {"error": "rate_limited"}
    if not user_resp.ok:
        return {"error": "github_error"}

    user = user_resp.json()

    repos_resp = requests.get(
        f"https://api.github.com/users/{username}/repos",
        headers=headers,
        params={"sort": "updated", "per_page": 30},
        timeout=10,
    )
    repos = repos_resp.json() if repos_resp.ok else []
    if isinstance(repos, dict):  # error response
        repos = []

    return {"user": user, "repos": repos}


def build_roast_prompt(user: dict, repos: list, style: str, albanian: bool) -> str:
    name = user.get("name") or user.get("login")
    bio = user.get("bio") or "no bio (classic)"
    location = user.get("location") or "unknown location"
    followers = user.get("followers", 0)
    following = user.get("following", 0)
    public_repos = user.get("public_repos", 0)
    company = user.get("company") or "unemployed probably"
    created_at = user.get("created_at", "")[:4]

    repo_details = []
    for r in repos[:15]:
        lang = r.get("language") or "no language"
        stars = r.get("stargazers_count", 0)
        name_r = r.get("name", "unnamed")
        desc = r.get("description") or "no description"
        repo_details.append(f"- {name_r} ({lang}, {stars} stars): {desc}")

    repo_text = "\n".join(repo_details) if repo_details else "No public repos. Impressive commitment to privacy (or laziness)."

    total_stars = sum(r.get("stargazers_count", 0) for r in repos)
    languages = list({r.get("language") for r in repos if r.get("language")})

    if albanian:
        user_section = f"""Zhvilluesi GitHub:
- Emri: {name}
- Bio: {bio}
- Vendndodhja: {location}
- Ndjekës: {followers} | Duke ndjekur: {following}
- Repo publike: {public_repos}
- Kompania: {company}
- Anëtar që nga: {created_at}
- Yje total: {total_stars}
- Gjuhët e përdorura: {', '.join(languages) if languages else 'asnjë'}

Repo-t e tyre:
{repo_text}"""
        instruction = "Tallo këtë zhvillues në mënyrë qesharake bazuar në të dhënat e mësipërme. Ji specifik — referoju repo-ve reale, gjuhëve dhe statistikave. Bëje personale dhe qesharake. MOS shkruaj asnjë fjalë në anglisht."
    else:
        user_section = f"""GitHub Developer Profile:
- Name: {name}
- Bio: {bio}
- Location: {location}
- Followers: {followers} | Following: {following}
- Public repos: {public_repos}
- Company: {company}
- Member since: {created_at}
- Total stars: {total_stars}
- Languages used: {', '.join(languages) if languages else 'none'}

Their repositories:
{repo_text}"""
        instruction = "Roast this developer in a funny, specific way based on the data above. Reference their actual repos, languages, and stats. Make it personal and hilarious. Keep it under 250 words."

    style_map = STYLE_PROMPTS_ALBANIAN if albanian else STYLE_PROMPTS
    system = style_map.get(style, style_map["savage"])

    return system, f"{user_section}\n\n{instruction}"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/roast", methods=["POST"])
def roast():
    data = request.get_json()
    username = (data.get("username") or "").strip()
    style = data.get("style", "savage")

    if not username:
        return jsonify({"error": "Please enter a GitHub username."}), 400

    if len(username) > 39 or not all(c.isalnum() or c in "-" for c in username):
        return jsonify({"error": "That doesn't look like a valid GitHub username."}), 400

    gh_data = fetch_github_data(username)

    if "error" in gh_data:
        messages = {
            "user_not_found": f"No GitHub user found with the username '{username}'. Maybe they deleted their account out of shame?",
            "rate_limited": "GitHub API rate limit hit. Try adding a GITHUB_TOKEN to your environment.",
            "github_error": "GitHub is having a moment. Try again shortly.",
        }
        return jsonify({"error": messages.get(gh_data["error"], "Something went wrong.")}), 404

    user = gh_data["user"]
    repos = gh_data["repos"]
    albanian = is_albanian(user.get("location", ""))

    system_prompt, user_prompt = build_roast_prompt(user, repos, style, albanian)

    try:
        message = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=600,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        roast_text = message.content[0].text
    except Exception as e:
        return jsonify({"error": "The roast machine broke. Even Claude can't handle this one."}), 500

    return jsonify({
        "roast": roast_text,
        "user": {
            "login": user.get("login"),
            "name": user.get("name"),
            "avatar_url": user.get("avatar_url"),
            "public_repos": user.get("public_repos", 0),
            "followers": user.get("followers", 0),
            "location": user.get("location"),
        },
        "albanian": albanian,
        "style": style,
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
