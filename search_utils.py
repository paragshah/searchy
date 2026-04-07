import re
import inflect

_engine = inflect.engine()


def parse_query(query_string):
    """Parse a search query into terms. Quoted strings are exact-match terms.

    A leading dash negates a term: -word or -"exact phrase" will exclude
    results that have the matching tag.
    """
    # Normalize commas to spaces (but not inside quotes)
    query_string = re.sub(r',(?=(?:[^"]*"[^"]*")*[^"]*$)', ' ', query_string)
    terms = []
    pattern = r'-"([^"]+)"|"([^"]+)"|-(\S+)|(\S+)'
    for match in re.finditer(pattern, query_string):
        neg_quoted = match.group(1)
        quoted = match.group(2)
        neg_unquoted = match.group(3)
        unquoted = match.group(4)
        if neg_quoted is not None:
            terms.append({"value": neg_quoted.lower(), "exact": True, "negate": True})
        elif quoted is not None:
            terms.append({"value": quoted.lower(), "exact": True, "negate": False})
        elif neg_unquoted is not None:
            terms.append({"value": neg_unquoted.lower(), "exact": False, "negate": True})
        elif unquoted is not None:
            terms.append({"value": unquoted.lower(), "exact": False, "negate": False})
    return terms


def get_variants(term):
    """Return a list of singular/plural variants for a term.

    For exact terms, return only the original. For non-exact terms,
    return the original plus its singular and plural forms.
    """
    if term["exact"]:
        return [term["value"]]

    word = term["value"]
    variants = {word}

    plural = _engine.plural(word)
    if plural:
        variants.add(plural.lower())

    singular = _engine.singular_noun(word)
    if singular and singular is not False:
        variants.add(singular.lower())

    return sorted(variants)
