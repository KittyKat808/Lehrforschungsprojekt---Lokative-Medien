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

# Großstädte-Mapping 
GROSSSTAEDTE_MAPPING = {
    "Berlin": "Berlin", "Hamburg": "Hamburg", "Munich": "München",
    "Cologne": "Köln", "Frankfurt": "Frankfurt am Main",
    "Frankfurt am Main": "Frankfurt am Main",
    "Dusseldorf": "Düsseldorf", "Düsseldorf": "Düsseldorf",
    "Stuttgart": "Stuttgart", "Leipzig": "Leipzig", "Dortmund": "Dortmund",
    "Bremen": "Bremen", "Essen": "Essen", "Dresden": "Dresden",
    "Nuremberg": "Nürnberg", "Nürnberg": "Nürnberg",
    "Hanover": "Hannover", "Hannover": "Hannover",
    "Duisburg": "Duisburg", "Bochum": "Bochum", "Wuppertal": "Wuppertal",
    "Bielefeld": "Bielefeld", "Bonn": "Bonn", "Mannheim": "Mannheim",
    "Karlsruhe": "Karlsruhe", "Munster": "Münster", "Münster": "Münster",
    "Augsburg": "Augsburg", "Wiesbaden": "Wiesbaden",
    "Gelsenkirchen": "Gelsenkirchen",
    "Monchengladbach": "Mönchengladbach", "Mönchengladbach": "Mönchengladbach",
    "Aachen": "Aachen", "Brunswick": "Braunschweig", "Braunschweig": "Braunschweig",
    "Kiel": "Kiel", "Chemnitz": "Chemnitz", "Magdeburg": "Magdeburg",
    "Freiburg": "Freiburg im Breisgau", "Freiburg im Breisgau": "Freiburg im Breisgau",
    "Krefeld": "Krefeld", "Halle": "Halle (Saale)", "Halle (Saale)": "Halle (Saale)",
    "Mainz": "Mainz", "Erfurt": "Erfurt", "Lubeck": "Lübeck", "Lübeck": "Lübeck",
    "Oberhausen": "Oberhausen", "Rostock": "Rostock", "Kassel": "Kassel",
    "Hagen": "Hagen", "Potsdam": "Potsdam",
    "Saarbrucken": "Saarbrücken", "Saarbrücken": "Saarbrücken",
    "Hamm": "Hamm", "Ludwigshafen": "Ludwigshafen am Rhein",
    "Ludwigshafen am Rhein": "Ludwigshafen am Rhein",
    "Oldenburg": "Oldenburg",
    "Mulheim": "Mülheim an der Ruhr", "Mülheim": "Mülheim an der Ruhr",
    "Mülheim an der Ruhr": "Mülheim an der Ruhr",
    "Leverkusen": "Leverkusen", "Darmstadt": "Darmstadt",
    "Osnabruck": "Osnabrück", "Osnabrück": "Osnabrück",
    "Solingen": "Solingen", "Paderborn": "Paderborn", "Herne": "Herne",
    "Heidelberg": "Heidelberg", "Neuss": "Neuss", "Regensburg": "Regensburg",
    "Ingolstadt": "Ingolstadt", "Pforzheim": "Pforzheim",
    "Wurzburg": "Würzburg", "Würzburg": "Würzburg",
    "Offenbach": "Offenbach am Main", "Offenbach am Main": "Offenbach am Main",
    "Furth": "Fürth", "Fürth": "Fürth", "Heilbronn": "Heilbronn",
    "Ulm": "Ulm", "Wolfsburg": "Wolfsburg",
    "Gottingen": "Göttingen", "Göttingen": "Göttingen",
    "Reutlingen": "Reutlingen", "Bremerhaven": "Bremerhaven",
    "Bottrop": "Bottrop", "Erlangen": "Erlangen",
    "Recklinghausen": "Recklinghausen", "Remscheid": "Remscheid",
    "Koblenz": "Koblenz", "Bergisch Gladbach": "Bergisch Gladbach",
    "Jena": "Jena", "Salzgitter": "Salzgitter", "Trier": "Trier",
    "Siegen": "Siegen", "Moers": "Moers",
    "Gutersloh": "Gütersloh", "Gütersloh": "Gütersloh"
}

GROSSSTAEDTE_ENGLISCH = set(GROSSSTAEDTE_MAPPING.keys())

# Stadtstaaten
STADTSTAATEN = ['Berlin', 'Hamburg', 'Bremen', 'Free Hanseatic City of Bremen', 'Hanseatic City']


