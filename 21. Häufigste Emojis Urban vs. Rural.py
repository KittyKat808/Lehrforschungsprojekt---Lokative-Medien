import json
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from collections import Counter
import os
from datetime import datetime

# Emoji-Modifier, die gefiltert werden sollen
EMOJI_MODIFIERS = {
    '🏻', '🏼', '🏽', '🏾', '🏿',
    '♂', '♀', '⚧',
    '️', '\ufe0f',
}

# Urban/Rural Klassifizierung
CITY_CLASSIFICATION = {
    'Berlin': 'urban',
    'Hamburg': 'urban',
    'München': 'urban',
    'Köln': 'urban',
    'Frankfurt': 'urban',
    'Stuttgart': 'urban',
    'Düsseldorf': 'urban',
    'Dortmund': 'urban',
    'Essen': 'urban',
    'Leipzig': 'urban',
    'Bremen': 'urban',
    'Dresden': 'urban',
    'Hannover': 'urban',
    'Nürnberg': 'urban',
    'Duisburg': 'urban',
    'Bochum': 'urban',
    'Wuppertal': 'urban',
    'Bielefeld': 'urban',
    'Bonn': 'urban',
    'Münster': 'urban',
    'Karlsruhe': 'urban',
    'Mannheim': 'urban',
    'Augsburg': 'urban',
    'Wiesbaden': 'urban',
    'Gelsenkirchen': 'urban',
    'Mönchengladbach': 'urban',
    'Braunschweig': 'urban',
    'Chemnitz': 'urban',
    'Kiel': 'urban',
    'Aachen': 'urban',
    'Halle': 'urban',
    'Magdeburg': 'urban',
    'Freiburg': 'urban',
    'Krefeld': 'urban',
    'Lübeck': 'urban',
    'Oberhausen': 'urban',
    'Erfurt': 'urban',
    'Mainz': 'urban',
    'Rostock': 'urban',
    'Kassel': 'urban',
    'Hagen': 'urban',
    'Hamm': 'urban',
    'Saarbrücken': 'urban',
    'Mülheim': 'urban',
    'Potsdam': 'urban',
    'Ludwigshafen': 'urban',
    'Oldenburg': 'urban',
    'Leverkusen': 'urban',
    'Osnabrück': 'urban',
    'Solingen': 'urban',
    'Heidelberg': 'urban',
    'Herne': 'urban',
    'Neuss': 'urban',
    'Darmstadt': 'urban',
    'Paderborn': 'urban',
    'Regensburg': 'urban',
    'Ingolstadt': 'urban',
    'Würzburg': 'urban',
    'Fürth': 'urban',
    'Wolfsburg': 'urban',
    'Offenbach': 'urban',
    'Ulm': 'urban',
    'Heilbronn': 'urban',
    'Pforzheim': 'urban',
    'Göttingen': 'urban',
    'Bottrop': 'urban',
    'Trier': 'urban',
    'Recklinghausen': 'urban',
    'Reutlingen': 'urban',
    'Bremerhaven': 'urban',
    'Koblenz': 'urban',
    'Bergisch Gladbach': 'urban',
    'Jena': 'urban',
    'Remscheid': 'urban',
    'Erlangen': 'urban',
    'Moers': 'urban',
    'Siegen': 'urban',
    'Hildesheim': 'urban',
    'Salzgitter': 'urban',
}


def filter_emoji_modifiers(emojis):
    """Filtert Emoji-Modifier aus einer Liste von Emojis"""
    return [emoji for emoji in emojis if emoji not in EMOJI_MODIFIERS]


def classify_location(tweet):
    """Klassifiziert Tweet als urban oder rural basierend auf Stadt"""
    city = None

    geo_source = tweet.get('geo_source')

    if geo_source == 'coordinates' and tweet.get('geo'):
        city = tweet['geo'].get('city')
    elif geo_source == 'place' and tweet.get('place'):
        city = tweet['place'].get('city')

    if not city:
        return None

    return CITY_CLASSIFICATION.get(city, 'rural')


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


