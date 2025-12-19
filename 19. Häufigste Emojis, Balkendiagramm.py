import json
import plotly.graph_objects as go
from collections import Counter
import os
from datetime import datetime

# Emoji-Modifier, die gefiltert werden sollen
EMOJI_MODIFIERS = {
    '🏻', '🏼', '🏽', '🏾', '🏿',
    '♂', '♀', '⚧',
    '️', '\ufe0f',
}


def filter_emoji_modifiers(emojis):
    """Filtert Emoji-Modifier aus einer Liste von Emojis"""
    return [emoji for emoji in emojis if emoji not in EMOJI_MODIFIERS]


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


def visualize_top_emojis(tweets, output_dir):
    """Erstellt einfaches Balkendiagramm der Top 20 Emojis"""

    print("Analysiere Emojis...")

    all_emojis = []
    tweets_with_emojis = 0
    filtered_modifiers = 0

    # Tweets durchgehen
    for tweet in tweets:
        emojis = tweet.get('entities', {}).get('emojis', [])

        if not emojis:
            continue

        # Modifier herausfiltern
        original_count = len(emojis)
        emojis = filter_emoji_modifiers(emojis)
        filtered_modifiers += (original_count - len(emojis))

        if not emojis:
            continue

        tweets_with_emojis += 1
        all_emojis.extend(emojis)

    print(f"✓ {tweets_with_emojis:,} Tweets mit Emojis")
    print(f"✓ {filtered_modifiers:,} Emoji-Modifier herausgefiltert\n")

    # Counter erstellen
    emoji_counter = Counter(all_emojis)

    # Top 20 extrahieren
    top_20 = emoji_counter.most_common(20)
    emojis = [emoji for emoji, _ in top_20]
    counts = [count for _, count in top_20]

    # Prozente berechnen
    total = sum(emoji_counter.values())
    percentages = [(count / total * 100) for count in counts]

    # Output-Verzeichnis erstellen
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # --- EINFACHES BALKENDIAGRAMM ---
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=counts,
        y=emojis,
        orientation='h',
        marker=dict(
            color='steelblue',
            line=dict(color='darkblue', width=1)
        ),
        text=[f'{count:,} ({pct:.1f}%)' for count, pct in zip(counts, percentages)],
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>Anzahl: %{x:,}<extra></extra>'
    ))

    fig.update_layout(
        title='Top 20 Emojis',
        xaxis=dict(
            title='Anzahl Verwendungen',
            showgrid=True,
            gridcolor='lightgray'
        ),
        yaxis=dict(
            title='',
            tickfont=dict(size=20),
            autorange='reversed'
        ),
        height=700,
        margin=dict(l=100, r=150, t=80, b=80),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )

    # Als HTML speichern
    html_file = os.path.join(output_dir, f"emoji_top20_bar_{timestamp}.html")
    fig.write_html(html_file)
    print(f"✓ Balkendiagramm: {html_file}")

    # Optional: Als PNG speichern
    try:
        png_file = os.path.join(output_dir, f"emoji_top20_bar_{timestamp}.png")
        fig.write_image(png_file, width=1200, height=700)
        print(f"✓ PNG: {png_file}")
    except Exception as e:
        print(f"⚠ PNG konnte nicht erstellt werden: {e}")

    print(f"\n{'=' * 60}")
    print("EMOJI-VISUALISIERUNG ABGESCHLOSSEN!")
    print(f"{'=' * 60}\n")


def main():
    input_file = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\Cleaned_Data.jsonl"
    output_dir = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\Emojis"

    tweets = load_tweets(input_file)
    visualize_top_emojis(tweets, output_dir)


if __name__ == "__main__":
    main()