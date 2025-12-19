import json
from collections import Counter
import os
from datetime import datetime
from wordcloud import WordCloud
import matplotlib.pyplot as plt


def load_corona_stopwords(stopwords_file):
    """Lädt Corona-Stopwords aus Textdatei"""
    print(f"Lade Corona-Stopwords aus: {stopwords_file}")

    stopwords = set()
    with open(stopwords_file, 'r', encoding='utf-8') as f:
        for line in f:
            token = line.strip().lower()
            if token:
                stopwords.add(token)

    print(f"✓ {len(stopwords)} Corona-Stopwords geladen\n")
    return stopwords


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


def analyze_tokens(tweets, corona_stopwords, output_dir):
    """Analysiert Tokens, erstellt Top-100-Liste und Wortwolke (gefiltert)"""

    print("Analysiere Tokens...")

    # Alle Tokens sammeln und filtern
    all_tokens = []
    for tweet in tweets:
        tokens = tweet.get('tokens', [])
        if tokens:
            # Filtere Corona-Stopwords
            filtered_tokens = [token for token in tokens if token.lower() not in corona_stopwords]
            all_tokens.extend(filtered_tokens)

    print(f"✓ {len(all_tokens):,} Tokens analysiert (nach Filterung)\n")

    # Counter erstellen
    token_counter = Counter(all_tokens)
    total_tokens = sum(token_counter.values())

    # Output-Verzeichnis erstellen
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # --- TOP 100 TOKENS TXT ---
    print("Erstelle Top-100-Liste...")
    txt_file = os.path.join(output_dir, f"top100_tokens_gefiltert_{timestamp}.txt")

    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write("TOP 100 HÄUFIGSTE TOKENS (NACH CORONA-STOPWORD-FILTERUNG)\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"{'Rang':<6} {'Token':<30} {'Anzahl':<12} {'Anteil':<10}\n")
        f.write("-" * 70 + "\n")

        for idx, (token, count) in enumerate(token_counter.most_common(100), 1):
            anteil = (count / total_tokens) * 100
            f.write(f"{idx:<6} {token:<30} {count:<12,} {anteil:>6.2f}%\n")

    print(f"✓ Top-100-Liste: {txt_file}")

    # --- WORTWOLKE ---
    print("Erstelle Wortwolke...")

    wordcloud = WordCloud(
        width=1600,
        height=800,
        background_color='white',
        colormap='viridis',
        max_words=200,
        relative_scaling=0.5,
        min_font_size=10
    ).generate_from_frequencies(token_counter)

    plt.figure(figsize=(20, 10))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.title(f'Top Tokens ({len(tweets):,} Tweets, ohne Corona-Stopwords)',
              fontsize=20, pad=20)

    wordcloud_file = os.path.join(output_dir, f"wordcloud_gefiltert_{timestamp}.png")
    plt.savefig(wordcloud_file, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()

    print(f"✓ Wortwolke: {wordcloud_file}")
    print(f"\n{'=' * 70}")
    print("ANALYSE ABGESCHLOSSEN!")
    print(f"{'=' * 70}\n")


def main():
    # An eigene Pfade anpassen!
    input_file = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\Cleaned_Data.jsonl"
    stopwords_file = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\corona_stopwords.txt"
    output_dir = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\Tokens"

    corona_stopwords = load_corona_stopwords(stopwords_file)
    tweets = load_tweets(input_file)
    analyze_tokens(tweets, corona_stopwords, output_dir)


if __name__ == "__main__":

    main()
