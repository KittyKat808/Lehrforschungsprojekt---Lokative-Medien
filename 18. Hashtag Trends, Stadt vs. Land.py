import json
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
import os
from datetime import datetime

# Matplotlib auf Deutsch
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False


# Großstädte-Mapping (Englisch → Deutsch)
GROSSSTAEDTE_MAPPING = {
    "Berlin": "Berlin",
    "Hamburg": "Hamburg",
    "Munich": "München",
    "Cologne": "Köln",
    "Frankfurt": "Frankfurt am Main",
    "Frankfurt am Main": "Frankfurt am Main",
    "Dusseldorf": "Düsseldorf",
    "Düsseldorf": "Düsseldorf",
    "Stuttgart": "Stuttgart",
    "Leipzig": "Leipzig",
    "Dortmund": "Dortmund",
    "Bremen": "Bremen",
    "Essen": "Essen",
    "Dresden": "Dresden",
    "Nuremberg": "Nürnberg",
    "Nürnberg": "Nürnberg",
    "Hanover": "Hannover",
    "Hannover": "Hannover",
    "Duisburg": "Duisburg",
    "Bochum": "Bochum",
    "Wuppertal": "Wuppertal",
    "Bielefeld": "Bielefeld",
    "Bonn": "Bonn",
    "Mannheim": "Mannheim",
    "Karlsruhe": "Karlsruhe",
    "Munster": "Münster",
    "Münster": "Münster",
    "Augsburg": "Augsburg",
    "Wiesbaden": "Wiesbaden",
    "Gelsenkirchen": "Gelsenkirchen",
    "Monchengladbach": "Mönchengladbach",
    "Mönchengladbach": "Mönchengladbach",
    "Aachen": "Aachen",
    "Brunswick": "Braunschweig",
    "Braunschweig": "Braunschweig",
    "Kiel": "Kiel",
    "Chemnitz": "Chemnitz",
    "Magdeburg": "Magdeburg",
    "Freiburg": "Freiburg im Breisgau",
    "Freiburg im Breisgau": "Freiburg im Breisgau",
    "Krefeld": "Krefeld",
    "Halle": "Halle (Saale)",
    "Halle (Saale)": "Halle (Saale)",
    "Mainz": "Mainz",
    "Erfurt": "Erfurt",
    "Lubeck": "Lübeck",
    "Lübeck": "Lübeck",
    "Oberhausen": "Oberhausen",
    "Rostock": "Rostock",
    "Kassel": "Kassel",
    "Hagen": "Hagen",
    "Potsdam": "Potsdam",
    "Saarbrucken": "Saarbrücken",
    "Saarbrücken": "Saarbrücken",
    "Hamm": "Hamm",
    "Ludwigshafen": "Ludwigshafen am Rhein",
    "Ludwigshafen am Rhein": "Ludwigshafen am Rhein",
    "Oldenburg": "Oldenburg",
    "Mulheim": "Mülheim an der Ruhr",
    "Mülheim": "Mülheim an der Ruhr",
    "Mülheim an der Ruhr": "Mülheim an der Ruhr",
    "Leverkusen": "Leverkusen",
    "Darmstadt": "Darmstadt",
    "Osnabruck": "Osnabrück",
    "Osnabrück": "Osnabrück",
    "Solingen": "Solingen",
    "Paderborn": "Paderborn",
    "Herne": "Herne",
    "Heidelberg": "Heidelberg",
    "Neuss": "Neuss",
    "Regensburg": "Regensburg",
    "Ingolstadt": "Ingolstadt",
    "Pforzheim": "Pforzheim",
    "Wurzburg": "Würzburg",
    "Würzburg": "Würzburg",
    "Offenbach": "Offenbach am Main",
    "Offenbach am Main": "Offenbach am Main",
    "Furth": "Fürth",
    "Fürth": "Fürth",
    "Heilbronn": "Heilbronn",
    "Ulm": "Ulm",
    "Wolfsburg": "Wolfsburg",
    "Gottingen": "Göttingen",
    "Göttingen": "Göttingen",
    "Reutlingen": "Reutlingen",
    "Bremerhaven": "Bremerhaven",
    "Bottrop": "Bottrop",
    "Erlangen": "Erlangen",
    "Recklinghausen": "Recklinghausen",
    "Remscheid": "Remscheid",
    "Koblenz": "Koblenz",
    "Bergisch Gladbach": "Bergisch Gladbach",
    "Jena": "Jena",
    "Salzgitter": "Salzgitter",
    "Trier": "Trier",
    "Siegen": "Siegen",
    "Moers": "Moers",
    "Gutersloh": "Gütersloh",
    "Gütersloh": "Gütersloh",
}

