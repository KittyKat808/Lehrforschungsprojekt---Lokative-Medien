import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import os
from collections import Counter


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
    # Twitter Format: "Sat Feb 01 17:11:42 +0000 2020"
    return datetime.strptime(date_str, '%a %b %d %H:%M:%S %z %Y')


def create_temporal_analysis(tweets, output_dir):
    """Erstellt zeitliche Analysen"""

    print("Erstelle zeitliche Analysen...")

    # Timestamps extrahieren und parsen
    dates = []
    for tweet in tweets:
        try:
            date = parse_twitter_date(tweet['created_at'])
            dates.append(date)
        except:
            continue

    print(f"✓ {len(dates)} Tweets mit gültigem Datum\n")

    # DataFrame erstellen
    df = pd.DataFrame({'timestamp': dates})
    df['date'] = df['timestamp'].dt.date
    df['week'] = df['timestamp'].dt.to_period('W')
    df['month'] = df['timestamp'].dt.to_period('M')
    df['weekday'] = df['timestamp'].dt.day_name()
    df['hour'] = df['timestamp'].dt.hour

    # Ausgabe-Verzeichnis erstellen
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # --- TÄGLICHE TWEETS ZÄHLEN ---
    daily_counts = df['date'].value_counts().sort_index()
    daily_df = pd.DataFrame({
        'Datum': daily_counts.index,
        'Anzahl_Tweets': daily_counts.values
    })

    # --- WÖCHENTLICHE TWEETS ZÄHLEN ---
    weekly_counts = df['week'].value_counts().sort_index()
    weekly_df = pd.DataFrame({
        'Woche': [str(w) for w in weekly_counts.index],
        'Anzahl_Tweets': weekly_counts.values
    })

    # --- PEAK ANALYSEN ---
    # Top 10 Tage
    top_days = daily_df.nlargest(10, 'Anzahl_Tweets')

    # Top 5 Wochen
    top_weeks = weekly_df.nlargest(5, 'Anzahl_Tweets')

    # Statistiken
    mean_daily = daily_df['Anzahl_Tweets'].mean()
    median_daily = daily_df['Anzahl_Tweets'].median()
    std_daily = daily_df['Anzahl_Tweets'].std()

    mean_weekly = weekly_df['Anzahl_Tweets'].mean()
    median_weekly = weekly_df['Anzahl_Tweets'].median()

    # Zeitraum
    start_date = df['date'].min()
    end_date = df['date'].max()
    total_days = (end_date - start_date).days + 1

    # --- TXT-REPORT ERSTELLEN ---
    txt_file = os.path.join(output_dir, f"zeitliche_analyse_{timestamp}.txt")
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write("ZEITLICHE ANALYSE DER CORONA-TWEETS\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Analysezeitpunkt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Gesamtzahl Tweets: {len(tweets):,}\n")
        f.write(f"Tweets mit gültigem Datum: {len(dates):,}\n\n")

        f.write("=" * 80 + "\n")
        f.write("ZEITRAUM\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Start: {start_date}\n")
        f.write(f"Ende: {end_date}\n")
        f.write(f"Dauer: {total_days} Tage\n")
        f.write(f"Anzahl Wochen: {len(weekly_df)}\n\n")

        f.write("=" * 80 + "\n")
        f.write("STATISTIKEN (TÄGLICH)\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Durchschnitt pro Tag: {mean_daily:,.2f} Tweets\n")
        f.write(f"Median pro Tag: {median_daily:,.0f} Tweets\n")
        f.write(f"Standardabweichung: {std_daily:,.2f}\n")
        f.write(f"Minimum: {daily_df['Anzahl_Tweets'].min():,} Tweets\n")
        f.write(f"Maximum: {daily_df['Anzahl_Tweets'].max():,} Tweets\n\n")

        f.write("=" * 80 + "\n")
        f.write("STATISTIKEN (WÖCHENTLICH)\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Durchschnitt pro Woche: {mean_weekly:,.2f} Tweets\n")
        f.write(f"Median pro Woche: {median_weekly:,.0f} Tweets\n\n")

        f.write("=" * 80 + "\n")
        f.write("TOP 10 TAGE MIT DEN MEISTEN TWEETS\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"{'Rang':<6} {'Datum':<15} {'Anzahl Tweets':<15} {'% vom Durchschnitt':<20} {'Wochentag':<12}\n")
        f.write("-" * 80 + "\n")

        for idx, (_, row) in enumerate(top_days.iterrows(), 1):
            datum = row['Datum']
            anzahl = row['Anzahl_Tweets']
            prozent = (anzahl / mean_daily) * 100
            wochentag = pd.to_datetime(datum).day_name()
            f.write(f"{idx:<6} {str(datum):<15} {anzahl:<15,} {prozent:>6.1f}% {wochentag:<12}\n")

        f.write("\n" + "=" * 80 + "\n")
        f.write("TOP 5 WOCHEN MIT DEN MEISTEN TWEETS\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"{'Rang':<6} {'Woche':<20} {'Anzahl Tweets':<15} {'% vom Durchschnitt':<20}\n")
        f.write("-" * 80 + "\n")

        for idx, (_, row) in enumerate(top_weeks.iterrows(), 1):
            woche = row['Woche']
            anzahl = row['Anzahl_Tweets']
            prozent = (anzahl / mean_weekly) * 100
            f.write(f"{idx:<6} {woche:<20} {anzahl:<15,} {prozent:>6.1f}%\n")

        # Wochentags-Analyse
        weekday_counts = df['weekday'].value_counts()
        weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        weekday_counts = weekday_counts.reindex(weekday_order)

        f.write("\n" + "=" * 80 + "\n")
        f.write("VERTEILUNG NACH WOCHENTAGEN\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"{'Wochentag':<15} {'Anzahl Tweets':<15} {'Durchschnitt/Tag':<20}\n")
        f.write("-" * 80 + "\n")

        weekday_mapping = {
            'Monday': 'Montag',
            'Tuesday': 'Dienstag',
            'Wednesday': 'Mittwoch',
            'Thursday': 'Donnerstag',
            'Friday': 'Freitag',
            'Saturday': 'Samstag',
            'Sunday': 'Sonntag'
        }

        for day_en, count in weekday_counts.items():
            day_de = weekday_mapping[day_en]
            num_days = len(df[df['weekday'] == day_en]['date'].unique())
            avg_per_day = count / num_days if num_days > 0 else 0
            f.write(f"{day_de:<15} {count:<15,} {avg_per_day:>6.1f}\n")

        # Interpretation
        f.write("\n\n" + "=" * 80 + "\n")
        f.write("INTERPRETATION\n")
        f.write("=" * 80 + "\n\n")

        f.write("1. PEAKS:\n")
        peak_day = top_days.iloc[0]
        f.write(f"   - Der aktivste Tag war {peak_day['Datum']} mit {peak_day['Anzahl_Tweets']:,} Tweets\n")
        f.write(f"   - Das sind {(peak_day['Anzahl_Tweets'] / mean_daily):.1f}x mehr als der Durchschnitt\n")

        peak_week = top_weeks.iloc[0]
        f.write(f"\n   - Die aktivste Woche war {peak_week['Woche']} mit {peak_week['Anzahl_Tweets']:,} Tweets\n")

        f.write("\n2. VARIABILITÄT:\n")
        cv = (std_daily / mean_daily) * 100  # Variationskoeffizient
        f.write(f"   - Variationskoeffizient: {cv:.1f}%\n")
        if cv > 50:
            f.write("   - Hohe Schwankung: Die Tweet-Aktivität variiert stark über die Zeit\n")
        elif cv > 30:
            f.write("   - Moderate Schwankung: Die Tweet-Aktivität zeigt mittlere Variabilität\n")
        else:
            f.write("   - Geringe Schwankung: Die Tweet-Aktivität ist relativ konstant\n")

        f.write("\n3. WOCHENTAGS-MUSTER:\n")
        max_weekday = weekday_counts.idxmax()
        min_weekday = weekday_counts.idxmin()
        f.write(f"   - Aktivster Wochentag: {weekday_mapping[max_weekday]} ({weekday_counts[max_weekday]:,} Tweets)\n")
        f.write(f"   - Ruhigster Wochentag: {weekday_mapping[min_weekday]} ({weekday_counts[min_weekday]:,} Tweets)\n")

    print(f"✓ TXT-Report: {txt_file}")

    # --- VISUALISIERUNG 1: TÄGLICHE TWEETS MIT PEAK-MARKIERUNG ---
    # Top 5 Peak-Tage identifizieren
    top_5_dates = set(top_days.head(5)['Datum'])

    # Farben für Balken: Peak-Tage rot, normale Tage blau
    colors = ['#e74c3c' if date in top_5_dates else 'steelblue' for date in daily_df['Datum']]

    fig1 = go.Figure()
    fig1.add_trace(go.Bar(
        x=daily_df['Datum'],
        y=daily_df['Anzahl_Tweets'],
        marker_color=colors,
        hovertemplate='<b>%{x}</b><br>Tweets: %{y:,}<extra></extra>'
    ))

    # Durchschnittslinie hinzufügen
    fig1.add_hline(
        y=mean_daily,
        line_dash="dash",
        line_color="orange",
        annotation_text=f"Durchschnitt: {mean_daily:,.0f}",
        annotation_position="right"
    )

    # Annotationen für Top 5 Peak-Tage - vertikaler Text nahe der X-Achse
    # Finde die niedrigste Y-Position für alle Labels (gleiche Höhe)
    label_y_position = mean_daily * 0.6  # Unter der Durchschnittslinie, näher an X-Achse

    for idx, (_, row) in enumerate(top_days.head(5).iterrows(), 1):
        datum = row['Datum']
        datum_formatted = pd.to_datetime(datum).strftime('%b %d')

        fig1.add_annotation(
            x=datum,
            y=label_y_position,  # Alle auf gleicher Höhe
            text=f"<b>{datum_formatted}</b>",
            showarrow=False,
            font=dict(size=14, color="black", family="Arial Black"),
            textangle=-90  # Vertikaler Text
        )

    fig1.update_layout(
        title='Tweet-Aktivität pro Tag <br><sub>Top 5 Peak-Tage in Rot markiert</sub>',
        xaxis_title='Datum',
        yaxis_title='Anzahl Tweets',
        height=600,
        hovermode='x unified'
    )


    html_file1 = os.path.join(output_dir, f"tweets_pro_tag_{timestamp}.html")
    fig1.write_html(html_file1)
    print(f"✓ Visualisierung (täglich): {html_file1}")


def main():
    input_file = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\Cleaned_Data.jsonl"
    output_dir = r"C:\Users\k[NUTZERNAME]\[ORDNERNAME]\Zeitliche Analyse"

    tweets = load_tweets(input_file)
    create_temporal_analysis(tweets, output_dir)

    print("\n" + "=" * 60)
    print("ZEITLICHE ANALYSE ABGESCHLOSSEN!")
    print("=" * 60)
    print(f"Interaktive HTML-Datei und 1 TXT-Report erstellt.")
    print(f"Öffne sie im Browser: {output_dir}\n")


if __name__ == "__main__":
    main()
