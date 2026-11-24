"""Deterministic format 2.0 key-schema checks and gate reachability."""

from __future__ import annotations

import itertools
import math
import operator
import re
from collections import defaultdict
from collections.abc import Iterable
from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal

ROLES = {
    "prohibition": "prohibition",
    "obligation": "obligation",
    "permission_exception": "exception",
    "condition_scope": "scope",
}
CHOICE_OPS = ("in", "not_in")
NUMBER_OPS = ("lt", "le", "gt", "ge", "between")
TOKEN = re.compile(r"[^\s=+?]+")
NUMBER_TOKEN = re.compile(r"-?[0-9]+(?:\.[0-9]+)?")
WORD = re.compile(r"[^\W_]+")


def normalized(text):
    """Use the same case-folding and whitespace matching as term references."""
    return " ".join(text.casefold().split()) if isinstance(text, str) else ""


def clause_map(terms_doc):
    """Index source clauses. Embedded 1.6 text or summary is the evidence, not a label."""
    terms = terms_doc.get("clauses", []) if isinstance(terms_doc, dict) else []
    return {
        clause["id"]: clause for clause in terms
        if isinstance(clause, dict) and isinstance(clause.get("id"), str)
    } if isinstance(terms, list) else {}


def dimension_map(keys):
    dims = keys.get("dimensions") if isinstance(keys, dict) else None
    return {
        dim["key"]: dim for dim in dims
        if isinstance(dim, dict) and isinstance(dim.get("key"), str)
    } if isinstance(dims, list) else {}


def _refs(clause, kind):
    refs = clause.get("refs", [])
    result = {
        r["to"] for r in refs
        if isinstance(r, dict) and r.get("kind") == kind and isinstance(r.get("to"), str)
    } if isinstance(refs, list) else set()
    if kind == "modifies" and isinstance(clause.get("modifies"), str) and clause["modifies"]:
        result.add(clause["modifies"])
    return result


def _source_text(clause):
    return normalized(clause.get("text") or clause.get("summary"))


def anchor_sources(clauses, term):
    """An anchor may occur verbatim in the term or a directly linked definition."""
    clause = clauses.get(term, {})
    return {
        term: _source_text(clause),
        **{
            target: _source_text(clauses[target])
            for target in sorted(_refs(clause, "uses_definition"))
            if clauses.get(target, {}).get("class") == "definition"
        },
    }


def _numeric(value):
    return type(value) is int or (type(value) is float and math.isfinite(value))


def _dec(value):
    return Decimal(str(value))


def decimal_token(value):
    if not value:
        return "0"
    token = format(_dec(value), "f")
    return token.rstrip("0").rstrip(".") if "." in token else token


_SMALL = dict(zip(
    ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"],
    range(20),
))
_TENS = dict(zip(
    ["twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"], range(20, 100, 10)
))
_SCALE = {"hundred": 100, "thousand": 1_000, "million": 1_000_000, "billion": 1_000_000_000}
_NUMBER_WORDS = _SMALL.keys() | _TENS.keys() | _SCALE.keys() | {"and", "point", "minus", "negative"}
_NUMERIC_WORD_MATCH = re.compile(
    r"(?<![\w.])-?[0-9]+(?:,[0-9]{3})*(?:\.[0-9]+)?(?!\w)|[^\W\d_]+"
)
_UNITS = {
    "year": ("yr", "yrs", "year-old", "years-old"), "month": ("mo", "mos"), "week": ("wk", "wks"),
    "day": (), "hour": ("hr", "hrs", "h"), "minute": ("min", "mins"),
    "second": ("sec", "secs", "s"), "millisecond": ("ms",), "dollar": ("usd", "$"),
    "euro": ("eur", "€"), "pound sterling": ("gbp", "£"), "percent": ("per cent", "%"),
    "byte": ("b",), "kilobyte": ("kb",), "megabyte": ("mb",), "gigabyte": ("gb",),
    "gram": ("g",), "kilogram": ("kg",), "meter": ("metre", "m"), "mile": ("mi",),
}


