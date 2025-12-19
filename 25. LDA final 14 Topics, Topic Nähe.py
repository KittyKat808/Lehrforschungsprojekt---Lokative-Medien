import json
import pandas as pd
import numpy as np
from gensim import corpora
from gensim.models import LdaModel
import pyLDAvis
import pyLDAvis.gensim_models as gensimvis
import os
from datetime import datetime


def main():
    # Pfade
    input_file = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\Cleaned_Data.jsonl"
    stopwords_file = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]corona_stopwords.txt"
    spacy_stopwords_file = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\spacy_stopwords_deutsch.txt"
    output_dir = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\LDA\final_14_topics"

    # Output-Ordner erstellen
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 70)
    print("LDA TOPIC MODELING - VISUALISIERUNG")
    print(f"Gestartet: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # 1. Daten laden
    print("\n[1/5] Lade Daten...")
    tweets = []
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            tweets.append(json.loads(line))
    print(f"✓ Gesamtanzahl Tweets: {len(tweets)}")

    # 2. Stopwörter laden
    print("\n[2/5] Lade Stopwörter...")
    with open(stopwords_file, 'r', encoding='utf-8') as f:
        corona_stopwords = set([line.strip().lower() for line in f if line.strip()])

    with open(spacy_stopwords_file, 'r', encoding='utf-8') as f:
        spacy_stopwords = set([
            line.strip().lower() for line in f
            if line.strip() and not line.startswith('#')
        ])

    all_stopwords = corona_stopwords | spacy_stopwords
    print(f"✓ Gesamt: {len(all_stopwords)} Stopwörter")

    # 3. Tokens vorbereiten
    print("\n[3/5] Bereite Tokens vor und filtere Stopwörter...")
    documents = []
    for tweet in tweets:
        filtered_tokens = [
            token for token in tweet['tokens']
            if token.lower() not in all_stopwords
               and len(token) > 2
               and not token.isnumeric()
        ]
        if len(filtered_tokens) > 0:
            documents.append(filtered_tokens)

    print(f"✓ Anzahl verwendbare Dokumente: {len(documents)}")

    # 4. Dictionary und Corpus erstellen
    print("\n[4/5] Erstelle Dictionary und Corpus...")
    dictionary = corpora.Dictionary(documents)
    print(f"✓ Vokabular vor Filterung: {len(dictionary)}")

    dictionary.filter_extremes(no_below=5, no_above=0.5, keep_n=10000)
    print(f"✓ Vokabular nach Filterung: {len(dictionary)}")

    corpus = [dictionary.doc2bow(doc) for doc in documents]

    # 5. LDA-Modell mit 14 Topics trainieren
    print("\n[5/5] Trainiere LDA-Modell mit 14 Topics...")

    lda_model = LdaModel(
        corpus=corpus,
        id2word=dictionary,
        num_topics=14,
        random_state=42,
        passes=15,
        iterations=500,
        alpha='auto',
        eta='auto',
        per_word_topics=True
    )

    print("✓ Modell trainiert!")

    # Timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # PYLDAVIS VISUALISIERUNG ERSTELLEN
    print("\n" + "=" * 70)
    print("ERSTELLE PYLDAVIS VISUALISIERUNG")
    print("=" * 70)

    print("\nBereite Visualisierung vor...")

    # pyLDAvis-Daten vorbereiten
    vis_data = gensimvis.prepare(
        lda_model,
        corpus,
        dictionary,
        mds='mmds',  # Multidimensional scaling method
        sort_topics=False  # Topics in ursprünglicher Reihenfolge
    )

    # Als interaktive HTML speichern
    html_file = os.path.join(output_dir, f'pyLDAvis_14_topics_{timestamp}.html')
    pyLDAvis.save_html(vis_data, html_file)
    print(f"✓ Interaktive Visualisierung gespeichert: {html_file}")

if __name__ == '__main__':
    main()