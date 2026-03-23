"""
╔══════════════════════════════════════════════════════════════╗
║         TIKTOK TREND BOT — Détecteur de tendances           ║
║  Sources : Google Trends + TikTok scraping + IA Claude      ║
║  Alerte  : Telegram avec idée contenu personnalisée         ║
╚══════════════════════════════════════════════════════════════╝

INSTALLATION :
  pip install requests pytrends beautifulsoup4

CONFIGURATION :
  1. Même TELEGRAM_TOKEN et TELEGRAM_CHAT_ID que le bot Vinted
  2. Lance : python tiktok_trends.py
"""

import requests
import time
import json
import re
from datetime import datetime
from pytrends.request import TrendReq

TELEGRAM_TOKEN   = "8611988792:AAGOJ7xDWPRJveS0jOe71NH5rWczdKwPUgI"
TELEGRAM_CHAT_ID = "8559815820"
ANTHROPIC_API_KEY = ""  # Optionnel — pour les idées contenu IA

CHECK_INTERVAL = 3600   # Scan toutes les heures
MIN_TREND_SCORE = 60    # Score Google Trends minimum (0-100)

# ════════════════════════════════════════════════════════
#  🎯  TES NICHES & PROFIL
# ════════════════════════════════════════════════════════

MY_PROFILE = """
Créateur de contenu homme, 20 ans environ.
Passions : musculation, sport, mode streetwear et luxe, lifestyle.
Style de contenu : authentique, dynamique, transitions, before/after.
Plateformes : TikTok principal, Instagram secondaire.
"""

NICHES = [
    "musculation", "sport", "mode homme", "streetwear",
    "lifestyle", "fitness", "motivation", "psychologie",
    "mode luxe", "sneakers", "outfit", "transformation"
]

# Mots-clés à surveiller sur Google Trends
TREND_KEYWORDS = {
    "Sport & Fitness": [
        "routine musculation", "programme fitness", "transformation physique",
        "bulk cut", "seche muscu", "prise de masse", "cardio hiit",
        "calisthenics", "street workout", "home workout"
    ],
    "Mode & Style": [
        "outfit homme", "tenue casual", "streetwear 2025", "look stylé homme",
        "sneakers tendance", "vinted trouvaille", "mode luxe abordable",
        "capsule wardrobe", "tenue sport chic"
    ],
    "Lifestyle & Motivation": [
        "routine matinale", "discipline", "mindset gagnant", "productive day",
        "day in my life", "vlog quotidien", "goals 2025",
        "psychologie motivation", "habitudes succès"
    ],
    "Tendances TikTok": [
        "tiktok trend", "viral tiktok", "son viral", "challenge tiktok",
        "transition tiktok", "pov tiktok", "trending sound"
    ]
}

# ════════════════════════════════════════════════════════
#  📊  GOOGLE TRENDS — Détection tendances montantes
# ════════════════════════════════════════════════════════

def get_google_trends(keywords, timeframe="now 7-d", geo="FR"):
    """
    Récupère les scores Google Trends pour une liste de mots-clés.
    Retourne un dict {keyword: score_moyen}
    """
    results = {}
    pytrends = TrendReq(hl="fr-FR", tz=60)

    # Google Trends accepte max 5 mots-clés par requête
    chunks = [keywords[i:i+5] for i in range(0, len(keywords), 5)]

    for chunk in chunks:
        try:
            pytrends.build_payload(chunk, timeframe=timeframe, geo=geo)
            df = pytrends.interest_over_time()

            if df.empty:
                continue

            for kw in chunk:
                if kw in df.columns:
                    # Score moyen sur la période
                    avg_score    = int(df[kw].mean())
                    # Score récent (derniers 2 jours)
                    recent_score = int(df[kw].tail(2).mean())
                    # Tendance : score récent vs moyenne
                    trend_delta  = recent_score - avg_score
                    results[kw] = {
                        "avg":    avg_score,
                        "recent": recent_score,
                        "delta":  trend_delta,
                        "score":  recent_score
                    }
            time.sleep(2)  # Respect rate limit Google
        except Exception as e:
            print(f"  [Trends] Erreur '{chunk}': {e}")
            time.sleep(5)

    return results

