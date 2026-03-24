import requests
import time
import re
import random
from datetime import datetime

TELEGRAM_TOKEN = "8666345176:AAGGNb8WDXcwchrLaU-nPJj3UVtGX9Hk6Xc"
TELEGRAM_CHAT_ID = "8559815820"

CHECK_INTERVAL = 3600

KEYWORDS_FR = [
    "musculation tendance", "fitness routine viral",
    "transformation physique", "workout viral france",
    "outfit homme tendance", "streetwear 2025",
    "sneakers viral france", "tenue stylée homme",
    "son viral tiktok france", "trend tiktok france",
    "routine matinale viral", "day in my life france",
    "motivation discipline france", "mindset 2025",
    "psychologie motivation viral", "productivite routine",
    "cold plunge france", "bain de glace tendance",
    "red light therapy france", "biohacking homme",
    "soin visage homme tendance", "barbe entretien viral",
]

KEYWORDS_US = [
    "tiktok trend viral", "viral sound tiktok",
    "gym motivation viral", "body transformation viral",
    "outfit men trend", "style men viral",
    "morning routine viral", "life hack viral",
    "cold plunge viral", "red light therapy viral",
    "biohacking viral", "men skincare viral",
    "discipline mindset viral", "hustle motivation viral",
    "clean eating viral", "fitness aesthetic viral",
]

US_TO_FR = {
    "cold plunge viral":         "bain de glace froid",
    "red light therapy viral":   "lampe lumiere rouge soin",
    "biohacking viral":          "biohacking sante homme",
    "men skincare viral":        "soin visage homme routine",
    "gym motivation viral":      "motivation salle musculation",
    "body transformation viral": "transformation physique avant apres",
    "morning routine viral":     "routine matinale productive",
    "outfit men trend":          "tenue homme tendance style",
    "discipline mindset viral":  "discipline mindset gagnant",
    "fitness aesthetic viral":   "physique esthetique musculation",
    "life hack viral":           "astuce vie quotidienne",
    "hustle motivation viral":   "motivation travail succes",
    "clean eating viral":        "alimentation saine equilibree",
    "style men viral":           "style homme moderne classe",
    "viral sound tiktok":        "son viral tiktok semaine",
    "tiktok trend viral":        "tendance tiktok france",
}

CONTENT_IDEAS = {
    "musculation": [
        "Montre ta progression en 15 secondes\nHook: X mois de travail pour ca",
        "Les 3 erreurs que tu fais a la salle\nHook: Arrete de faire ca",
        "Ta routine muscu du matin en accelere\nHook: Ma methode pour progresser",
    ],
    "outfit": [
        "Transition tenue avant apres en 3 secondes\nHook: POV tu sais t habiller",
        "3 tenues avec 5 pieces seulement\nHook: Tu n as pas besoin de plus",
        "Mon avis honnete sur cette tendance mode\nHook: Cette trend vaut-elle le coup",
    ],
    "routine": [
        "Ma journee type en 30 secondes\nHook: Ma journee quand je suis productif",
        "Ce que j ai appris cette semaine\nHook: Personne ne te dit ca",
        "Avant vs apres ma routine matinale\nHook: La difference est enorme",
    ],
    "biohacking": [
        "J ai essaye le bain de glace pendant 30 jours\nHook: Ce que ca change vraiment",
        "Ma routine bien-etre en 60 secondes\nHook: Ce que je fais chaque matin",
        "Les 5 choses qui ont change ma sante\nHook: Je regrette de ne pas avoir fait ca avant",
    ],
    "default": [
        "Surfe sur cette tendance MAINTENANT\nHook: Jump cut dynamique des la 1ere seconde",
        "Ta version unique de cette trend\nHook: Inattendu des le depart",
        "POV version sport et style\nHook: POV tu...",
    ],
}

def get_content_idea(keyword):
    kw = keyword.lower()
    if any(w in kw for w in ["muscu", "gym", "fitness", "sport", "workout"]):
        return random.choice(CONTENT_IDEAS["musculation"])
    elif any(w in kw for w in ["outfit", "tenue", "style", "mode", "sneaker"]):
        return random.choice(CONTENT_IDEAS["outfit"])
    elif any(w in kw for w in ["routine", "matin", "journee", "productiv"]):
        return random.choice(CONTENT_IDEAS["routine"])
    elif any(w in kw for w in ["bain", "cold", "biohack", "soin", "sante", "bien"]):
        return random.choice(CONTENT_IDEAS["biohacking"])
    else:
        return random.choice(CONTENT_IDEAS["default"])

