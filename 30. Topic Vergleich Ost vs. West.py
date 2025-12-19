import json
import pandas as pd
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

# Ost-Bundesländer
OST_BUNDESLAENDER = {
    'Berlin', 'Brandenburg', 'Mecklenburg-Vorpommern',
    'Sachsen', 'Sachsen-Anhalt', 'Thüringen'
}


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
    output_dir = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\LDA\ost_west_analyse"

    os.makedirs(output_dir, exist_ok=True)

    print("=" * 70)
    print("OST-WEST-VERGLEICH: 6 AUSGEWÄHLTE TOPICS")
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

    # Zähle Tweets nach Ost/West und Topic
    ost_topic_counts = defaultdict(int)
    west_topic_counts = defaultdict(int)
    ost_total = 0
    west_total = 0

    tweets_with_geo = 0

    for idx, doc_bow in enumerate(corpus):
        if idx % 10000 == 0 and idx > 0:
            print(f"  Verarbeitet: {idx:,} Tweets...")

        bundesland = extract_bundesland(valid_tweets[idx])
        if not bundesland:
            continue

        tweets_with_geo += 1

        topic_dist = lda_model.get_document_topics(doc_bow, minimum_probability=0.0)
        if not topic_dist:
            continue

        dominant_topic, prob = max(topic_dist, key=lambda x: x[1])

        # Ost oder West?
        is_ost = bundesland in OST_BUNDESLAENDER

        if is_ost:
            ost_total += 1
            if dominant_topic in SELECTED_TOPICS:
                ost_topic_counts[dominant_topic] += 1
        else:
            west_total += 1
            if dominant_topic in SELECTED_TOPICS:
                west_topic_counts[dominant_topic] += 1

    print(f"\n✓ Tweets mit Geo-Info: {tweets_with_geo:,}")
    print(f"   Ost: {ost_total:,} ({ost_total / tweets_with_geo * 100:.1f}%)")
    print(f"   West: {west_total:,} ({west_total / tweets_with_geo * 100:.1f}%)")

    # 5. Berechne Anteile
    print("\n[5/5] Berechne Anteile und erstelle Visualisierungen...")

    results = []
    for topic_id in sorted(SELECTED_TOPICS.keys()):
        topic_label = SELECTED_TOPICS[topic_id]
        display_id = TOPIC_DISPLAY[topic_id]

        ost_count = ost_topic_counts[topic_id]
        west_count = west_topic_counts[topic_id]

        ost_anteil = (ost_count / ost_total * 100) if ost_total > 0 else 0
        west_anteil = (west_count / west_total * 100) if west_total > 0 else 0

        differenz = ost_anteil - west_anteil

        results.append({
            'Topic_ID': topic_id,
            'Topic_Display': display_id,
            'Topic_Label': topic_label,
            'Ost_Tweets': ost_count,
            'West_Tweets': west_count,
            'Ost_Anteil': ost_anteil,
            'West_Anteil': west_anteil,
            'Differenz': differenz
        })

    df_results = pd.DataFrame(results)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # TXT-Report
    create_txt_report(df_results, ost_total, west_total, output_dir, timestamp)

    # Grouped Bar Chart
    create_grouped_bar_chart(df_results, output_dir, timestamp)


