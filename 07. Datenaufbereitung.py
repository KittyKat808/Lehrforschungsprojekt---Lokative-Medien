import json
import re
from typing import List, Dict, Any, Optional
import os
from datetime import datetime
import emoji

# spaCy mit deutschem Large-Modell laden
try:
    import spacy
    from spacy.lang.de.stop_words import STOP_WORDS  # Importiere Stopwörter

    nlp_de = spacy.load("de_core_news_lg")
    SPACY_AVAILABLE = True
except:
    raise ImportError("spaCy de_core_news_lg nicht gefunden. Installiere mit: python -m spacy download de_core_news_lg")


class GermanTweetPreprocessor:
    def __init__(self):
        # Stoppwörter Ergänzung
        self.custom_stopwords = {
            'rt', 'via', 'amp', 'https', 'http', 'www', 'com', 'html', 'htm', 'mal', 'eigentlich'
        }

        # Häufige deutsche Abkürzungen für Expansion
        self.abbreviations = {
            'mfg': 'mit freundlichen grüßen',
            'lg': 'liebe grüße',
            'vllt': 'vielleicht',
            'vlt': 'vielleicht',
            'evtl': 'eventuell',
            'usw': 'und so weiter',
            'bzw': 'beziehungsweise',
            'etc': 'et cetera',
            'ca': 'circa',
            'zb': 'zum beispiel',
            'z.b.': 'zum beispiel',
            'd.h.': 'das heißt',
            'u.a.': 'unter anderem',
            'v.a.': 'vor allem',
            'incl': 'inklusive',
            'inkl': 'inklusive',
            'ggf': 'gegebenenfalls',
            'mind': 'mindestens',
            'max': 'maximal',
            'min': 'minimal',
        }

    def extract_emojis(self, text: str) -> List[str]:
        """Extrahiert alle Emojis aus Text mit der emoji-Bibliothek"""
        return [char for char in text if char in emoji.EMOJI_DATA]

    def clean_text(self, text: str) -> str:
        if not text:
            return ""

        # URLs, Mentions entfernen
        text = re.sub(r'http[s]?://\S+|www\.\S+|t\.co/\S+', '', text)
        text = re.sub(r'@\w+', '', text)
        text = re.sub(r'^RT\s+|\bRT\b', '', text, flags=re.IGNORECASE)

        # Emojis mit der emoji-Bibliothek entfernen
        text = emoji.replace_emoji(text, replace='')

        # News-typische Muster entfernen
        text = re.sub(r'(News|Live)-?Ticker\w*|Eilmeldung\w*', '', text, flags=re.IGNORECASE)

        # WICHTIG: Named Entities VOR Bindestrich-Ersetzung zusammenschreiben

        # Institutionen (alle möglichen Schreibweisen + Genitiv)
        text = re.sub(r'\bRobert[\s-]+Koch[\s-]+Instituts?\b', 'RobertKochInstitut', text, flags=re.IGNORECASE)
        text = re.sub(r'\bRKI\b', 'RobertKochInstitut', text, flags=re.IGNORECASE)

        # Apps & Tech (alle möglichen Schreibweisen + Genitiv)
        text = re.sub(r'\bCorona[\s-]+Warn[\s-]+App\b', 'CoronaWarnApp', text, flags=re.IGNORECASE)
        text = re.sub(r'\bHome[\s-]+Offices?\b', 'HomeOffice', text, flags=re.IGNORECASE)

        # Bundesländer (alle möglichen Schreibweisen + Genitiv)
        text = re.sub(r'\bBaden[\s-]+Württembergs?\b', 'BadenWürttemberg', text, flags=re.IGNORECASE)
        text = re.sub(r'\bNordrhein[\s-]+Westfalens?\b', 'NordrheinWestfalen', text, flags=re.IGNORECASE)
        text = re.sub(r'\bRheinland[\s-]+Pfalzs?\b', 'RheinlandPfalz', text, flags=re.IGNORECASE)
        text = re.sub(r'\bSachsen[\s-]+Anhalts?\b', 'SachsenAnhalt', text, flags=re.IGNORECASE)
        text = re.sub(r'\bSchleswig[\s-]+Holsteins?\b', 'SchleswigHolstein', text, flags=re.IGNORECASE)
        text = re.sub(r'\bMecklenburg[\s-]+Vorpommerns?\b', 'MecklenburgVorpommern', text, flags=re.IGNORECASE)

        # Hashtag-Symbol entfernen, Inhalt behalten
        text = re.sub(r'#(\w+)', r'\1', text)

        # Datumsformate entfernen
        text = re.sub(r'\d{1,2}\.\d{1,2}\.\d{2,4}', '', text)
        text = re.sub(r'\d{1,2}:\d{2}', '', text)
        text = re.sub(r'\|\s*\d+', '', text)

        # Zahlen am Anfang von Wörtern entfernen (2019nCoV → nCoV)
        text = re.sub(r'\b(\d+)([a-zA-ZäöüÄÖÜß]+)', r'\2', text)

        # Zahlen am Ende von Wörtern entfernen (Covid19 → Covid)
        text = re.sub(r'([a-zA-ZäöüÄÖÜß]+?)(\d+)\b', r'\1', text)

        # Deutsche Abkürzungen expandieren
        words = text.split()
        expanded_words = []
        for word in words:
            clean_word = word.strip('.,!?-').lower()
            if clean_word in self.abbreviations:
                expanded_words.append(self.abbreviations[clean_word])
            else:
                expanded_words.append(word)
        text = ' '.join(expanded_words)

        # Bindestriche zwischen Wörtern durch Leerzeichen ersetzen
        text = re.sub(r'(\w)-(\w)', r'\1 \2', text)

        # Slashes und andere Sonderzeichen vor/nach Wörtern entfernen
        text = re.sub(r'[/\\]+', ' ', text)

        # Wiederholte Sonderzeichen entfernen (!!!!, ????, etc.)
        text = re.sub(r'([!?.,;:"\']){2,}', r'\1', text)

        # Alle verbleibenden Sonderzeichen durch Leerzeichen ersetzen
        # AUSNAHME: Behalte nur Buchstaben, Zahlen, Leerzeichen, Umlaute und Bindestriche (für Komposita)
        text = re.sub(r'[^\w\s\-äöüÄÖÜß]', ' ', text)

        # Bindestriche am Wortanfang/-ende entfernen (-corona → corona, corona- → corona)
        text = re.sub(r'\b-+|-+\b', '', text)

        # Mehrfache Leerzeichen normalisieren
        text = re.sub(r'\s+', ' ', text)

        return text.strip()

    def lemmatize(self, text: str) -> List[str]:
        """
        SpaCy-Lemmatisierung mit 2-stufigem Stopwort-Filter:
        1. Filter auf Token-Ebene (während Verarbeitung)
        2. Filter auf Lemma-Ebene (nach Lemmatisierung)
        """
        if not text:
            return []

        # spaCy verarbeitet Text MIT Großschreibung
        doc = nlp_de(text)

        # Filtern und lemmatisieren
        lemmas = []
        for token in doc:
            # Token-Text bereinigen: Alle verbleibenden Sonderzeichen entfernen
            clean_token = re.sub(r'[^\w\säöüÄÖÜß]', '', token.text)
            clean_lemma = re.sub(r'[^\w\säöüÄÖÜß]', '', token.lemma_)

            # FILTER STUFE 1: Token-basiert
            if (clean_lemma
                    and not token.is_stop  # spaCy Stopwörter auf Token-Ebene
                    and not token.is_punct
                    and not token.is_space
                    and not token.like_num
                    and len(clean_lemma) > 2
                    and not any(c.isdigit() for c in clean_lemma)
                    and sum(c.isalpha() for c in clean_lemma) >= 2
                    and clean_lemma.lower() not in self.custom_stopwords
                    and clean_lemma.isalpha()):

                # FILTER STUFE 2: Lemma-basiert (NEU!)
                lemma_lower = clean_lemma.lower()
                if lemma_lower not in STOP_WORDS:  # spaCy Stopwörter auf Lemma-Ebene
                    lemmas.append(lemma_lower)

        return lemmas

    def process_tweet(self, tweet: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Verarbeitet einen Tweet komplett: Cleaning → Lemmatisierung → Output.
        Gibt None zurück wenn Tweet leer oder keine validen Tokens.
        """
        text = tweet.get('text', '')
        if not text:
            return None

        # Schritt 1: Emojis vor dem Cleaning extrahieren
        emojis = self.extract_emojis(text)

        # Schritt 2: Text bereinigen (behält Großschreibung)
        cleaned = self.clean_text(text)

        # Schritt 3: Lemmatisieren (nutzt Großschreibung, gibt lowercase zurück)
        tokens = self.lemmatize(cleaned)

        if not tokens:
            return None

        # Entities mit extrahierten Emojis anreichern (für spätere Sentiment-Analyse)
        entities = tweet.get('entities', {}).copy()
        entities['emojis'] = emojis

        # Finales verarbeitetes Tweet-Objekt
        return {
            'tweet_id': tweet.get('tweet_id'),
            'created_at': tweet.get('created_at'),
            'user_id': tweet.get('user_id'),
            'geo_source': tweet.get('geo_source'),
            'geo': tweet.get('geo'),
            'place': tweet.get('place'),
            'original_text': text,
            'processed_text': ' '.join(tokens),
            'tokens': tokens,
            'entities': entities
        }

    def process_dataset(self, input_file: str, output_dir: str) -> str:
        """
        Verarbeitet kompletten Datensatz: liest JSONL, verarbeitet jeden Tweet,
        schreibt Ergebnis in neue JSONL-Datei.
        """
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"preprocessed_{timestamp}.jsonl")

        processed = skipped = 0

        with open(input_file, 'r', encoding='utf-8') as infile, \
                open(output_file, 'w', encoding='utf-8') as outfile:

            for line_num, line in enumerate(infile, 1):
                if line_num % 1000 == 0:
                    print(f"{line_num} tweets verarbeitet...")

                try:
                    tweet = json.loads(line.strip())
                    result = self.process_tweet(tweet)

                    if result:
                        json.dump(result, outfile, ensure_ascii=False)
                        outfile.write('\n')
                        processed += 1
                    else:
                        skipped += 1
                except:
                    skipped += 1

        print(f"Fertig: {processed} verarbeitet, {skipped} übersprungen")
        return output_file


def main():
    preprocessor = GermanTweetPreprocessor()
    preprocessor.process_dataset(
        r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\Final_Dataset.json",
        r"C:\Users\[NUTZERNAME]\[ORDNERNAME]\Data Cleaning"
    )


if __name__ == "__main__":
    main()
