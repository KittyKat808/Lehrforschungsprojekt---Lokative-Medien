import json
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as path_effects
from collections import Counter, defaultdict
import os
from datetime import datetime

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

# Ost-Bundesländer
OST_BUNDESLAENDER = {
    'Berlin', 'Brandenburg', 'Mecklenburg-Vorpommern',
    'Sachsen', 'Sachsen-Anhalt', 'Thüringen'
}

# Alle Bundesländer
ALLE_BUNDESLAENDER = [
    'Baden-Württemberg', 'Bayern', 'Berlin', 'Brandenburg', 'Bremen',
    'Hamburg', 'Hessen', 'Mecklenburg-Vorpommern', 'Niedersachsen',
    'Nordrhein-Westfalen', 'Rheinland-Pfalz', 'Saarland', 'Sachsen',
    'Sachsen-Anhalt', 'Schleswig-Holstein', 'Thüringen'
]

# Mapping von Natural Earth Namen zu deutschen Namen
NATURAL_EARTH_MAPPING = {
    'Baden-Württemberg': 'Baden-Württemberg',
    'Bayern': 'Bayern',
    'Berlin': 'Berlin',
    'Brandenburg': 'Brandenburg',
    'Bremen': 'Bremen',
    'Hamburg': 'Hamburg',
    'Hessen': 'Hessen',
    'Mecklenburg-Vorpommern': 'Mecklenburg-Vorpommern',
    'Niedersachsen': 'Niedersachsen',
    'Nordrhein-Westfalen': 'Nordrhein-Westfalen',
    'Rheinland-Pfalz': 'Rheinland-Pfalz',
    'Saarland': 'Saarland',
    'Sachsen': 'Sachsen',
    'Sachsen-Anhalt': 'Sachsen-Anhalt',
    'Schleswig-Holstein': 'Schleswig-Holstein',
    'Thüringen': 'Thüringen'
}


def normalize_hashtag(hashtag):
    """
    Normalisiert Hashtags zu Kategorien
    Returns: (normalized_tag, category) oder (None, None) wenn nicht relevant
    """
    tag_lower = hashtag.lower().replace('_', '').replace('-', '').replace(' ', '').replace('ー', '')

    # Ausschlussliste - diese Hashtags werden NICHT kategorisiert
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


def load_natural_earth_shapefile(shapefile_path):
    """Lädt Natural Earth Shapefile und filtert deutsche Bundesländer"""
    print("Lade Natural Earth Shapefile...")

    # Lade den kompletten Datensatz
    gdf = gpd.read_file(shapefile_path)

    # Filtere nur deutsche Bundesländer
    gdf_germany = gdf[gdf['admin'] == 'Germany'].copy()

    # Verwende 'name' Spalte für Bundesland-Namen
    gdf_germany['bundesland'] = gdf_germany['name']

    # Mappe zu standardisierten deutschen Namen falls nötig
    gdf_germany['name'] = gdf_germany['bundesland'].map(NATURAL_EARTH_MAPPING)

    # Entferne Zeilen ohne Mapping
    gdf_germany = gdf_germany[gdf_germany['name'].notna()]

    print(f"✓ {len(gdf_germany)} deutsche Bundesländer geladen")

    return gdf_germany


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
    """Extrahiert und übersetzt Bundesland aus geo_source (place oder coordinates)"""
    geo_source = tweet.get('geo_source')

    if not geo_source:
        return None

    bundesland_en = None
    if geo_source == 'coordinates' and tweet.get('geo'):
        bundesland_en = tweet['geo'].get('state')
    elif geo_source == 'place' and tweet.get('place'):
        bundesland_en = tweet['place'].get('state')

    return STATE_MAPPING.get(bundesland_en) if bundesland_en else None