def kategorisiere_urban_rural(tweet):
    """Kategorisiert Tweet als Urban (Großstadt >100k) oder Rural"""
    geo_source = tweet.get('geo_source')

    if not geo_source:
        return None

    if geo_source == 'place' and tweet.get('place'):
        location_data = tweet['place']
    elif geo_source == 'coordinates' and tweet.get('geo'):
        location_data = tweet['geo']
    else:
        return None

    # Stadtstaaten sind immer Urban
    state = location_data.get('state', '')
    if any(stadtstaat in state for stadtstaat in STADTSTAATEN):
        return 'Urban'

    # Bestimme Ortsnamen
    ort = None
    if 'city' in location_data and location_data['city']:
        ort = location_data['city']
    elif 'county' in location_data and location_data['county']:
        ort = location_data['county']

    if not ort:
        return None

    ort_clean = ort.replace("Region ", "").replace("City of ", "").strip()

    if ort_clean in GROSSSTAEDTE_ENGLISCH:
        return 'Urban'
    else:
        return 'Rural'


def main():
    # Pfade
    model_dir = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\LDA\final_14_topics"
    input_file = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\Cleaned_Data.jsonl"
    stopwords_file = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\corona_stopwords.txt"
    spacy_stopwords_file = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\spacy_stopwords_deutsch.txt"
    output_dir = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\LDA\urban_rural_analyse"

    os.makedirs(output_dir, exist_ok=True)

    print("=" * 70)
    print("STADT-LAND-VERGLEICH: 6 AUSGEWÄHLTE TOPICS")
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

    # Zähle Tweets nach Urban/Rural und Topic
    urban_topic_counts = defaultdict(int)
    rural_topic_counts = defaultdict(int)
    urban_total = 0
    rural_total = 0

    tweets_with_geo = 0

    for idx, doc_bow in enumerate(corpus):
        if idx % 10000 == 0 and idx > 0:
            print(f"  Verarbeitet: {idx:,} Tweets...")

        kategorie = kategorisiere_urban_rural(valid_tweets[idx])
        if not kategorie:
            continue

        tweets_with_geo += 1

        topic_dist = lda_model.get_document_topics(doc_bow, minimum_probability=0.0)
        if not topic_dist:
            continue

        dominant_topic, prob = max(topic_dist, key=lambda x: x[1])

        # Urban oder Rural?
        if kategorie == 'Urban':
            urban_total += 1
            if dominant_topic in SELECTED_TOPICS:
                urban_topic_counts[dominant_topic] += 1
        elif kategorie == 'Rural':
            rural_total += 1
            if dominant_topic in SELECTED_TOPICS:
                rural_topic_counts[dominant_topic] += 1

    print(f"\n✓ Tweets mit Geo-Info: {tweets_with_geo:,}")
    print(f"   Urban: {urban_total:,} ({urban_total / tweets_with_geo * 100:.1f}%)")
    print(f"   Rural: {rural_total:,} ({rural_total / tweets_with_geo * 100:.1f}%)")

    # 5. Berechne Anteile
    print("\n[5/5] Berechne Anteile und erstelle Visualisierungen...")

    results = []
    for topic_id in sorted(SELECTED_TOPICS.keys()):
        topic_label = SELECTED_TOPICS[topic_id]
        display_id = TOPIC_DISPLAY[topic_id]

        urban_count = urban_topic_counts[topic_id]
        rural_count = rural_topic_counts[topic_id]

        urban_anteil = (urban_count / urban_total * 100) if urban_total > 0 else 0
        rural_anteil = (rural_count / rural_total * 100) if rural_total > 0 else 0

        differenz = urban_anteil - rural_anteil

        results.append({
            'Topic_ID': topic_id,
            'Topic_Display': display_id,
            'Topic_Label': topic_label,
            'Urban_Tweets': urban_count,
            'Rural_Tweets': rural_count,
            'Urban_Anteil': urban_anteil,
            'Rural_Anteil': rural_anteil,
            'Differenz': differenz
        })

    df_results = pd.DataFrame(results)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # TXT-Report
    create_txt_report(df_results, urban_total, rural_total, output_dir, timestamp)

    # Grouped Bar Chart
    create_grouped_bar_chart(df_results, output_dir, timestamp)

    print("\n" + "=" * 70)
    print("✅ ANALYSE ABGESCHLOSSEN")
    print("=" * 70)
    print(f"\n📁 Dateien in: {output_dir}")
    print("📊 Erstellt: 1 CSV, 1 TXT-Report, 1 Grouped Bar Chart")


