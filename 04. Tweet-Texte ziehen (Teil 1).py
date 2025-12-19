import tweepy  # Tweepy Bibliothek importieren
import json
import time
import re

# =============================================================================
# API ZUGANGSDATEN EINGEBEN
# =============================================================================

# API-Zugangsdaten einrichten
consumer_key = '[consumer key]'
consumer_secret = '[consumer secret]'
access_token = '[access token]'
access_token_secret = '[access token secret]'
bearer_token = '[bearer token]'

# Tweepy Client erstellen
client = tweepy.Client(bearer_token)

# =============================================================================
# INPUT UND OUTPUT PFADE DEFINIEREN - HIER EIGENE PFADE ANPASSEN!
# =============================================================================

# Input- und Output-Pfade festlegen
input_path = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\tweet_ids-split1.json"
output_path = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\pulled_tweets-split1.json"
formatted_output_path = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\pulled_tweets-split1_formatted.json"
entity_output_path = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\split1_with_entities.json"


# =============================================================================
# HILFSFUNKTIONEN
# =============================================================================

# Funktion zur Extraktion von Entities (Hashtags, Mentions, URL) ohne Symbole
def extract_entities(text):
    """
    Extrahiert Hashtags, Mentions und URLs aus dem Tweet-Text.
    - Hashtags: ohne das #-Symbol
    - Mentions: ohne das @-Symbol
    - URLs: komplette HTTP/HTTPS URLs
    """
    hashtags = [tag.strip("#") for tag in re.findall(r'#\w+', text)]
    mentions = [mention.strip("@") for mention in re.findall(r'@\w+', text)]
    urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
    return {
        "hashtags": hashtags,
        "mentions": mentions,
        "urls": urls
    }


# =============================================================================
# TWEETS MITHILFE VON TWEEPY ÜBER DIE API BEZIEHEN; DABEI RATE LIMITS BEACHTEN
# =============================================================================

# Tweet-IDs aus der Input-JSON-Datei einlesen
with open(input_path, 'r') as file:
    tweet_ids = json.load(file)

# Zusätzliche Parameter (tweet_fields)
tweet_fields = ["id", "text", "lang", "source", "public_metrics"]

# Liste zum Speichern der Tweet-Informationen
all_tweet_info = []

# Batch-Größe festlegen
batch_size = 100

try:
    # Schleife durch Tweet-IDs in Batches
    for i in range(0, len(tweet_ids), batch_size):
        batch_ids = tweet_ids[i:i + batch_size]

        # Tweets des aktuellen Batches abrufen
        tweets = client.get_tweets(ids=batch_ids, tweet_fields=tweet_fields)

        # Jeden Tweet im Batch verarbeiten
        if tweets.data:
            for tweet in tweets.data:
                tweet_info = {
                    "tweet_id": tweet['id'],
                    "text": tweet['text'],
                    "lang": tweet['lang'],
                    "source": tweet['source'],
                    "public_metrics": tweet['public_metrics']
                }

                # Tweet-Informationen zur Liste hinzufügen
                all_tweet_info.append(tweet_info)

        # Rate Limits beachten -> eine Minute warten
        time.sleep(60)

except Exception as e:
    print(f"Fehler beim Abrufen der Tweets: {e}")

# Die gesammelten Tweet-Informationen in eine neue JSON-Datei speichern
with open(output_path, 'w', encoding='utf-8') as output_file:
    json.dump(all_tweet_info, output_file, indent=2, ensure_ascii=False)

print(f"Tweet-Abruf abgeschlossen. {len(all_tweet_info)} Tweets abgerufen.")

# =============================================================================
# FORMATIERUNG DER GEZOGENEN TWEETS (JEDES OBJEKT IN EINER ZEILE)
# =============================================================================

print("Formatierung der Tweets wird gestartet...")

# Jedes JSON-Objekt in eine neue Datei schreiben, mit jedem Objekt in einer eigenen Zeile
with open(formatted_output_path, 'w', encoding='utf-8') as file:
    for obj in all_tweet_info:
        json.dump(obj, file, ensure_ascii=False)
        file.write('\n')

print("Formatierung abgeschlossen.")

# =============================================================================
# SPRACHFILTERUNG UND ENTITY-EXTRAKTION
# =============================================================================

print("Sprachfilterung und Entity-Extraktion wird gestartet...")

# Zähler für englische und deutsche Tweets initialisieren
total_count = 0
filtered_tweets = []

# Tweets basierend auf Sprache filtern und Entities ohne Symbole hinzufügen
for tweet in all_tweet_info:
    lang = tweet.get('lang', '')
    if lang.lower() in ['de']:  # Nur Tweets auf Deutsch werden berücksichtigt
        total_count += 1
        entities = extract_entities(tweet['text'])
        tweet['entities'] = entities
        filtered_tweets.append(tweet)

# Gefilterte und aktualisierte Tweets in eine neue Datei schreiben
with open(entity_output_path, 'w', encoding='utf-8') as file:
    for tweet in filtered_tweets:
        json.dump(tweet, file, ensure_ascii=False)
        file.write('\n')

# =============================================================================
# ZUSAMMENFASSUNG
# =============================================================================

print("\n" + "=" * 50)
print("VERARBEITUNG VON TEIL 1 ABGESCHLOSSEN")
print("=" * 50)
print(f"Tweets insgesamt abgerufen: {len(all_tweet_info)}")
print(f"Deutsche Tweets gefiltert: {total_count}")
print(f"Originaldaten gespeichert in: {output_path}")
print(f"Formatierte Daten gespeichert in: {formatted_output_path}")
print(f"Gefilterte Daten mit Entities gespeichert in: {entity_output_path}")
print("=" * 50)
