import re


def lookup(text: str, lexicon: dict) -> list[float]:
    """
    Look up words from input text in a emotion lexicon.

    Extracts word tokens from the input text, finds matching entries in the
    lexicon dictionary, and calculates the mean scores across each dimension
    along with the hit ratio.

    Args:
        text: Input sentence to analyze.
        lexicon: Dictionary mapping lowercase word strings to dimension values

    Returns:
        list[float]: A list of [mean_v1, mean_v2, mean_v3, hit_ratio] rounded to 4 decimal
            places, or [0.0, 0.0, 0.0, 0.0] if no words from the text match the lexicon.
    """
    # Extract words from the sentence into word array
    words = re.findall(r"[a-z']+(?:'[a-z]+)?", text.lower())
    # Look for hits inside lexicon to assign proper VAD values
    hits = [lexicon[w] for w in words if w in lexicon]

    if not hits:
        return [0.0, 0.0, 0.0, 0.0]

    # Calculate mean from the words found inside the sentence
    mean_v1 = sum(hit[0] for hit in hits) / len(hits)
    mean_v2 = sum(hit[1] for hit in hits) / len(hits)
    mean_v3 = sum(hit[2] for hit in hits) / len(hits)
    hit_ratio = len(hits) / len(words)

    result = [mean_v1, mean_v2, mean_v3, hit_ratio]
    return [round(x, 4) for x in result]