import json
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from collections import Counter
import os
from datetime import datetime

# Matplotlib auf Deutsch
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

# Übersetzung Englisch → Deutsch
STATE_MAPPING = {
    'Berlin': 'Berlin',
    'North Rhine-Westphalia': 'Nordrhein-Westfalen',
    'Bavaria': 'Bayern',
    'Baden-Württemberg': 'Baden-Württemberg',
    'Hamburg': 'Hamburg',
    'Hesse': 'Hessen',
    'Lower Saxony': 'Niedersachsen',
    'Rhineland-Palatinate': 'Rheinland-Pfalz',
    'Saxony': 'Sachsen',
    'Brandenburg': 'Brandenburg',
    'Schleswig-Holstein': 'Schleswig-Holstein',
    'Saxony-Anhalt': 'Sachsen-Anhalt',
    'Free Hanseatic City of Bremen': 'Bremen',
    'Thuringia': 'Thüringen',
    'Mecklenburg-Vorpommern': 'Mecklenburg-Vorpommern',
    'Mecklenburg-Western Pomerania': 'Mecklenburg-Vorpommern',
    'Saarland': 'Saarland'
}

# Einwohnerzahlen Bundesländer, Stand 31.12.2019
# https://www.destatis.de/DE/Presse/Pressemitteilungen/2021/06/PD21_287_12411.html)
EINWOHNER_2020 = {
    'Baden-Württemberg': 11_100_400,
    'Bayern': 13_124_700,
    'Berlin': 3_669_500,
    'Brandenburg': 2_521_900,
    'Bremen': 681_200,
    'Hamburg': 1_847_300,
    'Hessen': 6_288_100,
    'Mecklenburg-Vorpommern': 1_608_100,
    'Niedersachsen': 7_993_600,
    'Nordrhein-Westfalen': 17_947_200,
    'Rheinland-Pfalz': 4_093_900,
    'Saarland': 986_900,
    'Sachsen': 4_072_000,
    'Sachsen-Anhalt': 2_194_800,
    'Schleswig-Holstein': 2_903_800,
    'Thüringen': 2_133_400
}

# Ost-Bundesländer
OST_BUNDESLAENDER = {
    'Berlin', 'Brandenburg', 'Mecklenburg-Vorpommern',
    'Sachsen', 'Sachsen-Anhalt', 'Thüringen'
}

# Ost-Bundesländer OHNE Berlin
OST_OHNE_BERLIN = {
    'Brandenburg', 'Mecklenburg-Vorpommern',
    'Sachsen', 'Sachsen-Anhalt', 'Thüringen'
}

# Pfad zu den Shapefiles
SHAPEFILE_PATH = r"C:\Users\katri\Desktop\LFP Datensätze\ne_10m_admin_1_states_provinces\ne_10m_admin_1_states_provinces.shp"


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


def extract_bundesland(tweet):
    """Extrahiert und übersetzt Bundesland aus geo_source"""
    geo_source = tweet.get('geo_source')

    if not geo_source:
        return None

    bundesland_en = None
    if geo_source == 'place' and tweet.get('place'):
        bundesland_en = tweet['place'].get('state')
    elif geo_source == 'coordinates' and tweet.get('geo'):
        bundesland_en = tweet['geo'].get('state')

    return STATE_MAPPING.get(bundesland_en) if bundesland_en else None


