"""
Smart name resolver: determines whether a prospect name looks like a real
person's name or a brand/business name, and returns the appropriate greeting.

Rules:
- If it looks like a person name (e.g. "Britteny La'Shay") → use first name: "Hey Britteny"
- If it looks like a brand/org (e.g. "Arab Youtubers Reaction") → use: "Hey {app_name} Team"
- If it's junk (e.g. "12 34", "TEST TEST") → use: "Hey there"
"""

import re
import unicodedata


# Names that are clearly test/junk
JUNK_PATTERNS = [
    r"^\d",                    # starts with a digit
    r"^test\b",               # starts with "test"
    r"^qa\b",                 # starts with "qa"
    r"^demo\b",               # starts with "demo"
    r"^admin\b",              # starts with "admin"
    r"^user\b",               # starts with "user"
    r"^sample\b",             # starts with "sample"
]

# Words that signal a brand/org name rather than a person
BRAND_SIGNALS = [
    "network", "studio", "studios", "media", "group", "team", "agency",
    "academy", "fitness", "coaching", "collective", "hub", "club",
    "reaction", "youtubers", "tv", "official", "global", "pro",
    "digital", "online", "solutions", "services", "consulting",
    "wellness", "health", "training", "institute", "foundation",
]


def _is_latin(text):
    """Check if text is primarily Latin characters."""
    latin_count = sum(1 for c in text if unicodedata.category(c).startswith(("L",)) and ord(c) < 0x0250)
    total_letters = sum(1 for c in text if unicodedata.category(c).startswith(("L",)))
    if total_letters == 0:
        return False
    return latin_count / total_letters > 0.7


def _is_junk(name):
    """Check if name matches junk patterns."""
    lower = name.lower().strip()
    for pattern in JUNK_PATTERNS:
        if re.search(pattern, lower):
            return True
    return False


def _is_brand_name(name):
    """Check if name looks like a brand/business name rather than a person."""
    words = name.lower().strip().split()

    # Single word names that are 3+ words long are likely brands
    if len(words) >= 3:
        # But "John Michael Smith" is still a person — check for brand signals
        for word in words:
            if word in BRAND_SIGNALS:
                return True

    # Check for brand signals in any position
    for word in words:
        if word in BRAND_SIGNALS:
            return True

    return False


def _looks_like_person_name(name):
    """
    Heuristic: a person's name is typically 2-3 Latin words,
    each starting with a capital letter, no numbers.
    """
    name = name.strip()

    # Must be Latin characters
    if not _is_latin(name):
        return False

    words = name.split()

    # Typically 1-3 words
    if len(words) < 1 or len(words) > 4:
        return False

    # Each word should start with a letter (allow apostrophes, hyphens)
    for word in words:
        cleaned = word.strip("'\"")
        if not cleaned or not cleaned[0].isalpha():
            return False

    return True


def resolve_greeting(name, app_name=None):
    """
    Returns (greeting_name, is_personal).

    - greeting_name: the name to use in "Hey {greeting_name}"
    - is_personal: True if we're addressing a person, False if a team/brand

    Examples:
        "Britteny La'Shay" → ("Britteny", True)
        "Arab Youtubers Reaction" → ("Arab Youtubers Reaction Team", False)
        "12 34" → ("there", False)
        "反射的棱镜" → ("there", False)
    """
    if not name or not name.strip():
        return "there", False

    name = name.strip()

    # Junk → generic
    if _is_junk(name):
        return "there", False

    # Non-Latin → use app_name + Team, or generic
    if not _is_latin(name):
        if app_name and _is_latin(app_name):
            return f"{app_name.strip()} Team", False
        return "there", False

    # Brand name → "{name} Team"
    if _is_brand_name(name):
        return f"{name.strip()} Team", False

    # Looks like a person → use first name
    if _looks_like_person_name(name):
        first_name = name.strip().split()[0]
        # Title-case the first name
        first_name = first_name.capitalize() if first_name.islower() else first_name
        return first_name, True

    # Fallback: use app_name + Team or generic
    if app_name and app_name.strip() != name.strip():
        return f"{app_name.strip()} Team", False
    return f"{name.strip()} Team", False


if __name__ == "__main__":
    # Test cases
    tests = [
        ("Britteny La'Shay", "Britteny La'Shay"),
        ("Arab Youtubers Reaction", "Arab Youtubers Reaction"),
        ("Brittney Carr", "Brittney Carr"),
        ("Travis Lodatz", "Travis Lodatz"),
        ("12 34", "12 34"),
        ("TEST TEST", "TEST TEST"),
        ("QA  Coach Type", "QA  Coach Type"),
        ("反射的棱镜", "反射的棱镜"),
        ("Loroly Network", "Loroly Network"),
        ("Jess Foster", "Jess Foster"),
        ("Fred", "Fred"),
        ("sanchez brown", "sanchez brown"),
        ("va grim", "va grim"),
    ]
    for name, app_name in tests:
        greeting, personal = resolve_greeting(name, app_name)
        tag = "PERSON" if personal else "TEAM  "
        print(f"  {tag}  {name:35s} → Hey {greeting}")
