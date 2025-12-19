import json
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from gensim.models import LdaModel
import os
from datetime import datetime

# Matplotlib auf Deutsch
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False


def main():
    # An eigene Pfade anpassen!
    model_dir = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\LDA\final_14_topics"
    output_dir = r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\LDA\wortwolken"

    os.makedirs(output_dir, exist_ok=True)

    print("=" * 70)
    print("WORTWOLKEN FÜR AUSGEWÄHLTE TOPICS")
    print("=" * 70)

    # 1. Modell laden
    print("\n[1/2] Lade Modell...")
    model_file = os.path.join(model_dir, "lda_model_14_topics_20251124_235500")
    lda_model = LdaModel.load(model_file)
    print("✓ Modell geladen")

    # 2. Wortwolken erstellen
    print("\n[2/2] Erstelle Wortwolken...")

    # Die 6 ausgewählten Topics (0-basiert im Modell, 1-basiert in Darstellung)
    selected_topics = {
        0: 1,  # Topic 0 → Topic 1
        2: 3,  # Topic 2 → Topic 3
        5: 6,  # Topic 5 → Topic 6
        6: 7,  # Topic 6 → Topic 7
        9: 10,  # Topic 9 → Topic 10
        11: 12  # Topic 11 → Topic 12
    }

    # Figure mit 3×2 Grid (3 Zeilen, 2 Spalten)
    # Reduzierter Abstand: wspace=0.15 (zwischen Spalten), hspace=0.2 (zwischen Zeilen)
    fig, axes = plt.subplots(3, 2, figsize=(16, 18))
    fig.subplots_adjust(wspace=0.15, hspace=0.2)  # ← WENIGER Abstand
    axes = axes.flatten()

    for idx, (topic_id_model, topic_id_display) in enumerate(selected_topics.items()):
        print(f"  Erstelle Wortwolke für Topic {topic_id_display}...")

        # Hole Top 40 Wörter mit Wahrscheinlichkeiten
        topic_words = lda_model.show_topic(topic_id_model, topn=40)

        # Konvertiere zu Dictionary für WordCloud
        word_freq = {word: prob for word, prob in topic_words}

        # Erstelle Wortwolke
        wordcloud = WordCloud(
            width=1600,
            height=800,
            background_color='white',
            colormap='viridis',
            max_words=40,
            relative_scaling=0.5,
            min_font_size=10,
            prefer_horizontal=0.7
        ).generate_from_frequencies(word_freq)

        # Plotte Wortwolke
        ax = axes[idx]
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.set_title(f'Topic {topic_id_display}', fontsize=16, fontweight='bold', pad=10)
        ax.axis('off')
        # KEINE Umrandung mehr!

    # Speichern
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f'wortwolken_6_topics_{timestamp}.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"\n✓ Wortwolken gespeichert: {output_file}")

    plt.close()

    # BONUS: Erstelle auch einzelne Wortwolken (für Präsentation/Flexibilität)
    print("\n[BONUS] Erstelle einzelne Wortwolken...")

    single_dir = os.path.join(output_dir, 'einzelne_wortwolken')
    os.makedirs(single_dir, exist_ok=True)

    for topic_id_model, topic_id_display in selected_topics.items():
        # Hole Wörter
        topic_words = lda_model.show_topic(topic_id_model, topn=40)
        word_freq = {word: prob for word, prob in topic_words}

        # Erstelle Wortwolke
        wordcloud = WordCloud(
            width=1600,
            height=800,
            background_color='white',
            colormap='viridis',
            max_words=40,
            relative_scaling=0.5,
            min_font_size=10,
            prefer_horizontal=0.7
        ).generate_from_frequencies(word_freq)

        # Plotte
        fig, ax = plt.subplots(figsize=(20, 10))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.set_title(f'Topic {topic_id_display}', fontsize=20, fontweight='bold', pad=20)
        ax.axis('off')

        # Speichern
        single_file = os.path.join(single_dir, f'wortwolke_topic_{topic_id_display}_{timestamp}.png')
        plt.savefig(single_file, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()

        print(f"  ✓ Topic {topic_id_display}")

    print(f"\n✓ Einzelne Wortwolken gespeichert in: {single_dir}")

    # BONUS 2: Erstelle auch eine Wortliste als TXT
    print("\n[BONUS 2] Erstelle Wortlisten...")

    txt_file = os.path.join(output_dir, f'top_woerter_6_topics_{timestamp}.txt')

    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("TOP-WÖRTER FÜR DIE 6 AUSGEWÄHLTEN TOPICS\n")
        f.write(f"Erstellt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")

        for topic_id_model, topic_id_display in selected_topics.items():
            f.write("\n" + "=" * 80 + "\n")
            f.write(f"TOPIC {topic_id_display}\n")
            f.write("=" * 80 + "\n\n")

            # Top 30 Wörter mit Wahrscheinlichkeiten
            topic_words = lda_model.show_topic(topic_id_model, topn=30)

            f.write(f"{'Rang':<6} {'Wort':<25} {'Relevanz':<15}\n")
            f.write("-" * 50 + "\n")

            for rank, (word, prob) in enumerate(topic_words, 1):
                f.write(f"{rank:<6} {word:<25} {prob:<15.6f}\n")

            f.write("\n")

    print(f"✓ Wortlisten gespeichert: {txt_file}")


if __name__ == '__main__':

    main()
