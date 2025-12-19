import json
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from collections import Counter
import os
from datetime import datetime

# Matplotlib auf Deutsch
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

# Großstädte-Mapping (Englisch → Deutsch)
GROSSSTAEDTE_MAPPING = {
    # Englischer Name (Twitter) : Deutscher Name
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

# Nur englische Namen als Set (für schnelles Lookup)
GROSSSTAEDTE_ENGLISCH = set(GROSSSTAEDTE_MAPPING.keys())

# Stadtstaaten (alle möglichen Schreibweisen)
STADTSTAATEN = ['Berlin', 'Hamburg', 'Bremen', 'Free Hanseatic City of Bremen', 'Hanseatic City']

# Einwohnerzahlen Deutschland gesamt (Stand 31.12.2020)
EINWOHNER_DEUTSCHLAND = 83_200_000

# Einwohnerzahlen Urban/Rural (Quelle: Destatis 2021b)
# "Ende 2020 lebten knapp 24,5 Millionen Menschen in kreisfreien Großstädten
# ab 100 000 Einwohnerinnen und Einwohnern. Das waren rund 29,4 % der Gesamtbevölkerung."
EINWOHNER_URBAN = 24_500_000  # Kreisfreie Großstädte ab 100.000 EW
EINWOHNER_RURAL = 58_700_000  # Rest (gerundet)


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
    """
    Kategorisiert Tweet als Urban (Großstadt >100k) oder Rural

    Logik:
    1. Stadtstaaten (Berlin, Hamburg, Bremen) → Urban
    2. Wenn city vorhanden → prüfe ob Großstadt
    3. Wenn nur county → behandle wie city und prüfe ob Großstadt

    Returns:
        'Urban', 'Rural', oder 'Unknown'
    """
    geo_source = tweet.get('geo_source')

    if not geo_source:
        return 'Unknown'

    # Hole die richtigen Geodaten je nach Quelle
    if geo_source == 'place' and tweet.get('place'):
        location_data = tweet['place']
    elif geo_source == 'coordinates' and tweet.get('geo'):
        location_data = tweet['geo']
    else:
        return 'Unknown'

    # Stadtstaaten sind immer Urban
    # (verschiedene Schreibweisen: "Hamburg", "Free Hanseatic City of Bremen", etc.)
    state = location_data.get('state', '')
    if any(stadtstaat in state for stadtstaat in STADTSTAATEN):
        return 'Urban'

    # Bestimme den zu prüfenden Ortsnamen (Priorität: city > county)
    ort = None
    if 'city' in location_data and location_data['city']:
        ort = location_data['city']
    elif 'county' in location_data and location_data['county']:
        ort = location_data['county']

    if not ort:
        return 'Unknown'

    # Bereinige Ortsnamen
    ort_clean = ort.replace("Region ", "").replace("City of ", "").strip()

    # Prüfe ob Großstadt
    if ort_clean in GROSSSTAEDTE_ENGLISCH:
        return 'Urban'
    else:
        return 'Rural'


def get_city_or_county(tweet):
    """Extrahiert city oder county aus Tweet für Statistiken"""
    geo_source = tweet.get('geo_source')

    if geo_source == 'place' and tweet.get('place'):
        loc = tweet['place']
    elif geo_source == 'coordinates' and tweet.get('geo'):
        loc = tweet['geo']
    else:
        return 'Unknown'

    # Priorität: city > county > state (für Stadtstaaten)
    city = loc.get('city')
    if city:
        return city

    county = loc.get('county')
    if county:
        return county.replace("Region ", "").replace("City of ", "").strip()

    # Für Stadtstaaten: Extrahiere Namen aus state
    state = loc.get('state', '')
    for stadtstaat in ['Berlin', 'Hamburg', 'Bremen']:
        if stadtstaat in state:
            return stadtstaat

    return 'Unknown'


def create_urban_rural_analysis(tweets, output_dir):
    """Erstellt Urban/Rural-Analyse"""

    print("Erstelle Urban/Rural-Analyse...")

    # Kategorisiere alle Tweets
    kategorien = []
    for tweet in tweets:
        kategorie = kategorisiere_tweet_urban_rural(tweet)
        kategorien.append(kategorie)

    # Zähle
    kategorie_counts = Counter(kategorien)

    urban_count = kategorie_counts.get('Urban', 0)
    rural_count = kategorie_counts.get('Rural', 0)
    unknown_count = kategorie_counts.get('Unknown', 0)

    total_classified = urban_count + rural_count

    print(f"\nUrban: {urban_count} ({urban_count / len(tweets) * 100:.1f}%)")
    print(f"Rural: {rural_count} ({rural_count / len(tweets) * 100:.1f}%)")
    print(f"Unknown: {unknown_count} ({unknown_count / len(tweets) * 100:.1f}%)")

    # Pro-Kopf-Berechnung
    urban_pro_100k = (urban_count / EINWOHNER_URBAN) * 100000 if urban_count > 0 else 0
    rural_pro_100k = (rural_count / EINWOHNER_RURAL) * 100000 if rural_count > 0 else 0

    # DataFrame erstellen
    data = {
        'Kategorie': ['Urban', 'Rural'],
        'Tweets_absolut': [urban_count, rural_count],
        'Anteil_Prozent': [urban_count / total_classified * 100 if total_classified > 0 else 0,
                           rural_count / total_classified * 100 if total_classified > 0 else 0],
        'Einwohner': [EINWOHNER_URBAN, EINWOHNER_RURAL],
        'Tweets_pro_100k': [urban_pro_100k, rural_pro_100k]
    }

    df = pd.DataFrame(data)

    # Erstelle Ausgabeverzeichnis
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Top Städte analysieren
    urban_tweets = [tweet for tweet, kat in zip(tweets, kategorien) if kat == 'Urban']
    urban_orte = [get_city_or_county(tweet) for tweet in urban_tweets]
    top_urban_orte = Counter(urban_orte).most_common(20)

    # TXT-Report erstellen
    save_txt_report(df, tweets, urban_count, rural_count, unknown_count,
                    total_classified, urban_pro_100k, rural_pro_100k,
                    top_urban_orte, output_dir, timestamp)

    # Visualisierungen erstellen
    create_visualizations(df, top_urban_orte, output_dir, timestamp)

    return df


def save_txt_report(df, tweets, urban_count, rural_count, unknown_count,
                    total_classified, urban_pro_100k, rural_pro_100k,
                    top_urban_orte, output_dir, timestamp):
    """Speichert TXT-Report"""

    txt_file = os.path.join(output_dir, f"urban_rural_analyse_{timestamp}.txt")
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write("URBAN/RURAL-VERTEILUNG DER CORONA-TWEETS\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Analysezeitpunkt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Gesamtzahl Tweets: {len(tweets):,}\n")
        f.write(f"Klassifizierte Tweets: {total_classified:,} ({total_classified / len(tweets) * 100:.1f}%)\n")
        f.write(f"Nicht klassifiziert: {unknown_count:,} ({unknown_count / len(tweets) * 100:.1f}%)\n\n")

        f.write("=" * 80 + "\n")
        f.write("DEFINITION\n")
        f.write("=" * 80 + "\n\n")
        f.write("Urban: Großstädte mit über 100.000 Einwohnern (n=79)\n")
        f.write("Rural: Alle anderen Städte und Gemeinden\n")
        f.write("Stadtstaaten Berlin, Hamburg, Bremen werden immer als Urban klassifiziert\n\n")

        f.write("=" * 80 + "\n")
        f.write("ÜBERSICHT URBAN VS. RURAL\n")
        f.write("=" * 80 + "\n\n")

        f.write(f"{'Kategorie':<15} {'Tweets':<15} {'Anteil':<12} {'Einwohner':<18} {'Tweets/100k EW':<15}\n")
        f.write("-" * 80 + "\n")
        f.write(
            f"{'Urban':<15} {urban_count:<15,} {urban_count / total_classified * 100 if total_classified > 0 else 0:>6.1f}% "
            f"{EINWOHNER_URBAN:<18,} {urban_pro_100k:>12.1f}\n")
        f.write(
            f"{'Rural':<15} {rural_count:<15,} {rural_count / total_classified * 100 if total_classified > 0 else 0:>6.1f}% "
            f"{EINWOHNER_RURAL:<18,} {rural_pro_100k:>12.1f}\n")
        f.write("-" * 80 + "\n")

        if rural_count > 0:
            f.write(f"Urban/Rural-Ratio (absolut): {urban_count / rural_count:.1f}:1\n")
        if rural_pro_100k > 0:
            f.write(f"Urban/Rural-Ratio (pro Kopf): {urban_pro_100k / rural_pro_100k:.1f}:1\n")

        f.write("\n\n" + "=" * 80 + "\n")
        f.write("TOP 20 STÄDTE (URBAN)\n")
        f.write("=" * 80 + "\n\n")

        f.write(f"{'Rang':<6} {'Stadt':<30} {'Anzahl Tweets':<15}\n")
        f.write("-" * 80 + "\n")
        for i, (stadt, count) in enumerate(top_urban_orte, 1):
            # Übersetze englische Namen ins Deutsche
            stadt_de = GROSSSTAEDTE_MAPPING.get(stadt, stadt)
            f.write(f"{i:<6} {stadt_de:<30} {count:>10,}\n")

        f.write("\n\n" + "=" * 80 + "\n")
        f.write("INTERPRETATION\n")
        f.write("=" * 80 + "\n\n")

        if rural_pro_100k > 0:
            f.write(f"Die urbanen Regionen zeigen mit {urban_pro_100k:.1f} Tweets/100k EW eine\n")

            if urban_pro_100k > rural_pro_100k:
                diff_pct = ((urban_pro_100k / rural_pro_100k) - 1) * 100
                f.write(f"{diff_pct:.0f}% höhere Twitter-Aktivität als ländliche Regionen ")
                f.write(f"({rural_pro_100k:.1f} Tweets/100k EW).\n\n")
            else:
                diff_pct = ((rural_pro_100k / urban_pro_100k) - 1) * 100
                f.write(f"{diff_pct:.0f}% niedrigere Twitter-Aktivität als ländliche Regionen ")
                f.write(f"({rural_pro_100k:.1f} Tweets/100k EW).\n\n")

            f.write("Dies bestätigt die höhere Social-Media-Nutzung in urbanen Zentren,\n")
            f.write("die durch bessere digitale Infrastruktur, höhere Bevölkerungsdichte\n")
            f.write("und demografische Faktoren (jünger, höher gebildet) begünstigt wird.\n")

    print(f"✓ TXT-Report: {txt_file}")


def create_visualizations(df, top_urban_orte, output_dir, timestamp):
    """Erstellt Visualisierungen: Balkendiagramme"""

    print("\nErstelle Visualisierungen...")

    # Figure mit 1x2 Layout
    fig = plt.figure(figsize=(16, 8))

    # 1. BALKENDIAGRAMM: Absolute Zahlen Urban vs. Rural
    ax1 = plt.subplot(1, 2, 1)
    colors = ['#e74c3c', '#27ae60']  # Urban=Rot, Rural=Grün

    ax1.bar(df['Kategorie'], df['Tweets_absolut'], color=colors, alpha=0.8, edgecolor='black')
    ax1.set_ylabel('Anzahl Tweets', fontsize=11)
    ax1.set_title('Tweets: Urban vs. Rural (Absolute Zahlen)', fontsize=13, fontweight='bold')
    ax1.grid(axis='y', alpha=0.3)

    # Werte auf Balken
    for i, (kat, val) in enumerate(zip(df['Kategorie'], df['Tweets_absolut'])):
        ax1.text(i, val + 50, f"{val:,}", ha='center', fontsize=10, fontweight='bold')

    # 2. BALKENDIAGRAMM: Pro 100k Einwohner
    ax2 = plt.subplot(1, 2, 2)

    ax2.bar(df['Kategorie'], df['Tweets_pro_100k'], color=colors, alpha=0.8, edgecolor='black')
    ax2.set_ylabel('Tweets pro 100.000 Einwohner', fontsize=11)
    ax2.set_title('Tweets: Urban vs. Rural (Pro 100k Einwohner)', fontsize=13, fontweight='bold')
    ax2.grid(axis='y', alpha=0.3)

    # Werte auf Balken
    for i, (kat, val) in enumerate(zip(df['Kategorie'], df['Tweets_pro_100k'])):
        ax2.text(i, val + 0.5, f"{val:.1f}", ha='center', fontsize=10, fontweight='bold')

    plt.tight_layout()

    viz_file = os.path.join(output_dir, f"urban_rural_visualisierung_{timestamp}.png")
    plt.savefig(viz_file, dpi=300, bbox_inches='tight')
    print(f"✓ Visualisierung gespeichert: {viz_file}")

    plt.close()

    # ZUSÄTZLICH: Top 20 Städte als separates Diagramm
    if len(top_urban_orte) > 0:
        fig2, ax = plt.subplots(figsize=(12, 10))

        # Übersetze Stadt-Namen ins Deutsche
        stadte = [GROSSSTAEDTE_MAPPING.get(stadt, stadt) for stadt, _ in top_urban_orte[:20]]
        counts = [count for _, count in top_urban_orte[:20]]

        ax.barh(stadte[::-1], counts[::-1], color='#e74c3c', alpha=0.8, edgecolor='black')
        ax.set_xlabel('Anzahl Tweets', fontsize=11)
        ax.set_title('Top 20 Städte nach Tweet-Anzahl', fontsize=13, fontweight='bold')
        ax.grid(axis='x', alpha=0.3)

        plt.tight_layout()

        top_cities_file = os.path.join(output_dir, f"top_20_staedte_{timestamp}.png")
        plt.savefig(top_cities_file, dpi=300, bbox_inches='tight')
        print(f"✓ Top 20 Städte gespeichert: {top_cities_file}")

        plt.close()


def main():
    # PASSE DIESE PFADE AN!
    input_file = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\Cleaned_Data.jsonl"
    output_dir = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\Urban_Rural"

    tweets = load_tweets(input_file)
    df = create_urban_rural_analysis(tweets, output_dir)

    print("\n" + "=" * 60)
    print("ANALYSE ABGESCHLOSSEN!")
    print("=" * 60)
    print(f"\nTXT-Report und Visualisierungen wurden erstellt.")
    print(f"Speicherort: {output_dir}\n")


if __name__ == "__main__":
    main()
