"""
TIKTOK TREND BOT v3 — US + FR + Toutes niches
Sources : Google Trends US+FR, Billboard, TikTok Creative Center,
          YouTube Charts, Spotify Charts
Logique : détecte ce qui explose aux US AVANT que ça arrive en France
"""

import requests
import time
import re
import random
from datetime import datetime

TELEGRAM_TOKEN   = "8666345176:AAGGNb8WDXcwchrLaU-nPJj3UVtGX9Hk6Xc"
TELEGRAM_CHAT_ID = "8559815820"

CHECK_INTERVAL = 3600   # toutes les heures
MIN_SCORE      = 40     # score Google Trends minimum

# ════════════════════════════════════════════════════════
#  🌍  SURVEILLANCE MULTI-PAYS
#  Logique : US explose → France dans 2-4 semaines → tu es premier
# ════════════════════════════════════════════════════════

GEO_CONFIGS = {
    "🇺🇸 USA":     {"geo": "US", "lang": "en-US", "flag": "🇺🇸", "delay_weeks": 0},
    "🇬🇧 UK":      {"geo": "GB", "lang": "en-GB", "flag": "🇬🇧", "delay_weeks": 1},
    "🇫🇷 France":  {"geo": "FR", "lang": "fr-FR", "flag": "🇫🇷", "delay_weeks": 3},
}

# ════════════════════════════════════════════════════════
#  🔍  MOTS-CLÉS LARGES — toutes niches sans limites
# ════════════════════════════════════════════════════════

BROAD_KEYWORDS = {
    "Viral & Trends":        ["viral video", "trending now", "tiktok trend", "new challenge", "tiktok sound"],
    "Sport & Body":          ["workout routine", "gym transformation", "fitness tips", "weight loss", "muscle gain", "calisthenics"],
    "Mode & Fashion":        ["outfit ideas", "style tips men", "streetwear", "fashion trend", "outfit of the day", "sneakers"],
    "Music & Sounds":        ["new music", "song viral", "trending song", "music trend", "top hits"],
    "Lifestyle":             ["day in my life", "morning routine", "productive day", "daily vlog", "life tips"],
    "Mental & Psychology":   ["mindset", "motivation", "psychology tips", "mental health", "self improvement"],
    "Food & Health":         ["meal prep", "healthy food", "diet tips", "nutrition", "high protein meal"],
    "Tech & AI":             ["ai trend", "new technology", "tech tips", "artificial intelligence"],
    "Entertainment":         ["funny video", "prank", "reaction video", "story time", "drama"],
    "Money & Business":      ["side hustle", "make money online", "passive income", "invest money", "resell tips"],
    # Versions françaises
    "Tendances FR":          ["tendance tiktok", "son viral tiktok", "challenge france", "video virale france"],
    "Sport FR":              ["routine muscu", "transformation physique", "programme fitness", "seche muscu"],
    "Mode FR":               ["tenue homme", "outfit stylé", "streetwear france", "sneakers tendance"],
    "Lifestyle FR":          ["routine matinale", "journée productive", "vlog quotidien", "motivation france"],
}

# ════════════════════════════════════════════════════════
#  📊  GOOGLE TRENDS — US + FR en parallèle
# ════════════════════════════════════════════════════════

