import json
import pandas as pd
from collections import Counter, defaultdict
import re


def normalize_hashtag(hashtag):
    """
    Normalisiert Hashtags zu Kategorien - IDENTISCH zur Hauptanalyse
    """
    tag_lower = hashtag.lower().replace('_', '').replace('-', '').replace(' ', '').replace('ー', '')

    # Ausschlussliste - diese Hashtags werden NICHT kategorisiert
    excluded = ['aviationlockdownnow', 'ausgangssperrejetzt', 'ausgangssperreüberfällig',
                'endthelockdown', 'lockdownend',
                'trotzabstandhaltenwirzusammen', 'friendlydistancing']

    if tag_lower in excluded:
        return None, None

    # 1. FlattenTheCurve Varianten
    if any(x in tag_lower for x in ['flattenthecurve', 'flatenthecurve', 'flatthecurve',
                                    'kurveflachen', 'kurveabflachen', 'diekurveflachen']):
        return 'FlattenTheCurve', 'Gesundheitsmaßnahmen'

    # 2. Stay Home / Bleibt Zuhause Varianten
    if any(x in tag_lower for x in ['wirbleibenzuhause', 'bleibtzuhause', 'bleibzuhause',
                                    'ichbleibezuhause', 'bleibtdaheim', 'bleibtheim',
                                    'zuhausebleiben', 'daheimbleiben',
                                    'stayhome', 'stayathome', 'stayinghome',
                                    'stayindoors', 'stayinside',
                                    'wirbleibendaheim', 'ichbleibedaheim']):
        return 'WirBleibenZuhause', 'Solidarität'

    # 3. Social Distancing Varianten
    if any(x in tag_lower for x in ['socialdistancing', 'socialdistance', 'socialdist',
                                    'physicaldistancing', 'physicaldistance',
                                    'sozialedistanzierung', 'sozialedistanz',
                                    'abstandhalten', 'abstandhalte', 'keepdistance',
                                    'distancing', 'distanz']):
        return 'SocialDistancing', 'Gesundheitsmaßnahmen'

    # 4. Lockdown Varianten
    if any(x in tag_lower for x in ['lockdown', 'coronalockdown', 'covidlockdown',
                                    'shutdown', 'ausgangssperre', 'ausgangsbeschränkung', 'ausgangsverbot',
                                    'kontaktsperre', 'kontaktverbot', 'kontaktbeschränkung']):
        return 'Lockdown', 'Maßnahmen'

    # 5. Coronakrise Varianten
    if any(x in tag_lower for x in ['coronakrise', 'coronacrisis', 'covidkrise', 'covidcrisis',
                                    'coronaviruskrise', 'coronaviruscrisis',
                                    'covid19krise', 'covid19crisis']):
        return 'Coronakrise', 'Framing'

    return None, None


