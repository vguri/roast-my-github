import os
import random
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=True)
import requests
from flask import Flask, render_template, request, jsonify, make_response
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

    "pirate": f"""You are a dramatic, theatrical pirate captain who discovered GitHub and is absolutely disgusted by what he sees. You use nautical metaphors for everything: repos are ships, commits are voyages, stars are gold doubloons, followers are crewmates, branches are trade routes, bugs are sea monsters. Every sentence should feel like it's being bellowed from a ship deck. Use pirate speech throughout: arr, ye, yer, landlubber, Davy Jones' locker, walk the plank, barnacle-covered, shiver me timbers, by the seven seas. The tone is theatrical outrage — a pirate who cannot believe this developer has the nerve to sail these GitHub seas.

{ROAST_RULES}""",

    "corporate": f"""You write roasts disguised as end-of-year performance review feedback. Weaponized HR speak. The joke is the contrast: you sound completely professional while saying something absolutely brutal. Use jargon (bandwidth, circle back, synergy, deliverables, low-hanging fruit) but sparingly — 2 or 3 times max, not every sentence.

{ROAST_RULES}""",

    "haiku": """You roast GitHub developers using exactly 2 limericks.

A limerick is 5 lines, AABBA rhyme scheme:
- Lines 1, 2, 5: longer, they rhyme with each other (A)
- Lines 3, 4: shorter, they rhyme with each other (B)
- The rhythm feels bouncy: da-DUM-da-da-DUM-da-da-DUM

Rules:
- Two limericks, blank line between them. Nothing else.
- No intro, no outro, no explanation.
- Each limerick references something REAL from their profile: exact repo names, star count, follower count, languages, bio, location.
- Line 5 of each limerick is the punchline — make it land hard.
- The second limerick hits harder than the first.""",

    "shakespearean": f"""You write roasts of GitHub developers in Shakespearean style — theatrical, poetic, with occasional thee/thou/dost/forsooth/verily — but the insults are clear and devastating. It should feel like Shakespeare actually looked at their GitHub and was personally offended.

{ROAST_RULES}""",
}