def _cardinal(words):
    """Read the cardinal portion of an anchor, including conventional hyphenation."""
    if not words:
        return None
    sign = -1 if words[0] in {"minus", "negative"} else 1
    if sign == -1:
        words = words[1:]
    if "point" in words:
        at = words.index("point")
        left, right = words[:at], words[at + 1:]
        whole = _cardinal(left) if left else 0
        if whole is None or not right or any(w not in _SMALL or _SMALL[w] > 9 for w in right):
            return None
        digits = "".join(str(_SMALL[w]) for w in right)
        return sign * _dec(f"{whole}.{digits}")
    if not words or words[0] == "and" or words[-1] == "and":
        return None
    total = current = 0
    previous = None
    major = float("inf")
    for word in words:
        if word == "and":
            if previous not in _SCALE:
                return None
        elif word == "hundred":
            if previous not in _SMALL or not 0 < current < 10:
                return None
            current *= 100
        elif word in _SCALE:
            scale = _SCALE[word]
            if not current or scale >= major:
                return None
            total, current, major = total + current * scale, 0, scale
        elif word in _TENS or word in _SMALL:
            if previous in _SMALL or previous in _TENS and (word not in _SMALL or _SMALL[word] > 9):
                return None
            current += _TENS[word] if word in _TENS else _SMALL[word]
        else:
            return None
        previous = word
    return sign * _dec(total + current)


def _number_mentions(anchor):
    """Return numeric values and their character spans."""
    tokens = list(_NUMERIC_WORD_MATCH.finditer(anchor))
    i = 0
    while i < len(tokens):
        match = tokens[i]
        word = match.group()
        if NUMBER_TOKEN.fullmatch(word.replace(",", "")):
            yield _dec(word.replace(",", "")), match.start(), match.end()
            i += 1
            continue
        if word not in _NUMBER_WORDS or word == "and":
            i += 1
            continue
        candidates = [word]
        end = i + 1
        while (
            end < len(tokens)
            and tokens[end].group() in _NUMBER_WORDS
            and re.fullmatch(r"[\s-]+", anchor[tokens[end - 1].end():tokens[end].start()])
        ):
            candidates.append(tokens[end].group())
            end += 1
        for width in range(len(candidates), 0, -1):
            if (number := _cardinal(candidates[:width])) is not None:
                yield number, match.start(), tokens[i + width - 1].end()
                i += width
                break
        else:
            i += 1


def _unit_aliases(unit):
    name = normalized(unit)
    for canonical, alternatives in _UNITS.items():
        aliases = {canonical, canonical + "s", *alternatives}
        if name in aliases:
            return canonical, aliases
    base = name[:-1] if name.endswith("s") and len(name) > 2 else name
    return base, {base, base + "s"}


def _explicit_units(anchor, spans, units):
    suffixes = {}
    for unit in (*_UNITS, *units):
        canonical, aliases = _unit_aliases(unit)
        for spelling in aliases - {""}:
            suffixes.setdefault(spelling, canonical)
    alternatives = "|".join(re.escape(x) for x in sorted(suffixes, key=lambda x: (-len(x), x)))
    found = set()
    for start, end in spans:
        suffix = re.match(rf"^[\s-]*({alternatives})(?!\w)", anchor[end:])
        if suffix:
            found.add(suffixes[suffix[1]])
        prefix = re.search(r"([$€£])\s*$", anchor[:start])
        if prefix:
            found.add(suffixes[prefix[1]])
    return found


def _operators(leaf):
    return [op for op in (*CHOICE_OPS, *NUMBER_OPS) if op in leaf]


def key_leaves(key):
    """Return leaves, stripping the key ID from the shape only during compilation."""
    return key["any"] if isinstance(key, dict) and "any" in key else [key]