def create_heatmaps(tweets, output_dir):
    """Erstellt Heatmaps und Statistiken"""

    print("Erstelle Analyse...")

    # Shapefile laden
    print("Lade Shapefile...")
    germany_gdf = gpd.read_file(SHAPEFILE_PATH)
    germany_gdf = germany_gdf[germany_gdf['admin'] == 'Germany'].copy()

    # Bundesländer extrahieren
    bundeslaender = [extract_bundesland(tweet) for tweet in tweets]
    bundeslaender = [bl for bl in bundeslaender if bl]

    print(
        f"Tweets mit Geo-Info: {len(bundeslaender)} / {len(tweets)} ({len(bundeslaender) / len(tweets) * 100:.1f}%)\n")

    # Zählen
    bl_counts = Counter(bundeslaender)

    # DataFrame erstellen
    data = []
    for bl in EINWOHNER_2020.keys():
        count = bl_counts.get(bl, 0)
        data.append({
            'Bundesland': bl,
            'Tweets_absolut': count,
            'Tweets_pro_100k': (count / EINWOHNER_2020[bl]) * 100000,
            'Einwohner': EINWOHNER_2020[bl],
            'Ost_West': 'Ost' if bl in OST_BUNDESLAENDER else 'West'
        })

    df = pd.DataFrame(data)

    # Rankings
    df_sorted_abs = df.sort_values('Tweets_absolut', ascending=False).copy()
    df_sorted_abs['Rang_absolut'] = range(1, len(df_sorted_abs) + 1)

    df_sorted_pro = df.sort_values('Tweets_pro_100k', ascending=False).copy()
    df_sorted_pro['Rang_pro_100k'] = range(1, len(df_sorted_pro) + 1)

    df = df_sorted_abs.merge(df_sorted_pro[['Bundesland', 'Rang_pro_100k']], on='Bundesland')

    # Ost-West Statistiken
    ost_tweets = df[df['Ost_West'] == 'Ost']['Tweets_absolut'].sum()
    west_tweets = df[df['Ost_West'] == 'West']['Tweets_absolut'].sum()
    ost_einwohner = sum(EINWOHNER_2020[bl] for bl in OST_BUNDESLAENDER)
    west_einwohner = sum(EINWOHNER_2020[bl] for bl in EINWOHNER_2020.keys() if bl not in OST_BUNDESLAENDER)
    ost_pro_100k = (ost_tweets / ost_einwohner) * 100000
    west_pro_100k = (west_tweets / west_einwohner) * 100000

    # Ost ohne Berlin Statistiken
    ost_ohne_berlin_tweets = df[df['Bundesland'].isin(OST_OHNE_BERLIN)]['Tweets_absolut'].sum()
    berlin_tweets = df[df['Bundesland'] == 'Berlin']['Tweets_absolut'].sum()
    ost_ohne_berlin_einwohner = sum(EINWOHNER_2020[bl] for bl in OST_OHNE_BERLIN)
    berlin_einwohner = EINWOHNER_2020['Berlin']
    ost_ohne_berlin_pro_100k = (ost_ohne_berlin_tweets / ost_ohne_berlin_einwohner) * 100000
    berlin_pro_100k = (berlin_tweets / berlin_einwohner) * 100000

    # Mit Shapefile mergen
    germany_gdf['Bundesland'] = germany_gdf['name']
    germany_gdf = germany_gdf.merge(df, on='Bundesland', how='left')

    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # TXT-Report erstellen
    save_txt_report(df, df_sorted_pro, tweets, bundeslaender,
                    ost_tweets, west_tweets, ost_einwohner, west_einwohner,
                    ost_pro_100k, west_pro_100k,
                    ost_ohne_berlin_tweets, berlin_tweets, ost_ohne_berlin_einwohner,
                    berlin_einwohner, ost_ohne_berlin_pro_100k, berlin_pro_100k,
                    output_dir, timestamp)

    # Visualisierungen erstellen
    create_visualizations(germany_gdf, df, output_dir, timestamp)

    return df