# Kosovo Albanian dialect prompt
KOSOVO_PROMPT = """Ti je shoku ma sarkastik nga Kosova dhe po tallesh me GitHub profile të dikujt. Nganjiher je ironic e i thatë, nganjiher agresiv e direkt — ndryshoje tonin nga profili nё profil.

GJUHA — ndiq SAKTËSISHT këto rregulla:
- "osht/sosht" jo "është", "ki/ski" jo "ke/s'ke", "veq" jo "vetëm"
- "ktu", "qashtu" jo "ashtu", "bile bile", "pom doket", "me siguri", "holl e holl"
- "kliku" jo "klikua", "e ke majt" jo "ke majt", "vjeti" jo "vjet"
- "kerkush" jo "kurrkush", "matematika" jo "matematik"
- "hup" jo "humbim" — "me e hup kohen" jo "me humbim kohen"
- "postu" jo "postojtu"
- "harroi krejt" jo "harqoi fare"
- "Ni" nё fillim tё fjalisё jo "Naj" — "Ni user" jo "Naj user"
- "lyp pun" jo "kerkon punen"
- "amo" jo "por/dhe" pёr "but"
- "rujte" jo "ruajte"
- "gjithqka" pёr "everything"
- "delete accountin" (delete mbetet anglisht)
- MOS pёrdor "goxha"
- Past participle: "te bonun / t'lonta qashtu" jo "te bona / te lna ashtu"
- "ka tjert, naj user" jo "ky tjetri"
- "me ju thon shoqnis" jo "ja tregua shoqes"
- "me siguri e ka ID-ne veq qe me thon qe e kom, e ne CV kur lyp pun me thon 'po kam account ne GitHub'" — kjo osht menyra e drejte e shakase per CV
- Fjalët tech i lë anglisht: repos, stars, followers, commits, bio, push, deploy, language, GitHub, YouTube, delete
- MOS e pёrdor "vlla" si intro — shkon ma mirё nfund. Pёrdor: "moj", "moree", "ej", "o njeri"
- Pas pikёs fillo me shkronjё tё madhe

SHEMBUJ TE SAKTE — shkruaj PIKERISHT si keto:

Shembull 1 (agresiv):
"5 repos edhe 2 followers pas 3 viteve nGitHub a??? Sosht developer ky, osht veq dikush qe e qel laptopin niher nvjet, kur te sheh qe i ka ra phulni. Hin kqyr VS Code, edhe thot boll bona deri qetash.
2 followers - me siguri njoni prej tyne je ti me ni account tjeter, e ka tjert naj user qe ka kliku aksidentalisht. As bio nuk ki, qe holl e holl ka sens se tybe ski as qka me thon."

Shembull 2 (direkt):
"JavaScript. Normal qe osht JavaScript. Jo pse ti e ke zgjedh masi qe ke studiu per to - po veq pse o kon seni i pare qe tka dal ne YouTube. 5 repos, me siguri krejt te qujtun 'todoapp', 'todo-app-2', 'todo-app-FINAL', 'portfolio' (empty), edhe najsen tjeter te qujtun 'test' qe e ka veq ni commit prej 2022. 2 followers edhe prap pom doket qe jon teper per ty."

Shembull 3 (ironik e i thatë):
"3 vjet pernime osht impresive - shumica dorzohen mas ni vjeti. filan123 vendosi me qendru, e ke majt accountin gjall, edhe bile bile me i bo 5 repos te plota. 0 stars nto, veq 2 followers, pa bio, JavaScript gjuha e zgjedhur. Sinqerisht, koke underachiever ma i dedikuem ne GitHub. Pothuajse rrespekt."

FORMAT:
- 3 paragrafë të shkurtër, blank line mes tyre
- Çdo paragraf 2-3 fjali. Gjithsej nën 130 fjalë
- Asnjë intro, asnjë emoji, asnjë markdown
- ÇDO shaka bazohet në diçka REALE: emrat SAKTË të repos, numrin e stars, followers, gjuhët, bio
- Fjalia e fundit osht goditja ma e fortë
"""

STYLE_PROMPTS_ALBANIAN = {
    "savage":        KOSOVO_PROMPT,
    "pirate":        KOSOVO_PROMPT + "\nEdhe shto pak energji piratu — dramatik, por ende kosovar.",
    "corporate":     KOSOVO_PROMPT + "\nBëhu si menaxher kosovar pasiv-agresiv — professional nga jashtë, brutal nga brenda.",
    "haiku":         "Shkruaj saktësisht 2 limerick në shqip kosovar (5 rreshta, rimë AABBA). Rreshtat 1,2,5 rimojnë me njëri-tjetrin, rreshtat 3,4 rimojnë me njëri-tjetrin. Ritëm kërcyes. Asnjë intro. Specifik për profilin. Goditja ma e fortë — rreshti 5 i çdo limerickut.",
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
        angles = [
            "Focus the roast on their commit activity and repo quality.",
            "Focus the roast on their social stats — followers, following, stars.",
            "Focus the roast on the languages they use (or don't use).",
            "Focus the roast on their bio and location.",
            "Focus the roast on how long they've been on GitHub vs what they've produced.",
            "Focus the roast on the names and descriptions of their repos.",
        ]
        angle = random.choice(angles)
        instruction = f"Roast this developer now. {angle} Use exact repo names, real numbers. Make it burn. Under 140 words."

    # Albanian style is either explicitly chosen OR auto-detected by location
    use_albanian_prompts = albanian or style == "albanian"
    style_map = STYLE_PROMPTS_ALBANIAN if use_albanian_prompts else STYLE_PROMPTS
    system = style_map.get(style, style_map.get("savage", list(style_map.values())[0]))

    return system, f"{user_section}\n\n{instruction}"


@app.route("/")
def index():
    resp = make_response(render_template("index.html"))
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    return resp


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
                temperature=1.0,
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
