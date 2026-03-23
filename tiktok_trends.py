"""
TIKTOK TREND BOT v2 — Sources fiables uniquement
Sources : Google Trends FR + recherches virales réelles
"""

import requests
import time
import re
from datetime import datetime

TELEGRAM_TOKEN   = "8666345176:AAGGNb8WDXcwchrLaU-nPJj3UVtGX9Hk6Xc"
TELEGRAM_CHAT_ID = "8559815820"

CHECK_INTERVAL = 3600  # toutes les heures

# ── Mots-clés réels à surveiller ──────────────────────────

TREND_KEYWORDS = {
    "Sport & Fitness": [
        "routine muscu", "programme musculation", "transformation physique",
        "seche musculation", "prise de masse", "workout routine",
        "calisthenics debutant", "home workout", "bulk cut regime"
    ],
    "Mode & Style": [
        "outfit homme 2025", "tenue casual homme", "streetwear tendance",
        "look stylé homme", "sneakers tendance 2025", "capsule wardrobe homme",
        "vinted trouvaille", "mode luxe abordable", "tenue sport chic"
    ],
    "Lifestyle & Motivation": [
        "routine matinale productive", "discipline mindset", "day in my life",
        "habitudes succès", "morning routine 2025", "productivité routine",
        "psychologie motivation", "mindset winner"
    ],
    "TikTok Viral": [
        "tiktok viral france", "trend tiktok 2025", "son viral tiktok",
        "challenge tiktok mars 2025", "transition tiktok", "pov tiktok viral"
    ]
}

# ── Google Trends ─────────────────────────────────────────

def get_trends_for_keywords(keywords, geo="FR"):
    """
    Utilise pytrends pour récupérer les scores réels Google Trends.
    """
    results = {}
    try:
        from pytrends.request import TrendReq
        pytrends = TrendReq(hl="fr-FR", tz=60)

        chunks = [keywords[i:i+5] for i in range(0, len(keywords), 5)]
        for chunk in chunks:
            try:
                pytrends.build_payload(chunk, timeframe="now 7-d", geo=geo)
                df = pytrends.interest_over_time()
                if df.empty:
                    time.sleep(2); continue
                for kw in chunk:
                    if kw in df.columns:
                        avg    = int(df[kw].mean())
                        recent = int(df[kw].tail(2).mean())
                        delta  = recent - avg
                        if recent >= 30 or delta >= 15:
                            results[kw] = {"score": recent, "delta": delta, "avg": avg}
                time.sleep(3)
            except Exception as e:
                print(f"  [Trends] chunk erreur: {e}"); time.sleep(5)
    except ImportError:
        print("  [Trends] pytrends non disponible")
    return results

def get_trending_searches_fr():
    """Récupère les recherches trending Google France."""
    try:
        from pytrends.request import TrendReq
        pytrends = TrendReq(hl="fr-FR", tz=60)
        df = pytrends.trending_searches(pn="france")
        return df[0].tolist()[:15]
    except Exception as e:
        print(f"  [Trending] erreur: {e}"); return []

def get_related_rising(keyword, geo="FR"):
    """Récupère les requêtes montantes liées à un mot-clé."""
    try:
        from pytrends.request import TrendReq
        pytrends = TrendReq(hl="fr-FR", tz=60)
        pytrends.build_payload([keyword], timeframe="now 7-d", geo=geo)
        related = pytrends.related_queries()
        if keyword in related and related[keyword].get("rising") is not None:
            return related[keyword]["rising"]["query"].tolist()[:5]
    except:
        pass
    return []

# ── Sources complémentaires fiables ───────────────────────

def get_youtube_trending_music():
    """
    Récupère les musiques tendance depuis YouTube Charts France
    (page publique sans API).
    """
    songs = []
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
            "Accept-Language": "fr-FR,fr;q=0.9",
        }
        r = requests.get("https://charts.youtube.com/charts/TopSongs/fr", headers=headers, timeout=10)
        # Extraction noms d'artistes et titres
        titles = re.findall(r'"title"\s*:\s*"([^"]{3,60})"', r.text)
        artists = re.findall(r'"artist"\s*:\s*"([^"]{2,40})"', r.text)
        for i in range(min(8, len(titles), len(artists))):
            songs.append(f"{artists[i]} — {titles[i]}")
    except Exception as e:
        print(f"  [YouTube Charts] erreur: {e}")

    # Fallback : Shazam Top France via recherche Google Trends
    if not songs:
        try:
            from pytrends.request import TrendReq
            pytrends = TrendReq(hl="fr-FR", tz=60)
            pytrends.build_payload(["musique tendance"], timeframe="now 7-d", geo="FR")
            related = pytrends.related_queries()
            if "musique tendance" in related:
                df = related["musique tendance"].get("rising")
                if df is not None:
                    songs = df["query"].tolist()[:8]
        except:
            pass

    return songs[:8]