GROSSSTAEDTE_ENGLISCH = set(GROSSSTAEDTE_MAPPING.keys())
STADTSTAATEN = ['Berlin', 'Hamburg', 'Bremen', 'Free Hanseatic City of Bremen', 'Hanseatic City']


def normalize_hashtag(hashtag):
    """
    Normalisiert Hashtags zu Kategorien
    Returns: (normalized_tag, category) oder (None, None) wenn nicht relevant
    """
    tag_lower = hashtag.lower().replace('_', '').replace('-', '').replace(' ', '').replace('ー', '')

    # Ausschlussliste
    excluded = ['aviationlockdownnow', 'ausgangssperrejetzt', 'ausgangssperreüberfällig',
                'endthelockdown', 'lockdownend',
                'trotzabstandhaltenwirzusammen', 'friendlydistancing']

    if tag_lower in excluded:
        return None, None

    # 1. FlattenTheCurve Varianten
    if any(x in tag_lower for x in ['flattenthecurve', 'flatenthecurve', 'flatthecurve',
                                    'kurveflachen', 'kurveabflachen', 'diekurveflachen']):
        return 'FlattenTheCurve', 'Gesundheitsmaßnahmen'

    # 2. Stay Home / Bleibt Zuhause Varianten
    if any(x in tag_lower for x in ['wirbleibenzuhause', 'bleibtzuhause', 'bleibzuhause',
                                    'ichbleibezuhause', 'bleibtdaheim', 'bleibtheim',
                                    'zuhausebleiben', 'daheimbleiben',
                                    'stayhome', 'stayathome', 'stayinghome',
                                    'stayindoors', 'stayinside',
                                    'wirbleibendaheim', 'ichbleibedaheim']):
        return 'WirBleibenZuhause', 'Solidarität'

    # 3. Social Distancing Varianten
    if any(x in tag_lower for x in ['socialdistancing', 'socialdistance', 'socialdist',
                                    'physicaldistancing', 'physicaldistance',
                                    'sozialedistanzierung', 'sozialedistanz',
                                    'abstandhalten', 'abstandhalte', 'keepdistance',
                                    'distancing', 'distanz']):
        return 'SocialDistancing', 'Gesundheitsmaßnahmen'

    # 4. Lockdown Varianten
    if any(x in tag_lower for x in ['lockdown', 'coronalockdown', 'covidlockdown',
                                    'shutdown', 'ausgangssperre', 'ausgangsbeschränkung', 'ausgangsverbot',
                                    'kontaktsperre', 'kontaktverbot', 'kontaktbeschränkung']):
        return 'Lockdown', 'Maßnahmen'

    # 5. Coronakrise Varianten
    if any(x in tag_lower for x in ['coronakrise', 'coronacrisis', 'covidkrise', 'covidcrisis',
                                    'coronaviruskrise', 'coronaviruscrisis',
                                    'covid19krise', 'covid19crisis']):
        return 'Coronakrise', 'Framing'

    return None, None