def get_trends_multi_geo(keywords, geos=["US", "FR"]):
    """
    Compare les scores entre pays pour détecter ce qui explose aux US
    avant d'arriver en France.
    """
    results = {}
    try:
        from pytrends.request import TrendReq
        pytrends = TrendReq(hl="en-US", tz=0)
        chunks   = [keywords[i:i+5] for i in range(0, len(keywords), 5)]

        for chunk in chunks:
            geo_scores = {}
            for geo in geos:
                try:
                    pytrends.build_payload(chunk, timeframe="now 7-d", geo=geo)
                    df = pytrends.interest_over_time()
                    if df.empty: time.sleep(2); continue
                    for kw in chunk:
                        if kw in df.columns:
                            if kw not in geo_scores:
                                geo_scores[kw] = {}
                            geo_scores[kw][geo] = {
                                "avg":    int(df[kw].mean()),
                                "recent": int(df[kw].tail(2).mean()),
                                "delta":  int(df[kw].tail(2).mean()) - int(df[kw].mean()),
                            }
                    time.sleep(2)
                except Exception as e:
                    print(f"  [Trends {geo}] erreur: {e}"); time.sleep(3)

            # Analyse cross-pays
            for kw, scores in geo_scores.items():
                us_score = scores.get("US", {}).get("recent", 0)
                fr_score = scores.get("FR", {}).get("recent", 0)
                us_delta = scores.get("US", {}).get("delta", 0)
                fr_delta = scores.get("FR", {}).get("delta", 0)

                # OPPORTUNITÉ : fort aux US, faible en France = arriving soon
                us_fr_gap = us_score - fr_score

                if us_score >= MIN_SCORE or fr_score >= MIN_SCORE:
                    opportunity = "normal"
                    if us_score >= 50 and fr_score < 30:
                        opportunity = "🔮 ARRIVE EN FRANCE BIENTÔT"
                    elif us_score >= 70 and us_delta >= 20:
                        opportunity = "🚀 EXPLOSE AUX US MAINTENANT"
                    elif fr_score >= 60 and fr_delta >= 20:
                        opportunity = "🔥 VIRAL EN FRANCE MAINTENANT"

                    results[kw] = {
                        "us_score":    us_score,
                        "fr_score":    fr_score,
                        "us_delta":    us_delta,
                        "fr_delta":    fr_delta,
                        "us_fr_gap":   us_fr_gap,
                        "opportunity": opportunity,
                        "score":       max(us_score, fr_score),
                        "priority":    us_score * 1.5 + fr_score + us_delta * 2,
                    }
            time.sleep(3)
    except ImportError:
        print("  [Trends] pytrends non disponible")
    return results

def get_trending_searches_both():
    """Trending searches US et FR."""
    results = {"US": [], "FR": []}
    try:
        from pytrends.request import TrendReq
        pytrends = TrendReq(hl="en-US", tz=0)
        for geo, pn in [("US", "united_states"), ("FR", "france")]:
            try:
                df = pytrends.trending_searches(pn=pn)
                results[geo] = df[0].tolist()[:10]
                time.sleep(2)
            except Exception as e:
                print(f"  [Trending {geo}] erreur: {e}")
    except:
        pass
    return results

# ════════════════════════════════════════════════════════
#  🎵  BILLBOARD HOT 100 — Sons qui vont exploser en France
# ════════════════════════════════════════════════════════

def get_billboard_hot100():
    """
    Scrape Billboard Hot 100 — ce qui est chaud aux US
    arrive en France 2-4 semaines après.
    """
    songs = []
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }
        r = requests.get("https://www.billboard.com/charts/hot-100/", headers=headers, timeout=12)
        if r.status_code == 200:
            # Extraction titres et artistes
            titles  = re.findall(r'class="c-title[^"]*"[^>]*>\s*<[^>]+>([^<]+)<', r.text)
            artists = re.findall(r'class="c-label[^"]*"[^>]*>\s*<[^>]+>([^<]+)<', r.text)
            for i in range(min(10, len(titles), len(artists))):
                t = titles[i].strip()
                a = artists[i].strip()
                if t and a and len(t) > 1 and len(a) > 1:
                    songs.append(f"{a} — {t}")
    except Exception as e:
        print(f"  [Billboard] erreur: {e}")
    return songs[:10]

def get_spotify_viral():
    """
    Récupère le top Spotify viral France depuis l'embed public.
    """
    songs = []
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
        }
        r = requests.get(
            "https://charts.spotify.com/charts/view/viral-fr-daily/latest",
            headers=headers, timeout=10
        )
        if r.status_code == 200:
            titles  = re.findall(r'"trackName"\s*:\s*"([^"]+)"', r.text)
            artists = re.findall(r'"artistName"\s*:\s*"([^"]+)"', r.text)
            for i in range(min(8, len(titles), len(artists))):
                songs.append(f"{artists[i]} — {titles[i]}")
    except Exception as e:
        print(f"  [Spotify] erreur: {e}")
    return songs[:8]

# ════════════════════════════════════════════════════════
#  💡  GÉNÉRATEUR D'IDÉES CONTENU — Adapté à TON profil
# ════════════════════════════════════════════════════════