def create_txt_report(df_results, ost_total, west_total, output_dir, timestamp):
    """Erstellt TXT-Report"""

    txt_file = os.path.join(output_dir, f'ost_west_vergleich_{timestamp}.txt')

    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("OST-WEST-VERGLEICH: ANTEIL AM DISKURS\n")
        f.write(f"Erstellt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")

        f.write(f"Tweets Ost (gesamt): {ost_total:,}\n")
        f.write(f"Tweets West (gesamt): {west_total:,}\n\n")

        f.write("Metrik: Anteil der Tweets aus Ost/West, die dem jeweiligen Topic\n")
        f.write("        zugeordnet wurden (in Prozent).\n\n")

        f.write("=" * 80 + "\n")
        f.write("VERGLEICH PRO TOPIC\n")
        f.write("=" * 80 + "\n\n")

        f.write(f"{'Topic':<8} {'Label':<45} {'Ost (%)':<10} {'West (%)':<10} {'Diff.':<10}\n")
        f.write("-" * 80 + "\n")

        for _, row in df_results.iterrows():
            f.write(f"{row['Topic_Display']:<8} {row['Topic_Label']:<45} "
                    f"{row['Ost_Anteil']:>8.2f}% {row['West_Anteil']:>8.2f}% "
                    f"{row['Differenz']:>+7.2f}\n")

        f.write("\n\n" + "=" * 80 + "\n")
        f.write("INTERPRETATION\n")
        f.write("=" * 80 + "\n\n")

        # Finde größte Unterschiede
        df_sorted = df_results.sort_values('Differenz', key=abs, ascending=False)

        f.write("Größte Unterschiede:\n\n")

        for idx, (_, row) in enumerate(df_sorted.head(3).iterrows(), 1):
            if row['Differenz'] > 0:
                richtung = "höher im Osten"
            else:
                richtung = "höher im Westen"

            f.write(f"{idx}. Topic {row['Topic_Display']} ({row['Topic_Label']})\n")
            f.write(f"   Differenz: {abs(row['Differenz']):.2f} Prozentpunkte {richtung}\n")
            f.write(f"   Ost: {row['Ost_Anteil']:.2f}%, West: {row['West_Anteil']:.2f}%\n\n")

        # Homogene Topics
        f.write("\nNahezu homogene Topics (Differenz < 1 Prozentpunkt):\n\n")

        homogen = df_results[df_results['Differenz'].abs() < 1.0]
        if len(homogen) > 0:
            for _, row in homogen.iterrows():
                f.write(f"- Topic {row['Topic_Display']} ({row['Topic_Label']}): "
                        f"Ost {row['Ost_Anteil']:.2f}%, West {row['West_Anteil']:.2f}%\n")
        else:
            f.write("Keine homogenen Topics gefunden.\n")

    print(f"✓ TXT-Report: {txt_file}")


def create_grouped_bar_chart(df_results, output_dir, timestamp):
    """Erstellt Grouped Bar Chart"""

    fig, ax = plt.subplots(figsize=(14, 7))

    x = range(len(df_results))
    width = 0.35

    # Balken für Ost
    bars_ost = ax.bar([i - width / 2 for i in x], df_results['Ost_Anteil'],
                      width, label='Ost', color='#e74c3c', alpha=0.8)

    # Balken für West
    bars_west = ax.bar([i + width / 2 for i in x], df_results['West_Anteil'],
                       width, label='West', color='#3498db', alpha=0.8)

    # Achsenbeschriftungen
    ax.set_xlabel('Topic', fontsize=12, fontweight='bold')
    ax.set_ylabel('Anteil am Diskurs (%)', fontsize=12, fontweight='bold')
    ax.set_title('Ost-West-Vergleich: Anteil der Topics am jeweiligen Diskurs',
                 fontsize=14, fontweight='bold', pad=20)

    # X-Achse Labels
    ax.set_xticks(x)
    ax.set_xticklabels([f"Topic {row['Topic_Display']}" for _, row in df_results.iterrows()],
                       rotation=0)

    # Legende
    ax.legend(loc='upper right', fontsize=11)

    # Grid
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)

    # Werte auf Balken anzeigen
    for bars in [bars_ost, bars_west]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2., height,
                    f'{height:.1f}%',
                    ha='center', va='bottom', fontsize=9)

    plt.tight_layout()

    # Speichern
    chart_file = os.path.join(output_dir, f'ost_west_grouped_bar_{timestamp}.png')
    plt.savefig(chart_file, dpi=300, bbox_inches='tight')
    print(f"✓ Grouped Bar Chart: {chart_file}")

    plt.close()


if __name__ == '__main__':

    main()
