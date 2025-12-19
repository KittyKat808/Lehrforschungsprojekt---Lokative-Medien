import os  # Dateisystem-Operationen (Pfade erstellen, Verzeichnisse anlegen)
import json  # JSON-Dateien lesen und schreiben
import zipfile  # ZIP-Dateien öffnen und Inhalte extrahieren (Da Datensätze als zip vorliegen)

# =============================================================================
# INPUT UND OUTPUT PFADE DEFINIEREN - HIER EIGENE PFADE ANPASSEN!
# =============================================================================

# Input Verzeichnis definieren, dass alle Datensätze enthält
dataset_directory = r'C:\Users\[NUTZERNAME]\[ORDNERNAME]'
dataset_paths = [os.path.join(dataset_directory, f) for f in os.listdir(dataset_directory) if f.endswith('.zip')]
dataset_paths.sort()

# Output Verzeichnisse definieren
output_directory = r'C:\Users\[NUTZERNAME]\[ORDNERNAME]'
log_directory = r'C:\Users\[NUTZERNAME]\[ORDNERNAME]'


# =============================================================================
# DATENSÄTZE FILTERN
# =============================================================================

def should_include_tweet(tweet):
    geo_source = tweet.get('geo_source', '')

    # Nur tweets mit geo_source 'coordinates' oder 'place'
    if geo_source not in ['coordinates', 'place']:
        return False

    desired_country_code = "de"

    # Je nach geo_source das entsprechende Feld prüfen
    if geo_source == 'coordinates':
        # Prüfe das 'geo' Feld
        geo_data = tweet.get('geo', {})
        return (geo_data.get('country_code') == desired_country_code and
                geo_data.get('state') is not None and
                geo_data.get('state').strip() != '')

    elif geo_source == 'place':
        # Prüfe das 'place' Feld
        place_data = tweet.get('place', {})
        return (place_data.get('country_code') == desired_country_code and
                place_data.get('state') is not None and
                place_data.get('state').strip() != '')

    return False


# Liste zum Speichern der gefilterten TWeets
combined_filtered_tweets = []

# Liste zum Speichern der Tweet-IDs
all_tweet_ids = []

# Liste zum Speichern der Nutzer-IDs
unique_user_ids = set()

# Zähler für die Gesamtanzahl der gefilterten Tweets
number_filtered_tweets = 0

# Durchlaufe jede ZIP-Datei
for zip_path in dataset_paths:
    print(f"Verarbeite ZIP-Datei: {os.path.basename(zip_path)}")

    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Alle JSON-Dateien in der ZIP finden
            json_files = [f for f in zip_ref.namelist() if f.endswith('.json')]

            if not json_files:
                print(f"  Keine JSON-Dateien in {os.path.basename(zip_path)} gefunden!")
                continue

            for json_file in json_files:
                print(f"  Verarbeite: {json_file}")

                with zip_ref.open(json_file) as file:
                    for line_num, line in enumerate(file, 1):
                        try:
                            # Bytes zu String dekodieren, dann JSON parsen
                            line_str = line.decode('utf-8').strip()
                            if not line_str:  # Leere Zeilen überspringen
                                continue

                            item = json.loads(line_str)

                            if should_include_tweet(item):
                                # Tweet zur Liste der gefilterten Tweets hinzufügen
                                combined_filtered_tweets.append(item)

                                # Tweet-ID und User-ID extrahieren und zu den Listen hinzufügen
                                tweet_id = item.get('tweet_id')
                                user_id = item.get('user_id')

                                all_tweet_ids.append(tweet_id)
                                unique_user_ids.add(user_id)

                                # Zähler für die Gesamtanzahl der gefilterten Tweets erhöhen
                                number_filtered_tweets += 1

                        except json.JSONDecodeError as e:
                            print(f"    Fehler beim Parsen von Zeile {line_num}: {e}")
                            continue
                        except UnicodeDecodeError as e:
                            print(f"    Encoding-Fehler in Zeile {line_num}: {e}")
                            continue

    except zipfile.BadZipFile:
        print(f"  Fehler: {os.path.basename(zip_path)} ist keine gültige ZIP-Datei!")
        continue
    except FileNotFoundError:
        print(f"  Fehler: {zip_path} nicht gefunden!")
        continue