PROFILE = {
    "sport":   ["muscu", "foot", "cardio", "marche", "transformation"],
    "mode":    ["streetwear", "luxe", "vinted", "outfit", "sneakers"],
    "mindset": ["psychologie", "discipline", "motivation", "routine"],
    "vie":     ["étudiant", "lifestyle", "vlog", "journée"],
}

CONTENT_TEMPLATES = [
    # Sport
    ("Sport", "🎬 CONCEPT : Montre ta progression en {kw}\n⏱️ DURÉE : 15-30 sec\n📋 SCRIPT : Avant → pendant → résultat\n💡 HOOK : 'X semaines pour ça' ou 'Ce que personne dit sur {kw}'\n⚡ POURQUOI : La transformation = emotion = partage"),
    ("Sport", "🎬 CONCEPT : Démystifie une idée reçue sur {kw}\n⏱️ DURÉE : 20-45 sec\n📋 SCRIPT : Idée reçue → ta réponse → preuve\n💡 HOOK : 'Arrête de croire que...' ou 'La vérité sur {kw}'\n⚡ POURQUOI : Le contraste crée l'engagement"),
    # Mode
    ("Mode", "🎬 CONCEPT : Transition tenue avec {kw}\n⏱️ DURÉE : 7-15 sec\n📋 SCRIPT : Tenue basique → transformation en 1 geste\n💡 HOOK : Premier frame stylé qui arrête le scroll\n⚡ POURQUOI : Les transitions = forte rétention"),
    ("Mode", "🎬 CONCEPT : Trouvaille {kw} → vraie valeur\n⏱️ DURÉE : 20-30 sec\n📋 SCRIPT : Prix payé → marque → prix réel → comment styler\n💡 HOOK : 'J'ai payé X€ pour ça' (prix choquant)\n⚡ POURQUOI : L'argent économisé = partage massif"),
    # Lifestyle
    ("Lifestyle", "🎬 CONCEPT : Ma routine {kw} en accéléré\n⏱️ DURÉE : 30-60 sec\n📋 SCRIPT : Réveil → étapes clés → résultat de la journée\n💡 HOOK : 'Ma journée type à {heure}h' + musique motivante\n⚡ POURQUOI : Les routines = aspiration = abonnement"),
    ("Lifestyle", "🎬 CONCEPT : Ce que {kw} m'a appris\n⏱️ DURÉE : 30-45 sec\n📋 SCRIPT : Contexte → leçon 1 → 2 → 3 → conclusion\n💡 HOOK : 'X mois de {kw} pour comprendre ça'\n⚡ POURQUOI : La valeur éducative = sauvegarde"),
    # Psychologie
    ("Psycho", "🎬 CONCEPT : Concept psy appliqué à {kw}\n⏱️ DURÉE : 30-60 sec\n📋 SCRIPT : Problème commun → explication psy → solution concrète\n💡 HOOK : 'La psychologie explique pourquoi tu...'\n⚡ POURQUOI : Unique = personne ne fait ça = différenciation"),
    # Viral
    ("Viral", "🎬 CONCEPT : Adapte la trend {kw} à ta niche\n⏱️ DURÉE : 7-30 sec selon trend\n📋 SCRIPT : Même format que la trend mais version toi\n💡 HOOK : Même son/format mais contexte sport/mode/lifestyle\n⚡ POURQUOI : Trend + niche = algorithme booste"),
    ("Viral", "🎬 CONCEPT : POV version {kw}\n⏱️ DURÉE : 15-30 sec\n📋 SCRIPT : Situation → réaction → twist ou conseil\n💡 HOOK : 'POV tu es...' + situation relatable\n⚡ POURQUOI : Le POV = identification = partage"),
]

def get_content_idea(keyword, niche_category=""):
    template_type, template = random.choice(CONTENT_TEMPLATES)
    idea = template.replace("{kw}", keyword)
    idea = idea.replace("{heure}", str(random.choice([6, 7, 8])))
    return idea

# ════════════════════════════════════════════════════════
#  ⏰  HORAIRES OPTIMAUX PAR JOUR
# ════════════════════════════════════════════════════════

def get_best_times():
    day = datetime.now().weekday()
    schedule = {
        0: ["7h00", "12h30", "19h00", "21h00"],
        1: ["7h00", "12h30", "18h00", "20h00"],
        2: ["7h00", "12h00", "19h00", "21h00"],
        3: ["7h00", "12h30", "20h00", "22h00"],
        4: ["7h00", "12h00", "17h00", "21h00"],
        5: ["10h00", "13h00", "20h00", "23h00"],
        6: ["10h00", "12h00", "19h00", "22h00"],
    }
    times = schedule.get(day, ["7h00", "12h00", "19h00"])
    return " | ".join(times)