def get_best_times():
    day = datetime.now().weekday()
    times = {
        0: "7h-9h | 12h-13h | 19h-21h",
        1: "7h-9h | 12h-13h | 18h-20h",
        2: "7h-9h | 12h-13h | 19h-21h",
        3: "7h-9h | 12h-13h | 20h-22h",
        4: "7h-9h | 12h-13h | 17h-19h",
        5: "10h-12h | 15h-17h | 20h-23h",
        6: "10h-12h | 14h-16h | 19h-22h",
    }
    return times.get(day, "7h-9h | 19h-21h")

def get_google_trends(keywords, geo="FR"):
    results = {}
    try:
        from pytrends.request import TrendReq
        hl = "fr-FR" if geo == "FR" else "en-US"
        tz = 60 if geo == "FR" else -300
        pytrends = TrendReq(hl=hl, tz=tz)
        chunks = [keywords[i:i+5] for i in range(0, len(keywords), 5)]
        for chunk in chunks:
            try:
                pytrends.build_payload(chunk, timeframe="now 7-d", geo=geo)
                df = pytrends.interest_over_time()
                if df.empty:
                    time.sleep(2)
                    continue
                for kw in chunk:
                    if kw in df.columns:
                        avg = int(df[kw].mean())
                        recent = int(df[kw].tail(2).mean())
                        delta = recent - avg
                        if recent >= 25 or delta >= 15:
                            results[kw] = {
                                "score": recent,
                                "delta": delta,
                                "geo": geo,
                            }
                time.sleep(3)
            except Exception as e:
                print("Trends chunk error: " + str(e))
                time.sleep(5)
    except ImportError:
        print("pytrends not available")
    return results

def get_trending_searches(geo="FR"):
    try:
        from pytrends.request import TrendReq
        pn = "france" if geo == "FR" else "united_states"
        pytrends = TrendReq(hl="fr-FR" if geo == "FR" else "en-US", tz=60)
        df = pytrends.trending_searches(pn=pn)
        return df[0].tolist()[:15]
    except Exception as e:
        print("Trending error: " + str(e))
        return []

def get_youtube_charts():
    songs = []
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
            "Accept-Language": "fr-FR,fr;q=0.9",
        }
        r = requests.get("https://charts.youtube.com/charts/TopSongs/fr", headers=headers, timeout=10)
        if r.status_code == 200:
            artists = re.findall(r'"artist"\s*:\s*"([^"]{2,40})"', r.text)
            titles = re.findall(r'"title"\s*:\s*"([^"]{3,60})"', r.text)
            for i in range(min(6, len(artists), len(titles))):
                songs.append(artists[i] + " - " + titles[i])
    except Exception as e:
        print("YouTube Charts error: " + str(e))
    return songs[:6]

def send_telegram(message):
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "disable_web_page_preview": True,
    }
    try:
        r = requests.post(
            "https://api.telegram.org/bot" + TELEGRAM_TOKEN + "/sendMessage",
            json=payload, timeout=10
        )
        return r.status_code == 200
    except Exception as e:
        print("Telegram error: " + str(e))
        return False

already_alerted = set()