def analyze_spatial_hashtags(tweets, output_dir, shapefile_path):
    """Analysiert räumliche Verteilung der Hashtag-Kategorien"""

    print("Analysiere räumliche Verteilung der Hashtag-Kategorien...")

    # Datenstruktur: {bundesland: {hashtag_category: count}}
    bundesland_hashtags = defaultdict(lambda: defaultdict(int))

    tweets_processed = 0

    for tweet in tweets:
        bundesland = extract_bundesland(tweet)
        if not bundesland:
            continue

        hashtags = tweet.get('entities', {}).get('hashtags', [])

        for hashtag in hashtags:
            normalized, category = normalize_hashtag(hashtag)
            if normalized:
                bundesland_hashtags[bundesland][normalized] += 1
                tweets_processed += 1

    print(f"✓ {tweets_processed:,} relevante Hashtags mit Geo-Info gefunden\n")

    # DataFrame erstellen
    data = []
    for bundesland in ALLE_BUNDESLAENDER:
        if bundesland not in bundesland_hashtags:
            # Bundesland ohne Daten
            data.append({
                'name': bundesland,
                'Top_Hashtag': 'Keine Daten',
                'Top_Hashtag_Count': 0,
                'FlattenTheCurve': 0,
                'WirBleibenZuhause': 0,
                'SocialDistancing': 0,
                'Lockdown': 0,
                'Coronakrise': 0,
                'Gesamt': 0,
                'Ost_West': 'Ost' if bundesland in OST_BUNDESLAENDER else 'West'
            })
        else:
            counts = bundesland_hashtags[bundesland]

            # Top-Hashtag finden
            if counts:
                top_hashtag = max(counts.items(), key=lambda x: x[1])
                top_name = top_hashtag[0]
                top_count = top_hashtag[1]
            else:
                top_name = 'Keine Daten'
                top_count = 0

            data.append({
                'name': bundesland,
                'Top_Hashtag': top_name,
                'Top_Hashtag_Count': top_count,
                'FlattenTheCurve': counts.get('FlattenTheCurve', 0),
                'WirBleibenZuhause': counts.get('WirBleibenZuhause', 0),
                'SocialDistancing': counts.get('SocialDistancing', 0),
                'Lockdown': counts.get('Lockdown', 0),
                'Coronakrise': counts.get('Coronakrise', 0),
                'Gesamt': sum(counts.values()),
                'Ost_West': 'Ost' if bundesland in OST_BUNDESLAENDER else 'West'
            })

    df = pd.DataFrame(data)

    # Natural Earth Shapefile laden und mit Daten mergen
    gdf = load_natural_earth_shapefile(shapefile_path)
    gdf = gdf.merge(df, on='name', how='left')

    # Output-Verzeichnis erstellen
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Farben für Hashtag-Kategorien (wie in den anderen Plots)
    colors = {
        'FlattenTheCurve': '#e74c3c',
        'WirBleibenZuhause': '#3498db',
        'SocialDistancing': '#2ecc71',
        'Lockdown': '#f39c12',
        'Coronakrise': '#9b59b6',
        'Keine Daten': '#95a5a6'
    }

    # --- TXT-REPORT ---
    txt_file = os.path.join(output_dir, f"hashtag_raeumlich_{timestamp}.txt")
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write("RÄUMLICHE VERTEILUNG DER HASHTAG-KATEGORIEN\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Analysezeitpunkt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Analysierte Tweets: {len(tweets):,}\n")
        f.write(f"Relevante Hashtags: {tweets_processed:,}\n\n")

        f.write("=" * 80 + "\n")
        f.write("TOP-HASHTAG PRO BUNDESLAND\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"{'Bundesland':<25} {'Top-Hashtag':<25} {'Anzahl':<12} {'Gesamt':<12}\n")
        f.write("-" * 80 + "\n")

        for _, row in df.sort_values('name').iterrows():
            f.write(
                f"{row['name']:<25} #{row['Top_Hashtag']:<24} {row['Top_Hashtag_Count']:<12,} {row['Gesamt']:<12,}\n")

        f.write("\n\n" + "=" * 80 + "\n")
        f.write("DETAILLIERTE VERTEILUNG PRO BUNDESLAND\n")
        f.write("=" * 80 + "\n\n")

        for _, row in df.sort_values('Gesamt', ascending=False).iterrows():
            if row['Gesamt'] == 0:
                continue

            f.write(f"\n{row['name'].upper()}\n")
            f.write("-" * 80 + "\n")
            f.write(f"Gesamt relevante Hashtags: {row['Gesamt']:,}\n\n")

            # Prozentuale Verteilung
            total = row['Gesamt']
            f.write(
                f"  #FlattenTheCurve:      {row['FlattenTheCurve']:>6,} ({row['FlattenTheCurve'] / total * 100:>5.1f}%)\n")
            f.write(
                f"  #WirBleibenZuhause:    {row['WirBleibenZuhause']:>6,} ({row['WirBleibenZuhause'] / total * 100:>5.1f}%)\n")
            f.write(
                f"  #SocialDistancing:     {row['SocialDistancing']:>6,} ({row['SocialDistancing'] / total * 100:>5.1f}%)\n")
            f.write(f"  #Lockdown:             {row['Lockdown']:>6,} ({row['Lockdown'] / total * 100:>5.1f}%)\n")
            f.write(f"  #Coronakrise:          {row['Coronakrise']:>6,} ({row['Coronakrise'] / total * 100:>5.1f}%)\n")

        f.write("\n\n" + "=" * 80 + "\n")
        f.write("OST-WEST-VERGLEICH\n")
        f.write("=" * 80 + "\n\n")

        ost_df = df[df['Ost_West'] == 'Ost']
        west_df = df[df['Ost_West'] == 'West']

        ost_totals = {
            'FlattenTheCurve': ost_df['FlattenTheCurve'].sum(),
            'WirBleibenZuhause': ost_df['WirBleibenZuhause'].sum(),
            'SocialDistancing': ost_df['SocialDistancing'].sum(),
            'Lockdown': ost_df['Lockdown'].sum(),
            'Coronakrise': ost_df['Coronakrise'].sum()
        }

        west_totals = {
            'FlattenTheCurve': west_df['FlattenTheCurve'].sum(),
            'WirBleibenZuhause': west_df['WirBleibenZuhause'].sum(),
            'SocialDistancing': west_df['SocialDistancing'].sum(),
            'Lockdown': west_df['Lockdown'].sum(),
            'Coronakrise': west_df['Coronakrise'].sum()
        }

        ost_sum = sum(ost_totals.values())
        west_sum = sum(west_totals.values())

        f.write(f"{'Hashtag':<25} {'Ost':<15} {'West':<15} {'Ost %':<10} {'West %':<10}\n")
        f.write("-" * 80 + "\n")

        for hashtag in ['FlattenTheCurve', 'WirBleibenZuhause', 'SocialDistancing', 'Lockdown', 'Coronakrise']:
            ost_count = ost_totals[hashtag]
            west_count = west_totals[hashtag]
            ost_pct = (ost_count / ost_sum * 100) if ost_sum > 0 else 0
            west_pct = (west_count / west_sum * 100) if west_sum > 0 else 0

            f.write(f"#{hashtag:<24} {ost_count:<15,} {west_count:<15,} {ost_pct:>6.1f}%    {west_pct:>6.1f}%\n")

        f.write("-" * 80 + "\n")
        f.write(f"{'GESAMT':<25} {ost_sum:<15,} {west_sum:<15,}\n")

        # Dominant Hashtag pro Region
        f.write("\n\nDominante Hashtags:\n")
        if ost_sum > 0:
            ost_dominant = max(ost_totals.items(), key=lambda x: x[1])
            f.write(f"  Ost: #{ost_dominant[0]} ({ost_dominant[1] / ost_sum * 100:.1f}%)\n")
        if west_sum > 0:
            west_dominant = max(west_totals.items(), key=lambda x: x[1])
            f.write(f"  West: #{west_dominant[0]} ({west_dominant[1] / west_sum * 100:.1f}%)\n")

        f.write("\n\n" + "=" * 80 + "\n")
        f.write("INTERPRETATION\n")
        f.write("=" * 80 + "\n\n")

        # Welche Hashtags dominieren wo?
        hashtag_counts = df['Top_Hashtag'].value_counts()
        f.write("Regionale Dominanz:\n")
        for hashtag, count in hashtag_counts.items():
            if hashtag != 'Keine Daten':
                f.write(f"  #{hashtag} ist Top-Hashtag in {count} Bundesländern\n")

    print(f"✓ TXT-Report: {txt_file}")

    # --- VISUALISIERUNG 1: Hauptkarte mit Top-Hashtag ---
    fig, ax = plt.subplots(1, 1, figsize=(14, 12))

    # Karte plotten
    gdf['color'] = gdf['Top_Hashtag'].map(colors)
    gdf.plot(ax=ax, color=gdf['color'], edgecolor='black', linewidth=0.8)

    # Bundesland-Namen hinzufügen mit speziellen Offsets
    for idx, row in gdf.iterrows():
        centroid = row.geometry.centroid

        # Brandenburg nach oben verschieben
        if row['name'] == 'Brandenburg':
            y_offset = 0.3
        else:
            y_offset = 0

        ax.text(centroid.x, centroid.y + y_offset, row['name'],
                fontsize=8, ha='center', va='center',
                weight='bold', color='white',
                path_effects=[path_effects.withStroke(linewidth=3, foreground='black')])

    # Legende erstellen
    legend_elements = [mpatches.Patch(facecolor=color, label=f'#{hashtag}', edgecolor='black')
                       for hashtag, color in colors.items() if hashtag != 'Keine Daten']
    ax.legend(handles=legend_elements, loc='lower left', fontsize=11, frameon=True, fancybox=True, shadow=True)

    ax.set_title('Dominanter Hashtag pro Bundesland', fontsize=18, weight='bold', pad=20)
    ax.axis('off')

    plt.tight_layout()
    png_file1 = os.path.join(output_dir, f"hashtag_map_dominant_{timestamp}.png")
    plt.savefig(png_file1, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"✓ Karte (dominanter Hashtag): {png_file1}")

    # --- VISUALISIERUNG 2: Einzelne Karten pro Hashtag (OHNE Zahlen) ---
    for hashtag in ['FlattenTheCurve', 'WirBleibenZuhause', 'SocialDistancing', 'Lockdown', 'Coronakrise']:
        fig, ax = plt.subplots(1, 1, figsize=(14, 12))

        # Normalisieren für bessere Farbskala
        vmin = 0
        vmax = gdf[hashtag].max()

        gdf.plot(column=hashtag, ax=ax, cmap='Reds', edgecolor='black', linewidth=0.8,
                 legend=True, vmin=vmin, vmax=vmax,
                 legend_kwds={'label': f"Anzahl #{hashtag}", 'orientation': 'horizontal', 'shrink': 0.5, 'pad': 0.05})

        # Nur Bundesland-Namen hinzufügen (OHNE Zahlen)
        for idx, row in gdf.iterrows():
            centroid = row.geometry.centroid

            # Brandenburg nach oben verschieben
            if row['name'] == 'Brandenburg':
                y_offset = 0.3
            else:
                y_offset = 0

            # Nur Name, keine Zahlen
            ax.text(centroid.x, centroid.y + y_offset, row['name'],
                    fontsize=8, ha='center', va='center', weight='bold',
                    color='white',
                    path_effects=[path_effects.withStroke(linewidth=2.5, foreground='black')])

        ax.set_title(f'Verbreitung von #{hashtag} nach Bundesländern', fontsize=18, weight='bold', pad=20)
        ax.axis('off')

        plt.tight_layout()
        png_file = os.path.join(output_dir, f"hashtag_map_{hashtag.lower()}_{timestamp}.png")
        plt.savefig(png_file, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        print(f"✓ Karte (#{hashtag}): {png_file}")

    print(f"\n{'=' * 60}")
    print("RÄUMLICHE HASHTAG-ANALYSE ABGESCHLOSSEN!")
    print(f"{'=' * 60}\n")
    print(f"Erstellt: 1 TXT-Report, 6 PNG-Karten (1 Hauptkarte + 5 Einzelkarten)")


def main():
    input_file = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\Cleaned_Data.jsonl"
    output_dir = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\Hashtags"
    shapefile_path = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\ne_10m_admin_1_states_provinces\ne_10m_admin_1_states_provinces.shp"

    tweets = load_tweets(input_file)
    analyze_spatial_hashtags(tweets, output_dir, shapefile_path)


if __name__ == "__main__":
    main()