# ════════════════════════════════════════════════════════
#  📲  TELEGRAM
# ════════════════════════════════════════════════════════

def send_telegram(message):
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message[:4096],
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json=payload, timeout=10
        )
        return r.status_code == 200
    except Exception as e:
        print(f"[ERREUR] Telegram: {e}"); return False

# ════════════════════════════════════════════════════════
#  🚀  ANALYSE PRINCIPALE
# ════════════════════════════════════════════════════════

already_alerted = set()

def analyze_and_alert():
    print(f"\n[{datetime.now().strftime('%H:%M')}] Analyse US+FR en cours...")
    alerts_sent = 0
    all_trends  = []

    # ── 1. Google Trends toutes niches US+FR ──
    print("  [1/5] Google Trends US + FR...")
    for category, keywords in BROAD_KEYWORDS.items():
        results = get_trends_multi_geo(keywords, geos=["US", "FR"])
        for kw, data in results.items():
            all_trends.append({
                "name":        kw,
                "category":    category,
                "us_score":    data["us_score"],
                "fr_score":    data["fr_score"],
                "us_delta":    data["us_delta"],
                "opportunity": data["opportunity"],
                "priority":    data["priority"],
            })
        time.sleep(2)

    # ── 2. Trending searches US + FR ──
    print("  [2/5] Trending searches US + FR...")
    trending = get_trending_searches_both()
    for term in trending.get("US", []):
        all_trends.append({
            "name":        term,
            "category":    "🇺🇸 Trending USA",
            "us_score":    85,
            "fr_score":    20,
            "us_delta":    50,
            "opportunity": "🔮 ARRIVE EN FRANCE BIENTÔT",
            "priority":    200,
        })
    for term in trending.get("FR", []):
        all_trends.append({
            "name":        term,
            "category":    "🇫🇷 Trending France",
            "us_score":    30,
            "fr_score":    85,
            "us_delta":    10,
            "opportunity": "🔥 VIRAL EN FRANCE MAINTENANT",
            "priority":    180,
        })

    # ── Tri par priorité ──
    all_trends.sort(key=lambda x: x["priority"], reverse=True)

    # ── Envoi top 6 trends ──
    top = 0
    for trend in all_trends:
        if top >= 6: break
        key = trend["name"].lower().replace(" ", "_")[:40]
        if key in already_alerted: continue
        already_alerted.add(key)

        name        = trend["name"]
        category    = trend["category"]
        us_score    = trend["us_score"]
        fr_score    = trend["fr_score"]
        us_delta    = trend["us_delta"]
        opportunity = trend["opportunity"]
        idea        = get_content_idea(name, category)

        # Fenêtre
        if "MAINTENANT" in opportunity or "MAINTENANT" in opportunity:
            window = "⚡ Poste AUJOURD'HUI"
        elif "BIENTÔT" in opportunity:
            window = "📅 Poste cette semaine — sois premier en FR"
        elif us_delta >= 30:
            window = "🔴 48h maximum"
        else:
            window = "🟡 Cette semaine"

        msg = (
            f"🎯 <b>TREND DÉTECTÉE</b> — {opportunity}\n\n"
            f"📌 <b>{name}</b>\n"
            f"🏷️ Catégorie : {category}\n\n"
            f"📊 <b>Scores :</b>\n"
            f"🇺🇸 USA    : {us_score}/100 (+{us_delta} cette semaine)\n"
            f"🇫🇷 France : {fr_score}/100\n\n"
            f"⏰ <b>Fenêtre : {window}</b>\n\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💡 <b>IDÉE CONTENU :</b>\n\n"
            f"{idea}\n\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🔍 Cherche : <b>{name}</b> sur TikTok\n"
            f"⏰ Poster à : {get_best_times()}\n"
            f"📅 {datetime.now().strftime('%H:%M — %d/%m/%Y')}"
        )
        send_telegram(msg)
        alerts_sent += 1
        top += 1
        time.sleep(2)

    # ── 3. Billboard Hot 100 ──
    print("  [3/5] Billboard Hot 100...")
    billboard = get_billboard_hot100()
    if billboard:
        msg = (
            f"🎵 <b>BILLBOARD HOT 100 — Sons qui arrivent en France</b>\n"
            f"🇺🇸 Ces sons explosent aux US maintenant\n"
            f"📅 Attendus en France dans 2-4 semaines\n\n"
        )
        for i, s in enumerate(billboard[:8], 1):
            msg += f"{i}. {s}\n"
        msg += (
            f"\n💡 <b>Stratégie :</b>\n"
            f"→ Cherche ces sons sur TikTok US\n"
            f"→ Regarde les trends autour\n"
            f"→ Prépare ton contenu maintenant\n"
            f"→ Poste dès que le son arrive en FR\n\n"
            f"⏰ {datetime.now().strftime('%H:%M — %d/%m/%Y')}"
        )
        send_telegram(msg)
        alerts_sent += 1

    # ── 4. Spotify Viral France ──
    print("  [4/5] Spotify Viral France...")
    spotify = get_spotify_viral()
    if spotify:
        msg = (
            f"🎧 <b>SPOTIFY VIRAL FRANCE — Sons TikTok du moment</b>\n\n"
        )
        for i, s in enumerate(spotify, 1):
            msg += f"{i}. {s}\n"
        msg += (
            f"\n💡 Ces sons sont déjà viraux en France\n"
            f"→ Utilise-les MAINTENANT avant saturation\n\n"
            f"⏰ {datetime.now().strftime('%H:%M — %d/%m/%Y')}"
        )
        send_telegram(msg)
        alerts_sent += 1

    # ── 5. Résumé stratégique ──
    print("  [5/5] Résumé stratégique...")
    us_trends  = [t for t in all_trends if t["us_score"] > 60 and t["fr_score"] < 30][:3]
    fr_trends  = [t for t in all_trends if t["fr_score"] > 60][:3]

    if us_trends or fr_trends:
        summary = (
            f"📊 <b>RÉSUMÉ STRATÉGIQUE — {datetime.now().strftime('%d/%m/%Y')}</b>\n\n"
            f"🇺🇸 <b>À surveiller (arrivent en FR) :</b>\n"
        )
        for t in us_trends:
            summary += f"• {t['name']} (US: {t['us_score']}/100)\n"
        summary += f"\n🇫🇷 <b>À utiliser maintenant (viral FR) :</b>\n"
        for t in fr_trends:
            summary += f"• {t['name']} (FR: {t['fr_score']}/100)\n"
        summary += (
            f"\n⏰ <b>Meilleurs horaires aujourd'hui :</b>\n"
            f"{get_best_times()}\n\n"
            f"📅 {datetime.now().strftime('%d/%m/%Y')}"
        )
        send_telegram(summary)
        alerts_sent += 1

    return alerts_sent

