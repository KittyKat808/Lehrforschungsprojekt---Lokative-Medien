import json

# =============================================================================
# PFADE DEFINIEREN - HIER EIGENE PFADE ANPASSEN!
# =============================================================================

# Eingabedateien für die ersten zwei Splits
split1_path = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\split1_with_entities.json"
split2_path = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\split2_with_entities.json"

# Gefilterter Datensatz mit Informationen zu Standort, Uhrzeit, etc.
additional_data_path = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\filtered_tweets_sample_20k.json"

# Ausgabedateien
merged_splits_path = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\split1-split2_merged.json"
final_dataset_path = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\Final_Dataset.json"


# =============================================================================
# HILFSFUNKTIONEN
# =============================================================================

def load_jsonl_file(file_path):
    """
    Lädt eine JSONL-Datei und gibt eine Liste von Objekten zurück
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return [json.loads(line) for line in file if line.strip()]
    except FileNotFoundError:
        print(f"Datei nicht gefunden: {file_path}")
        return []
    except Exception as e:
        print(f"Fehler beim Laden der Datei {file_path}: {e}")
        return []


def save_jsonl_file(data, file_path):
    """
    Speichert eine Liste von Objekten als JSONL-Datei
    """
    with open(file_path, 'w', encoding='utf-8') as file:
        for item in data:
            json.dump(item, file, ensure_ascii=False)
            file.write('\n')


# =============================================================================
# SCHRITT 1: SPLIT1 UND SPLIT2 ZUSAMMENFÜHREN
# =============================================================================

print("Schritt 1: Laden und Zusammenführen von Split1 und Split2...")

# Beide Split-Dateien laden
split1_data = load_jsonl_file(split1_path)
split2_data = load_jsonl_file(split2_path)

# Einfaches Zusammenführen durch Listenverknüpfung
merged_splits = split1_data + split2_data

# Zwischenergebnis speichern
save_jsonl_file(merged_splits, merged_splits_path)

print(f"Split1 Tweets: {len(split1_data)}")
print(f"Split2 Tweets: {len(split2_data)}")
print(f"Zusammengeführte Tweets: {len(merged_splits)}")
print(f"Zwischenergebnis gespeichert: {merged_splits_path}")

# =============================================================================
# SCHRITT 2: MIT ZUSATZDATEN ANHAND VON TWEET-IDS ZUSAMMENFÜHREN
# =============================================================================

print("\nSchritt 2: Zusammenführen mit zusätzlichen Tweet-Informationen...")

# Zusatzdaten laden
additional_data = load_jsonl_file(additional_data_path)

# Dictionary für schnelle Tweet-ID-Suche erstellen
additional_tweets_dict = {str(tweet['tweet_id']): tweet for tweet in additional_data}

# Finale Zusammenführung anhand von Tweet-IDs
final_merged_tweets = []
matched_count = 0

for tweet in merged_splits:
    tweet_id = str(tweet['tweet_id'])

    # Prüfen ob Tweet-ID in Zusatzdaten existiert
    if tweet_id in additional_tweets_dict:
        # Daten zusammenführen (zusätzliche Daten haben Priorität bei Duplikaten)
        merged_tweet = {**tweet, **additional_tweets_dict[tweet_id]}
        final_merged_tweets.append(merged_tweet)
        matched_count += 1

# =============================================================================
# SCHRITT 3: NUR DEUTSCHE TWEETS FILTERN
# =============================================================================

print("\nSchritt 3: Filterung auf deutsche Tweets...")

# Anzahl vor Filterung
tweets_before_filter = len(final_merged_tweets)

# Nur deutsche Tweets behalten
german_tweets = []
for tweet in final_merged_tweets:
    lang = tweet.get('lang', '')
    if lang.lower() == 'de':  # Nur deutsche Tweets
        german_tweets.append(tweet)

# Finalen Datensatz speichern
if german_tweets:
    save_jsonl_file(german_tweets, final_dataset_path)

    # =============================================================================
    # ZUSAMMENFASSUNG
    # =============================================================================

    print("\n" + "=" * 60)
    print("DATASET-MERGING ERFOLGREICH ABGESCHLOSSEN")
    print("=" * 60)
    print(f"Tweets vor Sprachfilterung:           {tweets_before_filter}")
    print(f"Deutsche Tweets gefiltert:            {len(german_tweets)}")
    print(f"Reduzierung um:                       {tweets_before_filter - len(german_tweets)} Tweets")
    print(f"Anteil deutsche Tweets:               {len(german_tweets)/tweets_before_filter*100:.1f}%")
    print("-" * 60)
    print(f"Zwischendatei:  {merged_splits_path}")
    print(f"Finaler Datensatz (nur DE): {final_dataset_path}")
    print("=" * 60)

else:
    print("FEHLER: Keine deutschen Tweets gefunden!")