def analyze_and_alert():
    print(datetime.now().strftime("%H:%M") + " Analyse trends US + FR...")
    all_trends = []

    print("  [1/4] Google Trends France...")
    fr_results = get_google_trends(KEYWORDS_FR, geo="FR")
    for kw, data in fr_results.items():
        all_trends.append({
            "name": kw,
            "score": data["score"],
            "delta": data["delta"],
            "geo": "France",
            "flag": "FR",
            "urgency": "now",
        })
    time.sleep(3)

    print("  [2/4] Google Trends USA...")
    us_results = get_google_trends(KEYWORDS_US, geo="US")
    for kw, data in us_results.items():
        fr_equiv = US_TO_FR.get(kw, kw)
        all_trends.append({
            "name": kw,
            "fr_name": fr_equiv,
            "score": data["score"],
            "delta": data["delta"],
            "geo": "USA - arrive en France dans 2-4 semaines",
            "flag": "US",
            "urgency": "upcoming",
        })
    time.sleep(3)

    print("  [3/4] Trending France...")
    trending_fr = get_trending_searches("FR")
    for t in trending_fr[:8]:
        t_lower = t.lower()
        if any(w in t_lower for w in ["sport", "mode", "fit", "gym", "style", "musique", "son", "trend", "tenue", "soin"]):
            all_trends.append({
                "name": t,
                "score": 85,
                "delta": 45,
                "geo": "France - EN CE MOMENT",
                "flag": "FR",
                "urgency": "urgent",
            })
    time.sleep(2)

    print("  [4/4] Trending USA...")
    trending_us = get_trending_searches("US")
    for t in trending_us[:6]:
        t_lower = t.lower()
        if any(w in t_lower for w in ["sport", "fitness", "style", "men", "workout", "trend", "music", "viral"]):
            all_trends.append({
                "name": t,
                "score": 80,
                "delta": 40,
                "geo": "USA - arrive bientot en France",
                "flag": "US",
                "urgency": "upcoming",
            })

    urgency_w = {"urgent": 3, "now": 2, "upcoming": 1}
    all_trends.sort(
        key=lambda x: urgency_w.get(x["urgency"], 1) * 100 + x["score"] + x["delta"] * 1.5,
        reverse=True
    )

    sent = 0
    for trend in all_trends:
        if sent >= 5:
            break
        key = trend["name"].lower().replace(" ", "_")[:40]
        if key in already_alerted:
            continue
        already_alerted.add(key)

        name = trend["name"]
        display_name = trend.get("fr_name", name)
        score = trend["score"]
        delta = trend["delta"]
        geo = trend["geo"]
        flag = trend["flag"]
        urgency = trend["urgency"]

        if urgency == "urgent" or delta >= 40:
            window = "MAINTENANT - moins de 24h"
        elif delta >= 25:
            window = "48h maximum"
        elif urgency == "upcoming":
            window = "Prepare maintenant - poste dans 1-2 semaines"
        else:
            window = "Cette semaine"

        idea = get_content_idea(display_name)

        us_badge = ""
        if flag == "US":
            us_badge = "\nAVANT-PREMIERE US - sois le premier en France !"

        msg = (
            "TREND TIKTOK DETECTEE\n"
            + us_badge + "\n\n"
            + "Tendance: " + display_name + "\n"
            + "Source: " + flag + " - " + geo + "\n"
            + "Score viralite: " + str(score) + "/100\n"
            + "Progression: +" + str(delta) + " pts\n"
            + "Fenetre: " + window + "\n\n"
            + "---\n"
            + "IDEE CONTENU:\n\n"
            + idea + "\n\n"
            + "---\n"
            + "Cherche sur TikTok: " + display_name + "\n"
            + "Meilleurs horaires: " + get_best_times() + "\n"
            + datetime.now().strftime("%H:%M - %d/%m/%Y")
        )

        send_telegram(msg)
        sent += 1
        time.sleep(2)

    songs = get_youtube_charts()
    if songs:
        msg = (
            "SONS VIRAUX - " + datetime.now().strftime("%d/%m") + "\n\n"
            + "YouTube Charts France:\n"
        )
        for i, s in enumerate(songs, 1):
            msg += str(i) + ". " + s + "\n"
        msg += (
            "\nComment utiliser ces sons:\n"
            + "-> Cherche le son sur TikTok\n"
            + "-> Regarde les videos qui performent\n"
            + "-> Adapte a ta niche sport/mode\n"
            + "-> Poste dans les 24h\n\n"
            + "Meilleurs horaires: " + get_best_times()
        )
        send_telegram(msg)
        sent += 1

    return sent

def main():
    print("TikTok Trend Bot v3 starting...")
    print("Sources: Google Trends US+FR + YouTube Charts")
    print("Interval: " + str(CHECK_INTERVAL // 60) + " minutes")

    send_telegram(
        "TikTok Trend Bot v3 demarre!\n\n"
        "Sources actives:\n"
        "- Google Trends France temps reel\n"
        "- Google Trends USA (avant-premiere)\n"
        "- YouTube Charts France\n"
        "- Trending searches FR + US\n\n"
        "Toutes niches - detection automatique\n"
        "Meilleurs horaires de publication\n\n"
        "Premiere analyse en cours..."
    )

    cycle = 0
    while True:
        cycle += 1
        print("ANALYSE #" + str(cycle) + " " + datetime.now().strftime("%H:%M"))
        sent = analyze_and_alert()
        print("FIN #" + str(cycle) + " - " + str(sent) + " alertes")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
