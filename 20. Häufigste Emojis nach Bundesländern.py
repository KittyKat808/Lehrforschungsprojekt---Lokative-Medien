import json
import pandas as pd
import plotly.graph_objects as go
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

# Emoji-Modifier, die gefiltert werden sollen
EMOJI_MODIFIERS = {
    '🏻', '🏼', '🏽', '🏾', '🏿',
    '♂', '♀', '⚧',
    '️', '\ufe0f'
}

# Koordinaten für Bundesländer (ungefähre Zentren)
BUNDESLAND_COORDS = {
    'Baden-Württemberg': (48.6616, 9.3501),
    'Bayern': (48.7904, 11.4979),
    'Berlin': (52.5200, 13.4050),
    'Brandenburg': (52.4125, 12.5316),
    'Bremen': (53.0793, 8.8017),
    'Hamburg': (53.5511, 9.9937),
    'Hessen': (50.6521, 9.1624),
    'Mecklenburg-Vorpommern': (53.6127, 12.4296),
    'Niedersachsen': (52.6367, 9.8451),
    'Nordrhein-Westfalen': (51.4332, 7.6616),
    'Rheinland-Pfalz': (50.1183, 7.3089),
    'Saarland': (49.3964, 7.0229),
    'Sachsen': (51.1045, 13.2017),
    'Sachsen-Anhalt': (51.9503, 11.6923),
    'Schleswig-Holstein': (54.2194, 9.6961),
    'Thüringen': (51.0110, 10.8453)
}


def filter_emoji_modifiers(emojis):
    """Filtert Emoji-Modifier aus einer Liste von Emojis"""
    return [emoji for emoji in emojis if emoji not in EMOJI_MODIFIERS]


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


