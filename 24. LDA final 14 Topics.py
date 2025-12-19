import json
import pandas as pd
import numpy as np
from gensim import corpora
from gensim.models import LdaModel, CoherenceModel
import os
from datetime import datetime


def main():
    # An eigene Pfade anpassen!
    input_file = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\Cleaned_Data.jsonl"
    stopwords_file = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\corona_stopwords.txt"
    spacy_stopwords_file = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\spacy_stopwords_deutsch.txt"
    output_dir = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\LDA\final_14_topics"

    # Output-Ordner erstellen
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 70)
    print("LDA TOPIC MODELING - 14 TOPICS (FINALE VERSION)")
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

    # Metriken berechnen
    coherence_model = CoherenceModel(
        model=lda_model,
        texts=documents,
        dictionary=dictionary,
        coherence='c_v',
        processes=1
    )
    coherence = coherence_model.get_coherence()
    perplexity = lda_model.log_perplexity(corpus)

    print(f"✓ Coherence Score: {coherence:.4f}")
    print(f"✓ Log Perplexity: {perplexity:.4f}")

    # Dokumentenverteilung berechnen (welches Topic ist dominant in jedem Dokument)
    print("\nBerechne Topic-Verteilung...")
    doc_topics = []
    for doc_bow in corpus:
        topic_dist = lda_model.get_document_topics(doc_bow)
        if topic_dist:
            # Dominantes Topic für dieses Dokument
            dominant_topic = max(topic_dist, key=lambda x: x[1])[0]
            doc_topics.append(dominant_topic)

    # Anteil Dokumente pro Topic
    from collections import Counter
    topic_counts = Counter(doc_topics)
    total_docs = len(doc_topics)

    # Timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # HAUPTTABELLE Top 7 Wörtern
    print("\nErstelle Haupttabelle für wissenschaftliche Arbeit...")

    main_table_data = []
    for topic_id in range(14):
        top_words = lda_model.show_topic(topic_id, topn=7)
        words = [word for word, prob in top_words]

        # Dokumentenanteil berechnen
        doc_percentage = (topic_counts.get(topic_id, 0) / total_docs) * 100

        main_table_data.append({
            'Topic': topic_id,
            'Thematisches Label': '[LABEL HIER EINFÜGEN]',  # Platzhalter für deine Interpretation
            'Charakteristische Begriffe': ', '.join(words),
            'Anteil Tweets (%)': f'{doc_percentage:.1f}'
        })

    main_df = pd.DataFrame(main_table_data)

    # Als Excel für Haupttabelle
    main_excel = os.path.join(output_dir, f'lda_haupttabelle_{timestamp}.xlsx')
    with pd.ExcelWriter(main_excel, engine='openpyxl') as writer:
        main_df.to_excel(writer, sheet_name='LDA Topics', index=False)

        worksheet = writer.sheets['LDA Topics']
        # Spaltenbreiten
        worksheet.column_dimensions['A'].width = 8  # Topic
        worksheet.column_dimensions['B'].width = 30  # Label
        worksheet.column_dimensions['C'].width = 60  # Begriffe
        worksheet.column_dimensions['D'].width = 15  # Anteil

        # Header fett
        from openpyxl.styles import Font, Alignment
        for cell in worksheet[1]:
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center', vertical='center')

        # Topic-Spalte zentriert
        for row in range(2, 16):
            worksheet[f'A{row}'].alignment = Alignment(horizontal='center')
            worksheet[f'D{row}'].alignment = Alignment(horizontal='center')

    print(f"✓ Haupttabelle gespeichert: {main_excel}")

    # ANHANG-TABELLE (mit allen Top 10 Wörtern + Wahrscheinlichkeiten)
    print("\nErstelle Anhang-Tabelle mit vollständigen Informationen...")

    appendix_data = []
    for topic_id in range(14):
        top_words = lda_model.show_topic(topic_id, topn=10)
        words_with_prob = [f"{word} ({prob:.3f})" for word, prob in top_words]

        doc_percentage = (topic_counts.get(topic_id, 0) / total_docs) * 100

        appendix_data.append({
            'Topic': topic_id,
            'Top 10 Begriffe (mit Wahrscheinlichkeiten)': ', '.join(words_with_prob),
            'Anzahl Tweets': topic_counts.get(topic_id, 0),
            'Anteil (%)': f'{doc_percentage:.2f}'
        })

    appendix_df = pd.DataFrame(appendix_data)

    # Als Excel für Anhang
    appendix_excel = os.path.join(output_dir, f'lda_anhang_{timestamp}.xlsx')
    with pd.ExcelWriter(appendix_excel, engine='openpyxl') as writer:
        appendix_df.to_excel(writer, sheet_name='Vollständige Topic-Liste', index=False)

        worksheet = writer.sheets['Vollständige Topic-Liste']
        worksheet.column_dimensions['A'].width = 8
        worksheet.column_dimensions['B'].width = 100
        worksheet.column_dimensions['C'].width = 15
        worksheet.column_dimensions['D'].width = 12

        # Header fett
        for cell in worksheet[1]:
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center', vertical='center')

        for row in range(2, 16):
            worksheet[f'A{row}'].alignment = Alignment(horizontal='center')
            worksheet[f'C{row}'].alignment = Alignment(horizontal='center')
            worksheet[f'D{row}'].alignment = Alignment(horizontal='center')

    print(f"✓ Anhang-Tabelle gespeichert: {appendix_excel}")

    # DETAILLIERTE TEXTDATEI (für Dokumentation)
    txt_file = os.path.join(output_dir, f'lda_14_topics_documentation_{timestamp}.txt')

    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("LDA TOPIC MODELING - 14 TOPICS (FINALE VERSION)\n")
        f.write(f"Trainiert: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")

        f.write("MODELL-PARAMETER:\n")
        f.write("-" * 80 + "\n")
        f.write(f"Anzahl Topics: 14\n")
        f.write(f"Coherence Score (C_v): {coherence:.4f}\n")
        f.write(f"Log Perplexity: {perplexity:.4f}\n")
        f.write(f"Anzahl Dokumente: {len(documents)}\n")
        f.write(f"Vokabulargröße: {len(dictionary)}\n")
        f.write(f"Passes: 15\n")
        f.write(f"Iterations: 500\n")
        f.write(f"Alpha: auto\n")
        f.write(f"Eta: auto\n\n")

        f.write("=" * 80 + "\n")
        f.write("TOPICS MIT DETAILLIERTEN INFORMATIONEN\n")
        f.write("=" * 80 + "\n\n")

        for topic_id in range(14):
            doc_count = topic_counts.get(topic_id, 0)
            doc_percentage = (doc_count / total_docs) * 100

            f.write(f"Topic {topic_id}:\n")
            f.write("-" * 80 + "\n")
            f.write(f"Anzahl Tweets: {doc_count} ({doc_percentage:.2f}%)\n")
            f.write(f"Top 10 Begriffe:\n")

            top_words = lda_model.show_topic(topic_id, topn=10)
            for i, (word, prob) in enumerate(top_words, 1):
                f.write(f"  {i:2d}. {word:20s} {prob:.5f}\n")
            f.write("\n")

    print(f"✓ Dokumentation gespeichert: {txt_file}")

    # MODELL SPEICHERN
    model_file = os.path.join(output_dir, f'lda_model_14_topics_{timestamp}')
    lda_model.save(model_file)
    print(f"✓ Modell gespeichert: {model_file}")

    # ZUSAMMENFASSUNG
    print("\n" + "=" * 70)
    print("ANALYSE ABGESCHLOSSEN!")
    print("=" * 70)
    print(f"Alle Dateien gespeichert in: {output_dir}\n")
    print("Erstellte Dateien:")
    print(f"  • HAUPTTABELLE (für Arbeit): {os.path.basename(main_excel)}")
    print(f"  • ANHANG-TABELLE (komplett): {os.path.basename(appendix_excel)}")
    print(f"  • Dokumentation: {os.path.basename(txt_file)}")
    print(f"  • Gespeichertes Modell: {os.path.basename(model_file)}")


if __name__ == '__main__':

    main()