def analyze_hashtag_variants(input_file, output_file):
    """
    Analysiert alle im Datensatz vorkommenden Hashtag-Varianten
    und gruppiert sie nach den definierten Kategorien
    """
    print("=" * 80)
    print("ANALYSE DER HASHTAG-VARIANTEN IM DATENSATZ")
    print("=" * 80)
    print(f"\nLade Daten aus: {input_file}\n")

    # Datenstrukturen
    category_variants = defaultdict(lambda: defaultdict(int))  # {category: {original_hashtag: count}}
    all_hashtags = Counter()  # Alle Hashtags zählen

    tweet_count = 0
    hashtag_count = 0

    # Tweets durchgehen
    with open(input_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if line_num % 10000 == 0:
                print(f"  Verarbeite Zeile {line_num:,}...")

            try:
                tweet = json.loads(line.strip())
                tweet_count += 1

                hashtags = tweet.get('entities', {}).get('hashtags', [])

                for hashtag in hashtags:
                    original_tag = hashtag  # Originalschreibweise
                    all_hashtags[original_tag] += 1
                    hashtag_count += 1

                    # Prüfen, ob Hashtag zu einer Kategorie gehört
                    normalized, category = normalize_hashtag(original_tag)

                    if normalized:
                        category_variants[normalized][original_tag] += 1

            except Exception as e:
                continue

    print(f"\n✓ {tweet_count:,} Tweets analysiert")
    print(f"✓ {hashtag_count:,} Hashtags gefunden")
    print(f"✓ {len(all_hashtags):,} einzigartige Hashtags\n")

    # Top 100 Hashtags berechnen
    top_100_hashtags = all_hashtags.most_common(100)

    # Ergebnisse speichern
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 100 + "\n")
        f.write("HASHTAG-VARIANTEN ANALYSE\n")
        f.write("=" * 100 + "\n\n")

        f.write(f"Anzahl Tweets: {tweet_count:,}\n")
        f.write(f"Anzahl Hashtags (gesamt): {hashtag_count:,}\n")
        f.write(f"Einzigartige Hashtags: {len(all_hashtags):,}\n\n")

        # Top 100 Hashtags
        f.write("=" * 100 + "\n")
        f.write("TOP 100 HASHTAGS IM DATENSATZ\n")
        f.write("=" * 100 + "\n\n")

        f.write(f"{'Rang':<6} {'Hashtag':<50} {'Anzahl':<12} {'Anteil'}\n")
        f.write("-" * 100 + "\n")

        for rank, (hashtag, count) in enumerate(top_100_hashtags, 1):
            percentage = (count / hashtag_count) * 100
            f.write(f"{rank:<6} #{hashtag:<49} {count:<12,} {percentage:>6.2f}%\n")

        f.write("\n\n")

        f.write("=" * 100 + "\n")
        f.write("KATEGORISIERTE HASHTAG-VARIANTEN\n")
        f.write("=" * 100 + "\n\n")

        # Für jede Kategorie
        for idx, (normalized, variants) in enumerate(sorted(category_variants.items()), 1):
            total_count = sum(variants.values())
            num_variants = len(variants)

            f.write("\n" + "=" * 100 + "\n")
            f.write(f"KATEGORIE: #{normalized}\n")
            f.write("=" * 100 + "\n\n")

            f.write(f"Anzahl unterschiedlicher Schreibweisen: {num_variants}\n")
            f.write(f"Gesamtvorkommen: {total_count:,}\n\n")

            f.write(f"{'Rang':<6} {'Original-Hashtag':<50} {'Häufigkeit':<12} {'Anteil'}\n")
            f.write("-" * 100 + "\n")

            # Varianten nach Häufigkeit sortieren
            sorted_variants = sorted(variants.items(), key=lambda x: x[1], reverse=True)

            for rank, (variant, count) in enumerate(sorted_variants, 1):
                percentage = (count / total_count) * 100
                f.write(f"{rank:<6} #{variant:<49} {count:<12,} {percentage:>6.2f}%\n")

            f.write("\n")

        # Zusammenfassung
        f.write("\n" + "=" * 100 + "\n")
        f.write("ZUSAMMENFASSUNG\n")
        f.write("=" * 100 + "\n\n")

        total_categorized = sum(sum(variants.values()) for variants in category_variants.values())
        percentage_categorized = (total_categorized / hashtag_count) * 100

        f.write(f"Gesamt-Hashtags im Datensatz: {hashtag_count:,}\n")
        f.write(f"Kategorisierte Hashtags: {total_categorized:,} ({percentage_categorized:.2f}%)\n")
        f.write(f"Nicht kategorisierte Hashtags: {hashtag_count - total_categorized:,}\n\n")

        f.write("VERTEILUNG NACH KATEGORIEN\n")
        f.write("-" * 100 + "\n\n")

        rankings = []
        for normalized, variants in category_variants.items():
            total = sum(variants.values())
            num_variants = len(variants)
            rankings.append((normalized, total, num_variants))

        rankings.sort(key=lambda x: x[1], reverse=True)

        f.write(f"{'Rang':<6} {'Kategorie':<30} {'Varianten':<12} {'Vorkommen':<15} {'Anteil'}\n")
        f.write("-" * 100 + "\n")

        for rank, (normalized, total, num_variants) in enumerate(rankings, 1):
            percentage = (total / total_categorized) * 100
            f.write(f"{rank:<6} #{normalized:<29} {num_variants:<12} {total:<15,} {percentage:>6.2f}%\n")

    print(f"✓ Analyse abgeschlossen!")
    print(f"✓ Ergebnisse gespeichert in: {output_file}\n")

    # Konsolenausgabe - Top 20 Hashtags
    print("=" * 80)
    print("TOP 20 HASHTAGS IM DATENSATZ")
    print("=" * 80)
    print(f"\n{'Rang':<6} {'Hashtag':<45} {'Anzahl'}")
    print("-" * 80)

    for rank, (hashtag, count) in enumerate(top_100_hashtags[:20], 1):
        print(f"{rank:<6} #{hashtag:<44} {count:,}")

    if len(top_100_hashtags) > 20:
        print(f"\n... und {len(top_100_hashtags) - 20} weitere (siehe Ausgabedatei)\n")

    # Konsolenausgabe - Übersicht der Kategorien
    print("=" * 80)
    print("ÜBERSICHT DER GEFUNDENEN VARIANTEN")
    print("=" * 80)

    for normalized, variants in sorted(category_variants.items()):
        total = sum(variants.values())
        print(f"\n#{normalized}: {len(variants)} Varianten, {total:,} Vorkommen")

        # Top 5 anzeigen
        sorted_variants = sorted(variants.items(), key=lambda x: x[1], reverse=True)
        for variant, count in sorted_variants[:5]:
            print(f"  • #{variant}: {count:,}")

        if len(sorted_variants) > 5:
            print(f"  ... und {len(sorted_variants) - 5} weitere")


def main():
    input_file = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\Cleaned_Data.jsonl"
    output_file = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\Hashtags\Hashtag_Varianten_Dokumentation.txt"
    analyze_hashtag_variants(input_file, output_file)


if __name__ == "__main__":
    main()