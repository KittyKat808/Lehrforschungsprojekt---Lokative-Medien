import json
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from collections import defaultdict
import os
from datetime import datetime
from gensim import corpora
from gensim.models import LdaModel

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

# Liste aller Bundesländer
BUNDESLAENDER = [
    'Baden-Württemberg', 'Bayern', 'Berlin', 'Brandenburg', 'Bremen',
    'Hamburg', 'Hessen', 'Mecklenburg-Vorpommern', 'Niedersachsen',
    'Nordrhein-Westfalen', 'Rheinland-Pfalz', 'Saarland', 'Sachsen',
    'Sachsen-Anhalt', 'Schleswig-Holstein', 'Thüringen'
]

# Pfad zum Shapefile
SHAPEFILE_PATH = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\ne_10m_admin_1_states_provinces\ne_10m_admin_1_states_provinces.shp"


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


def main():
    # Pfade
    model_dir = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\LDA\final_14_topics"
    input_file = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\Cleaned_Data.jsonl"
    stopwords_file = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\corona_stopwords.txt"
    spacy_stopwords_file = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\spacy_stopwords_deutsch.txt"
    output_dir = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\LDA\raeumliche_analyse"

    os.makedirs(output_dir, exist_ok=True)

    print("=" * 70)
    print("RÄUMLICHE TOPIC-ANALYSE: ANTEIL AM BUNDESLAND")
    print("=" * 70)

    # Die 6 ausgewählten Topics
    SELECTED_TOPICS = {
        0: "Gesellschaftspolitische Reflexion",
        2: "Soziale Distanzierung",
        5: "Maskenpflicht",
        6: "Wirtschaftliche Lage & Finanzielle Unterstützung",
        9: "Hashtag-Kampagnen & Solidarität",
        11: "Regionales Infektionsgeschehen"
    }

    TOPIC_DISPLAY = {0: 1, 2: 3, 5: 6, 6: 7, 9: 10, 11: 12}

    # 1. Modell laden
    print("\n[1/5] Lade Modell...")
    model_file = os.path.join(model_dir, "lda_model_14_topics_20251124_235500")
    lda_model = LdaModel.load(model_file)
    print("✓ Modell geladen")

    # 2. Tweets laden
    print("\n[2/5] Lade Tweets...")
    tweets = []
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            tweets.append(json.loads(line))
    print(f"✓ {len(tweets):,} Tweets geladen")

    # 3. Preprocessing
    print("\n[3/5] Preprocessing...")
    with open(stopwords_file, 'r', encoding='utf-8') as f:
        corona_stopwords = set([line.strip().lower() for line in f if line.strip()])

    with open(spacy_stopwords_file, 'r', encoding='utf-8') as f:
        spacy_stopwords = set([
            line.strip().lower() for line in f
            if line.strip() and not line.startswith('#')
        ])

    all_stopwords = corona_stopwords | spacy_stopwords

    documents = []
    valid_tweets = []

    for tweet in tweets:
        filtered_tokens = [
            token for token in tweet['tokens']
            if token.lower() not in all_stopwords
               and len(token) > 2
               and not token.isnumeric()
        ]
        if len(filtered_tokens) > 0:
            documents.append(filtered_tokens)
            valid_tweets.append(tweet)

    print(f"✓ {len(valid_tweets):,} verwendbare Tweets")

    dictionary = corpora.Dictionary(documents)
    dictionary.filter_extremes(no_below=5, no_above=0.5, keep_n=10000)
    corpus = [dictionary.doc2bow(doc) for doc in documents]

    # 4. Topic-Zuordnung
    print("\n[4/5] Weise Topics zu und aggregiere...")

    # Zähle Tweets pro Bundesland und Topic
    bundesland_topic_counts = defaultdict(lambda: defaultdict(int))
    bundesland_total_counts = defaultdict(int)

    tweets_with_geo = 0

    for idx, doc_bow in enumerate(corpus):
        if idx % 10000 == 0 and idx > 0:
            print(f"  Verarbeitet: {idx:,} Tweets...")

        # Bundesland extrahieren
        bundesland = extract_bundesland(valid_tweets[idx])
        if not bundesland:
            continue

        tweets_with_geo += 1

        # Dominantes Topic finden
        topic_dist = lda_model.get_document_topics(doc_bow, minimum_probability=0.0)
        if not topic_dist:
            continue

        dominant_topic, prob = max(topic_dist, key=lambda x: x[1])

        # Zähle alle Tweets pro Bundesland
        bundesland_total_counts[bundesland] += 1

        # Zähle nur ausgewählte Topics
        if dominant_topic in SELECTED_TOPICS:
            bundesland_topic_counts[bundesland][dominant_topic] += 1

    print(f"\n✓ Tweets mit Geo-Info: {tweets_with_geo:,}")

    # 5. Berechne Anteile
    print("\n[5/5] Berechne Anteile und erstelle Visualisierungen...")

    # Erstelle DataFrame für jedes Topic
    topic_dataframes = {}

    for topic_id in SELECTED_TOPICS.keys():
        data = []
        for bundesland in BUNDESLAENDER:
            topic_count = bundesland_topic_counts[bundesland][topic_id]
            total_count = bundesland_total_counts[bundesland]

            if total_count > 0:
                anteil_prozent = (topic_count / total_count) * 100
            else:
                anteil_prozent = 0.0

            data.append({
                'Bundesland': bundesland,
                'Topic_Tweets': topic_count,
                'Gesamt_Tweets': total_count,
                'Anteil_Prozent': anteil_prozent
            })

        topic_dataframes[topic_id] = pd.DataFrame(data)

    # Shapefile laden
    germany_gdf = gpd.read_file(SHAPEFILE_PATH)
    germany_gdf = germany_gdf[germany_gdf['admin'] == 'Germany'].copy()
    germany_gdf['Bundesland'] = germany_gdf['name']

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # TXT-Report
    create_txt_report(topic_dataframes, SELECTED_TOPICS, TOPIC_DISPLAY,
                      tweets_with_geo, output_dir, timestamp)

    # Karten
    create_maps(germany_gdf, topic_dataframes, SELECTED_TOPICS, TOPIC_DISPLAY,
                output_dir, timestamp)

    print("\n" + "=" * 70)
    print("ANALYSE ABGESCHLOSSEN")
    print("=" * 70)
    print(f"\nDateien in: {output_dir}")


