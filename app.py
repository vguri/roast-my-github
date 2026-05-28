import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=True)
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

ROAST_RULES = """FORMAT:
- Write exactly 3 short paragraphs, separated by a blank line.
- Each paragraph is 2-3 sentences. Total under 130 words.
- No intro lines like "Ladies and gentlemen" or "Let me introduce..."
- No markdown, no headers, no bullet points, no emoji, no bold.

TONE:
- Sarcastic, dry, like a friend who's a little too honest after two drinks.
- Every single joke must reference something REAL from their profile: repo names, languages, star counts, follower counts, bio, location.
- No generic insults that could apply to anyone. Be specific.
- The last sentence of the last paragraph should be the hardest hit.
- Vary sentence length. Short punchy lines. Then occasionally one that takes its time and goes somewhere unexpected.
"""

STYLE_PROMPTS = {
    "savage": f"You write short, devastating roasts of GitHub developers. No mercy, no sugarcoating — just sharp, specific, funny observations that would make their coworkers lose it.\n\n{ROAST_RULES}",
    "pirate": f"You write roasts of GitHub developers in pirate voice — but a smart pirate, not a cartoon one. Drop pirate phrases naturally (arr, landlubber, Davy Jones, walk the plank) but only where they actually land, not every sentence.\n\n{ROAST_RULES}",
    "corporate": f"You write roasts disguised as performance review feedback. Passive-aggressive, weaponized HR-speak. Use corporate jargon (bandwidth, circle back, low-hanging fruit, synergy) but only 2-3 times — the joke is the contrast between the professional tone and the brutal truth underneath.\n\n{ROAST_RULES}",
    "haiku": """You roast GitHub developers using exactly 3 haikus (5-7-5 syllables each).

Format: three haikus, each on its own line, blank line between them.
No intro. No outro. Just the haikus.
Each one should reference something specific from their profile.
The last one should be the most devastating.""",
    "shakespearean": f"You write roasts of GitHub developers in Shakespearean style — dramatic, poetic, using thee/thou/dost/forsooth occasionally. It should feel theatrical but the insults should still land clearly. Not so old-English that it becomes unreadable.\n\n{ROAST_RULES}",
}

STYLE_PROMPTS_ALBANIAN = {
    "savage": f"Ti shkruan talljet e shkurtra dhe shkatërruese për zhvillues GitHub. Asnjë mëshirë — vetëm vërejtje të mprehta, specifike dhe qesharake.\n\nFORMAT:\n- Saktësisht 3 paragrafë të shkurtër, të ndarë me rresht bosh.\n- Çdo paragraf 2-3 fjali. Gjithsej nën 130 fjalë.\n- Asnjë intro, asnjë markdown, asnjë emoji.\n- Çdo shaka duhet të bazohet në diçka REALE nga profili: emrat e repo-ve, gjuhët, yjet, ndjekësit.\n- Fjalia e fundit godet më fort.\nShkruaj VETËM në shqip.",
    "pirate": f"Ti shkruan talljet për zhvillues GitHub me zërin e një piratu shqiptar. Fjalë pirate natyrshëm, jo me forcë.\n\nFormat: 3 paragrafë, ndarë me rresht bosh. Nën 130 fjalë. Specifik. Shkruaj VETËM në shqip.",
    "corporate": f"Ti shkruan talljet e maskuara si feedback i performancës korporative. Pasiv-agresiv, zhargon HR. Kontrast midis tonit profesional dhe së vërtetës brutale.\n\nFormat: 3 paragrafë, ndarë me rresht bosh. Nën 130 fjalë. Shkruaj VETËM në shqip.",
    "haiku": "Ti tallesh me zhvillues GitHub me saktësisht 3 haiku (5-7-5 rrokje secili). Çdo haiku në rresht të veçantë, rresht bosh mes tyre. Asnjë intro. Specifik për profilin e tyre. Shkruaj VETËM në shqip.",
    "shakespearean": f"Ti shkruan talljet për zhvillues GitHub në stilin shekspirian — dramatik, poetik, me 'ti/ty/dost' herë pas here. Të kuptueshëm por teatral.\n\nFormat: 3 paragrafë, ndarë me rresht bosh. Nën 130 fjalë. Shkruaj VETËM në shqip.",
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
        instruction = "Tallo këtë zhvillues tani. Përdor të dhënat reale — emrat e repo-ve, statistikat, gjuhët. Shkurtër, prerë, nën 120 fjalë. MOS shkruaj asnjë fjalë në anglisht."
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
        instruction = "Roast this developer now. Use the real data above — specific repo names, stats, languages. Short, punchy, under 120 words."

    style_map = STYLE_PROMPTS_ALBANIAN if albanian else STYLE_PROMPTS
    system = style_map.get(style, style_map["savage"])

    return system, f"{user_section}\n\n{instruction}"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/profile", methods=["POST"])
def profile():
    data = request.get_json()
    username = (data.get("username") or "").strip()

    if not username:
        return jsonify({"error": "Please enter a GitHub username."}), 400
    if len(username) > 39 or not all(c.isalnum() or c in "-" for c in username):
        return jsonify({"error": "That doesn't look like a valid GitHub username."}), 400

    gh_data = fetch_github_data(username)
    if "error" in gh_data:
        messages = {
            "user_not_found": f"No GitHub user found with the username '{username}'. Maybe they deleted their account out of shame?",
            "rate_limited": "GitHub API rate limit hit. Try again in a moment.",
            "github_error": "GitHub is having a moment. Try again shortly.",
        }
        return jsonify({"error": messages.get(gh_data["error"], "Something went wrong.")}), 404

    user = gh_data["user"]
    repos = gh_data["repos"]
    albanian = is_albanian(user.get("location", ""))

    return jsonify({
        "user": {
            "login": user.get("login"),
            "name": user.get("name"),
            "avatar_url": user.get("avatar_url"),
            "public_repos": user.get("public_repos", 0),
            "followers": user.get("followers", 0),
            "location": user.get("location"),
        },
        "albanian": albanian,
        "repos": [{"name": r.get("name"), "language": r.get("language"), "stargazers_count": r.get("stargazers_count", 0), "description": r.get("description")} for r in repos[:15]],
    })


@app.route("/roast", methods=["POST"])
def roast():
    data = request.get_json()
    user = data.get("user")
    repos = data.get("repos", [])
    style = data.get("style", "savage")
    albanian = data.get("albanian", False)

    if not user:
        return jsonify({"error": "Missing user data."}), 400

    system_prompt, user_prompt = build_roast_prompt(user, repos, style, albanian)

    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=320,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        roast_text = message.content[0].text
    except Exception as e:
        return jsonify({"error": "The roast machine broke. Even Claude can't handle this one."}), 500

    return jsonify({"roast": roast_text, "style": style})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
