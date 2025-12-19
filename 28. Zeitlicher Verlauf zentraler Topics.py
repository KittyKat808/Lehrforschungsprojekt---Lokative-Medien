import json
import pandas as pd
import plotly.graph_objects as go
from collections import defaultdict
import os
from datetime import datetime
from gensim import corpora
from gensim.models import LdaModel


def parse_twitter_date(date_str):
    """Konvertiert Twitter-Datum in datetime-Objekt"""
    return datetime.strptime(date_str, '%a %b %d %H:%M:%S %z %Y')


def main():
    # Pfade
    model_dir = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\LDA\final_14_topics"
    input_file = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\Cleaned_Data.jsonl"
    stopwords_file = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\corona_stopwords.txt"
    spacy_stopwords_file = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\spacy_stopwords_deutsch.txt"
    output_dir = r"C:\Users\katri\[NUTZERNAME]\[ORDNERNAME]\LDA\zeitliche_analyse"

    os.makedirs(output_dir, exist_ok=True)

    print("=" * 70)
    print("ZEITLICHE ANALYSE DER 6 AUSGEWÄHLTEN TOPICS")
    print("=" * 70)

    # Die 6 ausgewählten Topics (Modell-Nummerierung 0-13)
    SELECTED_TOPICS = {
        0: "Gesellschaftspolitische Reflexion",
        2: "Soziale Distanzierung",
        5: "Maskenpflicht",
        6: "Wirtschaftliche Lage & Finanzielle Unterstützung",
        9: "Hashtag-Kampagnen & Solidarität",
        11: "Regionales Infektionsgeschehen"
    }

    # Mapping für Darstellung (Modell → Darstellung)
    TOPIC_DISPLAY = {0: 1, 2: 3, 5: 6, 6: 7, 9: 10, 11: 12}

    # 1. Modell laden
    print("\n[1/5] Lade Modell...")
    model_file = os.path.join(model_dir, "lda_model_14_topics_20251124_235500")
    lda_model = LdaModel.load(model_file)
    print("✓ Modell geladen")

    # 2. Tweets laden
    print("\n[2/5] Lade Tweets...")
    tweets = []
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            tweets.append(json.loads(line))
    print(f"✓ {len(tweets):,} Tweets geladen")

    # 3. Stopwörter und Preprocessing
    print("\n[3/5] Preprocessing...")
    with open(stopwords_file, 'r', encoding='utf-8') as f:
        corona_stopwords = set([line.strip().lower() for line in f if line.strip()])

    with open(spacy_stopwords_file, 'r', encoding='utf-8') as f:
        spacy_stopwords = set([
            line.strip().lower() for line in f
            if line.strip() and not line.startswith('#')
        ])

    all_stopwords = corona_stopwords | spacy_stopwords

    documents = []
    valid_tweets = []

    for tweet in tweets:
        filtered_tokens = [
            token for token in tweet['tokens']
            if token.lower() not in all_stopwords
               and len(token) > 2
               and not token.isnumeric()
        ]
        if len(filtered_tokens) > 0:
            documents.append(filtered_tokens)
            valid_tweets.append(tweet)

    print(f"✓ {len(valid_tweets):,} verwendbare Tweets")

    # Dictionary und Corpus
    dictionary = corpora.Dictionary(documents)
    dictionary.filter_extremes(no_below=5, no_above=0.5, keep_n=10000)
    corpus = [dictionary.doc2bow(doc) for doc in documents]

    # 4. Zeitliche Zuordnung
    print("\n[4/5] Weise Topics zu und analysiere zeitlich...")

    # Datenstruktur: {topic_id: {date: count}}
    topic_timeline = {topic_id: defaultdict(int) for topic_id in SELECTED_TOPICS.keys()}

    total_tweets = 0
    analyzed_tweets = 0

    for idx, doc_bow in enumerate(corpus):
        if idx % 10000 == 0 and idx > 0:
            print(f"  Verarbeitet: {idx:,} Tweets...")

        total_tweets += 1

        # Finde dominantes Topic (aus ALLEN 14)
        topic_dist = lda_model.get_document_topics(doc_bow, minimum_probability=0.0)
        if not topic_dist:
            continue

        dominant_topic, prob = max(topic_dist, key=lambda x: x[1])

        # Nur wenn es eines der 6 ausgewählten ist
        if dominant_topic in SELECTED_TOPICS:
            analyzed_tweets += 1

            # Datum extrahieren
            try:
                date = parse_twitter_date(valid_tweets[idx]['created_at']).date()
                topic_timeline[dominant_topic][date] += 1
            except:
                continue

    print(
        f"\n✓ Analysierte Tweets: {analyzed_tweets:,} / {total_tweets:,} ({analyzed_tweets / total_tweets * 100:.1f}%)")

    # In DataFrames konvertieren
    print("\n[5/5] Erstelle Visualisierungen...")

    dfs = {}
    for topic_id, dates in topic_timeline.items():
        df = pd.DataFrame(list(dates.items()), columns=['Datum', 'Anzahl'])
        df = df.sort_values('Datum')

        # Wöchentliche Aggregation - Explizite Montag-Berechnung
        df_temp = df.copy()
        df_temp['Datum_dt'] = pd.to_datetime(df_temp['Datum'])

        # Berechne den Montag für jedes Datum
        # dayofweek: Montag=0, Dienstag=1, ..., Sonntag=6
        df_temp['Montag'] = df_temp['Datum_dt'] - pd.to_timedelta(
            df_temp['Datum_dt'].dt.dayofweek, unit='D'
        )

        # Gruppiere nach Montag und summiere
        weekly = df_temp.groupby('Montag')['Anzahl'].sum().reset_index()
        weekly.columns = ['Datum', 'Anzahl']

        # Stelle sicher, dass Datum als datetime64 ist
        weekly['Datum'] = pd.to_datetime(weekly['Datum'])

        dfs[topic_id] = weekly

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # --- TXT-REPORT ---
    txt_file = os.path.join(output_dir, f'zeitliche_entwicklung_{timestamp}.txt')

    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("ZEITLICHE ENTWICKLUNG DER 6 AUSGEWÄHLTEN TOPICS\n")
        f.write(f"Erstellt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Gesamtanzahl Tweets: {total_tweets:,}\n")
        f.write(
            f"Analysierte Tweets (dominantes Topic in Auswahl): {analyzed_tweets:,} ({analyzed_tweets / total_tweets * 100:.1f}%)\n")
        f.write(
            f"Zeitraum: {min(min(df['Datum']) for df in dfs.values())} bis {max(max(df['Datum']) for df in dfs.values())}\n")
        f.write(f"Aggregation: Wöchentlich\n\n")

        f.write("=" * 80 + "\n")
        f.write("STATISTIK PRO TOPIC\n")
        f.write("=" * 80 + "\n\n")

        for topic_id in sorted(SELECTED_TOPICS.keys()):
            df = dfs[topic_id]
            topic_label = SELECTED_TOPICS[topic_id]
            display_id = TOPIC_DISPLAY[topic_id]

            total = df['Anzahl'].sum()
            peak_idx = df['Anzahl'].idxmax()
            peak_date = df.loc[peak_idx, 'Datum']
            peak_count = df.loc[peak_idx, 'Anzahl']
            mean_weekly = df['Anzahl'].mean()

            f.write(f"\nTOPIC {display_id}: {topic_label}\n")
            f.write("-" * 80 + "\n")
            f.write(f"Gesamt-Tweets: {total:,} ({total / analyzed_tweets * 100:.1f}% der analysierten Tweets)\n")
            f.write(f"Aktive Wochen: {len(df)}\n")
            f.write(f"Peak-Woche: {pd.to_datetime(peak_date).strftime('%d. %B %Y')} mit {peak_count:,} Tweets\n")
            f.write(f"Durchschnitt pro Woche: {mean_weekly:.1f} Tweets\n")

        f.write("\n\n" + "=" * 80 + "\n")
        f.write("VERGLEICHENDE STATISTIK\n")
        f.write("=" * 80 + "\n\n")

        # Ranking nach Gesamtvorkommen
        rankings = []
        for topic_id, df in dfs.items():
            total = df['Anzahl'].sum()
            rankings.append((TOPIC_DISPLAY[topic_id], SELECTED_TOPICS[topic_id], total))
        rankings.sort(key=lambda x: x[2], reverse=True)

        f.write("Ranking nach Gesamthäufigkeit:\n")
        for idx, (display_id, topic_label, total) in enumerate(rankings, 1):
            percentage = (total / analyzed_tweets) * 100
            f.write(f"  {idx}. Topic {display_id} ({topic_label}): {total:,} Tweets ({percentage:.1f}%)\n")

        f.write("\n\nChronologische Reihenfolge der Peaks:\n")
        peaks = []
        for topic_id, df in dfs.items():
            peak_idx = df['Anzahl'].idxmax()
            peak_date = df.loc[peak_idx, 'Datum']
            peak_count = df.loc[peak_idx, 'Anzahl']
            peaks.append((peak_date, TOPIC_DISPLAY[topic_id], SELECTED_TOPICS[topic_id], peak_count))

        peaks.sort()

        for peak_date, display_id, topic_label, peak_count in peaks:
            weekday = pd.to_datetime(peak_date).strftime('%d. %B %Y')
            f.write(f"  {weekday}: Topic {display_id} ({topic_label}) - {peak_count:,} Tweets\n")

    print(f"✓ TXT-Report gespeichert: {txt_file}")

    # --- VISUALISIERUNG 1: Alle 6 Topics kombiniert ---
    fig = go.Figure()

    colors = {
        0: '#e74c3c',  # Topic 1 - Rot
        2: '#3498db',  # Topic 3 - Blau
        5: '#2ecc71',  # Topic 6 - Grün
        6: '#f39c12',  # Topic 7 - Orange
        9: '#9b59b6',  # Topic 10 - Lila
        11: '#2c3e50'  # Topic 12 - Navy/Dunkelblau
    }

    for topic_id in sorted(SELECTED_TOPICS.keys()):
        df = dfs[topic_id].copy()
        topic_label = SELECTED_TOPICS[topic_id]
        display_id = TOPIC_DISPLAY[topic_id]

        # Erstelle String-Labels für X-Achse
        df['Datum_Label'] = df['Datum'].apply(lambda x: pd.to_datetime(x).strftime('%d. %b'))
        df['Datum_Hover'] = df['Datum'].apply(lambda x: pd.to_datetime(x).strftime('%d.%m.%Y'))

        # Hauptlinie
        fig.add_trace(go.Scatter(
            x=df['Datum_Label'],  # String statt datetime!
            y=df['Anzahl'],
            mode='lines+markers',
            name=f'Topic {display_id}: {topic_label}',
            line=dict(width=3, color=colors[topic_id]),
            marker=dict(size=6),
            customdata=df['Datum_Hover'],
            hovertemplate='<b>Topic %{fullData.name}</b><br>Woche: %{customdata}<br>Tweets: %{y}<extra></extra>'
        ))

        # Peak mit Stern markieren
        peak_idx = df['Anzahl'].idxmax()
        peak_label = df.loc[peak_idx, 'Datum_Label']
        peak_count = df.loc[peak_idx, 'Anzahl']

        fig.add_trace(go.Scatter(
            x=[peak_label],  # String-Label!
            y=[peak_count],
            mode='markers',
            marker=dict(
                size=10,
                color=colors[topic_id],
                symbol='star',
                line=dict(color='black', width=2)
            ),
            showlegend=False,
            customdata=[df.loc[peak_idx, 'Datum_Hover']],
            hovertemplate=f'<b>Peak Topic {display_id}</b><br>Woche: %{{customdata}}<br>Tweets: %{{y}}<extra></extra>'
        ))

    fig.update_layout(
        title='Zeitliche Entwicklung der 6 ausgewählten Topics (wöchentlich aggregiert)',
        xaxis_title='Woche (Beginn)',
        yaxis_title='Anzahl Tweets pro Woche',
        height=700,
        hovermode='x unified',
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(255,255,255,0.9)"
        ),
        plot_bgcolor='#f8f9fa',
        font=dict(size=12)
    )

    html_combined = os.path.join(output_dir, f'zeitverlauf_kombiniert_{timestamp}.html')
    fig.write_html(html_combined)
    print(f"✓ Kombinierte Visualisierung: {html_combined}")

    # --- VISUALISIERUNG 2: Einzelplots pro Topic ---
    for topic_id in sorted(SELECTED_TOPICS.keys()):
        df = dfs[topic_id].copy()
        topic_label = SELECTED_TOPICS[topic_id]
        display_id = TOPIC_DISPLAY[topic_id]

        # Erstelle String-Labels für X-Achse (um Plotly-Bug zu umgehen)
        df['Datum_Label'] = df['Datum'].apply(lambda x: pd.to_datetime(x).strftime('%d. %b'))
        df['Datum_Hover'] = df['Datum'].apply(lambda x: pd.to_datetime(x).strftime('%d.%m.%Y'))

        fig_single = go.Figure()

        # Balkendiagramm mit String-Labels
        fig_single.add_trace(go.Bar(
            x=df['Datum_Label'],  # String statt datetime!
            y=df['Anzahl'],
            marker_color=colors[topic_id],
            customdata=df['Datum_Hover'],
            hovertemplate='<b>Woche: %{customdata}</b><br>Tweets: %{y}<extra></extra>'
        ))

        # Peak ermitteln
        peak_idx = df['Anzahl'].idxmax()
        peak_label = df.loc[peak_idx, 'Datum_Label']
        peak_count = df.loc[peak_idx, 'Anzahl']
        peak_date = df.loc[peak_idx, 'Datum']

        # Berechne Wochenstart und Wochenende
        peak_date_dt = pd.to_datetime(peak_date)
        week_start = peak_date_dt
        week_end = week_start + pd.Timedelta(days=6)

        # Peak-Week als Annotation
        fig_single.add_annotation(
            x=peak_label,  # String-Label!
            y=peak_count,
            text=f"Peak-Woche: {week_start.strftime('%d.%m.')} - {week_end.strftime('%d.%m.%Y')}<br>{peak_count:,} Tweets",
            showarrow=True,
            arrowhead=2,
            arrowcolor=colors[topic_id],
            ax=0,
            ay=-60,
            bgcolor="white",
            bordercolor=colors[topic_id],
            borderwidth=2,
            font=dict(size=11, color=colors[topic_id])
        )

        # Durchschnittslinie
        mean_val = df['Anzahl'].mean()
        fig_single.add_hline(
            y=mean_val,
            line_dash="dash",
            line_color="gray",
            annotation_text=f"Durchschnitt: {mean_val:.1f}",
            annotation_position="right",
            annotation=dict(font=dict(size=10))
        )

        fig_single.update_layout(
            title=f'Topic {display_id}: {topic_label} - Zeitlicher Verlauf',
            xaxis_title='Woche (Beginn)',
            yaxis_title='Anzahl Tweets pro Woche',
            height=500,
            plot_bgcolor='#f8f9fa',
            font=dict(size=12)
        )

        html_single = os.path.join(output_dir, f'topic_{display_id}_{timestamp}.html')
        fig_single.write_html(html_single)
        print(f"✓ Einzelplot Topic {display_id}: {html_single}")


if __name__ == '__main__':
    main()