def create_txt_report(topic_dataframes, SELECTED_TOPICS, TOPIC_DISPLAY,
                      tweets_with_geo, output_dir, timestamp):
    """Erstellt TXT-Report"""

    txt_file = os.path.join(output_dir, f'raeumliche_topic_verteilung_{timestamp}.txt')

    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("RÄUMLICHE TOPIC-VERTEILUNG: ANTEIL AM BUNDESLAND\n")
        f.write(f"Erstellt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")

        f.write(f"Tweets mit Geo-Information: {tweets_with_geo:,}\n\n")

        f.write("Metrik: Anteil der Tweets aus dem Bundesland, die dem jeweiligen Topic\n")
        f.write("        zugeordnet wurden (in Prozent).\n\n")

        for topic_id in sorted(SELECTED_TOPICS.keys()):
            df = topic_dataframes[topic_id]
            topic_label = SELECTED_TOPICS[topic_id]
            display_id = TOPIC_DISPLAY[topic_id]

            df_sorted = df.sort_values('Anteil_Prozent', ascending=False)

            f.write("=" * 80 + "\n")
            f.write(f"TOPIC {display_id}: {topic_label}\n")
            f.write("=" * 80 + "\n\n")

            f.write(f"{'Rang':<6} {'Bundesland':<25} {'Anteil (%)':<12} {'Tweets':<10} {'Gesamt':<10}\n")
            f.write("-" * 80 + "\n")

            for rank, (_, row) in enumerate(df_sorted.iterrows(), 1):
                if row['Gesamt_Tweets'] > 0:  # Nur Bundesländer mit Tweets
                    f.write(f"{rank:<6} {row['Bundesland']:<25} {row['Anteil_Prozent']:>10.2f}% "
                            f"{row['Topic_Tweets']:>8,} {row['Gesamt_Tweets']:>8,}\n")

            avg_anteil = df[df['Gesamt_Tweets'] > 0]['Anteil_Prozent'].mean()
            f.write(f"\nBundesweiter Durchschnitt: {avg_anteil:.2f}%\n\n")

    print(f"✓ TXT-Report: {txt_file}")


def create_maps(germany_gdf, topic_dataframes, SELECTED_TOPICS, TOPIC_DISPLAY,
                output_dir, timestamp):
    """Erstellt 6 Deutschlandkarten"""

    fig = plt.figure(figsize=(16, 20))

    for idx, (topic_id, topic_label) in enumerate(sorted(SELECTED_TOPICS.items())):
        display_id = TOPIC_DISPLAY[topic_id]
        df = topic_dataframes[topic_id]

        gdf_topic = germany_gdf.merge(df, on='Bundesland', how='left')

        ax = plt.subplot(3, 2, idx + 1)

        gdf_topic.plot(
            column='Anteil_Prozent',
            cmap='YlOrRd',
            linewidth=0.8,
            ax=ax,
            edgecolor='black',
            legend=True,
            legend_kwds={'label': 'Anteil (%)', 'shrink': 0.7},
            vmin=0,
            vmax=gdf_topic['Anteil_Prozent'].max()
        )

        ax.set_title(f'Topic {display_id}: {topic_label}',
                     fontsize=11, fontweight='bold', pad=10)
        ax.axis('off')

        # Labels
        for _, row in gdf_topic.iterrows():
            if pd.notna(row['Anteil_Prozent']) and row['Anteil_Prozent'] > 0:
                centroid = row['geometry'].centroid

                if row['Bundesland'] == 'Berlin':
                    label_x = centroid.x
                    label_y = centroid.y + 0.3
                    ax.plot([centroid.x, label_x], [centroid.y, label_y],
                            color='black', linewidth=0.5, linestyle='-', zorder=5)
                    ax.annotate(f"{row['Anteil_Prozent']:.1f}%",
                                xy=(label_x, label_y), ha='center',
                                fontsize=6, color='black', weight='bold')
                elif row['Bundesland'] == 'Brandenburg':
                    ax.annotate(f"{row['Anteil_Prozent']:.1f}%",
                                xy=(centroid.x, centroid.y - 0.4), ha='center',
                                fontsize=6, color='black', weight='bold')
                else:
                    ax.annotate(f"{row['Anteil_Prozent']:.1f}%",
                                xy=(centroid.x, centroid.y), ha='center',
                                fontsize=6, color='black', weight='bold')

    plt.suptitle('Räumliche Topic-Verteilung: Anteil am Bundesland-Diskurs (%)',
                 fontsize=14, fontweight='bold', y=0.995)
    plt.tight_layout(rect=[0, 0, 1, 0.99])

    map_file = os.path.join(output_dir, f'topic_karten_anteil_{timestamp}.png')
    plt.savefig(map_file, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✓ Karten: {map_file}")

    plt.close()


if __name__ == '__main__':

    main()