def create_txt_report(df_results, urban_total, rural_total, output_dir, timestamp):
    """Erstellt TXT-Report"""

    txt_file = os.path.join(output_dir, f'urban_rural_vergleich_{timestamp}.txt')

    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("STADT-LAND-VERGLEICH: ANTEIL AM DISKURS\n")
        f.write(f"Erstellt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")

        f.write("Definition:\n")
        f.write("  Urban: Großstädte mit über 100.000 Einwohnern (inkl. Stadtstaaten)\n")
        f.write("  Rural: Alle anderen Städte und Gemeinden\n\n")

        f.write(f"Tweets Urban (gesamt): {urban_total:,}\n")
        f.write(f"Tweets Rural (gesamt): {rural_total:,}\n\n")

        f.write("Metrik: Anteil der Tweets aus Urban/Rural, die dem jeweiligen Topic\n")
        f.write("        zugeordnet wurden (in Prozent).\n\n")

        f.write("=" * 80 + "\n")
        f.write("VERGLEICH PRO TOPIC\n")
        f.write("=" * 80 + "\n\n")

        f.write(f"{'Topic':<8} {'Label':<45} {'Urban (%)':<11} {'Rural (%)':<11} {'Diff.':<10}\n")
        f.write("-" * 80 + "\n")

        for _, row in df_results.iterrows():
            f.write(f"{row['Topic_Display']:<8} {row['Topic_Label']:<45} "
                    f"{row['Urban_Anteil']:>9.2f}% {row['Rural_Anteil']:>9.2f}% "
                    f"{row['Differenz']:>+7.2f}\n")

        f.write("\n\n" + "=" * 80 + "\n")
        f.write("INTERPRETATION\n")
        f.write("=" * 80 + "\n\n")

        # Größte Unterschiede
        df_sorted = df_results.sort_values('Differenz', key=abs, ascending=False)

        f.write("Größte Unterschiede:\n\n")

        for idx, (_, row) in enumerate(df_sorted.head(3).iterrows(), 1):
            if row['Differenz'] > 0:
                richtung = "höher in Städten"
            else:
                richtung = "höher auf dem Land"

            f.write(f"{idx}. Topic {row['Topic_Display']} ({row['Topic_Label']})\n")
            f.write(f"   Differenz: {abs(row['Differenz']):.2f} Prozentpunkte {richtung}\n")
            f.write(f"   Urban: {row['Urban_Anteil']:.2f}%, Rural: {row['Rural_Anteil']:.2f}%\n\n")

        # Homogene Topics
        f.write("\nNahezu homogene Topics (Differenz < 1 Prozentpunkt):\n\n")

        homogen = df_results[df_results['Differenz'].abs() < 1.0]
        if len(homogen) > 0:
            for _, row in homogen.iterrows():
                f.write(f"- Topic {row['Topic_Display']} ({row['Topic_Label']}): "
                        f"Urban {row['Urban_Anteil']:.2f}%, Rural {row['Rural_Anteil']:.2f}%\n")
        else:
            f.write("Keine homogenen Topics gefunden.\n")

    print(f"✓ TXT-Report: {txt_file}")


def create_grouped_bar_chart(df_results, output_dir, timestamp):
    """Erstellt Grouped Bar Chart"""

    fig, ax = plt.subplots(figsize=(14, 7))

    x = range(len(df_results))
    width = 0.35

    # Balken für Urban
    bars_urban = ax.bar([i - width / 2 for i in x], df_results['Urban_Anteil'],
                        width, label='Urban (Stadt)', color='#9b59b6', alpha=0.8)

    # Balken für Rural
    bars_rural = ax.bar([i + width / 2 for i in x], df_results['Rural_Anteil'],
                        width, label='Rural (Land)', color='#27ae60', alpha=0.8)

    # Achsenbeschriftungen
    ax.set_xlabel('Topic', fontsize=12, fontweight='bold')
    ax.set_ylabel('Anteil am Diskurs (%)', fontsize=12, fontweight='bold')
    ax.set_title('Stadt-Land-Vergleich: Anteil der Topics am jeweiligen Diskurs',
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
    for bars in [bars_urban, bars_rural]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2., height,
                    f'{height:.1f}%',
                    ha='center', va='bottom', fontsize=9)

    plt.tight_layout()

    # Speichern
    chart_file = os.path.join(output_dir, f'urban_rural_grouped_bar_{timestamp}.png')
    plt.savefig(chart_file, dpi=300, bbox_inches='tight')
    print(f"✓ Grouped Bar Chart: {chart_file}")

    plt.close()


if __name__ == '__main__':

    main()
