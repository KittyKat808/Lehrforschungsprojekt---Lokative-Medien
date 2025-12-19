# ANMERKUNG: Code, um Liste der Tweet IDs in zwei Datensätze mit jeweils 10.000 Tweets aufzuteilen.

import os
import json

# =============================================================================
# INPUT UND OUTPUT PFADE DEFINIEREN - HIER EIGENE PFADE ANPASSEN!
# =============================================================================

# Input-Verzeichnis definieren
input_file_path = r'C:\Users\[NUTZERNAME]\[ORDNERNAME]\filtered_tweet_ids_sample_20k.json'

# Output-Verzeichnisse definieren
output_file_path_1 = r'C:\Users\[NUTZERNAME]\[ORDNERNAME]\tweet_ids-split1.json'
output_file_path_2 = r'C:\Users\[NUTZERNAME]\[ORDNERNAME]\tweet_ids-split2.json'
# =============================================================================

# Tweet IDs des Input files einlesen
with open(input_file_path, 'r', encoding='utf-8') as input_file:
    tweet_ids = json.load(input_file)

# Liste der Tweet IDs in zwei Hälften teilen
half_length = len(tweet_ids) // 2
first_half = tweet_ids[:half_length]
second_half = tweet_ids[half_length:]

# Erste Hälfte in einem neuen JSON speichern
with open(output_file_path_1, 'w', encoding='utf-8') as output_file_1:
    json.dump(first_half, output_file_1, ensure_ascii=False, indent=2)

# Zweite Hälfte in einem neuen JSON speichern
with open(output_file_path_2, 'w', encoding='utf-8') as output_file_2:
    json.dump(second_half, output_file_2, ensure_ascii=False, indent=2)

print("Tweet IDs aufgeteilt und gespeichert.")