def _dispositions(keys):
    raw = keys.get("not_encoded", [])
    if not isinstance(raw, list):
        return {}
    return {
        e["clause"]: e["reason"]
        for e in raw
        if isinstance(e, dict) and isinstance(e.get("clause"), str) and normalized(e.get("reason"))
    }


def _canonical_key(key):
    leaves = []
    for leaf in key_leaves(key):
        if not isinstance(leaf, dict) or len(ops := _operators(leaf)) != 1:
            raise ValueError(f"not a canonicalizable key: {key!r}")
        op = ops[0]
        raw = leaf[op]
        if op in CHOICE_OPS:
            payload = tuple(sorted(set(raw)))
        elif op == "between":
            payload = tuple(decimal_token(v) for v in raw)
        else:
            payload = (decimal_token(raw),)
        leaves.append((leaf["dim"], op, payload))
    return tuple(sorted(set(leaves)))


def canonical_term(term):
    """Compare role and gate/require structure, ignoring titles, IDs and anchor prose."""
    return {
        "role": term["role"],
        **{side: sorted({_canonical_key(key) for key in term.get(side, [])})
           for side in ("gate", "require")},
    }


def keys_diff(a, b):
    """Compare two independent parses; every disagreeing term gets a before/after."""
    def profiles(doc):
        return {
            **{cid: {"not_encoded": True} for cid in _dispositions(doc)},
            **{cid: canonical_term(term) for cid, term in doc.get("terms", {}).items()},
        }

    left, right = profiles(a), profiles(b)
    terms = sorted(left.keys() | right.keys())
    differences = [
        {"term": term, "a": left.get(term), "b": right.get(term)}
        for term in terms if left.get(term) != right.get(term)
    ]
    total = len(terms)
    matched = total - len(differences)
    return {"score": matched / total if total else 1.0, "total": total, "matched": matched,
            "differences": differences}


def _number_satisfies(op, payload, value):
    if op == "between":
        return _dec(payload[0]) <= value <= _dec(payload[1])
    bound = _dec(payload)
    return {"lt": value < bound, "le": value <= bound, "gt": value > bound, "ge": value >= bound}[op]


def _number_witness(dim, leaves):
    lo = _dec(dim["min"]) if "min" in dim else None
    hi = _dec(dim["max"]) if "max" in dim else None
    bounds = {_dec(v) for leaf in leaves for op in _operators(leaf)
              for v in (leaf[op] if op == "between" else [leaf[op]])}
    bounds.update(v for v in (lo, hi) if v is not None)
    ordered = sorted(bounds)
    candidates = set(ordered)
    if dim.get("integer"):
        for b in ordered:
            floor, ceil = b.to_integral_value(rounding=ROUND_FLOOR), b.to_integral_value(rounding=ROUND_CEILING)
            candidates.update((floor - 1, floor, ceil, ceil + 1))
        candidates = {v for v in candidates if v == v.to_integral_value()}
    else:
        candidates.update((a + b) / 2 for a, b in itertools.pairwise(ordered))
        if ordered:
            candidates.update((ordered[0] - 1, ordered[-1] + 1))
    for value in sorted(candidates | {Decimal(0)}):
        if (lo is None or value >= lo) and (hi is None or value <= hi) and all(
            _number_satisfies(op, leaf[op], value) for leaf in leaves for op in _operators(leaf)
        ):
            return decimal_token(value)
    return None


def witness(leaves, dims):
    """Find one fully assigned vector satisfying a conjunction of validated leaves."""
    per_dim = defaultdict(list)
    for leaf in leaves:
        per_dim[leaf["dim"]].append(leaf)
    feats = {}
    for key, checks in per_dim.items():
        dim = dims[key]
        if dim.get("type", "choice") == "number":
            value = _number_witness(dim, checks)
        else:
            forbidden = set().union(*(check["not_in"] for check in checks if "not_in" in check))
            allowed = [v for v in dim["values"] if v not in forbidden]
            positive = [set(check["in"]) for check in checks if "in" in check]
            if dim.get("multi"):
                picks = [next((v for v in allowed if v in group), None) for group in positive]
                value = None if None in picks else "+".join(v for v in allowed if v in picks)
                if not positive:
                    value = allowed[0] if allowed else None
            else:
                value = next((v for v in allowed if all(v in group for group in positive)), None)
        if value is None:
            return None
        feats[key] = value
    return feats


