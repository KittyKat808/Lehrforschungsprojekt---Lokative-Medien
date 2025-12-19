import json
from collections import Counter
import os
from datetime import datetime


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


def find_corona_related_tokens(tweets, output_dir):
    """Findet ALLE Tokens die Corona/COVID/SARS enthalten"""

    print("Sammle alle Tokens...")

    # Alle Tokens sammeln
    all_tokens = []
    for tweet in tweets:
        tokens = tweet.get('tokens', [])
        if tokens:
            all_tokens.extend(tokens)

    # Counter erstellen
    token_counter = Counter(all_tokens)
    total_tokens = sum(token_counter.values())

    print(f"✓ {len(token_counter):,} unique Tokens gefunden\n")

    # Substrings für die Suche
    search_substrings = [
        'corona', 'covid', 'cov', 'sars', 'ncov', 'pandemic', 'pandemie', 'virus'
    ]

    print("Suche nach Corona/COVID/SARS/Virus-verwandten Tokens...")

    # Finde alle Tokens die einen der Substrings enthalten
    corona_tokens = {}

    for token in token_counter.keys():
        token_lower = token.lower()

        for substring in search_substrings:
            if substring in token_lower:
                corona_tokens[token] = {
                    'count': token_counter[token],
                    'percentage': (token_counter[token] / total_tokens) * 100
                }
                break

    # Sortiere alphabetisch
    corona_tokens_alphabetical = sorted(corona_tokens.items(), key=lambda x: x[0].lower())

    print(f"✓ {len(corona_tokens)} Corona-verwandte Tokens gefunden\n")

    # Output-Verzeichnis erstellen
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # --- TXT-DATEI ERSTELLEN ---
    txt_file = os.path.join(output_dir, f"corona_tokens_alphabetisch_{timestamp}.txt")
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write("CORONA-VERWANDTE TOKENS (ALPHABETISCH)\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Anzahl: {len(corona_tokens)} Tokens\n")
        f.write(f"Gesamt-Vorkommen: {sum(t[1]['count'] for t in corona_tokens_alphabetical):,}\n\n")
        f.write("=" * 80 + "\n\n")

        for token, info in corona_tokens_alphabetical:
            f.write(f"{token}\n")

    print(f"✓ Liste gespeichert: {txt_file}")


def main():
    # An eigene Pfade anpassen!
    input_file = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\Cleaned_Data.jsonl"
    output_dir = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\Tokens"

    tweets = load_tweets(input_file)
    find_corona_related_tokens(tweets, output_dir)


if __name__ == "__main__":
    main()

