from urllib.parse import urlparse
import re

STOPWORDS = {
    "com", "org", "net", "edu", "gov", "io", "co", "www", "http", "https",
    "html", "htm", "php", "asp", "jsp", "the", "and", "for", "are", "but",
    "not", "you", "all", "can", "had", "her", "was", "one", "our", "out",
    "index", "page", "site", "web", "blog",
}

# Common English stopwords for title parsing — articles, prepositions,
# pronouns, conjunctions, auxiliaries, and other low-signal words.
TITLE_STOPWORDS = STOPWORDS | {
    # articles
    "a", "an", "the",
    # prepositions
    "about", "above", "across", "after", "against", "along", "among", "around",
    "at", "before", "behind", "below", "beneath", "beside", "between", "beyond",
    "by", "down", "during", "except", "for", "from", "in", "inside", "into",
    "like", "near", "of", "off", "on", "onto", "out", "outside", "over",
    "past", "per", "since", "through", "throughout", "till", "to", "toward",
    "towards", "under", "underneath", "until", "up", "upon", "via", "with",
    "within", "without",
    # conjunctions
    "and", "but", "or", "nor", "for", "yet", "so", "both", "either", "neither",
    "whether", "although", "because", "since", "while", "whereas", "unless",
    "than",
    # pronouns
    "i", "me", "my", "mine", "myself", "you", "your", "yours", "yourself",
    "he", "him", "his", "himself", "she", "her", "hers", "herself",
    "it", "its", "itself", "we", "us", "our", "ours", "ourselves",
    "they", "them", "their", "theirs", "themselves",
    "this", "that", "these", "those", "who", "whom", "whose", "which", "what",
    "whoever", "whatever", "whichever",
    # auxiliaries / common verbs
    "am", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "having", "do", "does", "did", "doing",
    "will", "would", "shall", "should", "may", "might", "must", "can", "could",
    "get", "got", "gets", "getting",
    # adverbs / other common words
    "also", "as", "back", "been", "each", "else", "even", "ever", "every",
    "here", "how", "if", "just", "more", "most", "much", "no", "not", "now",
    "only", "other", "own", "quite", "really", "right", "same", "some", "such",
    "still", "then", "there", "too", "very", "well", "when", "where", "why",
    "all", "any", "few", "many", "new", "old", "one", "two",
}


def extract_words_from_title(title):
    """Extract meaningful words from a bookmark title for auto-tagging.

    Keeps words that are either:
    - Lowercase alphabetic and at least 3 characters, not a stopword
    - Uppercase acronyms (e.g. AWS, API) of 2+ characters
    """
    parts = re.split(r"[^a-zA-Z]+", title)
    words = set()
    for part in parts:
        stripped = part.strip()
        if not stripped:
            continue
        # Keep uppercase acronyms (2+ chars, all caps)
        if stripped.isupper() and len(stripped) >= 2 and stripped.isalpha():
            words.add(stripped.lower())
            continue
        word = stripped.lower()
        if len(word) >= 3 and word.isalpha() and word not in TITLE_STOPWORDS:
            words.add(word)
    return sorted(words)


def extract_words_from_url(url):
    """Extract meaningful words from a URL for auto-tagging."""
    parsed = urlparse(url)

    hostname = parsed.hostname or ""
    parts = hostname.split(".")

    path = parsed.path or ""
    path_parts = re.split(r"[^a-zA-Z]+", path)

    all_parts = parts + path_parts

    words = set()
    for part in all_parts:
        word = part.lower().strip()
        if len(word) >= 3 and word.isalpha() and word not in STOPWORDS:
            words.add(word)

    return sorted(words)