def get_trending_searches(geo="FR"):
    """Récupère les recherches tendances du moment sur Google."""
    try:
        pytrends = TrendReq(hl="fr-FR", tz=60)
        trending  = pytrends.trending_searches(pn="france")
        return trending[0].tolist()[:20]
    except Exception as e:
        print(f"  [Trends] Trending searches erreur: {e}")
        return []

def get_related_queries(keyword, geo="FR"):
    """Récupère les requêtes liées à un mot-clé trending."""
    try:
        pytrends = TrendReq(hl="fr-FR", tz=60)
        pytrends.build_payload([keyword], timeframe="now 7-d", geo=geo)
        related = pytrends.related_queries()
        if keyword in related and related[keyword]["rising"] is not None:
            return related[keyword]["rising"]["query"].tolist()[:5]
        return []
    except:
        return []

# ════════════════════════════════════════════════════════
#  🎵  TIKTOK TRENDS — Scraping sons et hashtags viraux
# ════════════════════════════════════════════════════════

SCRAPE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
}

def scrape_tiktok_trending_hashtags():
    """
    Scrape les hashtags trending TikTok depuis des sources publiques.
    Retourne une liste de hashtags avec leur popularité estimée.
    """
    hashtags = []

    # Source 1 : TikTok Creative Center (public)
    try:
        r = requests.get(
            "https://ads.tiktok.com/business/creativecenter/trend-calendar/pc/en",
            headers=SCRAPE_HEADERS, timeout=10
        )
        # Extraction basique des hashtags mentionnés
        found = re.findall(r'#([a-zA-Z0-9_]{3,30})', r.text)
        hashtags.extend(found[:20])
    except Exception as e:
        print(f"  [TikTok] Creative Center erreur: {e}")

    # Source 2 : Recherche tendances via Tokboard (site public de stats TikTok)
    try:
        r = requests.get(
            "https://www.tokboard.com/trending",
            headers=SCRAPE_HEADERS, timeout=10
        )
        found = re.findall(r'#([a-zA-Z0-9_]{3,30})', r.text)
        hashtags.extend(found[:20])
    except Exception as e:
        print(f"  [TikTok] Tokboard erreur: {e}")

    # Source 3 : TrendTok via scraping
    try:
        r = requests.get(
            "https://www.trendtok.com/trending",
            headers=SCRAPE_HEADERS, timeout=10
        )
        found = re.findall(r'#([a-zA-Z0-9_]{3,30})', r.text)
        hashtags.extend(found[:20])
    except Exception as e:
        print(f"  [TikTok] TrendTok erreur: {e}")

    # Dédupliquer et filtrer
    seen = set()
    unique = []
    for h in hashtags:
        h_lower = h.lower()
        if h_lower not in seen and len(h_lower) > 2:
            seen.add(h_lower)
            unique.append(h)

    return unique[:30]

def scrape_trending_sounds():
    """
    Récupère les sons TikTok trending depuis des trackers publics.
    """
    sounds = []

    try:
        r = requests.get(
            "https://www.tokboard.com/sounds",
            headers=SCRAPE_HEADERS, timeout=10
        )
        # Cherche des noms de sons (entre guillemets ou balises titre)
        found = re.findall(r'"([^"]{5,60})"', r.text)
        sounds.extend(found[:15])
    except Exception as e:
        print(f"  [Sons] Tokboard erreur: {e}")

    # Fallback : sons viraux connus du moment via recherche Google Trends
    try:
        pytrends = TrendReq(hl="fr-FR", tz=60)
        pytrends.build_payload(["son viral tiktok"], timeframe="now 7-d", geo="FR")
        related = pytrends.related_queries()
        if "son viral tiktok" in related:
            df = related["son viral tiktok"].get("rising")
            if df is not None:
                sounds.extend(df["query"].tolist()[:10])
    except:
        pass

    return sounds[:20]

# ════════════════════════════════════════════════════════
#  🤖  ANALYSE IA — Idées contenu personnalisées
# ════════════════════════════════════════════════════════

