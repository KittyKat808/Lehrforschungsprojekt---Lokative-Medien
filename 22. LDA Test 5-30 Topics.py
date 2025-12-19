import json
import pandas as pd
import numpy as np
from gensim import corpora
from gensim.models import LdaModel, CoherenceModel
import matplotlib.pyplot as plt
import os


def main():
    # Pfade
    input_file = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\Cleaned_Data.jsonl"
    stopwords_file = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\corona_stopwords.txt"
    output_dir = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\LDA"

    # Output-Ordner erstellen
    os.makedirs(output_dir, exist_ok=True)

    # 1. Daten laden
    print("Lade Daten...")
    tweets = []
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            tweets.append(json.loads(line))

    # 2. Corona-Stopwörter laden
    print("Lade Corona-Stopwörter...")
    with open(stopwords_file, 'r', encoding='utf-8') as f:
        corona_stopwords = set([line.strip().lower() for line in f])

    # 3. Tokens extrahieren und filtern
    print("Bereite Tokens vor...")
    documents = []
    for tweet in tweets:
        # Tokens filtern (Stopwörter entfernen)
        filtered_tokens = [token for token in tweet['tokens']
                           if token.lower() not in corona_stopwords and len(token) > 2]
        if len(filtered_tokens) > 0:  # Nur Tweets mit verbleibenden Tokens
            documents.append(filtered_tokens)

    print(f"Anzahl Dokumente: {len(documents)}")
    print(f"Beispiel: {documents[0][:10]}")

    # 4. Dictionary und Corpus erstellen
    print("\nErstelle Dictionary und Corpus...")
    dictionary = corpora.Dictionary(documents)

    # Extremwörter filtern (sehr selten oder sehr häufig)
    dictionary.filter_extremes(no_below=5, no_above=0.5, keep_n=10000)
    print(f"Vokabulargröße: {len(dictionary)}")

    # Corpus erstellen (Bag-of-Words)
    corpus = [dictionary.doc2bow(doc) for doc in documents]

    # 5. Coherence Score für verschiedene Topic-Anzahlen berechnen
    print("\n=== PARAMETEROPTIMIERUNG ===")
    print("Teste verschiedene Anzahlen von Topics...")

    # Teste verschiedene Topic-Anzahlen
    topic_range = range(5, 31, 1)  # 5 bis 30 topics testen
    coherence_scores = []
    perplexity_scores = []

    for num_topics in topic_range:
        print(f"\nTeste {num_topics} Topics...")

        # LDA-Modell trainieren
        lda_model = LdaModel(
            corpus=corpus,
            id2word=dictionary,
            num_topics=num_topics,
            random_state=42,
            passes=10,
            alpha='auto',  # Lernt alpha automatisch
            eta='auto',  # Lernt eta automatisch
            per_word_topics=True
        )

        # Coherence Score (höher = besser)
        coherence_model = CoherenceModel(
            model=lda_model,
            texts=documents,
            dictionary=dictionary,
            coherence='c_v',
            processes=1  # FIX für Windows: Kein Multiprocessing
        )
        coherence_score = coherence_model.get_coherence()
        coherence_scores.append(coherence_score)

        # Perplexity (niedriger = besser, aber weniger aussagekräftig)
        perplexity = lda_model.log_perplexity(corpus)
        perplexity_scores.append(perplexity)

        print(f"  Coherence Score: {coherence_score:.4f}")
        print(f"  Perplexity: {perplexity:.4f}")

    # 6. Ergebnisse visualisieren
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))

    # Coherence Score Plot
    ax1.plot(topic_range, coherence_scores, 'b-o')
    ax1.set_xlabel('Anzahl Topics')
    ax1.set_ylabel('Coherence Score')
    ax1.set_title('Coherence Score nach Anzahl Topics')
    ax1.grid(True)

    # Perplexity Plot
    ax2.plot(topic_range, perplexity_scores, 'r-o')
    ax2.set_xlabel('Anzahl Topics')
    ax2.set_ylabel('Perplexity')
    ax2.set_title('Perplexity nach Anzahl Topics')
    ax2.grid(True)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'parameter_optimization.png'), dpi=300)
    print(f"\nDiagramm gespeichert: {os.path.join(output_dir, 'parameter_optimization.png')}")

    # 7. Ergebnisse speichern
    results_df = pd.DataFrame({
        'num_topics': list(topic_range),
        'coherence_score': coherence_scores,
        'perplexity': perplexity_scores
    })
    results_df.to_csv(os.path.join(output_dir, 'optimization_results.csv'), index=False)
    print(f"Ergebnisse gespeichert: {os.path.join(output_dir, 'optimization_results.csv')}")

    # 8. Beste Konfiguration identifizieren
    best_idx = np.argmax(coherence_scores)
    best_num_topics = list(topic_range)[best_idx]
    best_coherence = coherence_scores[best_idx]

    print("\n" + "=" * 50)
    print(f"EMPFEHLUNG: {best_num_topics} Topics (Coherence: {best_coherence:.4f})")
    print("=" * 50)

    # 9. Finales Modell mit bester Konfiguration trainieren
    print(f"\nTrainiere finales LDA-Modell mit {best_num_topics} Topics...")
    final_lda = LdaModel(
        corpus=corpus,
        id2word=dictionary,
        num_topics=best_num_topics,
        random_state=42,
        passes=15,  # Mehr Passes für finales Modell
        iterations=400,
        alpha='auto',
        eta='auto',
        per_word_topics=True
    )

    # 10. Modell speichern
    final_lda.save(os.path.join(output_dir, 'lda_model'))
    dictionary.save(os.path.join(output_dir, 'dictionary'))
    corpora.MmCorpus.serialize(os.path.join(output_dir, 'corpus.mm'), corpus)
    print(f"Modell gespeichert in: {output_dir}")

    # 11. Topics anzeigen
    print("\n=== GEFUNDENE TOPICS ===")
    for idx, topic in final_lda.print_topics(-1, num_words=10):
        print(f"\nTopic {idx}:")
        print(topic)

    print("\n✓ Fertig!")


# WICHTIG für Windows: Dieser Block ist notwendig!
if __name__ == '__main__':
    main()