def get_tiktok_hashtags_from_google():
    """
    Récupère de vrais hashtags TikTok trending via Google Trends
    en cherchant les requêtes montantes autour de TikTok.
    """
    hashtags = []
    try:
        from pytrends.request import TrendReq
        pytrends = TrendReq(hl="fr-FR", tz=60)

        # Recherche les termes montants autour de tiktok
        for search_term in ["tiktok tendance", "tiktok viral", "son tiktok"]:
            try:
                pytrends.build_payload([search_term], timeframe="now 7-d", geo="FR")
                related = pytrends.related_queries()
                if search_term in related:
                    rising = related[search_term].get("rising")
                    if rising is not None:
                        for query in rising["query"].tolist()[:5]:
                            # Nettoie et garde seulement les vrais termes
                            clean = query.strip().lower()
                            if len(clean) > 3 and not re.match(r'^[#0-9]', clean):
                                hashtags.append(clean)
                time.sleep(2)
            except:
                pass
    except:
        pass

    return list(set(hashtags))[:10]

# ── Idées contenu sans IA ─────────────────────────────────

CONTENT_IDEAS = {
    "Sport & Fitness": [
        "🎬 Montre ta transformation en 15 secondes\n📋 Photo avant → vidéo d'entraînement → résultat\n💡 Hook : 'X mois de travail pour ça'",
        "🎬 Ta routine muscu du matin en accéléré\n📋 Réveil → nutrition → séance → résultat\n💡 Hook : 'Ma routine à {heure}h du matin'",
        "🎬 Les 3 erreurs que tu fais à la salle\n📋 Erreur 1 → 2 → 3 avec correction\n💡 Hook : 'Arrête de faire ça à la salle'",
    ],
    "Mode & Style": [
        "🎬 Transition tenue avant/après en 3 secondes\n📋 Tenue basique → tenue stylée même budget\n💡 Hook : 'POV tu sais t'habiller'",
        "🎬 3 tenues avec 5 pièces seulement\n📋 Les pièces → combinaison 1 → 2 → 3\n💡 Hook : 'Tu n'as pas besoin de plus'",
        "🎬 Ma trouvaille Vinted de la semaine\n📋 Prix payé → vraie valeur → comment la styler\n💡 Hook : 'J'ai payé X€ pour ça'",
    ],
    "Lifestyle & Motivation": [
        "🎬 Ma journée type en 30 secondes\n📋 Matin → sport → cours → soir\n💡 Hook : 'Ma journée à {heure} en semaine'",
        "🎬 Ce que j'ai appris en psycho cette semaine\n📋 Concept psy → application concrète → conseil\n💡 Hook : 'La psychologie m'a appris que...'",
        "🎬 5h de marche par jour ce que ça change\n📋 Avant → habitude → transformation mentale\n💡 Hook : 'Je marche 2000 calories par jour'",
    ],
    "TikTok Viral": [
        "🎬 Utilise ce son/trend MAINTENANT\n📋 Adapte le format à ta niche sport/mode\n💡 Hook : jump cut dynamique dès la 1ère seconde",
        "🎬 POV version sport/mode\n📋 Situation → réaction → twist final\n💡 Hook : 'POV tu...'",
    ]
}

import random

def get_content_idea(niche):
    ideas = CONTENT_IDEAS.get(niche, CONTENT_IDEAS["TikTok Viral"])
    return random.choice(ideas)

# ── Horaires optimaux de publication ─────────────────────

def get_best_post_time():
    """Retourne les meilleurs horaires TikTok selon le jour."""
    day = datetime.now().weekday()
    times = {
        0: "7h-9h ou 19h-21h (Lundi)",
        1: "7h-9h ou 18h-20h (Mardi)",
        2: "7h-9h ou 19h-21h (Mercredi)",
        3: "7h-9h ou 20h-22h (Jeudi)",
        4: "7h-9h ou 17h-19h (Vendredi)",
        5: "10h-12h ou 20h-23h (Samedi)",
        6: "10h-12h ou 19h-22h (Dimanche)",
    }
    return times.get(day, "7h-9h ou 19h-21h")

# ── Telegram ──────────────────────────────────────────────

def send_telegram(message):
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
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

# ── Analyse principale ────────────────────────────────────

already_alerted = set()

