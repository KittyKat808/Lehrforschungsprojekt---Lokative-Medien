import json
import pandas as pd
import plotly.graph_objects as go
from collections import Counter, defaultdict
import os
from datetime import datetime
import re

def normalize_hashtag(hashtag):
    """
    Normalisiert Hashtags zu Kategorien
    hashtag.lower wandelt in Kleinschreibung um
    Returns: (normalized_tag, category) oder (None, None) wenn nicht relevant
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


def parse_twitter_date(date_str):
    """Konvertiert Twitter-Datum in datetime-Objekt"""
    return datetime.strptime(date_str, '%a %b %d %H:%M:%S %z %Y')


def analyze_hashtag_trends(tweets, output_dir):
    """Analysiert zeitliche Trends von normalisierten Hashtags"""

    print("Analysiere Hashtag-Trends über Zeit...")

    # Datenstruktur: {normalized_hashtag: {date: count}}
    hashtag_timeline = defaultdict(lambda: defaultdict(int))
    category_timeline = defaultdict(lambda: defaultdict(int))

    # Alle Varianten tracken für Report
    hashtag_variants = defaultdict(set)

    processed = 0

    for tweet in tweets:
        try:
            date = parse_twitter_date(tweet['created_at']).date()
            hashtags = tweet.get('entities', {}).get('hashtags', [])

            for hashtag in hashtags:
                normalized, category = normalize_hashtag(hashtag)

                if normalized:
                    hashtag_timeline[normalized][date] += 1
                    category_timeline[category][date] += 1
                    hashtag_variants[normalized].add(hashtag)  # Original-Schreibweise behalten
                    processed += 1
        except:
            continue

    print(f"✓ {processed:,} relevante Hashtags gefunden\n")

    if processed == 0:
        print("⚠ Keine relevanten Hashtags gefunden. Analyse abgebrochen.")
        return

    # In DataFrames konvertieren
    dfs = {}
    for hashtag, dates in hashtag_timeline.items():
        df = pd.DataFrame(list(dates.items()), columns=['Datum', 'Anzahl'])
        df = df.sort_values('Datum')
        dfs[hashtag] = df

    # Output-Verzeichnis erstellen
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # --- TXT-REPORT ---
    txt_file = os.path.join(output_dir, f"hashtag_trends_{timestamp}.txt")
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write("ZEITLICHE ENTWICKLUNG VON CORONA-HASHTAGS\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Analysezeitpunkt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Analysierte Tweets: {len(tweets):,}\n")
        f.write(f"Relevante Hashtag-Vorkommen: {processed:,}\n\n")

        f.write("=" * 80 + "\n")
        f.write("ANALYSIERTE HASHTAG-KATEGORIEN\n")
        f.write("=" * 80 + "\n\n")
        f.write("Die folgenden Hashtags wurden zu 5 Hauptkategorien zusammengefasst:\n\n")
        f.write("1. FlattenTheCurve - Kampagne zur Verlangsamung der Infektionskurve\n")
        f.write("2. WirBleibenZuhause - Aufruf zum Zuhausebleiben (Stay Home)\n")
        f.write("3. SocialDistancing - Soziale Distanzierung als Schutzmaßnahme\n")
        f.write("4. Lockdown - Ausgangsbeschränkungen und Shutdown\n")
        f.write("5. Coronakrise - Framing der Pandemie als Krise\n\n")

        f.write("=" * 80 + "\n")
        f.write("GEFUNDENE HASHTAG-VARIANTEN\n")
        f.write("=" * 80 + "\n\n")
        f.write("Die folgenden Schreibweisen wurden automatisch normalisiert:\n\n")

        for normalized in sorted(hashtag_variants.keys()):
            variants = hashtag_variants[normalized]
            total = sum(hashtag_timeline[normalized].values())

            f.write(f"{normalized}:\n")
            f.write(f"  Anzahl Varianten: {len(variants)}\n")
            f.write(f"  Gefundene Schreibweisen: {', '.join(['#' + v for v in sorted(variants)])}\n")
            f.write(f"  Gesamt-Vorkommen: {total:,}\n\n")

        f.write("\n" + "=" * 80 + "\n")
        f.write("ZEITLICHE ENTWICKLUNG PRO HASHTAG\n")
        f.write("=" * 80 + "\n\n")

        for hashtag in sorted(hashtag_timeline.keys()):
            df = dfs[hashtag]
            total = df['Anzahl'].sum()
            peak_date = df.loc[df['Anzahl'].idxmax(), 'Datum']
            peak_count = df['Anzahl'].max()
            first_date = df['Datum'].min()
            last_date = df['Datum'].max()
            mean_daily = df['Anzahl'].mean()

            f.write(f"\n{hashtag.upper()}\n")
            f.write("-" * 80 + "\n")
            f.write(f"Gesamt-Vorkommen: {total:,}\n")
            f.write(f"Aktive Tage: {len(df)}\n")
            f.write(f"Zeitraum: {first_date} bis {last_date}\n")
            f.write(f"Peak-Tag: {peak_date} mit {peak_count:,} Tweets\n")
            f.write(f"Durchschnitt pro aktivem Tag: {mean_daily:.1f}\n")

            # Wochentagsanalyse
            df['Wochentag'] = pd.to_datetime(df['Datum']).dt.day_name()
            weekday_dist = df.groupby('Wochentag')['Anzahl'].sum()
            if not weekday_dist.empty:
                top_weekday = weekday_dist.idxmax()
                weekday_mapping = {
                    'Monday': 'Montag', 'Tuesday': 'Dienstag', 'Wednesday': 'Mittwoch',
                    'Thursday': 'Donnerstag', 'Friday': 'Freitag', 'Saturday': 'Samstag',
                    'Sunday': 'Sonntag'
                }
                f.write(f"Aktivster Wochentag: {weekday_mapping.get(top_weekday, top_weekday)}\n")

        f.write("\n\n" + "=" * 80 + "\n")
        f.write("VERGLEICHENDE STATISTIK\n")
        f.write("=" * 80 + "\n\n")

        # Ranking nach Gesamtvorkommen
        rankings = []
        for hashtag, df in dfs.items():
            total = df['Anzahl'].sum()
            rankings.append((hashtag, total))
        rankings.sort(key=lambda x: x[1], reverse=True)

        f.write("Ranking nach Gesamthäufigkeit:\n")
        for idx, (hashtag, total) in enumerate(rankings, 1):
            percentage = (total / processed) * 100
            f.write(f"  {idx}. {hashtag}: {total:,} ({percentage:.1f}% aller relevanten Hashtags)\n")

        f.write("\n\n" + "=" * 80 + "\n")
        f.write("INTERPRETATION\n")
        f.write("=" * 80 + "\n\n")

        f.write("Die zeitliche Analyse zeigt, wann bestimmte Hashtags/Kampagnen\n")
        f.write("in Deutschland viral gingen:\n\n")

        # Sortiere nach Peak-Datum
        peaks = []
        for hashtag, df in dfs.items():
            peak_date = df.loc[df['Anzahl'].idxmax(), 'Datum']
            peak_count = df['Anzahl'].max()
            peaks.append((peak_date, hashtag, peak_count))

        peaks.sort()

        f.write("Chronologische Reihenfolge der Peaks:\n")
        for peak_date, hashtag, peak_count in peaks:
            weekday = pd.to_datetime(peak_date).strftime('%A, %d.%m.%Y')
            f.write(f"  {weekday}: #{hashtag} ({peak_count:,} Tweets)\n")

        f.write("\n\nDie Peaks zeigen, wie sich verschiedene Narrative und Kampagnen\n")
        f.write("zeitlich entwickelt haben. Frühe Peaks deuten auf schnelle Adoption hin,\n")
        f.write("während spätere Peaks möglicherweise auf externe Events reagieren\n")
        f.write("(z.B. politische Entscheidungen, Medienberichte).\n")

    print(f"✓ TXT-Report: {txt_file}")

    # --- VISUALISIERUNG 1: Alle Hashtags in einem Plot ---
    fig = go.Figure()

    colors = {
        'FlattenTheCurve': '#e74c3c',
        'WirBleibenZuhause': '#3498db',
        'SocialDistancing': '#2ecc71',
        'Lockdown': '#f39c12',
        'Coronakrise': '#9b59b6'
    }

    for hashtag, df in sorted(dfs.items()):
        fig.add_trace(go.Scatter(
            x=df['Datum'],
            y=df['Anzahl'],
            mode='lines+markers',
            name=f'#{hashtag}',
            line=dict(width=3, color=colors.get(hashtag, '#95a5a6')),
            marker=dict(size=5),
            hovertemplate='<b>%{fullData.name}</b><br>Datum: %{x}<br>Anzahl: %{y}<extra></extra>'
        ))

    fig.update_layout(
        title='Zeitliche Entwicklung relevanter Corona-Hashtags',
        xaxis_title='Datum',
        yaxis_title='Anzahl Tweets pro Tag',
        height=600,
        hovermode='x unified',
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(255,255,255,0.8)"
        ),
        plot_bgcolor='#f8f9fa'
    )

    html_file = os.path.join(output_dir, f"hashtag_trends_combined_{timestamp}.html")
    fig.write_html(html_file)
    print(f"✓ Visualisierung (kombiniert): {html_file}")

    # --- VISUALISIERUNG 2: Separate Plots für jeden Hashtag ---
    for hashtag in sorted(dfs.keys()):
        df = dfs[hashtag]

        fig_single = go.Figure()
        fig_single.add_trace(go.Bar(
            x=df['Datum'],
            y=df['Anzahl'],
            marker_color=colors.get(hashtag, 'steelblue'),
            hovertemplate='<b>%{x}</b><br>Tweets: %{y}<extra></extra>'
        ))

        # Peak markieren
        peak_idx = df['Anzahl'].idxmax()
        peak_date = df.loc[peak_idx, 'Datum']
        peak_count = df.loc[peak_idx, 'Anzahl']

        fig_single.add_annotation(
            x=peak_date,
            y=peak_count,
            text=f"Peak: {pd.to_datetime(peak_date).strftime('%d. %b')}<br>{peak_count:,} Tweets",
            showarrow=True,
            arrowhead=2,
            arrowcolor=colors.get(hashtag, 'steelblue'),
            ax=0,
            ay=-50,
            bgcolor="white",
            bordercolor=colors.get(hashtag, 'steelblue'),
            borderwidth=2,
            font=dict(size=11)
        )

        # Durchschnittslinie
        mean_val = df['Anzahl'].mean()
        fig_single.add_hline(
            y=mean_val,
            line_dash="dash",
            line_color="gray",
            annotation_text=f"Durchschnitt: {mean_val:.1f}",
            annotation_position="right"
        )

        fig_single.update_layout(
            title=f'#{hashtag} - Zeitlicher Verlauf',
            xaxis_title='Datum',
            yaxis_title='Anzahl Tweets',
            height=500,
            plot_bgcolor='#f8f9fa'
        )

        html_single = os.path.join(output_dir, f"trend_{hashtag.lower()}_{timestamp}.html")
        fig_single.write_html(html_single)
        print(f"✓ Einzelplot: {html_single}")

    print(f"\n{'=' * 60}")
    print("HASHTAG-TREND-ANALYSE ABGESCHLOSSEN!")
    print(f"{'=' * 60}\n")
    print(f"Erstellt: 1 TXT-Report, 1 Kombinationsplot, {len(dfs)} Einzelplots")


def main():
    input_file = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\Cleaned_Data.jsonl"
    output_dir = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\Hashtags"

    tweets = load_tweets(input_file)
    analyze_hashtag_trends(tweets, output_dir)


if __name__ == "__main__":
    main()