def gate_paths(terms, term_id):
    """Yield each ancestor path's conjunctive groups, then the term's gate groups."""
    term = terms[term_id]
    own = [key_leaves(key) for key in term.get("gate", [])]
    parents = term.get("parents", [])
    if not parents:
        yield own
    for parent in parents:
        for outer in gate_paths(terms, parent):
            yield [*outer, *own]


def gate_witness(keys, term_id):
    """Return a vector activating the term via any parent path (validated tree only)."""
    dims = dimension_map(keys)

    def visit(groups, at, chosen, vector):
        if at == len(groups):
            return vector
        for leaf in groups[at]:
            extended = [*chosen, leaf]
            partial = witness(extended, dims)
            if partial is not None and (found := visit(groups, at + 1, extended, partial)) is not None:
                return found
        return None

    for groups in gate_paths(keys["terms"], term_id):
        if (found := visit(groups, 0, [], {})) is not None:
            return found
    return None


def _metric(matched, total):
    return {"score": matched / total if total else 1.0, "total": total, "matched": matched}


def _parse_dim(dim, subjective, errors):
    if not isinstance(dim, dict) or not isinstance(key := dim.get("key"), str):
        errors.append("dimension must be an object with a key")
        return None
    if not TOKEN.fullmatch(key) or key == "date":
        errors.append(f"dimension {key!r}: invalid code key")
    if key.casefold() in subjective:
        errors.append(f"dimension {key!r}: subjective word")
    if not normalized(dim.get("question")) or not normalized(dim.get("evidence")):
        errors.append(f"dimension {key}: question and evidence are required")
    dimension_type = dim.get("type", "choice")
    if dimension_type == "choice":
        values = dim.get("values")
        if not isinstance(values, dict) or not values:
            errors.append(f"dimension {key}: choice dimensions require a nonempty values object")
        else:
            for value in values:
                if not isinstance(value, str) or not TOKEN.fullmatch(value) or NUMBER_TOKEN.fullmatch(value):
                    errors.append(f"dimension {key}: invalid choice value {value!r}")
                if isinstance(value, str) and value.casefold() in subjective:
                    errors.append(f"dimension {key}: subjective choice value {value!r}")
            if "default" in dim and dim["default"] is not None:
                default = dim["default"]
                members = default.split("+") if isinstance(default, str) else []
                if not members or any(v not in values for v in members) or (
                    len(members) > 1 and not dim.get("multi")
                ):
                    errors.append(f"dimension {key}: invalid choice default")
    elif dimension_type == "number":
        if "values" in dim or dim.get("multi"):
            errors.append(f"dimension {key}: number dimensions have no values and cannot be multi")
        if not normalized(dim.get("unit")):
            errors.append(f"dimension {key}: number dimensions require a unit")
        for field in ("min", "max", "default"):
            if field in dim and not (field == "default" and dim[field] is None) and not _numeric(dim[field]):
                errors.append(f"dimension {key}: {field} must be a finite number")
        if _numeric(dim.get("min")) and _numeric(dim.get("max")) and dim["min"] > dim["max"]:
            errors.append(f"dimension {key}: min cannot exceed max")
        if "integer" in dim and not isinstance(dim["integer"], bool):
            errors.append(f"dimension {key}: integer must be a boolean")
        if key.casefold() == "age" and dim.get("fixable"):
            errors.append(f"dimension {key}: age cannot be fixable")
    else:
        errors.append(f"dimension {key}: type must be choice or number")
    if "multi" in dim and not isinstance(dim["multi"], bool):
        errors.append(f"dimension {key}: multi must be a boolean")
    return key


