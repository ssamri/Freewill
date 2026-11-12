"""Which language a text is written in, French or English, by counting common words.

The interface can guarantee the language of its own strings; it cannot
guarantee the language a model writes in. A small local model asked for French
may answer in English. This module tells the two apart well enough to notice,
with no model and no dependency, and says "unknown" when a text is too short
or too mixed to decide. It is a check, not a translator: nothing is rewritten.
"""

from __future__ import annotations

import re

_WORDS = {
    "fr": set("""le la les un une des du de au aux et ou mais donc car ni que qui quoi dont où ce cette ces cet
        je tu il elle nous vous ils elles on me te se moi toi lui leur leurs mon ma mes ton ta tes son sa ses notre
        votre nos vos est sont suis es sommes êtes était étais être avoir ai as avons avez ont avait pas ne plus
        très bien aussi avec sans pour par dans sur sous chez entre vers comme quand parce si oui non peut
        veux fait faire dit dire c'est j'ai n'est qu'il d'un d'une l'on aujourd'hui pourquoi comment encore
        rien tout tous toute toutes cela ça ici là alors déjà même autre""".split()),
    "en": set("""the a an and or but so because nor that which who whom whose what where when why how this these
        those i you he she we they me him her us them my your his its our their mine yours is are am was were be
        been being have has had do does did not no yes very well also with without for by in on under at into
        from about as if can could would should will shall may might must it's i'm don't isn't there here
        then already same other nothing everything all some any just only still today""".split()),
}
_TOKEN = re.compile(r"[a-zàâäçéèêëîïôöùûüÿœæ']+", re.I)
_ACCENTS = re.compile(r"[àâçéèêëîïôùûüœ]", re.I)
NAMES = {"en": {"en": "English", "fr": "French"}, "fr": {"en": "anglais", "fr": "français"}}


def detect(text: str, *, minimum: int = 4) -> str | None:
    """'fr', 'en', or None when the text is too short or too balanced to tell."""
    tokens = [t.lower().strip("'") for t in _TOKEN.findall(text or "")]
    if not tokens:
        return None
    scores = {code: sum(1 for t in tokens if t in words) for code, words in _WORDS.items()}
    scores["fr"] += min(3, len(_ACCENTS.findall(text or "")) // 2)
    total = scores["fr"] + scores["en"]
    if total < minimum:
        return None
    best = max(scores, key=scores.get)
    other = "en" if best == "fr" else "fr"
    if scores[best] < 2 * scores[other]:  # mixed: do not decide
        return None
    return best


_QUOTED = re.compile(r"«[^»]*»|“[^”]*”|\"[^\"]*\"")


def mismatch(fields: dict, expected: str) -> str | None:
    """The language detected in a model's answer when it is clearly not the expected one, else None.

    Only what the being writes in its own voice counts (what it says, thinks and gives as a reason);
    a quotation of the other person's words, between quotation marks, is left out.
    """
    if expected not in _WORDS:
        return None
    text = " ".join(str(fields.get(k) or "") for k in ("say", "thought", "reason"))
    found = detect(_QUOTED.sub(" ", text))
    return found if found and found != expected else None
