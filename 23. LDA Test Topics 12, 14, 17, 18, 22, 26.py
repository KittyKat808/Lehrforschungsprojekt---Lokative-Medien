import json
import pandas as pd
import numpy as np
from gensim import corpora
from gensim.models import LdaModel, CoherenceModel
import matplotlib.pyplot as plt
import os
from datetime import datetime
from collections import Counter


def main():
    # An eigene Pfade anpassen!
    input_file = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\Cleaned_Data.jsonl"
    stopwords_file = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\corona_stopwords.txt"
    spacy_stopwords_file = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\spacy_stopwords_deutsch.txt"
    output_dir = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\LDA\topic_comparison"

    # Output-Ordner erstellen
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 70)
    print("LDA TOPIC MODELING - VERGLEICH AUSGEWÄHLTER TOPIC-ANZAHLEN")
    print(f"Gestartet: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # 1. Daten laden
    print("\n[1/5] Lade Daten...")
    tweets = []
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            tweets.append(json.loads(line))

    print(f"✓ Gesamtanzahl Tweets: {len(tweets)}")

    # 2. ALLE Stopwörter laden und kombinieren
    print("\n[2/5] Lade Stopwörter...")

    # Corona-spezifische Stopwörter
    with open(stopwords_file, 'r', encoding='utf-8') as f:
        corona_stopwords = set([line.strip().lower() for line in f if line.strip()])
    corona_count = len(corona_stopwords)

    # SpaCy deutsche Stopwörter
    with open(spacy_stopwords_file, 'r', encoding='utf-8') as f:
        spacy_stopwords = set([
            line.strip().lower() for line in f
            if line.strip() and not line.startswith('#')
        ])
    spacy_count = len(spacy_stopwords)

    # ALLE Stopwörter kombinieren
    all_stopwords = corona_stopwords | spacy_stopwords

    print(f"✓ Corona-Stopwörter: {corona_count}")
    print(f"✓ SpaCy-Stopwörter: {spacy_count}")
    print(f"✓ GESAMT: {len(all_stopwords)} Stopwörter")

    # 3. Tokens extrahieren und GRÜNDLICH filtern
    print("\n[3/5] Bereite Tokens vor und filtere Stopwörter...")
    documents = []
    filtered_out_count = 0
    total_tokens = 0

    for tweet in tweets:
        total_tokens += len(tweet['tokens'])

        filtered_tokens = [
            token for token in tweet['tokens']
            if token.lower() not in all_stopwords  # Stopwort-Filter
               and len(token) > 2  # Mindestlänge 3
               and not token.isnumeric()  # Keine reinen Zahlen
        ]

        filtered_out_count += (len(tweet['tokens']) - len(filtered_tokens))

        if len(filtered_tokens) > 0:
            documents.append(filtered_tokens)

    print(f"✓ Anzahl verwendbare Dokumente: {len(documents)}")
    print(f"✓ Tokens gesamt: {total_tokens}")
    print(f"✓ Tokens gefiltert: {filtered_out_count} ({filtered_out_count / total_tokens * 100:.1f}%)")
    print(f"✓ Tokens verbleibend: {total_tokens - filtered_out_count}")

    # 4. Dictionary und Corpus erstellen
    print("\n[4/5] Erstelle Dictionary und Corpus...")
    dictionary = corpora.Dictionary(documents)
    print(f"✓ Vokabular vor Filterung: {len(dictionary)}")

    # Extremwörter filtern
    dictionary.filter_extremes(no_below=5, no_above=0.5, keep_n=10000)
    print(f"✓ Vokabular nach Filterung: {len(dictionary)}")

    # Corpus erstellen
    corpus = [dictionary.doc2bow(doc) for doc in documents]
    corpus_words = sum(cnt for doc in corpus for _, cnt in doc)
    print(f"✓ Gesamtanzahl Wörter im Corpus: {corpus_words}")

    # 5. TESTE AUSGEWÄHLTE TOPIC-ANZAHLEN
    print("\n" + "=" * 70)
    print("[5/5] TRAINIERE MODELLE MIT VERSCHIEDENEN TOPIC-ANZAHLEN")
    print("=" * 70)

    # Liste der zu testenden Topic-Anzahlen
    topic_numbers = [12, 14, 17, 18, 22, 26]

    print(f"\nZu testende Topic-Anzahlen: {topic_numbers}")
    print(f"Geschätzte Dauer: {len(topic_numbers) * 3}-{len(topic_numbers) * 5} Minuten")
    print("=" * 70)

    # Timestamp für alle Dateien
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Dictionary für Ergebnisse
    results = []
    all_models = {}

    # Für jede Topic-Anzahl trainieren
    for i, num_topics in enumerate(topic_numbers, 1):
        print(f"\n{'#' * 70}")
        print(f"TRAINIERE MODELL {i}/{len(topic_numbers)}: {num_topics} TOPICS")
        print(f"{'#' * 70}")

        # LDA trainieren
        print(f"Training läuft...")
        lda_model = LdaModel(
            corpus=corpus,
            id2word=dictionary,
            num_topics=num_topics,
            random_state=42,
            passes=15,
            iterations=500,
            alpha='auto',
            eta='auto',
            per_word_topics=True,
            eval_every=None  # Keine Zwischenausgaben
        )

        # Metriken berechnen
        print(f"Berechne Metriken...")

        # Coherence
        coherence_model = CoherenceModel(
            model=lda_model,
            texts=documents,
            dictionary=dictionary,
            coherence='c_v',
            processes=1
        )
        coherence = coherence_model.get_coherence()

        # Perplexity
        perplexity = lda_model.log_perplexity(corpus)

        print(f"✓ Coherence Score: {coherence:.4f}")
        print(f"✓ Log Perplexity: {perplexity:.4f}")

        # Ergebnisse speichern
        results.append({
            'num_topics': num_topics,
            'coherence_score': coherence,
            'log_perplexity': perplexity
        })

        # Modell speichern für spätere Verwendung
        all_models[num_topics] = lda_model

        # Topics als Text speichern
        print(f"Speichere Topics...")
        topics_file = os.path.join(output_dir, f'topics_{num_topics}topics_{timestamp}.txt')

        with open(topics_file, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write(f"LDA TOPIC MODELING - {num_topics} TOPICS\n")
            f.write(f"Trainiert: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 70 + "\n\n")
            f.write(f"Coherence Score: {coherence:.4f}\n")
            f.write(f"Log Perplexity: {perplexity:.4f}\n")
            f.write("\n" + "=" * 70 + "\n")
            f.write("TOPICS (Top 15 Wörter pro Topic)\n")
            f.write("=" * 70 + "\n\n")

            # Alle Topics ausgeben
            for idx, topic in lda_model.print_topics(-1, num_words=15):
                f.write(f"Topic {idx}:\n")
                f.write(f"{topic}\n\n")

        print(f"✓ Topics gespeichert: {topics_file}")

    # ZUSAMMENFASSUNG ERSTELLEN
    print("\n" + "=" * 70)
    print("ERSTELLE ZUSAMMENFASSUNG")
    print("=" * 70)

    # Ergebnisse als DataFrame
    results_df = pd.DataFrame(results)

    # CSV speichern
    csv_file = os.path.join(output_dir, f'comparison_results_{timestamp}.csv')
    results_df.to_csv(csv_file, index=False)
    print(f"✓ Ergebnisse-CSV gespeichert: {csv_file}")

    # GESAMTÜBERSICHT als TXT
    summary_file = os.path.join(output_dir, f'summary_all_topics_{timestamp}.txt')

    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("=" * 70 + "\n")
        f.write("VERGLEICH VERSCHIEDENER TOPIC-ANZAHLEN\n")
        f.write(f"Analysiert: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 70 + "\n\n")

        f.write("METRIKEN-ÜBERSICHT:\n")
        f.write("-" * 70 + "\n")
        for _, row in results_df.iterrows():
            f.write(f"{int(row['num_topics']):2d} Topics: ")
            f.write(f"Coherence = {row['coherence_score']:.4f}, ")
            f.write(f"Perplexity = {row['log_perplexity']:.4f}\n")

        f.write("\n" + "=" * 70 + "\n\n")

        # Für jede Topic-Anzahl: Top 10 Wörter pro Topic
        for num_topics in topic_numbers:
            f.write("\n" + "=" * 70 + "\n")
            f.write(f"MODELL MIT {num_topics} TOPICS\n")
            f.write("=" * 70 + "\n\n")

            lda_model = all_models[num_topics]

            # Kompakte Darstellung: Top 10 Wörter
            for idx in range(num_topics):
                top_words = [word for word, _ in lda_model.show_topic(idx, topn=10)]
                f.write(f"Topic {idx:2d}: {', '.join(top_words)}\n")

            f.write("\n")

    print(f"✓ Gesamtübersicht gespeichert: {summary_file}")

    # VISUALISIERUNG
    print("\nErstelle Visualisierung...")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Plot 1: Coherence Score
    ax1.plot(results_df['num_topics'], results_df['coherence_score'],
             marker='o', linewidth=2, markersize=8, color='steelblue')
    ax1.set_xlabel('Anzahl Topics', fontsize=12)
    ax1.set_ylabel('Coherence Score (C_v)', fontsize=12)
    ax1.set_title('Coherence Score Vergleich', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.set_xticks(topic_numbers)

    # Werte annotieren
    for _, row in results_df.iterrows():
        ax1.annotate(f"{row['coherence_score']:.3f}",
                     (row['num_topics'], row['coherence_score']),
                     textcoords="offset points", xytext=(0, 10), ha='center', fontsize=9)

    # Plot 2: Perplexity
    ax2.plot(results_df['num_topics'], results_df['log_perplexity'],
             marker='s', linewidth=2, markersize=8, color='coral')
    ax2.set_xlabel('Anzahl Topics', fontsize=12)
    ax2.set_ylabel('Log Perplexity', fontsize=12)
    ax2.set_title('Perplexity Vergleich', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.set_xticks(topic_numbers)

    # Werte annotieren
    for _, row in results_df.iterrows():
        ax2.annotate(f"{row['log_perplexity']:.2f}",
                     (row['num_topics'], row['log_perplexity']),
                     textcoords="offset points", xytext=(0, -15), ha='center', fontsize=9)

    plt.tight_layout()

    # Speichern
    plot_file = os.path.join(output_dir, f'comparison_plot_{timestamp}.png')
    plt.savefig(plot_file, dpi=300, bbox_inches='tight')
    print(f"✓ Visualisierung gespeichert: {plot_file}")

    # FINALE ZUSAMMENFASSUNG
    print("\n" + "=" * 70)
    print("ZUSAMMENFASSUNG")
    print("=" * 70)

    print("\nGetestete Topic-Anzahlen:")
    for _, row in results_df.iterrows():
        print(f"  {int(row['num_topics']):2d} Topics: "
              f"Coherence = {row['coherence_score']:.4f}, "
              f"Perplexity = {row['log_perplexity']:.4f}")

    # Beste nach Coherence
    best_coherence_idx = results_df['coherence_score'].idxmax()
    best_coherence = results_df.loc[best_coherence_idx]

    print(f"Höchste Coherence: {int(best_coherence['num_topics'])} Topics "
          f"({best_coherence['coherence_score']:.4f})")

    # Beste nach Perplexity
    best_perplexity_idx = results_df['log_perplexity'].idxmin()
    best_perplexity = results_df.loc[best_perplexity_idx]

    print(f" Niedrigste Perplexity: {int(best_perplexity['num_topics'])} Topics "
          f"({best_perplexity['log_perplexity']:.4f})")

    print(f" Alle Dateien gespeichert in: {output_dir}")


if __name__ == '__main__':

    main()