def lint_keys(keys: dict, terms_doc: dict, *, duty: dict | None = None,
              subjective: Iterable[str] = ()) -> dict:
    """Validate the frozen vocabulary, key anchors, term coverage, and reachability."""
    errors, warnings = [], []
    metrics = {"terms_coverage": _metric(0, 0), "key_anchors": _metric(0, 0)}
    result = {"errors": errors, "warnings": warnings, "metrics": metrics}
    if not isinstance(keys, dict):
        errors.append("keys.json must be an object")
        return result
    clauses = clause_map(terms_doc)
    if not clauses:
        errors.append("terms.json has no source clauses")
    source = keys.get("dimensions")
    if not isinstance(source, list):
        errors.append("keys.json dimensions must be an array")
        source = []
    dims = {}
    value_sets = {}
    subjective = {word.casefold() for word in subjective}
    for dim in source:
        key = _parse_dim(dim, subjective, errors)
        if key is None:
            continue
        if key in dims:
            errors.append(f"duplicate dimension: {key}")
        dims[key] = dim
        if isinstance(dim.get("values"), dict):
            values = frozenset(dim["values"])
            if values in value_sets:
                warnings.append(f"dimensions {value_sets[values]} and {key} have the same value set")
            else:
                value_sets[values] = key
    units = [dim.get("unit") for dim in dims.values() if normalized(dim.get("unit"))]
    terms = keys.get("terms")
    if not isinstance(terms, dict):
        errors.append("keys.json terms must be an object")
        return result
    dispositions = _dispositions(keys)
    raw_dispositions = keys.get("not_encoded", [])
    if not isinstance(raw_dispositions, list) or len(raw_dispositions) != len(dispositions):
        errors.append("not_encoded needs unique clause entries with a nonempty reason")
    for cid in sorted(dispositions):
        if not isinstance(klass := clauses.get(cid, {}).get("class"), str) or klass not in ROLES:
            errors.append(f"{cid}: not_encoded must reference a normative clause")
        if cid in terms:
            errors.append(f"{cid}: cannot have keys and a not_encoded entry")

    normative = {
        cid for cid, clause in clauses.items()
        if isinstance(klass := clause.get("class"), str) and klass in ROLES
        and clause.get("confidence") in ("high", "medium")
    }
    covered = {
        cid for cid, term in terms.items() if isinstance(term, dict)
        and any(isinstance(term.get(side), list) and term[side] for side in ("gate", "require"))
    } | dispositions.keys()
    for cid in sorted(normative - covered):
        errors.append(f"{cid}: normative clause has no keys or not_encoded reason")
    metrics["terms_coverage"] = _metric(len(normative & covered), len(normative))

    parents_by_term = {}
    touched_by_dim = defaultdict(set)
    anchor_count = anchor_matches = 0
    for cid, term in terms.items():
        if not isinstance(term, dict):
            errors.append(f"{cid}: term must be an object")
            continue
        clause = clauses.get(cid, {})
        role = term.get("role")
        klass = clause.get("class")
        expected = ROLES.get(klass) if isinstance(klass, str) else None
        if expected is None:
            errors.append(f"{cid}: unknown or descriptive clause cannot have keys")
        elif role != expected:
            errors.append(f"{cid}: role must be {expected!r} for class {clause['class']!r}")
        if not normalized(term.get("title")):
            errors.append(f"{cid}: title must be nonempty")
        if role in ("prohibition", "obligation") and not normalized(term.get("next_step")):
            errors.append(f"{cid}: next_step must be nonempty for a compiled rule")
        if "binds" in clause and term.get("binds") != clause["binds"]:
            errors.append(f"{cid}: binds must match the filtered term")
        if "binds" in term and not normalized(term["binds"]):
            errors.append(f"{cid}: binds must be a nonempty party name")
        parents = term.get("parents")
        if not isinstance(parents, list) or any(not isinstance(p, str) or not p for p in parents):
            errors.append(f"{cid}: parents must be an array of term IDs")
            parents = []
        elif len(set(parents)) != len(parents):
            errors.append(f"{cid}: parent IDs must be unique")
        parents_by_term[cid] = parents
        for parent in parents:
            if not isinstance(terms.get(parent), dict):
                errors.append(f"{cid}: missing parent {parent}")
        if role == "exception":
            targets = _refs(clause, "modifies")
            if not parents or set(parents) != targets:
                errors.append(f"{cid}: exception parents must equal its modifies targets")
        if role == "obligation" and not term.get("require"):
            errors.append(f"{cid}: obligation needs require keys")
        if role != "obligation" and term.get("require"):
            errors.append(f"{cid}: only obligations have require keys")
        seen = set()
        texts = anchor_sources(clauses, cid)
        clause_text = texts.get(cid, "")
        touched_spans = []
        for side in ("gate", "require"):
            raw = term.get(side, [])
            if not isinstance(raw, list):
                errors.append(f"{cid}: {side} must be an array")
                continue
            for key in raw:
                if not isinstance(key, dict) or not normalized(key.get("id")):
                    errors.append(f"{cid}: {side} key needs an id")
                    continue
                kid = key["id"]
                label = f"{cid}.{kid}"
                if not TOKEN.fullmatch(kid):
                    errors.append(f"{label}: invalid key id")
                if kid in seen:
                    errors.append(f"{label}: duplicate key id")
                seen.add(kid)
                leaves = key_leaves(key)
                if not isinstance(leaves, list) or not leaves:
                    errors.append(f"{label}: any must be a nonempty list of leaves")
                    continue
                if "any" in key and ("dim" in key or _operators(key)):
                    errors.append(f"{label}: any cannot also be a leaf")
                for leaf in leaves:
                    anchor_count += 1
                    if not isinstance(leaf, dict):
                        errors.append(f"{label}: key leaf must be an object")
                        continue
                    dim_name = leaf.get("dim")
                    dim = dims.get(dim_name) if isinstance(dim_name, str) else None
                    if dim is None:
                        errors.append(f"{label}: unknown dimension {dim_name!r}")
                    else:
                        touched_by_dim[dim_name].add(cid)
                    anchor = normalized(leaf.get("anchor"))
                    if anchor and any(anchor in source for source in texts.values()):
                        anchor_matches += 1
                        touched_spans.extend(m.span() for m in re.finditer(re.escape(anchor), clause_text))
                    else:
                        errors.append(f"{label}: anchor not found in the term or a linked definition")
                    operators = _operators(leaf)
                    if len(operators) != 1 or "any" in leaf:
                        errors.append(f"{label}: key leaf needs exactly one operator")
                        continue
                    op = operators[0]
                    raw_value = leaf[op]
                    if dim is None:
                        continue
                    if dim.get("type", "choice") == "number":
                        bounds = raw_value if op == "between" and isinstance(raw_value, list) else [raw_value]
                        size = 2 if op == "between" else 1
                        if (op not in NUMBER_OPS or len(bounds) != size
                                or not all(_numeric(v) for v in bounds)
                                or op == "between" and bounds[0] > bounds[1]):
                            errors.append(f"{label}: invalid number comparison")
                            continue
                        mentions = list(_number_mentions(anchor))
                        for bound in bounds:
                            spans = [(start, end) for value, start, end in mentions if value == _dec(bound)]
                            if not spans:
                                errors.append(f"{label}: number {bound} not found in anchor")
                            elif normalized(dim.get("unit")):
                                explicit = _explicit_units(anchor, spans, units)
                                # A short anchor such as "under 18" can omit the stated unit.
                                # Inspect units immediately beside that bound in its source.
                                if not explicit:
                                    for source in texts.values():
                                        for occurrence in re.finditer(re.escape(anchor), source):
                                            start = occurrence.start()
                                            explicit |= _explicit_units(
                                                source, [(start + a, start + b) for a, b in spans],
                                                units,
                                            )
                                unit, _ = _unit_aliases(dim["unit"])
                                if explicit - {unit}:
                                    errors.append(f"{label}: anchor unit does not match {dim['unit']!r}")
                    elif (op not in CHOICE_OPS or not isinstance(raw_value, list) or not raw_value
                          or any(not isinstance(v, str) for v in raw_value)):
                        errors.append(f"{label}: invalid choice comparison")
                    elif isinstance(dim.get("values"), dict):
                        invalid = sorted(set(raw_value) - dim["values"].keys())
                        if invalid:
                            errors.append(f"{label}: unknown values for {dim_name}: {invalid}")
                    _lint_preset(leaf, key, dim, label, texts, errors)
        unanchored = [m.group() for m in WORD.finditer(clause_text)
                      if not any(a <= m.start() and m.end() <= b for a, b in touched_spans)]
        if unanchored:
            warnings.append(f"{cid}: words outside key anchors: {' '.join(unanchored)}")

    metrics["key_anchors"] = _metric(anchor_matches, anchor_count)
    _lint_tree(clauses, parents_by_term, errors, warnings)
    if not errors:
        for cid, term in terms.items():
            if term.get("parents") and gate_witness(keys, cid) is None:
                errors.append(f"{cid}: child gate cannot be satisfied with any parent path")
    _lint_shared_duty(keys, terms, clauses, touched_by_dim, duty, warnings)
    return result