def visualize_urban_rural_emojis(tweets, output_dir):
    """Erstellt Visualisierungen für Urban vs. Rural Emojis"""

    print("Analysiere Emojis nach Urban/Rural...")

    # Datenstrukturen
    urban_emojis = []
    rural_emojis = []

    urban_tweets = 0
    rural_tweets = 0
    tweets_with_emojis = 0
    filtered_modifiers = 0

    for tweet in tweets:
        emojis = tweet.get('entities', {}).get('emojis', [])

        if not emojis:
            continue

        # Modifier filtern
        original_count = len(emojis)
        emojis = filter_emoji_modifiers(emojis)
        filtered_modifiers += (original_count - len(emojis))

        if not emojis:
            continue

        tweets_with_emojis += 1

        # Klassifizierung
        classification = classify_location(tweet)

        if classification == 'urban':
            urban_emojis.extend(emojis)
            urban_tweets += 1
        elif classification == 'rural':
            rural_emojis.extend(emojis)
            rural_tweets += 1

    print(f"✓ {tweets_with_emojis:,} Tweets mit Emojis")
    print(f"✓ {urban_tweets:,} Urban Tweets")
    print(f"✓ {rural_tweets:,} Rural Tweets")
    print(f"✓ {filtered_modifiers:,} Emoji-Modifier herausgefiltert\n")

    # Counter erstellen
    urban_counter = Counter(urban_emojis)
    rural_counter = Counter(rural_emojis)

    # Output-Verzeichnis erstellen
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # --- VISUALISIERUNG 1: Side-by-Side Balkendiagramme (Top 15) ---
    top_15_urban = urban_counter.most_common(15)
    top_15_rural = rural_counter.most_common(15)

    emojis_urban = [emoji for emoji, _ in top_15_urban]
    counts_urban = [count for _, count in top_15_urban]

    emojis_rural = [emoji for emoji, _ in top_15_rural]
    counts_rural = [count for _, count in top_15_rural]

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Urban (Städte)', 'Rural (Ländlich)'),
        horizontal_spacing=0.15
    )

    # Urban
    fig.add_trace(
        go.Bar(
            x=counts_urban,
            y=emojis_urban,
            orientation='h',
            marker=dict(color='steelblue'),
            name='Urban',
            hovertemplate='<b>%{y}</b><br>Anzahl: %{x:,}<extra></extra>'
        ),
        row=1, col=1
    )

    # Rural
    fig.add_trace(
        go.Bar(
            x=counts_rural,
            y=emojis_rural,
            orientation='h',
            marker=dict(color='forestgreen'),
            name='Rural',
            hovertemplate='<b>%{y}</b><br>Anzahl: %{x:,}<extra></extra>'
        ),
        row=1, col=2
    )

    fig.update_xaxes(title_text="Anzahl", row=1, col=1)
    fig.update_xaxes(title_text="Anzahl", row=1, col=2)

    # WICHTIG: tickfont size=20 für sichtbare Emojis!
    fig.update_yaxes(autorange="reversed", tickfont=dict(size=20), row=1, col=1)
    fig.update_yaxes(autorange="reversed", tickfont=dict(size=20), row=1, col=2)

    fig.update_layout(
        title_text='Top 15 Emojis: Urban vs. Rural',
        showlegend=False,
        height=700,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )

    html_file1 = os.path.join(output_dir, f"emoji_urban_rural_sidebyside_{timestamp}.html")
    fig.write_html(html_file1)
    print(f"✓ Side-by-Side Diagramm: {html_file1}")

    # --- VISUALISIERUNG 2: Direkter Vergleich (Top 10 gemeinsam) ---
    # Finde die Top 10 Emojis insgesamt
    all_emojis = urban_emojis + rural_emojis
    all_counter = Counter(all_emojis)
    top_10_overall = [emoji for emoji, _ in all_counter.most_common(10)]

    # Zähle für jedes dieser Emojis in Urban und Rural
    urban_values = [urban_counter.get(emoji, 0) for emoji in top_10_overall]
    rural_values = [rural_counter.get(emoji, 0) for emoji in top_10_overall]

    fig2 = go.Figure()

    fig2.add_trace(go.Bar(
        name='Urban',
        x=top_10_overall,
        y=urban_values,
        marker_color='steelblue',
        text=[f'{v:,}' for v in urban_values],
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Urban: %{y:,}<extra></extra>'
    ))

    fig2.add_trace(go.Bar(
        name='Rural',
        x=top_10_overall,
        y=rural_values,
        marker_color='forestgreen',
        text=[f'{v:,}' for v in rural_values],
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Rural: %{y:,}<extra></extra>'
    ))

    fig2.update_layout(
        title='Top 10 Emojis: Urban vs. Rural (Direktvergleich)',
        xaxis=dict(
            title='Emoji',
            tickfont=dict(size=24)  # Große Emojis auf X-Achse!
        ),
        yaxis=dict(
            title='Anzahl Verwendungen'
        ),
        barmode='group',
        height=600,
        plot_bgcolor='white',
        paper_bgcolor='white',
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="right",
            x=0.99
        )
    )

    html_file2 = os.path.join(output_dir, f"emoji_urban_rural_comparison_{timestamp}.html")
    fig2.write_html(html_file2)
    print(f"✓ Vergleichsdiagramm: {html_file2}")

    # --- VISUALISIERUNG 3: Prozentuale Anteile (Stacked) ---
    fig3 = go.Figure()

    total_urban = sum(urban_counter.values())
    total_rural = sum(rural_counter.values())

    urban_pct = [urban_counter.get(emoji, 0) / total_urban * 100 for emoji in top_10_overall]
    rural_pct = [rural_counter.get(emoji, 0) / total_rural * 100 for emoji in top_10_overall]

    fig3.add_trace(go.Bar(
        name='Urban',
        x=top_10_overall,
        y=urban_pct,
        marker_color='steelblue',
        text=[f'{v:.1f}%' for v in urban_pct],
        textposition='inside',
        hovertemplate='<b>%{x}</b><br>Urban: %{y:.1f}%<extra></extra>'
    ))

    fig3.add_trace(go.Bar(
        name='Rural',
        x=top_10_overall,
        y=rural_pct,
        marker_color='forestgreen',
        text=[f'{v:.1f}%' for v in rural_pct],
        textposition='inside',
        hovertemplate='<b>%{x}</b><br>Rural: %{y:.1f}%<extra></extra>'
    ))

    fig3.update_layout(
        title='Top 10 Emojis: Prozentualer Anteil (Urban vs. Rural)',
        xaxis=dict(
            title='Emoji',
            tickfont=dict(size=24)  # WICHTIG!
        ),
        yaxis=dict(
            title='Anteil (%)'
        ),
        barmode='group',
        height=600,
        plot_bgcolor='white',
        paper_bgcolor='white',
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="right",
            x=0.99
        )
    )

    html_file3 = os.path.join(output_dir, f"emoji_urban_rural_percentage_{timestamp}.html")
    fig3.write_html(html_file3)
    print(f"✓ Prozent-Diagramm: {html_file3}")

    # --- VISUALISIERUNG 4: Ratio-Diagramm (Urban/Rural Verhältnis) ---
    ratios = []
    emoji_labels = []

    for emoji in top_10_overall:
        urban_count = urban_counter.get(emoji, 0)
        rural_count = rural_counter.get(emoji, 0)

        if rural_count > 0:
            ratio = urban_count / rural_count
            ratios.append(ratio)
            emoji_labels.append(emoji)

    fig4 = go.Figure()

    colors_ratio = ['steelblue' if r >= 1 else 'forestgreen' for r in ratios]

    fig4.add_trace(go.Bar(
        x=emoji_labels,
        y=ratios,
        marker_color=colors_ratio,
        text=[f'{r:.2f}x' for r in ratios],
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Urban/Rural Ratio: %{y:.2f}<extra></extra>'
    ))

    fig4.add_hline(
        y=1.0,
        line_dash="dash",
        line_color="red",
        annotation_text="Gleichstand (1:1)",
        annotation_position="right"
    )

    fig4.update_layout(
        title='Urban/Rural Ratio (> 1 = mehr Urban, < 1 = mehr Rural)',
        xaxis=dict(
            title='Emoji',
            tickfont=dict(size=24)  # WICHTIG!
        ),
        yaxis=dict(
            title='Urban/Rural Verhältnis'
        ),
        height=600,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )

    html_file4 = os.path.join(output_dir, f"emoji_urban_rural_ratio_{timestamp}.html")
    fig4.write_html(html_file4)
    print(f"✓ Ratio-Diagramm: {html_file4}")

    print(f"\n{'=' * 60}")
    print("URBAN-RURAL VISUALISIERUNGEN ABGESCHLOSSEN!")
    print(f"{'=' * 60}\n")
    print(f"Erstellt: 4 interaktive Visualisierungen")


def main():
    # eigene Pfade anpassen!
    input_file = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\Cleaned_Data.jsonl"
    output_dir = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\Emojis"

    tweets = load_tweets(input_file)
    visualize_urban_rural_emojis(tweets, output_dir)


if __name__ == "__main__":

    main()