def save_txt_report(df, df_sorted_pro, tweets, bundeslaender,
                    ost_tweets, west_tweets, ost_einwohner, west_einwohner,
                    ost_pro_100k, west_pro_100k,
                    ost_ohne_berlin_tweets, berlin_tweets, ost_ohne_berlin_einwohner,
                    berlin_einwohner, ost_ohne_berlin_pro_100k, berlin_pro_100k,
                    output_dir, timestamp):
    """Speichert TXT-Report"""

    txt_file = os.path.join(output_dir, f"raeumliche_verteilung_{timestamp}.txt")
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write("RÄUMLICHE VERTEILUNG DER CORONA-TWEETS\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Analysezeitpunkt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Gesamtzahl Tweets: {len(tweets):,}\n")
        f.write(f"Tweets mit Geo-Info: {len(bundeslaender):,} ({len(bundeslaender) / len(tweets) * 100:.1f}%)\n\n")

        f.write("=" * 80 + "\n")
        f.write("BUNDESLÄNDER (sortiert nach absoluten Zahlen)\n")
        f.write("=" * 80 + "\n\n")
        f.write(
            f"{'Rang':<6} {'Bundesland':<25} {'Tweets':<12} {'Anteil':<10} {'Einw.':<12} {'Tweets/100k':<12} {'Rang/100k':<10} {'Ost/West':<10}\n")
        f.write("-" * 120 + "\n")
        for _, row in df.iterrows():
            anteil = (row['Tweets_absolut'] / len(bundeslaender)) * 100
            f.write(f"{row['Rang_absolut']:<6} {row['Bundesland']:<25} {row['Tweets_absolut']:<12,} "
                    f"{anteil:>6.2f}% {row['Einwohner']:<12,} "
                    f"{row['Tweets_pro_100k']:<12.2f} {row['Rang_pro_100k']:<10} {row['Ost_West']:<10}\n")

        f.write("\n" + "=" * 80 + "\n")
        f.write("BUNDESLÄNDER (sortiert nach Tweets pro 100.000 Einwohner)\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"{'Rang':<6} {'Bundesland':<25} {'Tweets/100k':<12} {'Tweets abs.':<12} {'Ost/West':<10}\n")
        f.write("-" * 80 + "\n")
        for _, row in df_sorted_pro.iterrows():
            f.write(f"{row['Rang_pro_100k']:<6} {row['Bundesland']:<25} {row['Tweets_pro_100k']:<12.2f} "
                    f"{row['Tweets_absolut']:<12,} {row['Ost_West']:<10}\n")

        f.write("\n" + "=" * 80 + "\n")
        f.write("OST-WEST-VERGLEICH\n")
        f.write("=" * 80 + "\n\n")

        # Tabelle 1: Klassischer Ost-West-Vergleich
        f.write("1. OST (inkl. Berlin) vs. WEST\n")
        f.write("-" * 80 + "\n")
        f.write(f"Ost-Bundesländer: {', '.join(sorted(OST_BUNDESLAENDER))}\n\n")
        f.write(f"{'Kategorie':<20} {'Tweets (absolut)':<18} {'Anteil':<12} {'Einwohner':<15} {'Tweets/100k EW':<15}\n")
        f.write("-" * 80 + "\n")
        f.write(f"{'Ost':<20} {ost_tweets:<18,} {ost_tweets / len(bundeslaender) * 100:>6.2f}% "
                f"{ost_einwohner:<15,} {ost_pro_100k:>12.2f}\n")
        f.write(f"{'West':<20} {west_tweets:<18,} {west_tweets / len(bundeslaender) * 100:>6.2f}% "
                f"{west_einwohner:<15,} {west_pro_100k:>12.2f}\n")
        f.write("-" * 80 + "\n")
        f.write(f"Ost/West-Ratio (absolut): 1:{west_tweets / ost_tweets:.2f}\n")
        f.write(f"Ost/West-Ratio (pro Kopf): 1:{west_pro_100k / ost_pro_100k:.2f}\n")

        # Tabelle 2: Ost ohne Berlin vs. Berlin vs. West
        f.write("\n\n2. OST (ohne Berlin) vs. BERLIN vs. WEST\n")
        f.write("-" * 80 + "\n")
        f.write(f"Ost ohne Berlin: {', '.join(sorted(OST_OHNE_BERLIN))}\n\n")
        f.write(f"{'Kategorie':<20} {'Tweets (absolut)':<18} {'Anteil':<12} {'Einwohner':<15} {'Tweets/100k EW':<15}\n")
        f.write("-" * 80 + "\n")
        f.write(
            f"{'Ost ohne Berlin':<20} {ost_ohne_berlin_tweets:<18,} {ost_ohne_berlin_tweets / len(bundeslaender) * 100:>6.2f}% "
            f"{ost_ohne_berlin_einwohner:<15,} {ost_ohne_berlin_pro_100k:>12.2f}\n")
        f.write(f"{'Berlin':<20} {berlin_tweets:<18,} {berlin_tweets / len(bundeslaender) * 100:>6.2f}% "
                f"{berlin_einwohner:<15,} {berlin_pro_100k:>12.2f}\n")
        f.write(f"{'West':<20} {west_tweets:<18,} {west_tweets / len(bundeslaender) * 100:>6.2f}% "
                f"{west_einwohner:<15,} {west_pro_100k:>12.2f}\n")
        f.write("-" * 80 + "\n")
        f.write(f"Ost o.B./West-Ratio (absolut): 1:{west_tweets / ost_ohne_berlin_tweets:.2f}\n")
        f.write(f"Ost o.B./West-Ratio (pro Kopf): 1:{west_pro_100k / ost_ohne_berlin_pro_100k:.2f}\n")
        f.write(f"Berlin/West-Ratio (pro Kopf): 1:{west_pro_100k / berlin_pro_100k:.2f}\n")
        f.write(f"Berlin/Ost o.B.-Ratio (pro Kopf): {berlin_pro_100k / ost_ohne_berlin_pro_100k:.2f}:1\n")

        # Interpretation
        f.write("\n\n" + "=" * 80 + "\n")
        f.write("INTERPRETATION\n")
        f.write("=" * 80 + "\n\n")

        f.write("BERLIN ALS SONDERFALL:\n")
        f.write(f"Berlin zeigt mit {berlin_pro_100k:.2f} Tweets/100k EW eine deutlich andere\n")
        f.write(f"Aktivität als der Rest Ostdeutschlands ({ost_ohne_berlin_pro_100k:.2f} Tweets/100k EW).\n")

        if berlin_pro_100k > ost_ohne_berlin_pro_100k:
            diff_pct = ((berlin_pro_100k / ost_ohne_berlin_pro_100k) - 1) * 100
            f.write(f"Berlin ist {diff_pct:.1f}% aktiver als Ost ohne Berlin.\n")
        else:
            diff_pct = ((ost_ohne_berlin_pro_100k / berlin_pro_100k) - 1) * 100
            f.write(f"Ost ohne Berlin ist {diff_pct:.1f}% aktiver als Berlin.\n")

        f.write("\nDies unterstreicht Berlins Sonderrolle als Hauptstadt und Metropole,\n")
        f.write("die sich sowohl von Ost- als auch von Westdeutschland unterscheidet.\n")

    print(f"✓ TXT-Report: {txt_file}")


def create_visualizations(germany_gdf, df, output_dir, timestamp):
    """Erstellt 2 Karten + 2 Balkendiagramme"""

    print("\nErstelle Visualisierungen...")

    # Figure mit 2x2 Layout
    fig = plt.figure(figsize=(20, 16))

    # 1. KARTE: Absolute Zahlen
    ax1 = plt.subplot(2, 2, 1)
    germany_gdf.plot(
        column='Tweets_absolut',
        cmap='YlOrRd',
        linewidth=0.8,
        ax=ax1,
        edgecolor='black',
        legend=True,
        legend_kwds={'label': 'Anzahl Tweets', 'shrink': 0.8}
    )
    ax1.set_title('Tweet-Verteilung (Absolute Zahlen)', fontsize=14, fontweight='bold')
    ax1.axis('off')

    for idx, row in germany_gdf.iterrows():
        centroid = row['geometry'].centroid

        if row['Bundesland'] == 'Berlin':
            label_x = centroid.x
            label_y = centroid.y + 0.3
            ax1.plot([centroid.x, label_x], [centroid.y, label_y],
                     color='black', linewidth=1, linestyle='-', zorder=5)
            ax1.annotate(
                text=row['Bundesland'],
                xy=(label_x, label_y),
                ha='center', fontsize=7, color='black', weight='bold'
            )
        elif row['Bundesland'] == 'Brandenburg':
            ax1.annotate(
                text=row['Bundesland'],
                xy=(centroid.x, centroid.y - 0.4),
                ha='center', fontsize=7, color='black', weight='bold'
            )
        else:
            ax1.annotate(
                text=row['Bundesland'],
                xy=(centroid.x, centroid.y),
                ha='center', fontsize=7, color='black', weight='bold'
            )

    # 2. KARTE: Pro 100k Einwohner
    ax2 = plt.subplot(2, 2, 2)
    germany_gdf.plot(
        column='Tweets_pro_100k',
        cmap='YlOrRd',
        linewidth=0.8,
        ax=ax2,
        edgecolor='black',
        legend=True,
        legend_kwds={'label': 'Tweets pro 100k EW', 'shrink': 0.8}
    )
    ax2.set_title('Tweet-Aktivität (Pro 100.000 Einwohner)', fontsize=14, fontweight='bold')
    ax2.axis('off')

    for idx, row in germany_gdf.iterrows():
        centroid = row['geometry'].centroid

        if row['Bundesland'] == 'Berlin':
            label_x = centroid.x
            label_y = centroid.y + 0.3
            ax2.plot([centroid.x, label_x], [centroid.y, label_y],
                     color='black', linewidth=1, linestyle='-', zorder=5)
            ax2.annotate(
                text=row['Bundesland'],
                xy=(label_x, label_y),
                ha='center', fontsize=7, color='black', weight='bold'
            )
        elif row['Bundesland'] == 'Brandenburg':
            ax2.annotate(
                text=row['Bundesland'],
                xy=(centroid.x, centroid.y - 0.4),
                ha='center', fontsize=7, color='black', weight='bold'
            )
        else:
            ax2.annotate(
                text=row['Bundesland'],
                xy=(centroid.x, centroid.y),
                ha='center', fontsize=7, color='black', weight='bold'
            )

    # 3. BALKENDIAGRAMM: Absolute Zahlen
    ax3 = plt.subplot(2, 2, 3)
    df_sorted_abs = df.sort_values('Tweets_absolut', ascending=True)
    colors_abs = ['#e74c3c' if bl in OST_BUNDESLAENDER else '#3498db' for bl in df_sorted_abs['Bundesland']]

    ax3.barh(df_sorted_abs['Bundesland'], df_sorted_abs['Tweets_absolut'], color=colors_abs)
    ax3.set_xlabel('Anzahl Tweets', fontsize=11)
    ax3.set_title('Tweets pro Bundesland (Absolute Zahlen)', fontsize=13, fontweight='bold')
    ax3.grid(axis='x', alpha=0.3)

    legend_elements = [
        Patch(facecolor='#3498db', label='West'),
        Patch(facecolor='#e74c3c', label='Ost')
    ]
    ax3.legend(handles=legend_elements, loc='lower right')

    # 4. BALKENDIAGRAMM: Pro 100k Einwohner
    ax4 = plt.subplot(2, 2, 4)
    df_sorted_pro = df.sort_values('Tweets_pro_100k', ascending=True)
    colors_pro = ['#e74c3c' if bl in OST_BUNDESLAENDER else '#3498db' for bl in df_sorted_pro['Bundesland']]

    ax4.barh(df_sorted_pro['Bundesland'], df_sorted_pro['Tweets_pro_100k'], color=colors_pro)
    ax4.set_xlabel('Tweets pro 100.000 Einwohner', fontsize=11)
    ax4.set_title('Tweets pro Bundesland (Pro 100k Einwohner)', fontsize=13, fontweight='bold')
    ax4.grid(axis='x', alpha=0.3)
    ax4.legend(handles=legend_elements, loc='lower right')

    plt.tight_layout()

    viz_file = os.path.join(output_dir, f"visualisierungen_{timestamp}.png")
    plt.savefig(viz_file, dpi=300, bbox_inches='tight')
    print(f"✓ Visualisierungen gespeichert: {viz_file}")

    plt.close()


def main():
    input_file = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\Cleaned_Data.jsonl"
    output_dir = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\Anzahl und Verteilung"

    tweets = load_tweets(input_file)
    df = create_heatmaps(tweets, output_dir)

    print("\n" + "=" * 60)
    print("ANALYSE ABGESCHLOSSEN!")
    print("=" * 60)
    print(f"\nTXT-Report, 2 Karten und 2 Balkendiagramme wurden erstellt.")
    print(f"Speicherort: {output_dir}\n")


if __name__ == "__main__":
    main()