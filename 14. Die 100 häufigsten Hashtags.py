import json
from collections import Counter
import os
from datetime import datetime


def load_tweets(input_file):
    """Lädt Tweets aus JSONL-Datei"""
    print(f"Lade Tweets aus: {input_file}")
    tweets = []

    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                tweets.append(json.loads(line.strip()))
            except:
                continue

    print(f"✓ {len(tweets)} Tweets geladen\n")
    return tweets


def analyze_top_hashtags(tweets, output_dir, top_n=100):
    """
    Extrahiert und zählt alle Hashtags, gibt Top N aus

    Args:
        tweets: Liste von Tweet-Dictionaries
        output_dir: Ausgabeverzeichnis
        top_n: Anzahl der Top-Hashtags (default: 100)
    """
    print(f"Analysiere Hashtags...")

    # Alle Hashtags sammeln
    all_hashtags = []
    for tweet in tweets:
        hashtags = tweet.get('entities', {}).get('hashtags', [])
        all_hashtags.extend(hashtags)

    # Zählen
    hashtag_counter = Counter(all_hashtags)

    print(f"✓ {len(all_hashtags):,} Hashtag-Vorkommen")
    print(f"✓ {len(hashtag_counter):,} unique Hashtags\n")

    # Output-Datei erstellen
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    txt_file = os.path.join(output_dir, f"top_{top_n}_hashtags_{timestamp}.txt")

    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write(f"TOP {top_n} HASHTAGS\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Analysezeitpunkt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Gesamt-Vorkommen: {len(all_hashtags):,}\n")
        f.write(f"Unique Hashtags: {len(hashtag_counter):,}\n\n")
        f.write("-" * 60 + "\n")
        f.write(f"{'Rang':<6} {'Hashtag':<40} {'Anzahl':<10}\n")
        f.write("-" * 60 + "\n")

        # Top N Hashtags schreiben
        for idx, (hashtag, count) in enumerate(hashtag_counter.most_common(top_n), 1):
            f.write(f"{idx:<6} #{hashtag:<39} {count:>8,}\n")

    print(f"✓ Gespeichert: {txt_file}\n")


def main():
    """Hauptfunktion"""
    # PASSE DIESE PFADE AN!
    input_file = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\Cleaned_Data.jsonl"
    output_dir = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\Hashtags"

    # Tweets laden
    tweets = load_tweets(input_file)

    # Top 100 Hashtags analysieren
    analyze_top_hashtags(tweets, output_dir, top_n=100)

    print("=" * 60)
    print("ANALYSE ABGESCHLOSSEN!")
    print("=" * 60)


if __name__ == "__main__":
    main()