def _lint_preset(leaf, key, dim, label, texts, errors):
    if "preset" not in leaf and "preset" not in key:
        return
    preset = leaf if "preset" in leaf else key
    value = preset["preset"]
    if isinstance(value, dict):
        preset = value
        value = preset.get("value")
    anchor = normalized(preset.get("preset_anchor", preset.get("anchor")))
    if preset.get("why") != "stated" or not anchor or not any(
        anchor in text for text in texts.values()
    ):
        errors.append(f"{label}: explicit preset needs why='stated' and a source anchor")
    if dim.get("type", "choice") == "number":
        if not _numeric(value) or (
            dim.get("integer") and _dec(value) != _dec(value).to_integral_value()
        ) or any(
            bound in dim and _numeric(dim[bound]) and compare(value, dim[bound])
            for bound, compare in (("min", operator.lt), ("max", operator.gt))
        ):
            errors.append(f"{label}: invalid numeric preset")
    elif not isinstance(value, str) or value not in (dim.get("values") or {}):
        errors.append(f"{label}: invalid choice preset")


def _lint_tree(clauses, parents, errors, warnings):
    active, done = [], set()

    def visit(cid):
        if cid in active:
            cycle = " -> ".join([*active[active.index(cid):], cid])
            errors.append(f"term tree cycle: {cycle}")
        elif cid not in done and cid in parents:
            active.append(cid)
            for parent in parents[cid]:
                visit(parent)
            active.pop()
            done.add(cid)

    for cid in parents:
        visit(cid)
        clause = clauses.get(cid, {})
        likely = _refs(clause, "subject_to") | _refs(clause, "condition_scope")
        for target in sorted(likely):
            if target not in parents[cid] and cid not in parents.get(target, []):
                warnings.append(f"{cid}: possible parent relation to {target} is not in the term tree")


def _lint_shared_duty(keys, terms, clauses, touched, duty, warnings):
    duty = duty if duty is not None else keys.get("duty")
    if not isinstance(duty, dict) or not isinstance(duty.get("parties"), list):
        return
    parties = {p for p in duty["parties"] if isinstance(p, str)}
    for key, owners in sorted(touched.items()):
        binds = [
            terms[cid].get("binds", clauses.get(cid, {}).get("binds"))
            for cid in sorted(owners)
        ]
        if any(isinstance(b, str) and b not in parties for b in binds) and any(
            not isinstance(b, str) or b in parties for b in binds
        ):
            warnings.append(f"dimension {key}: shared with a term that binds the user; no preset")