def generate_content_idea(trend_name, trend_type, niche, score):
    """
    Utilise Claude pour générer une idée de contenu TikTok personnalisée.
    Retourne une string avec l'idée.
    """
    if not ANTHROPIC_API_KEY:
        return _default_content_idea(trend_name, trend_type, niche)

    prompt = f"""Tu es un expert en stratégie de contenu TikTok.

PROFIL DU CRÉATEUR :
{MY_PROFILE}

TREND DÉTECTÉE :
- Nom : {trend_name}
- Type : {trend_type} (hashtag / son / sujet)
- Niche : {niche}
- Score de viralité : {score}/100

Ta mission : génère UNE idée de vidéo TikTok ultra-précise et actionnable pour ce créateur.

Format de réponse (court, direct) :
🎬 CONCEPT : [idée en 1 phrase]
🎵 SON/FORMAT : [son à utiliser ou format vidéo]
⏱️ DURÉE : [durée idéale]
📋 SCRIPT : [3 étapes max de la vidéo]
💡 HOOK : [première seconde accrocheur]
⚡ POURQUOI ÇA VA MARCHER : [1 phrase]"""

    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 400,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=15
        )
        if r.status_code == 200:
            return r.json()["content"][0]["text"]
    except Exception as e:
        print(f"  [IA] Erreur: {e}")

    return _default_content_idea(trend_name, trend_type, niche)

def _default_content_idea(trend_name, trend_type, niche):
    """Idée contenu basique sans IA."""
    ideas = {
        "Sport & Fitness": f"🎬 Vidéo transformation/résultat avec #{trend_name}\n📋 Avant → pendant → après entraînement\n💡 Hook : 'Ce que personne ne te dit sur...'",
        "Mode & Style": f"🎬 Transition tenue avec #{trend_name}\n📋 Tenue casual → tenue stylée en 3 secondes\n💡 Hook : 'POV tu sais t'habiller'",
        "Lifestyle & Motivation": f"🎬 Day in my life avec #{trend_name}\n📋 Routine matinale → entraînement → sortie\n💡 Hook : 'Ma journée type pour...'",
        "Tendances TikTok": f"🎬 Utilise ce son/trend immédiatement\n📋 Adapte le format trend à ta niche sport/mode\n💡 Hook : jump cut dynamique dès la 1ère seconde",
    }
    return ideas.get(niche, f"🎬 Contenu autour de #{trend_name} dans ta niche\n💡 Authentique + dynamique + hook fort dès la 1ère seconde")

# ════════════════════════════════════════════════════════
#  📊  ANALYSE COMPLÈTE DES TRENDS
# ════════════════════════════════════════════════════════

already_alerted = set()

