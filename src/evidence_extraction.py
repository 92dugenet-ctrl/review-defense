"""V6.6 deterministic evidence fact suggestion engine.

Only extracts bounded facts from explicitly readable text evidence. Suggestions are
never verified automatically and never trigger decisions or Google actions.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from hashlib import sha256
import re
from typing import Iterable

@dataclass(frozen=True)
class FactSuggestion:
    suggestion_id: str
    evidence_id: str
    key: str
    kind: str
    value: str
    source_location: str
    confidence: float
    verified: bool = False

_AMOUNT = re.compile(r"(?P<num>\d+(?:[\.,]\d{1,2})?)\s*(?P<currency>€|euros?|eur|\$|usd|dollars?)", re.I)
_DURATION = re.compile(r"(?P<num>\d+(?:[\.,]\d+)?)\s*(?P<unit>h|heures?|hours?|min|minutes?)", re.I)
_DATE = re.compile(r"\b(?:le\s+)?(?P<day>\d{1,2})[/-](?P<month>\d{1,2})(?:[/-](?P<year>\d{2,4}))?\b", re.I)


def _norm_num(value: str) -> str:
    value = value.replace(',', '.')
    return value.rstrip('0').rstrip('.') if '.' in value else value.lstrip('0') or '0'


def _suggestion_id(evidence_id: str, key: str, kind: str, value: str, location: str) -> str:
    raw = '|'.join((evidence_id, key, kind, value, location))
    return 'sug_' + sha256(raw.encode()).hexdigest()[:24]


def extract_text_fact_suggestions(*, evidence_id: str, content: bytes, content_type: str) -> tuple[FactSuggestion, ...]:
    if content_type.lower() not in {'text/plain', 'text/csv', 'application/json'}:
        return ()
    text = content.decode('utf-8', errors='strict')
    out: list[FactSuggestion] = []
    for line_no, line in enumerate(text.splitlines() or [text], 1):
        loc = f"line:{line_no}"
        for m in _AMOUNT.finditer(line):
            cur = m.group('currency').lower().replace('euros', 'eur').replace('euro', 'eur').replace('$', 'usd').replace('€', 'eur').replace('dollars', 'usd')
            value = _norm_num(m.group('num'))
            key = f"amount:{cur}"
            out.append(FactSuggestion(_suggestion_id(evidence_id,key,'AMOUNT',value,loc), evidence_id, key, 'AMOUNT', value, loc, 0.95))
        for m in _DURATION.finditer(line):
            unit = m.group('unit').lower(); n = float(m.group('num').replace(',', '.'))
            minutes = n * 60 if unit.startswith(('h','heure','hour')) else n
            value = _norm_num(str(minutes))
            key = 'duration:minutes'
            out.append(FactSuggestion(_suggestion_id(evidence_id,key,'DURATION',value,loc), evidence_id, key, 'DURATION', value, loc, 0.94))
        for m in _DATE.finditer(line):
            year = m.group('year') or ''
            if len(year) == 2: year = '20' + year
            value = f"{int(m.group('day')):02d}-{int(m.group('month')):02d}" + (f"-{year}" if year else '')
            key = 'date:day'
            out.append(FactSuggestion(_suggestion_id(evidence_id,key,'DATE',value,loc), evidence_id, key, 'DATE', value, loc, 0.90))
    # Stable de-duplication while retaining first source location.
    seen: set[str] = set(); unique: list[FactSuggestion] = []
    for item in out:
        if item.suggestion_id not in seen:
            seen.add(item.suggestion_id); unique.append(item)
    return tuple(unique)