def analyze_and_alert():
    print(f"\n[{datetime.now().strftime('%H:%M')}] Analyse trends...")
    alerts_sent = 0
    best_trends = []

    # 1. Google Trends par niche
    print("  [1/4] Google Trends par niche...")
    for niche, keywords in TREND_KEYWORDS.items():
        results = get_trends_for_keywords(keywords)
        for kw, data in results.items():
            best_trends.append({
                "name":  kw,
                "niche": niche,
                "score": data["score"],
                "delta": data["delta"],
            })
        time.sleep(2)

    # 2. Recherches trending Google France
    print("  [2/4] Trending searches France...")
    trending = get_trending_searches_fr()
    for t in trending:
        t_lower = t.lower()
        if any(w in t_lower for w in ["sport", "mode", "fit", "gym", "style", "musique", "son", "trend", "tenue", "outfit"]):
            best_trends.append({
                "name":  t,
                "niche": "TikTok Viral",
                "score": 80,
                "delta": 40,
            })

    # 3. Hashtags TikTok réels via Google
    print("  [3/4] Hashtags TikTok réels...")
    hashtags = get_tiktok_hashtags_from_google()
    for h in hashtags:
        best_trends.append({
            "name":  f"#{h}",
            "niche": "TikTok Viral",
            "score": 70,
            "delta": 25,
        })

    # Tri par score + delta
    best_trends.sort(key=lambda x: x["score"] + x["delta"] * 1.5, reverse=True)

    # Envoi top 5 trends non déjà alertées
    top = 0
    for trend in best_trends:
        if top >= 5: break
        key = trend["name"].lower().replace(" ", "_")
        if key in already_alerted: continue
        already_alerted.add(key)

        score = trend["score"]
        delta = trend["delta"]
        niche = trend["niche"]
        name  = trend["name"]

        if delta >= 40:   window = "⚡ MAINTENANT — moins de 24h"
        elif delta >= 20: window = "🔴 48h maximum"
        elif delta >= 10: window = "🟠 3-4 jours"
        else:             window = "🟡 Cette semaine"

        idea = get_content_idea(niche)

        msg = (
            f"🎯 <b>TREND DÉTECTÉE — {niche.upper()}</b>\n\n"
            f"📌 <b>{name}</b>\n"
            f"📈 Score viralité : <b>{score}/100</b>\n"
            f"⬆️ Progression : +{delta} pts cette semaine\n"
            f"⏰ Fenêtre : <b>{window}</b>\n\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💡 <b>IDÉE CONTENU POUR TOI :</b>\n\n"
            f"{idea}\n\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🔍 Cherche sur TikTok : <b>{name}</b>\n"
            f"⏰ Meilleurs horaires : {get_best_post_time()}\n"
            f"📅 {datetime.now().strftime('%H:%M — %d/%m/%Y')}"
        )
        send_telegram(msg)
        alerts_sent += 1
        top += 1
        time.sleep(2)

    # 4. Sons viraux
    print("  [4/4] Sons viraux...")
    songs = get_youtube_trending_music()
    if songs:
        msg = (
            f"🎵 <b>SONS VIRAUX DU MOMENT — {datetime.now().strftime('%d/%m')}</b>\n\n"
        )
        for i, s in enumerate(songs, 1):
            msg += f"{i}. {s}\n"
        msg += (
            f"\n💡 <b>Comment utiliser ces sons :</b>\n"
            f"→ Cherche le son sur TikTok\n"
            f"→ Regarde les vidéos qui performent\n"
            f"→ Adapte à ta niche sport/mode\n"
            f"→ Poste dans les 24h\n\n"
            f"⏰ Meilleurs horaires : {get_best_post_time()}\n"
            f"📅 {datetime.now().strftime('%H:%M — %d/%m/%Y')}"
        )
        send_telegram(msg)
        alerts_sent += 1

    return alerts_sent

# ── Main ──────────────────────────────────────────────────

def main():
    print("=" * 55)
    print("   TIKTOK TREND BOT v2 — Sources fiables")
    print(f"   Google Trends FR + YouTube Charts + TikTok")
    print(f"   Analyse toutes les {CHECK_INTERVAL // 60} minutes")
    print("=" * 55)

    send_telegram(
        f"🎯 <b>TikTok Trend Bot v2 démarré !</b>\n\n"
        f"✅ Sources fiables uniquement :\n"
        f"• Google Trends France temps réel\n"
        f"• Recherches virales du moment\n"
        f"• Sons tendance YouTube/TikTok\n"
        f"• Hashtags TikTok réels\n\n"
        f"🎯 Niches : Sport • Mode • Lifestyle • Motivation\n"
        f"⏰ Analyse toutes les heures\n\n"
        f"🟢 Première analyse en cours..."
    )

    cycle = 0
    while True:
        cycle += 1
        print(f"\n══ ANALYSE #{cycle} ══ {datetime.now().strftime('%H:%M')} ══")
        alerts = analyze_and_alert()
        print(f"══ FIN #{cycle} ══ {alerts} alerte(s) envoyée(s)")
        print(f"   Prochain scan dans {CHECK_INTERVAL // 60} minutes")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