# =============================================================================
# OUTPUT AUSGEBEN UND SPEICHERN
# =============================================================================

# Zusammenfassungsstatistiken ausgeben
print(f"\nFILTERUNG ABGESCHLOSSEN!")
print(f"Anzahl der Tweets: {number_filtered_tweets}")
print(f"Anzahl der Benutzer IDs: {len(unique_user_ids)}")

# Analyse der Geo-Source Verteilung im gefilterten Datensatz
print(f"\n=== GEO-SOURCE VERTEILUNG IM GEFILTERTEN DATENSATZ ===")
filtered_geo_source_counts = {}
for tweet in combined_filtered_tweets:
    geo_source = tweet.get('geo_source', 'unknown')
    filtered_geo_source_counts[geo_source] = filtered_geo_source_counts.get(geo_source, 0) + 1

for source, count in sorted(filtered_geo_source_counts.items()):
    percentage = (count / number_filtered_tweets) * 100 if number_filtered_tweets > 0 else 0
    print(f"  {source}: {count} ({percentage:.1f}%)")

# Output-Verzeichnisse erstellen falls sie noch nicht existieren
os.makedirs(output_directory, exist_ok=True)
os.makedirs(log_directory, exist_ok=True)

# Ausgabedateipfade generieren
json_output_path = os.path.join(output_directory, 'filtered_tweets.json')
json_tweet_ids_path = os.path.join(output_directory, 'filtered_IDs.json')
log_path = os.path.join(log_directory, 'filter_log_all.txt')

# Speichere lesbares Log als TXT
print(f"\nSpeichere Filterlog in: {log_path}")
with open(log_path, 'w', encoding='utf-8') as log_file:
    log_file.write("GEOCOV19 FILTER LOG\n")
    log_file.write("=" * 50 + "\n\n")

    log_file.write(f"Eingabedateien (ZIP): {', '.join([os.path.basename(path) for path in dataset_paths])}\n\n")

    log_file.write("FILTERKRITERIEN:\n")
    log_file.write("- geo_source: coordinates oder place\n")
    log_file.write("- country_code: de\n")
    log_file.write("- state: erforderlich\n\n")

    log_file.write("ERGEBNISSE:\n")
    log_file.write(f"- Gefilterte Tweets: {number_filtered_tweets:,}\n")
    log_file.write(f"- Unique User IDs: {len(unique_user_ids):,}\n\n")

    log_file.write("GEO-SOURCE VERTEILUNG:\n")
    for source, count in sorted(filtered_geo_source_counts.items()):
        percentage = (count / number_filtered_tweets) * 100 if number_filtered_tweets > 0 else 0
        log_file.write(f"- {source}: {count:,} ({percentage:.1f}%)\n")

    log_file.write(f"\nAUSGABEDATEIEN:\n")
    log_file.write(f"- Tweets: {os.path.basename(json_output_path)}\n")
    log_file.write(f"- Tweet-IDs: {os.path.basename(json_tweet_ids_path)}\n")
    log_file.write(f"- Log: {os.path.basename(log_path)}\n")

# Gefilterte Tweets in JSON-Datei speichern
# Ein Tweet pro Zeile
print(f"Speichere gefilterte Tweets in: {json_output_path}")
with open(json_output_path, 'w', encoding='utf-8') as json_file:
    for tweet in combined_filtered_tweets:
        json_file.write(json.dumps(tweet, ensure_ascii=False) + '\n')

# Alle Tweet-IDs in JSON-Datei speichern
print(f"Speichere Tweet-IDs in: {json_tweet_ids_path}")
with open(json_tweet_ids_path, 'w', encoding='utf-8') as json_file:
    json.dump(all_tweet_ids, json_file, ensure_ascii=False, indent=2)

print(f"\nAlle Dateien erfolgreich gespeichert!")
print(f"Gefilterte Tweets: {json_output_path}")
print(f"Tweet-IDs: {json_tweet_ids_path}")
print(f"Filter-Log: {log_path}")
