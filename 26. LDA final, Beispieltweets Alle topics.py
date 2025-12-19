import json
import pandas as pd
from gensim import corpora
from gensim.models import LdaModel
import os
from datetime import datetime
import re


def clean_text_for_comparison(text):
    """Entfernt Datum, URLs, Mentions für besseren Vergleich"""
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'@\w+', '', text)
    text = re.sub(r'\d{1,2}\.\d{1,2}\.\d{4}', 'DATUM', text)
    text = re.sub(r'\d{1,2}/\d{1,2}/\d{4}', 'DATUM', text)
    text = re.sub(r'\d{1,2}:\d{2}', 'UHRZEIT', text)
    text = re.sub(r'\d{1,2} Uhr', 'UHRZEIT', text)
    text = re.sub(r'zirka \d{1,2}', 'zirka UHRZEIT', text)
    text = re.sub(r'ca\. \d{1,2}', 'ca. UHRZEIT', text)
    weekdays = ['montag', 'dienstag', 'mittwoch', 'donnerstag', 'freitag', 'samstag', 'sonntag',
                'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    for day in weekdays:
        text = re.sub(day, 'WOCHENTAG', text, flags=re.IGNORECASE)
    text = re.sub(r'heute am \d{1,2}\.\d{1,2}\.\d{4}', 'heute am DATUM', text, flags=re.IGNORECASE)
    text = re.sub(r'am \d{1,2}\.\d{1,2}\.\d{4}', 'am DATUM', text, flags=re.IGNORECASE)
    text = re.sub(r'#\w+', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip().lower()


def main():
    # An eigene Pfade anpassen!
    model_dir = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\LDA\final_14_topics"
    input_file = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\Cleaned_Data.jsonl"
    stopwords_file = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\corona_stopwords.txt"
    spacy_stopwords_file = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\spacy_stopwords_deutsch.txt"

    # ALLE Topics analysieren
    TOPICS_TO_ANALYZE = list(range(14))  # 0-13

    # Wie viele Beispiele pro Topic?
    NUM_EXAMPLES = 20  # ← HIER KANNST DU DIE ANZAHL ÄNDERN

    print("=" * 70)
    print(f"ERWEITERTE BEISPIEL-TWEETS FÜR ALLE 14 TOPICS")
    print(f"Anzahl Beispiele pro Topic: {NUM_EXAMPLES}")
    print(f"Gestartet: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # 1. Modell laden
    print("\n[1/4] Lade gespeichertes Modell...")
    model_file = os.path.join(model_dir, "lda_model_14_topics_20251124_235500")
    lda_model = LdaModel.load(model_file)
    print(f"✓ Modell geladen")

    # 2. Daten laden
    print("\n[2/4] Lade Tweets...")
    tweets = []
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            tweets.append(json.loads(line))
    print(f"✓ Tweets geladen: {len(tweets)}")

    # 3. Stopwörter laden
    print("\n[3/4] Bereite Daten vor...")
    with open(stopwords_file, 'r', encoding='utf-8') as f:
        corona_stopwords = set([line.strip().lower() for line in f if line.strip()])

    with open(spacy_stopwords_file, 'r', encoding='utf-8') as f:
        spacy_stopwords = set([
            line.strip().lower() for line in f
            if line.strip() and not line.startswith('#')
        ])

    all_stopwords = corona_stopwords | spacy_stopwords

    # Dokumente vorbereiten
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

    print(f"✓ Verwendbare Tweets: {len(valid_tweets)}")

    # Dictionary und Corpus
    dictionary = corpora.Dictionary(documents)
    dictionary.filter_extremes(no_below=5, no_above=0.5, keep_n=10000)
    corpus = [dictionary.doc2bow(doc) for doc in documents]

    # 4. Beispiel-Tweets für alle Topics finden
    print(f"\n[4/4] Finde {NUM_EXAMPLES} Beispiele für alle Topics...")

    # Für alle Topics: Finde Tweets
    topic_tweets = {i: [] for i in range(14)}

    for idx, doc_bow in enumerate(corpus):
        # Topic-Verteilung für diesen Tweet
        topic_dist = dict(lda_model.get_document_topics(doc_bow, minimum_probability=0.01))

        if not topic_dist:
            continue

        # Finde dominantes Topic
        dominant_topic = max(topic_dist.items(), key=lambda x: x[1])
        topic_id, prob = dominant_topic

        # Kriterien für Aufnahme
        if prob > 0.3:  # ← HIER KANNST DU DIE SCHWELLE ÄNDERN (0.3 = 30%)

            # Prüfe, ob Tweet die Top-Wörter des Topics enthält
            top_words = [word for word, _ in lda_model.show_topic(topic_id, topn=15)]
            tweet_tokens = set([t.lower() for t in valid_tweets[idx]['tokens']])

            # Wie viele Top-Wörter sind im Tweet?
            overlap = len(tweet_tokens.intersection(set(top_words)))

            # Mindestens 1 Top-Wort
            if overlap >= 1:  # ← HIER KANNST DU DIE MINDEST-ÜBEREINSTIMMUNG ÄNDERN
                topic_tweets[topic_id].append({
                    'tweet_idx': idx,
                    'probability': prob,
                    'overlap_score': overlap,
                    'text': valid_tweets[idx]['original_text'],
                    'created_at': valid_tweets[idx].get('created_at', 'N/A'),
                    'retweets': valid_tweets[idx]['public_metrics']['retweet_count'],
                    'likes': valid_tweets[idx]['public_metrics']['like_count']
                })

    # Sortiere und entferne Duplikate
    print("\nVerarbeite Topics und entferne Duplikate...")
    for topic_id in range(14):
        # Sortiere primär nach Overlap, sekundär nach Probability
        topic_tweets[topic_id].sort(
            key=lambda x: (x['overlap_score'], x['probability']),
            reverse=True
        )

        # Entferne EXAKTE und NEAR-Duplikate
        seen_texts_exact = set()
        seen_texts_cleaned = set()
        unique_tweets = []
        removed_near_duplicates = 0

        for tweet in topic_tweets[topic_id]:
            text_lower = tweet['text'].lower().strip()

            # Check 1: Exakte Duplikate
            if text_lower in seen_texts_exact:
                continue

            # Check 2: Near-Duplikate
            cleaned_text = clean_text_for_comparison(tweet['text'])
            if cleaned_text in seen_texts_cleaned:
                removed_near_duplicates += 1
                continue

            # Check 3: Mindestlänge
            if len(text_lower) <= 20:
                continue

            # Tweet ist unique!
            seen_texts_exact.add(text_lower)
            seen_texts_cleaned.add(cleaned_text)
            unique_tweets.append(tweet)

            if len(unique_tweets) >= NUM_EXAMPLES:
                break

        topic_tweets[topic_id] = unique_tweets[:NUM_EXAMPLES]

        if removed_near_duplicates > 0:
            print(
                f"  Topic {topic_id:2d}: {len(topic_tweets[topic_id]):2d} Beispiele ({removed_near_duplicates} Near-Dups entfernt)")
        else:
            print(f"  Topic {topic_id:2d}: {len(topic_tweets[topic_id]):2d} Beispiele")

    # 5. AUSGABE ERSTELLEN
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Als Textdatei
    txt_file = os.path.join(model_dir, f'alle_topics_erweitert_{NUM_EXAMPLES}beispiele_{timestamp}.txt')

    print(f"\nErstelle Textdatei...")
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write(f"ERWEITERTE BEISPIEL-TWEETS FÜR ALLE TOPICS (Top {NUM_EXAMPLES})\n")
        f.write(f"Erstellt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("\nAuswahlkriterien:\n")
        f.write("- Tweet wird von Topic dominiert (>30%)\n")
        f.write("- Tweet enthält mindestens 1 Top-Wort des Topics\n")
        f.write("- Keine exakten Duplikate\n")
        f.write("- Keine Near-Duplikate\n")
        f.write("=" * 80 + "\n\n")

        for topic_id in range(14):
            # Topic-Info
            top_words = [word for word, prob in lda_model.show_topic(topic_id, topn=10)]

            f.write("\n" + "=" * 80 + "\n")
            f.write(f"TOPIC {topic_id} (Gensim) = TOPIC {topic_id + 1} (Darstellung)\n")
            f.write("=" * 80 + "\n")
            f.write(f"Top-Wörter: {', '.join(top_words)}\n")
            f.write(f"Anzahl Beispiele: {len(topic_tweets[topic_id])}\n")
            f.write("-" * 80 + "\n")

            if not topic_tweets[topic_id]:
                f.write("\n⚠️ Keine Beispiele gefunden\n\n")
                continue

            # Alle gefundenen Tweets
            for i, tweet_data in enumerate(topic_tweets[topic_id], 1):
                f.write(f"\n[{i:2d}] Prob: {tweet_data['probability']:.3f} | ")
                f.write(f"Overlap: {tweet_data['overlap_score']} Wörter | ")
                f.write(f"Likes: {tweet_data['likes']} | RT: {tweet_data['retweets']}\n")
                f.write(f"Datum: {tweet_data['created_at']}\n")
                f.write(f"Text: {tweet_data['text']}\n")
                f.write("-" * 80)

            f.write("\n\n")

    print(f"✓ Textdatei gespeichert: {txt_file}")

    # Als Excel
    print(f"Erstelle Excel-Datei...")
    excel_file = os.path.join(model_dir, f'alle_topics_erweitert_{NUM_EXAMPLES}beispiele_{timestamp}.xlsx')

    all_examples = []
    for topic_id in range(14):
        top_words = ', '.join([word for word, prob in lda_model.show_topic(topic_id, topn=7)])

        for i, tweet_data in enumerate(topic_tweets[topic_id], 1):
            all_examples.append({
                'Topic (Gensim)': topic_id,
                'Topic (Darstellung)': topic_id + 1,
                'Top-Wörter': top_words,
                'Beispiel Nr.': i,
                'Wahrscheinlichkeit': float(f"{tweet_data['probability']:.3f}"),
                'Übereinstimmung': tweet_data['overlap_score'],
                'Datum': tweet_data['created_at'],
                'Likes': tweet_data['likes'],
                'Retweets': tweet_data['retweets'],
                'Tweet-Text': tweet_data['text']
            })

    df = pd.DataFrame(all_examples)

    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        # Gesamtübersicht
        df.to_excel(writer, sheet_name='Alle Topics', index=False)

        worksheet = writer.sheets['Alle Topics']
        worksheet.column_dimensions['A'].width = 12
        worksheet.column_dimensions['B'].width = 15
        worksheet.column_dimensions['C'].width = 50
        worksheet.column_dimensions['D'].width = 12
        worksheet.column_dimensions['E'].width = 18
        worksheet.column_dimensions['F'].width = 15
        worksheet.column_dimensions['G'].width = 20
        worksheet.column_dimensions['H'].width = 8
        worksheet.column_dimensions['I'].width = 10
        worksheet.column_dimensions['J'].width = 80

        # Separate Sheets pro Topic
        for topic_id in range(14):
            topic_df = df[df['Topic (Gensim)'] == topic_id].copy()
            if len(topic_df) > 0:
                sheet_name = f'Topic {topic_id + 1}'
                topic_df.to_excel(writer, sheet_name=sheet_name, index=False)

                ws = writer.sheets[sheet_name]
                ws.column_dimensions['A'].width = 12
                ws.column_dimensions['B'].width = 15
                ws.column_dimensions['C'].width = 50
                ws.column_dimensions['D'].width = 12
                ws.column_dimensions['E'].width = 18
                ws.column_dimensions['F'].width = 15
                ws.column_dimensions['G'].width = 20
                ws.column_dimensions['H'].width = 8
                ws.column_dimensions['I'].width = 10
                ws.column_dimensions['J'].width = 80

    print(f"✓ Excel-Datei gespeichert: {excel_file}")

    # ZUSAMMENFASSUNG
    for topic_id in range(14):
        count = len(topic_tweets[topic_id])
        print(f"   Topic {topic_id:2d} (= Topic {topic_id + 1:2d} Darstellung): {count:2d} Beispiele")

    print(f"Excel hat {len(df)} Beispiele insgesamt")


if __name__ == '__main__':
    main()