def analyze_and_alert():
    """
    Lance une analyse complète et envoie les meilleures trends.
    """
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Analyse des trends en cours...")
    alerts_sent = 0

    # ── 1. Google Trends par niche ──
    print("  [1/4] Google Trends par niche...")
    all_trend_results = {}

    for niche, keywords in TREND_KEYWORDS.items():
        print(f"    → {niche}...")
        results = get_google_trends(keywords)
        for kw, data in results.items():
            if data["score"] >= MIN_TREND_SCORE or data["delta"] >= 20:
                all_trend_results[kw] = {"niche": niche, **data}
        time.sleep(3)

    # ── 2. Recherches tendances Google FR ──
    print("  [2/4] Recherches tendances Google FR...")
    trending_searches = get_trending_searches()
    for search in trending_searches:
        # Filtre : pertinent pour nos niches ?
        search_lower = search.lower()
        is_relevant  = any(
            niche_kw in search_lower
            for niche_kw in ["sport", "mode", "fit", "gym", "style", "music", "son", "trend", "tik"]
        )
        if is_relevant:
            all_trend_results[search] = {
                "niche": "Tendances TikTok",
                "score": 75,
                "delta": 30,
                "recent": 75,
                "avg": 45,
            }

    # ── 3. Hashtags TikTok trending ──
    print("  [3/4] Hashtags TikTok trending...")
    hashtags = scrape_tiktok_trending_hashtags()
    for h in hashtags[:10]:
        cache_key = f"hashtag_{h.lower()}"
        if cache_key not in already_alerted:
            all_trend_results[f"#{h}"] = {
                "niche": "Tendances TikTok",
                "score": 70,
                "delta": 25,
                "recent": 70,
                "avg": 45,
                "type": "hashtag"
            }

    # ── 4. Sons viraux ──
    print("  [4/4] Sons viraux TikTok...")
    sounds = scrape_trending_sounds()

    # ── Envoi des meilleures trends ──
    print(f"\n  Trends détectées : {len(all_trend_results)}")

    # Tri par score décroissant
    sorted_trends = sorted(
        all_trend_results.items(),
        key=lambda x: x[1].get("score", 0) + x[1].get("delta", 0) * 2,
        reverse=True
    )

    # On envoie les 5 meilleures non déjà alertées
    top_sent = 0
    for trend_name, data in sorted_trends:
        if top_sent >= 5:
            break

        cache_key = trend_name.lower().replace(" ", "_")
        if cache_key in already_alerted:
            continue

        already_alerted.add(cache_key)
        niche     = data.get("niche", "Tendances TikTok")
        score     = data.get("score", 70)
        delta     = data.get("delta", 0)
        trend_type = data.get("type", "sujet")

        # Idée contenu
        content_idea = generate_content_idea(trend_name, trend_type, niche, score)

        # Fenêtre d'opportunité
        if delta >= 40:   window = "⚡ MAINTENANT — moins de 24h"
        elif delta >= 20: window = "🔴 48h maximum"
        elif delta >= 10: window = "🟠 3-4 jours"
        else:             window = "🟡 Cette semaine"

        msg = (
            f"🎯 <b>TREND TIKTOK DÉTECTÉE</b>\n\n"
            f"📌 <b>{trend_name}</b>\n"
            f"🏷️ Niche : {niche}\n"
            f"📈 Score viralité : <b>{score}/100</b>\n"
            f"⬆️ Progression : +{delta} pts cette semaine\n"
            f"⏰ Fenêtre : <b>{window}</b>\n\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💡 <b>IDÉE CONTENU POUR TOI :</b>\n\n"
            f"{content_idea}\n\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🔗 Rechercher sur TikTok : {trend_name}\n"
            f"⏰ {datetime.now().strftime('%H:%M — %d/%m/%Y')}"
        )

        send_telegram(msg)
        alerts_sent += 1
        top_sent    += 1
        time.sleep(2)

    # ── Sons viraux (message séparé) ──
    if sounds:
        sounds_msg = (
            f"🎵 <b>SONS VIRAUX TIKTOK — {datetime.now().strftime('%d/%m')}</b>\n\n"
        )
        for i, sound in enumerate(sounds[:8], 1):
            sounds_msg += f"{i}. {sound}\n"
        sounds_msg += (
            f"\n💡 <b>Comment les utiliser :</b>\n"
            f"→ Cherche ces sons sur TikTok\n"
            f"→ Regarde les vidéos qui performent avec\n"
            f"→ Adapte le format à ta niche sport/mode\n"
            f"→ Poste dans les 24h pour surfer la vague\n\n"
            f"⏰ {datetime.now().strftime('%H:%M')}"
        )
        send_telegram(sounds_msg)
        alerts_sent += 1

    return alerts_sent

# ════════════════════════════════════════════════════════
#  📲  TELEGRAM
# ════════════════════════════════════════════════════════

def send_telegram(message):
    payload  = {
        "chat_id":               TELEGRAM_CHAT_ID,
        "text":                  message,
        "parse_mode":            "HTML",
        "disable_web_page_preview": True,
    }
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json=payload, timeout=10
        )
        return r.status_code == 200
    except Exception as e:
        print(f"[ERREUR] Telegram: {e}")
        return False

# ════════════════════════════════════════════════════════
#  🚀  MAIN
# ════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("   TIKTOK TREND BOT")
    print(f"   Sources    : Google Trends + TikTok scraping + IA")
    print(f"   Niches     : Sport, Mode, Lifestyle, Motivation")
    print(f"   Intervalle : toutes les {CHECK_INTERVAL // 60} minutes")
    print("=" * 60)

    send_telegram(
        f"🎯 <b>TikTok Trend Bot démarré !</b>\n\n"
        f"📊 Sources actives :\n"
        f"• Google Trends FR temps réel\n"
        f"• Hashtags TikTok trending\n"
        f"• Sons viraux du moment\n"
        f"• Idées contenu personnalisées\n\n"
        f"🎯 Niches surveillées :\n"
        f"Sport • Mode • Lifestyle • Motivation\n\n"
        f"⏰ Analyse toutes les {CHECK_INTERVAL // 60}h\n"
        f"🟢 Première analyse dans quelques secondes..."
    )

    cycle = 0
    while True:
        cycle += 1
        print(f"\n══ ANALYSE #{cycle} ══ {datetime.now().strftime('%H:%M:%S')} ══")
        alerts = analyze_and_alert()
        print(f"══ FIN #{cycle} ══ {alerts} alerte(s) | Prochain dans {CHECK_INTERVAL // 60}min")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
