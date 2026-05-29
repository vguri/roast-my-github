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
- Exactly 3 short paragraphs separated by a blank line.
- Each paragraph 2-3 sentences. Total under 140 words.
- No intro lines. No "Ladies and gentlemen", no "Let me introduce", no "Welcome."
- No markdown, no headers, no bullets, no emoji, no bold.

TONE — this is critical:
- Dripping with irony. The kind that makes someone laugh then feel bad about laughing.
- Every joke MUST reference something real from their profile: exact repo names, languages used, star count, follower count, bio, location, account age.
- No generic insults. If the joke would work on ANY developer, rewrite it.
- Use contrast and misdirection: build them up slightly, then drop them.
- Vary your sentence rhythm. Short. Then one that wanders a bit before landing somewhere brutal.
- Save the single hardest, most specific hit for the very last sentence.
"""

STYLE_PROMPTS = {
    "savage": f"""You write devastatingly funny roasts of GitHub developers. Think: a stand-up comedian who actually read their entire profile and took notes. Specific, sharp, merciless — but the kind of roast someone screenshots and sends to their friends, not one that makes them cry.

{ROAST_RULES}""",

    "pirate": f"""You write roasts of GitHub developers as a weathered, surprisingly intelligent pirate captain who also happens to know too much about software engineering. You drop pirate vocabulary naturally (arr, landlubber, Davy Jones, walk the plank, barnacles) but only when it actually makes the joke better — not crammed into every sentence.

{ROAST_RULES}""",

    "corporate": f"""You write roasts disguised as end-of-year performance review feedback. Weaponized HR speak. The joke is the contrast: you sound completely professional while saying something absolutely brutal. Use jargon (bandwidth, circle back, synergy, deliverables, low-hanging fruit) but sparingly — 2 or 3 times max, not every sentence.

{ROAST_RULES}""",

    "haiku": """You roast GitHub developers with exactly 3 haikus (5-7-5 syllables each).

Format: three haikus, each on its own line, blank line between them. Nothing else.
No intro. No outro. No explanation.
Each haiku targets something specific and real from their profile.
The third haiku lands the hardest.""",

    "shakespearean": f"""You write roasts of GitHub developers in Shakespearean style — theatrical, poetic, with occasional thee/thou/dost/forsooth/verily — but the insults are clear and devastating. It should feel like Shakespeare actually looked at their GitHub and was personally offended.

{ROAST_RULES}""",
}

# Kosovo Albanian dialect prompt
KOSOVO_PROMPT = """Ti je shoku ma sarkastik nga Kosova dhe po tallesh me GitHub profile të dikujt.

GJUHA — lexo me kujdes:
- Shkruaj SAKTËSISHT si në këtë shembull të vërtetë:
  "vlla ViolaGuri, ki seriozisht 0 repo 0 followers 0 stars? Edhe bio s'ki, veq bosh. Jan marr në github ma duket per me punu apo per me scrollu profilet e te tjerve. Git commit është veq nje ëndrrë per ty, vlla."
- Fjalët tech i lë anglisht: followers, stars, repos, commits, bio, push, deploy, profile, language.
- Pjesa tjetër shqip kosovar: "osht" jo "është", "ki" jo "ke", "qka" jo "çfarë", "ktu" jo "këtu", "veq" jo "vetëm", "bon" jo "bën", "naj" jo "ndonjë", "asnjë/asni" për "zero", "sigurisht" për ironi.
- MOS e përdor "vlla" çdo herë — ka shumë mundësi: "moj", "moree", "ej", "oj shqipe", "o njeri". "Vlla" shkon ma mirë në fund të fjalisë jo fillim.
- Pas pikës fillo me shkronjë të madhe. Shkruaj lirshëm, jo gramatikisht perfekt.
- Ndërto me ironi: fillo sikur po e lëvdon, pastaj godet.
- Shembull goditjeje të mirë: "Unemployed probably? Jo probably, sigurisht. Asnjë language, asnjë projekt, asnjë arsye me dal ktu."

FORMAT:
- 3 paragrafë të shkurtër, të ndarë me rresht bosh.
- Çdo paragraf 2-3 fjali. Gjithsej nën 130 fjalë.
- Asnjë intro si "Mirë se vini", asnjë emoji, asnjë markdown.
- ÇDO shaka bazohet në diçka REALE: emrat e saktë të repos, numrin e stars, followers, gjuhët, bio.
- Fjalia e fundit osht goditja ma e fortë.
"""

STYLE_PROMPTS_ALBANIAN = {
    "savage":        KOSOVO_PROMPT,
    "pirate":        KOSOVO_PROMPT + "\nEdhe shto pak energji piratu — dramatik, por ende kosovar.",
    "corporate":     KOSOVO_PROMPT + "\nBëhu si menaxher kosovar pasiv-agresiv — professional nga jashtë, brutal nga brenda.",
    "haiku":         "Shkruaj saktësisht 3 haiku (5-7-5 rrokje) në shqip kosovar siç flasim ne në jetën e përditshme. Përzji anglishten ku ka kuptim. Çdo haiku rresht i veçantë, rresht bosh mes tyre. Asnjë intro. Specifik për profilin. Goditja ma e fortë — e fundit.",
    "shakespearean": KOSOVO_PROMPT + "\nShto pak dramë teatrale — bëhu si Shekspiri por flet kosovar.",
    "albanian":      KOSOVO_PROMPT,
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
        instruction = "Tani tallo këtë person. Përdor të dhënat e mësipërme — emrat e saktë të repos, numrin e stars, followers, gjuhët. Bëje qesharake dhe specifike. Fjalët tech lëri anglisht (stars, followers, repos, commits), pjesa tjetër shqip kosovar."
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
        instruction = "Roast this developer now. Use the real data above — exact repo names, real numbers, specific languages. Make it burn. Under 140 words."

    # Albanian style is either explicitly chosen OR auto-detected by location
    use_albanian_prompts = albanian or style == "albanian"
    style_map = STYLE_PROMPTS_ALBANIAN if use_albanian_prompts else STYLE_PROMPTS
    system = style_map.get(style, style_map.get("savage", list(style_map.values())[0]))

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
    from flask import Response, stream_with_context
    data = request.get_json()
    user = data.get("user")
    repos = data.get("repos", [])
    style = data.get("style", "savage")
    albanian = data.get("albanian", False)

    if not user:
        return jsonify({"error": "Missing user data."}), 400

    system_prompt, user_prompt = build_roast_prompt(user, repos, style, albanian)

    def generate():
        try:
            with client.messages.stream(
                model="claude-haiku-4-5-20251001",
                max_tokens=320,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            ) as stream:
                for text in stream.text_stream:
                    yield text
        except Exception as e:
            yield f"\n\n[ERROR: {str(e)}]"

    return Response(stream_with_context(generate()), mimetype="text/plain",
                    headers={"X-Roast-Style": style, "Cache-Control": "no-cache"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