# ════════════════════════════════════════════════════════
#  🚀  MAIN
# ════════════════════════════════════════════════════════

def main():
    print("=" * 62)
    print("   TIKTOK TREND BOT v3 — US + FR + Toutes niches")
    print(f"   Sources : Google Trends US+FR, Billboard, Spotify")
    print(f"   Logique : US explose → tu es premier en France")
    print(f"   Analyse : toutes les {CHECK_INTERVAL // 60} minutes")
    print("=" * 62)

    send_telegram(
        f"🎯 <b>TikTok Trend Bot v3 — ULTIMATE</b>\n\n"
        f"🇺🇸 Surveillance US → détecte AVANT la France\n"
        f"🌍 Google Trends US + FR en parallèle\n"
        f"🎵 Billboard Hot 100 — sons qui arrivent\n"
        f"🎧 Spotify Viral France — sons actifs\n"
        f"💡 Idées contenu sans limites de niche\n"
        f"⏰ Meilleurs horaires de publication\n\n"
        f"🟢 Première analyse en cours..."
    )

    cycle = 0
    while True:
        cycle += 1
        print(f"\n══ ANALYSE #{cycle} ══ {datetime.now().strftime('%H:%M')} ══")
        alerts = analyze_and_alert()
        print(f"══ FIN #{cycle} ══ {alerts} message(s) envoyé(s)")
        print(f"   Prochain scan dans {CHECK_INTERVAL // 60} minutes")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