def load_geojson_from_shapefile(shapefile_path):
    """Konvertiert Shapefile zu GeoJSON für Plotly"""
    try:
        import geopandas as gpd

        print("Lade Shapefile und konvertiere zu GeoJSON...")
        gdf = gpd.read_file(shapefile_path)

        # Filtere nur deutsche Bundesländer
        gdf_germany = gdf[gdf['admin'] == 'Germany'].copy()

        # Mapping für Namen
        name_mapping = {
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

        gdf_germany['name'] = gdf_germany['name'].map(name_mapping)
        gdf_germany = gdf_germany[gdf_germany['name'].notna()]

        # Zu GeoJSON konvertieren
        geojson = json.loads(gdf_germany.to_json())

        print(f"✓ GeoJSON mit {len(gdf_germany)} Bundesländern erstellt")
        return geojson

    except ImportError:
        print("⚠ Geopandas nicht verfügbar. Karte wird ohne Grenzen erstellt.")
        return None
    except Exception as e:
        print(f"⚠ Fehler beim Laden der Shapefile: {e}")
        return None


def analyze_spatial_emojis(tweets, output_dir, shapefile_path=None):
    """Analysiert räumliche Verteilung der Emojis"""

    print("Analysiere räumliche Verteilung der Emojis...")

    # Datenstruktur: {bundesland: Counter(emojis)}
    bundesland_emojis = defaultdict(Counter)

    emojis_processed = 0
    filtered_modifiers = 0

    for tweet in tweets:
        bundesland = extract_bundesland(tweet)
        if not bundesland:
            continue

        emojis = tweet.get('entities', {}).get('emojis', [])

        if not emojis:
            continue

        # Modifier filtern
        original_count = len(emojis)
        emojis = filter_emoji_modifiers(emojis)
        filtered_modifiers += (original_count - len(emojis))

        if not emojis:
            continue

        for emoji in emojis:
            bundesland_emojis[bundesland][emoji] += 1
            emojis_processed += 1

    print(f"✓ {emojis_processed:,} Emojis mit Geo-Info gefunden")
    print(f"✓ {filtered_modifiers:,} Emoji-Modifier herausgefiltert\n")

    # DataFrame erstellen
    data = []
    for bundesland in ALLE_BUNDESLAENDER:
        if bundesland not in bundesland_emojis or len(bundesland_emojis[bundesland]) == 0:
            data.append({
                'name': bundesland,
                'Top_Emoji': '—',
                'Top_Emoji_Count': 0,
                'Gesamt': 0,
                'Unique_Emojis': 0,
                'Ost_West': 'Ost' if bundesland in OST_BUNDESLAENDER else 'West',
                'lat': BUNDESLAND_COORDS[bundesland][0],
                'lon': BUNDESLAND_COORDS[bundesland][1]
            })
        else:
            emoji_counter = bundesland_emojis[bundesland]
            top_emoji = emoji_counter.most_common(1)[0]

            data.append({
                'name': bundesland,
                'Top_Emoji': top_emoji[0],
                'Top_Emoji_Count': top_emoji[1],
                'Gesamt': sum(emoji_counter.values()),
                'Unique_Emojis': len(emoji_counter),
                'Ost_West': 'Ost' if bundesland in OST_BUNDESLAENDER else 'West',
                'lat': BUNDESLAND_COORDS[bundesland][0],
                'lon': BUNDESLAND_COORDS[bundesland][1]
            })

    df = pd.DataFrame(data)

    # Output-Verzeichnis erstellen
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # --- TXT-REPORT (wie vorher) ---
    txt_file = os.path.join(output_dir, f"emoji_raeumlich_{timestamp}.txt")
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write("RÄUMLICHE VERTEILUNG DER EMOJIS\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Analysezeitpunkt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Analysierte Tweets: {len(tweets):,}\n")
        f.write(f"Verarbeitete Emojis: {emojis_processed:,}\n")
        f.write(f"Gefilterte Modifier: {filtered_modifiers:,}\n\n")

        f.write("=" * 80 + "\n")
        f.write("TOP-EMOJI PRO BUNDESLAND\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"{'Bundesland':<25} {'Top-Emoji':<12} {'Anzahl':<12} {'Gesamt':<12} {'Unique':<10}\n")
        f.write("-" * 80 + "\n")

        for _, row in df.sort_values('name').iterrows():
            f.write(
                f"{row['name']:<25} {row['Top_Emoji']:<12} {row['Top_Emoji_Count']:<12,} "
                f"{row['Gesamt']:<12,} {row['Unique_Emojis']:<10}\n"
            )

        f.write("\n\n" + "=" * 80 + "\n")
        f.write("TOP 10 EMOJIS PRO BUNDESLAND\n")
        f.write("=" * 80 + "\n\n")

        for bundesland in sorted(ALLE_BUNDESLAENDER):
            if bundesland not in bundesland_emojis or len(bundesland_emojis[bundesland]) == 0:
                f.write(f"\n{bundesland.upper()}\n")
                f.write("-" * 80 + "\n")
                f.write("Keine Daten verfügbar\n")
                continue

            emoji_counter = bundesland_emojis[bundesland]
            total = sum(emoji_counter.values())

            f.write(f"\n{bundesland.upper()}\n")
            f.write("-" * 80 + "\n")
            f.write(f"Gesamt Emojis: {total:,}\n")
            f.write(f"Unique Emojis: {len(emoji_counter):,}\n\n")
            f.write(f"{'Rang':<6} {'Emoji':<10} {'Anzahl':<12} {'Anteil':<10}\n")
            f.write("-" * 80 + "\n")

            for idx, (emoji, count) in enumerate(emoji_counter.most_common(10), 1):
                anteil = (count / total) * 100
                f.write(f"{idx:<6} {emoji:<10} {count:<12,} {anteil:>6.2f}%\n")

        # Ost-West-Vergleich
        f.write("\n\n" + "=" * 80 + "\n")
        f.write("OST-WEST-VERGLEICH\n")
        f.write("=" * 80 + "\n\n")

        ost_df = df[df['Ost_West'] == 'Ost']
        west_df = df[df['Ost_West'] == 'West']

        ost_sum = ost_df['Gesamt'].sum()
        west_sum = west_df['Gesamt'].sum()
        ost_unique = ost_df['Unique_Emojis'].sum()
        west_unique = west_df['Unique_Emojis'].sum()

        f.write(f"{'Metrik':<30} {'Ost':<20} {'West':<20}\n")
        f.write("-" * 80 + "\n")
        f.write(f"{'Gesamt Emojis:':<30} {ost_sum:<20,} {west_sum:<20,}\n")
        f.write(f"{'Unique Emojis:':<30} {ost_unique:<20,} {west_unique:<20,}\n")
        f.write(
            f"{'Durchschn. pro Bundesland:':<30} {ost_sum / len(ost_df):<20,.1f} {west_sum / len(west_df):<20,.1f}\n")

        # Top-Emojis pro Region
        ost_all_emojis = Counter()
        west_all_emojis = Counter()

        for bundesland in ALLE_BUNDESLAENDER:
            if bundesland in bundesland_emojis:
                if bundesland in OST_BUNDESLAENDER:
                    ost_all_emojis.update(bundesland_emojis[bundesland])
                else:
                    west_all_emojis.update(bundesland_emojis[bundesland])

        f.write("\n\nTop 10 Emojis Ost-Deutschland:\n")
        f.write("-" * 80 + "\n")
        f.write(f"{'Rang':<6} {'Emoji':<10} {'Anzahl':<12} {'Anteil':<10}\n")
        f.write("-" * 80 + "\n")
        ost_total = sum(ost_all_emojis.values())
        for idx, (emoji, count) in enumerate(ost_all_emojis.most_common(10), 1):
            anteil = (count / ost_total) * 100 if ost_total > 0 else 0
            f.write(f"{idx:<6} {emoji:<10} {count:<12,} {anteil:>6.2f}%\n")

        f.write("\n\nTop 10 Emojis West-Deutschland:\n")
        f.write("-" * 80 + "\n")
        f.write(f"{'Rang':<6} {'Emoji':<10} {'Anzahl':<12} {'Anteil':<10}\n")
        f.write("-" * 80 + "\n")
        west_total = sum(west_all_emojis.values())
        for idx, (emoji, count) in enumerate(west_all_emojis.most_common(10), 1):
            anteil = (count / west_total) * 100 if west_total > 0 else 0
            f.write(f"{idx:<6} {emoji:<10} {count:<12,} {anteil:>6.2f}%\n")

    print(f"✓ TXT-Report: {txt_file}")

    # --- PLOTLY KARTE MIT GRENZEN ---
    # GeoJSON laden (falls Shapefile verfügbar)
    geojson = None
    if shapefile_path:
        geojson = load_geojson_from_shapefile(shapefile_path)

    # Erstelle Hover-Text
    df['hover_text'] = df.apply(
        lambda row: f"<b>{row['name']}</b><br>" +
                    f"Top-Emoji: {row['Top_Emoji']}<br>" +
                    f"Anzahl: {row['Top_Emoji_Count']:,}<br>" +
                    f"Gesamt: {row['Gesamt']:,}<br>" +
                    f"Unique: {row['Unique_Emojis']}",
        axis=1
    )

    # Erstelle die Karte
    fig = go.Figure()

    # Füge Bundesland-Grenzen hinzu (falls GeoJSON verfügbar)
    if geojson:
        # Erstelle ein Choropleth für die Grenzen
        fig.add_trace(go.Choropleth(
            geojson=geojson,
            locations=df['name'],
            z=[0] * len(df),  # Einheitliche Farbe
            featureidkey="properties.name",
            colorscale=[[0, 'lightgray'], [1, 'lightgray']],
            showscale=False,
            marker_line_color='darkgray',
            marker_line_width=2,
            hoverinfo='skip'
        ))

    # Füge Scattergeo für die Emojis hinzu
    fig.add_trace(go.Scattergeo(
        lon=df['lon'],
        lat=df['lat'],
        text=df['Top_Emoji'],
        mode='text',
        textfont=dict(size=40, family='Arial'),
        hovertext=df['hover_text'],
        hoverinfo='text',
        showlegend=False
    ))

    # Layout anpassen
    fig.update_geos(
        scope='europe',
        center=dict(lat=51.5, lon=10.5),
        projection_scale=8,
        visible=False,
        resolution=50
    )

    fig.update_layout(
        title=dict(
            text='Meistverwendetes Emoji pro Bundesland',
            x=0.5,
            xanchor='center',
            font=dict(size=24, family='Arial', color='black')
        ),
        height=800,
        margin=dict(l=0, r=0, t=80, b=0),
        paper_bgcolor='white',
        geo=dict(bgcolor='white')
    )

    # Speichern
    html_file = os.path.join(output_dir, f"emoji_map_{timestamp}.html")
    fig.write_html(html_file)
    print(f"✓ Interaktive Karte: {html_file}")

    # Optional: Als PNG speichern (benötigt kaleido)
    try:
        png_file = os.path.join(output_dir, f"emoji_map_{timestamp}.png")
        fig.write_image(png_file, width=1400, height=1000)
        print(f"✓ PNG-Karte: {png_file}")
    except Exception as e:
        print(f"⚠ PNG konnte nicht erstellt werden (kaleido benötigt): {e}")

    print(f"\n{'=' * 60}")
    print("RÄUMLICHE EMOJI-ANALYSE ABGESCHLOSSEN!")
    print(f"{'=' * 60}\n")


def main():
    input_file = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\Cleaned_Data.jsonl"
    output_dir = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\Emojis"
    shapefile_path = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\ne_10m_admin_1_states_provinces\ne_10m_admin_1_states_provinces.shp"

    tweets = load_tweets(input_file)
    analyze_spatial_emojis(tweets, output_dir, shapefile_path)


if __name__ == "__main__":
    main()