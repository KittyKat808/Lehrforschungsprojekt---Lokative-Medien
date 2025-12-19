import json
import random
import os

# =============================================================================
# INPUT UND OUTPUT PFADE DEFINIEREN - HIER EIGENE PFADE ANPASSEN!
# =============================================================================

# Input und Output Verzeichnisse definieren
input_file = r'C:\Users\[NUTZERNAME]\[ORDNERNAME]\filtered_tweets.json'
output_directory = r'C:\Users\[NUTZERNAME]\[ORDNERNAME]'
output_file = os.path.join(output_directory, 'filtered_tweets_sample_20k.json')
output_ids_file = os.path.join(output_directory, 'filtered_tweet_ids_sample_20k.json')

# =============================================================================
# SAMPLE ZIEHEN
# =============================================================================

# Sample-Größe
sample_size = 20000

print("Lade alle Tweets...")

# Alle Tweets laden
all_tweets = []
with open(input_file, 'r', encoding='utf-8') as file:
    for line in file:
        try:
            tweet = json.loads(line.strip())
            all_tweets.append(tweet)
        except json.JSONDecodeError:
            continue

print(f"Geladene Tweets: {len(all_tweets):,}")

# Randomisiertes Sample ziehen
print(f"Ziehe randomisiertes Sample von {sample_size:,} Tweets...")
random.shuffle(all_tweets)
sampled_tweets = all_tweets[:sample_size]

print(f"Sample erstellt: {len(sampled_tweets):,} Tweets")

# =============================================================================
# SAMPLE SPEICHERN
# =============================================================================

# Sample speichern (jeder Tweet in einer Zeile)
os.makedirs(output_directory, exist_ok=True)
print(f"\nSpeichere Sample in: {output_file}")
with open(output_file, 'w', encoding='utf-8') as file:
    for tweet in sampled_tweets:
        file.write(json.dumps(tweet, ensure_ascii=False) + '\n')

# Tweet-IDs extrahieren und speichern
tweet_ids = []
for tweet in sampled_tweets:
    tweet_id = tweet.get('tweet_id')
    if tweet_id:
        tweet_ids.append(tweet_id)

print(f"Speichere Tweet-IDs in: {output_ids_file}")
print(f"Sample erfolgreich gespeichert!")