def load_tweets(input_file):
    """Lädt Tweets aus JSONL-Datei"""
    print(f"Lade Tweets aus: {input_file}")
    tweets = []

    with open(input_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if line_num % 10000 == 0:
                print(f"  {line_num} Zeilen gelesen...")

            try:
                tweets.append(json.loads(line.strip()))
            except:
                continue

    print(f"✓ {len(tweets)} Tweets geladen\n")
    return tweets


def kategorisiere_tweet_urban_rural(tweet):
    """Kategorisiert Tweet als Urban oder Rural"""
    geo_source = tweet.get('geo_source')

    if not geo_source:
        return 'Unknown'

    if geo_source == 'place' and tweet.get('place'):
        location_data = tweet['place']
    elif geo_source == 'coordinates' and tweet.get('geo'):
        location_data = tweet['geo']
    else:
        return 'Unknown'

    # Stadtstaaten
    state = location_data.get('state', '')
    if any(stadtstaat in state for stadtstaat in STADTSTAATEN):
        return 'Urban'

    # city oder county
    ort = None
    if 'city' in location_data and location_data['city']:
        ort = location_data['city']
    elif 'county' in location_data and location_data['county']:
        ort = location_data['county']

    if not ort:
        return 'Unknown'

    ort_clean = ort.replace("Region ", "").replace("City of ", "").strip()

    if ort_clean in GROSSSTAEDTE_ENGLISCH:
        return 'Urban'
    else:
        return 'Rural'


def analyze_hashtag_trends_urban_rural(tweets, output_dir):
    """Analysiert Hashtag-Trends nach Urban/Rural - ANTEIL AN ALLEN HASHTAGS"""

    print("Analysiere Hashtag-Kategorien als Anteil aller Hashtags...")

    # Datenstrukturen
    # Kategorisierte Hashtags
    urban_trends = Counter()
    rural_trends = Counter()
    all_trends = Counter()

    # ALLE Hashtags (inkl. nicht-kategorisierte)
    urban_all_hashtags = 0
    rural_all_hashtags = 0
    total_all_hashtags = 0

    tweets_processed = 0
    tweets_with_hashtags_urban = 0
    tweets_with_hashtags_rural = 0

    # Tweets durchgehen
    for tweet in tweets:
        hashtags = tweet.get('entities', {}).get('hashtags', [])

        if not hashtags:
            continue

        tweets_processed += 1

        # Kategorisiere Tweet
        kategorie = kategorisiere_tweet_urban_rural(tweet)

        if kategorie == 'Unknown':
            continue

        # Zähle ALLE Hashtags
        num_hashtags = len(hashtags)
        total_all_hashtags += num_hashtags

        if kategorie == 'Urban':
            urban_all_hashtags += num_hashtags
            tweets_with_hashtags_urban += 1
        else:  # Rural
            rural_all_hashtags += num_hashtags
            tweets_with_hashtags_rural += 1

        # Normalisiere und zähle kategorisierte Hashtags
        for hashtag in hashtags:
            normalized, category = normalize_hashtag(hashtag)

            if normalized:
                all_trends[normalized] += 1

                if kategorie == 'Urban':
                    urban_trends[normalized] += 1
                else:  # Rural
                    rural_trends[normalized] += 1

    print(f"✓ {tweets_processed:,} Tweets mit Hashtags")
    print(f"  - Urban: {tweets_with_hashtags_urban:,} Tweets, {urban_all_hashtags:,} Hashtags gesamt")
    print(f"  - Rural: {tweets_with_hashtags_rural:,} Tweets, {rural_all_hashtags:,} Hashtags gesamt")
    print(f"\n✓ Kategorisierte Hashtags:")
    print(
        f"  - Urban: {sum(urban_trends.values()):,} ({sum(urban_trends.values()) / urban_all_hashtags * 100:.2f}% aller Urban-Hashtags)")
    print(
        f"  - Rural: {sum(rural_trends.values()):,} ({sum(rural_trends.values()) / rural_all_hashtags * 100:.2f}% aller Rural-Hashtags)\n")

    # Output-Verzeichnis erstellen
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # TXT-Report erstellen
    save_txt_report(all_trends, urban_trends, rural_trends,
                    urban_all_hashtags, rural_all_hashtags, total_all_hashtags,
                    tweets, tweets_processed, output_dir, timestamp)

    # Visualisierung erstellen
    create_visualization(urban_trends, rural_trends,
                         urban_all_hashtags, rural_all_hashtags,
                         output_dir, timestamp)

    print(f"\n{'=' * 60}")
    print("HASHTAG-KATEGORIE-ANALYSE ABGESCHLOSSEN!")
    print(f"{'=' * 60}\n")


def save_txt_report(all_trends, urban_trends, rural_trends,
                    urban_all_hashtags, rural_all_hashtags, total_all_hashtags,
                    tweets, tweets_processed, output_dir, timestamp):
    """Speichert TXT-Report mit Anteil an allen Hashtags"""

    txt_file = os.path.join(output_dir, f"hashtag_kategorien_anteil_{timestamp}.txt")

    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write("HASHTAG-KATEGORIEN: ANTEIL AN ALLEN HASHTAGS (URBAN VS. RURAL)\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Analysezeitpunkt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Gesamtzahl Tweets: {len(tweets):,}\n")
        f.write(f"Tweets mit Hashtags (Urban/Rural): {tweets_processed:,}\n\n")

        f.write(f"ALLE HASHTAGS:\n")
        f.write(f"  - Gesamt: {total_all_hashtags:,}\n")
        f.write(f"  - Urban: {urban_all_hashtags:,} ({urban_all_hashtags / total_all_hashtags * 100:.1f}%)\n")
        f.write(f"  - Rural: {rural_all_hashtags:,} ({rural_all_hashtags / total_all_hashtags * 100:.1f}%)\n\n")

        total_categorized = sum(all_trends.values())
        total_urban_categorized = sum(urban_trends.values())
        total_rural_categorized = sum(rural_trends.values())

        f.write(f"KATEGORISIERTE HASHTAGS:\n")
        f.write(
            f"  - Gesamt: {total_categorized:,} ({total_categorized / total_all_hashtags * 100:.2f}% aller Hashtags)\n")
        f.write(
            f"  - Urban: {total_urban_categorized:,} ({total_urban_categorized / urban_all_hashtags * 100:.2f}% aller Urban-Hashtags)\n")
        f.write(
            f"  - Rural: {total_rural_categorized:,} ({total_rural_categorized / rural_all_hashtags * 100:.2f}% aller Rural-Hashtags)\n\n")

        # Gesamt-Übersicht
        f.write("=" * 80 + "\n")
        f.write("KATEGORIEN-ÜBERSICHT (ANTEIL AN ALLEN HASHTAGS IM GEBIET)\n")
        f.write("=" * 80 + "\n\n")

        f.write(f"{'Kategorie':<25} {'Urban Anzahl':<15} {'Urban %':<12} {'Rural Anzahl':<15} {'Rural %':<12}\n")
        f.write("-" * 80 + "\n")

        all_trend_names = sorted(set(urban_trends.keys()) | set(rural_trends.keys()))
        for trend in all_trend_names:
            urban_count = urban_trends.get(trend, 0)
            rural_count = rural_trends.get(trend, 0)

            # Anteil an ALLEN Hashtags im jeweiligen Gebiet
            urban_pct = (urban_count / urban_all_hashtags * 100) if urban_all_hashtags > 0 else 0
            rural_pct = (rural_count / rural_all_hashtags * 100) if rural_all_hashtags > 0 else 0

            f.write(f"#{trend:<24} {urban_count:<15,} {urban_pct:>6.2f}%      {rural_count:<15,} {rural_pct:>6.2f}%\n")

        # Interpretation
        f.write("\n\n" + "=" * 80 + "\n")
        f.write("INTERPRETATION\n")
        f.write("=" * 80 + "\n\n")

        f.write(f"1. KATEGORISIERUNGSRATE:\n")
        f.write(
            f"   - In Urban werden {total_urban_categorized / urban_all_hashtags * 100:.2f}% aller Hashtags kategorisiert\n")
        f.write(
            f"   - In Rural werden {total_rural_categorized / rural_all_hashtags * 100:.2f}% aller Hashtags kategorisiert\n\n")

        if urban_trends and rural_trends:
            top_urban = urban_trends.most_common(1)[0]
            top_rural = rural_trends.most_common(1)[0]

            urban_top_pct = (top_urban[1] / urban_all_hashtags * 100)
            rural_top_pct = (top_rural[1] / rural_all_hashtags * 100)

            f.write(f"2. POPULÄRSTE KATEGORIEN:\n")
            f.write(f"   - Urban: #{top_urban[0]} ({urban_top_pct:.2f}% aller Urban-Hashtags)\n")
            f.write(f"   - Rural: #{top_rural[0]} ({rural_top_pct:.2f}% aller Rural-Hashtags)\n\n")

            f.write(f"3. STADT-LAND-UNTERSCHIED:\n")
            for trend in all_trend_names:
                urban_pct = (urban_trends.get(trend, 0) / urban_all_hashtags * 100) if urban_all_hashtags > 0 else 0
                rural_pct = (rural_trends.get(trend, 0) / rural_all_hashtags * 100) if rural_all_hashtags > 0 else 0
                diff = urban_pct - rural_pct

                if abs(diff) > 0.5:  # Nur relevante Unterschiede zeigen
                    if diff > 0:
                        f.write(f"   - #{trend}: {abs(diff):.2f} Prozentpunkte MEHR in Urban\n")
                    else:
                        f.write(f"   - #{trend}: {abs(diff):.2f} Prozentpunkte MEHR in Rural\n")

    print(f"✓ TXT-Report: {txt_file}")


def create_visualization(urban_trends, rural_trends,
                         urban_all_hashtags, rural_all_hashtags,
                         output_dir, timestamp):
    """Erstellt Balkendiagramm mit Anteil an allen Hashtags"""

    print("Erstelle Visualisierung...")

    # Daten vorbereiten - Anteil an ALLEN Hashtags
    all_trend_names = sorted(set(urban_trends.keys()) | set(rural_trends.keys()))

    urban_percentages = [(urban_trends.get(trend, 0) / urban_all_hashtags * 100) if urban_all_hashtags > 0 else 0
                         for trend in all_trend_names]
    rural_percentages = [(rural_trends.get(trend, 0) / rural_all_hashtags * 100) if rural_all_hashtags > 0 else 0
                         for trend in all_trend_names]

    # Erstelle DataFrame
    df = pd.DataFrame({
        'Kategorie': all_trend_names,
        'Urban': urban_percentages,
        'Rural': rural_percentages
    })

    # Sortiere nach Urban-Werten
    df = df.sort_values('Urban', ascending=True)

    # Figure erstellen
    fig, ax = plt.subplots(figsize=(12, 8))

    # Farben
    colors_map = {
        'Coronakrise': '#9b59b6',
        'FlattenTheCurve': '#e74c3c',
        'Lockdown': '#f39c12',
        'SocialDistancing': '#2ecc71',
        'WirBleibenZuhause': '#3498db'
    }

    y_pos = range(len(df))
    bar_height = 0.35

    # Balken erstellen
    for idx, row in df.iterrows():
        color = colors_map.get(row['Kategorie'], '#95a5a6')
        pos = list(df['Kategorie']).index(row['Kategorie'])

        # Urban Balken
        ax.barh(pos - bar_height / 2, row['Urban'], bar_height,
                label=f"Urban" if idx == 0 else "",
                color=color, alpha=0.8, edgecolor='white', linewidth=1.5)

        # Rural Balken
        ax.barh(pos + bar_height / 2, row['Rural'], bar_height,
                label=f"Rural" if idx == 0 else "",
                color=color, alpha=0.5, edgecolor='white', linewidth=1.5)

    # Styling
    ax.set_yticks(y_pos)
    ax.set_yticklabels(['#' + cat for cat in df['Kategorie']], fontsize=11)
    ax.set_xlabel('Anteil an allen Hashtags im Gebiet (%)', fontsize=12, fontweight='bold')
    ax.set_title('Hashtag-Kategorien: Anteil an allen Hashtags\nUrban vs. Rural',
                 fontsize=14, fontweight='bold', pad=20)
    ax.grid(axis='x', alpha=0.3, linestyle='--')

    # Legende
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='gray', alpha=0.5, label='Rural (Ländliche Regionen)'),
        Patch(facecolor='gray', alpha=0.8, label='Urban (Großstädte >100k)')
    ]
    ax.legend(handles=legend_elements, loc='lower right', fontsize=10, frameon=True)

    plt.tight_layout()

    output_file = os.path.join(output_dir, f"hashtag_kategorien_anteil_{timestamp}.png")
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Visualisierung gespeichert: {output_file}")

    plt.close()


def main():
    # PASSE DIESE PFADE AN!
    input_file = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\Cleaned_Data.jsonl"
    output_dir = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\Hashtag_Kategorien_Anteil"

    tweets = load_tweets(input_file)
    analyze_hashtag_trends_urban_rural(tweets, output_dir)


if __name__ == "__main__":
    main()