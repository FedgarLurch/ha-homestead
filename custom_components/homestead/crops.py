"""Crop profiles: what each crop needs, and the weeks that follow from it here (no HA dependency).

``data/crops.json`` stores needs, not calendars: the cold a crop survives, the soil its seed sprouts in,
the heat that stops it, days to harvest, chill hours and bloom warmth for fruit trees. The weeks to sow,
plant out, harvest, prune and feed are worked out from the garden's own weather history (52 weekly
normals, ``climate.weekly_normals``), so the same file is right in Phoenix and in Milan. Without that
history the old frost-anchored windows from CropGraph are used. The user's corrections
(``CropProfile`` records) always win.
"""

from __future__ import annotations

import json
import re
from datetime import date, timedelta
from pathlib import Path
from typing import Any

DEFAULTS_FILE = Path(__file__).parent / "data" / "crops.json"
# Without enough history: typical dates for the plains of northern Italy.
FALLBACK_FROST = {"last_spring": "04-10", "first_fall": "10-31"}
ANNUAL_CATEGORIES = {"vegetable", "herb", "legume", "root", "flower", "grain"}
WEEKS = 52
# Woody habit by genus: CropGraph only says "fruit, perennial" for an apple, a raspberry and a vine.
GENUS_TYPES: dict[str, str] = {
    **dict.fromkeys(
        "malus pyrus prunus cydonia citrus fortunella ficus olea juglans castanea diospyros eriobotrya "
        "mespilus morus punica persea mangifera carya pistacia ziziphus annona feijoa acca sorbus".split(),
        "fruit_tree",
    ),
    **dict.fromkeys(
        "corylus rubus ribes vaccinium sambucus aronia hippophae elaeagnus rosa buxus hydrangea viburnum "
        "forsythia syringa philadelphus spiraea weigela berberis cotoneaster pyracantha photinia ligustrum "
        "pittosporum camellia rhododendron azalea hibiscus nerium myrtus laurus".split(),
        "shrub",
    ),
    **dict.fromkeys(
        "vitis actinidia passiflora wisteria hedera clematis jasminum trachelospermum lonicera "
        "parthenocissus bougainvillea humulus".split(),
        "vine",
    ),
    **dict.fromkeys(
        "quercus fagus acer pinus abies picea larix betula fraxinus tilia ulmus populus salix carpinus "
        "platanus cedrus cupressus magnolia robinia alnus aesculus celtis paulownia catalpa liquidambar "
        "ginkgo sequoia ostrya cercis albizia lagerstroemia".split(),
        "tree",
    ),
    # Herbaceous crops grown in the vegetable garden although CropGraph files them under fruit.
    **dict.fromkeys("fragaria rheum asparagus cynara cucumis citrullus physalis".split(), "vegetable"),
}
CATEGORY_TYPES = {
    "vegetable": "vegetable",
    "root": "vegetable",
    "legume": "vegetable",
    "grain": "vegetable",
    "sprout": "vegetable",
    "herb": "herb",
    "medicinal": "herb",
    "flower": "flower",
}
TRAITS = (
    "exposure",
    "hardiness_c",
    "sow_indoor",
    "sow_outdoor",
    "plant_out",
    "flowering",
    "harvest",
    "spacing_cm",
    "heat_max_c",
    "pruning",
    "fertilizing",
    "end",
)
CALENDAR = ("sow_indoor", "sow_outdoor", "plant_out", "flowering", "harvest", "pruning", "fertilizing", "end")
RANKS = {"var.", "var", "subsp.", "subsp", "convar.", "convar", "group", "f."}


def load_crops() -> dict[str, dict[str, Any]]:
    """Blocking: read the built-in table (needs per crop), keyed by normalized name."""
    raw = json.loads(DEFAULTS_FILE.read_text(encoding="utf-8"))
    return raw["crops"]


def normalize(name: str | None) -> str:
    """'Citrus x limon' → 'citrus limon'; 'Brassica oleracea var. italica' → 'brassica oleracea italica'."""
    words = re.sub(r"\s[x×]\s|×", " ", (name or "").lower()).replace("'", "").split()
    key = words[:2]
    rest = [w for w in words[2:] if w not in RANKS]
    if len(key) == 2 and rest and len(words) > 2 and (words[2] in RANKS or words[-1] == "group"):
        key.append(rest[0])
    return " ".join(key)


def lookup(
    name: str | None, table: dict[str, dict[str, Any]], hint: str | None = None
) -> dict[str, Any] | None:
    """The crop group named in ``hint`` (a planting's name or variety, e.g. 'Broccoli'), else the species,
    else a genus-level entry (e.g. 'Rosa' for 'Rosa canina')."""
    key = normalize(name)
    if not key:
        return None
    if key in table and len(key.split()) == 3:
        return table[key]
    species = " ".join(key.split()[:2])
    words = (hint or "").lower()
    if words:
        for other, entry in table.items():
            if other.startswith(species + " ") and any(
                re.search(rf"\b{re.escape(n)}\b", words) for n in entry.get("group_names") or []
            ):
                return entry
    return table.get(species) or table.get(species.split()[0])


def crop_traits(
    name: str | None, table: dict[str, dict[str, Any]], profiles: list[Any], hint: str | None = None
) -> dict[str, Any] | None:
    """The user's values for the species, else the built-in ones worked out for this garden."""
    key = normalize(name)
    species = " ".join(key.split()[:2])
    mine = next((p for p in profiles if normalize(p.species) in (key, species)), None) if key else None
    if mine is not None:
        return {trait: getattr(mine, trait, None) for trait in TRAITS}
    return lookup(name, table, hint)


def crop_hint(planting: Any) -> str:
    """The words that can name a crop group on a planting: its name and variety ('Broccoli 1', 'Romaine')."""
    return f"{getattr(planting, 'name', '') or ''} {getattr(planting, 'variety', '') or ''}".strip()


def plant_type(name: str | None, category: str | None = None) -> str | None:
    """Tree, fruit tree, shrub, vine from the genus; vegetable, herb, flower from the CropGraph category."""
    genus = normalize(name).split(" ")[0] if name else ""
    return GENUS_TYPES.get(genus) or CATEGORY_TYPES.get(category or "")


# --- Weeks and months --------------------------------------------------------------------------


def week_month(week: int) -> int:
    """Month of the middle of a week (0-based week of a non-leap year)."""
    return (date(2025, 1, 1) + timedelta(days=(week % WEEKS) * 7 + 3)).month


def to_months(weeks: set[int]) -> list[int]:
    return sorted({week_month(w) for w in weeks})


def _span(start: int, end: int) -> list[int]:
    """Weeks from ``start`` to ``end`` inclusive, across the new year."""
    return [w % WEEKS for w in range(start, end + 1)] if end >= start else []


class Climate:
    """The 52 weekly normals: mean max, mean min, and the coldest night of the week in 9 years out of 10."""

    def __init__(self, weeks: list[dict[str, Any]]) -> None:
        self.t_max = [w["t_max"] for w in weeks]
        self.t_min = [w["t_min"] for w in weeks]
        self.low = [w["low"] for w in weeks]
        self.mean = [(a + b) / 2 for a, b in zip(self.t_max, self.t_min, strict=True)]
        self.coldest = min(range(WEEKS), key=lambda w: self.mean[w])

    def alive(self, week: int, survives: float) -> bool:
        return self.low[week % WEEKS] > survives

    def soil(self, week: int) -> float:
        # Top soil follows the mean air temperature, a little warmer in the sun.
        return self.mean[week % WEEKS] + 1

    def bloom(self, gdd: float, base: float = 4.5) -> int | None:
        """First week after the coldest one whose warmth (degree days above ``base``) reaches ``gdd``."""
        total = 0.0
        for step in range(1, 40):
            week = self.coldest + step
            total += max(0.0, self.mean[week % WEEKS] - base) * 7
            if total >= gdd:
                return week % WEEKS
        return None


def _days(crop: dict[str, Any]) -> tuple[float, float, str] | None:
    info = crop.get("days_to_harvest")
    if not info or not info.get("days"):
        return None
    low, high = info["days"]
    return low, high, info.get("from") or "sow"


def _annual(crop: dict[str, Any], cl: Climate) -> dict[str, set[int]] | None:
    days = _days(crop)
    survives, stall = crop.get("survives_c"), crop.get("stalls_above_c")
    if days is None or survives is None or stall is None:
        return None
    early, late, counted_from = days
    mid = (early + late) / 2
    start = set(crop.get("start") or [])
    cool = crop.get("season") == "cool"
    fruiting = crop.get("fruiting", crop.get("season") == "warm" and crop.get("type") == "vegetable")
    set_weeks = 3 if fruiting else max(2, round(mid / 14)) if cool else 2
    soil_min, soil_max = crop.get("sprouts_soil_c") or [None, None]
    out: dict[str, set[int]] = {k: set() for k in CALENDAR}

    def grows(first: int, days_to: float) -> int | None:
        """First harvest week (earliest varieties) for a crop that starts in the ground on ``first``,
        or None if it dies of cold first or its first fruit (or head) meets the heat."""
        ready = first + max(1, round(days_to / 7))
        if not all(cl.alive(w, survives) for w in range(first, ready + 1)):
            return None
        if any(cl.t_max[w % WEEKS] > stall for w in range(ready - set_weeks + 1, ready + 1)):
            return None
        return ready

    def harvest(ready: int) -> list[int]:
        weeks = []
        span = round((late - early) / 7) + max(1, crop.get("harvest_weeks") or 3)
        for w in range(ready, ready + span):
            if not cl.alive(w, survives) or (cool and cl.t_max[w % WEEKS] > stall + 3):
                break
            weeks.append(w % WEEKS)
        return weeks

    def add(kind: str, week: int, ready: int) -> None:
        out[kind].add(week % WEEKS)
        picked = harvest(ready)
        out["harvest"].update(picked)
        if fruiting:
            out["flowering"].update(w % WEEKS for w in range(ready - set_weeks, ready))
        if crop.get("life") == "annual" or crop.get("grown_as") == "annual":
            last = (picked or [ready % WEEKS])[-1]
            out["end"].add((last + 1) % WEEKS)

    lead = crop.get("indoor_weeks") or [4, 6]
    for week in range(WEEKS):
        if "direct" in start and soil_min is not None and soil_min <= cl.soil(week) <= (soil_max or 99):
            to = early if counted_from == "sow" else early + 21
            if (ready := grows(week, to)) is not None:
                add("sow_outdoor", week, ready)
        # Transplants go in when it is not too hot for them to settle.
        settle = min(stall + 8, 35) if cool else stall + 6
        if start & {"transplant", "indoor"} and cl.t_max[week] <= settle:
            to = early if counted_from == "plant_out" else max(14, early - 21)
            if (ready := grows(week, to)) is not None:
                add("plant_out", week, ready)
                if "indoor" in start:
                    out["sow_indoor"].update(w % WEEKS for w in range(week - lead[1], week - lead[0] + 1))
    out["end"] -= out["harvest"]
    return out if out["plant_out"] or out["sow_outdoor"] else None


def _blooming(crop: dict[str, Any], cl: Climate) -> dict[str, Any] | None:
    """Fruit trees and other perennials that flower after the cold: bloom, harvest, pruning, feeding."""
    bloom = cl.bloom(crop["bloom_gdd"])
    if bloom is None:
        return None
    out: dict[str, Any] = {k: set() for k in CALENDAR}
    out["flowering"].update(_span(bloom - 1, bloom + 1))
    low, high = crop.get("bloom_to_harvest") or [60, 90]
    first, last = bloom + round(low / 7), bloom + round(high / 7)
    stall = crop.get("stalls_above_c")
    picked = [w for w in _span(first, max(last, first + (crop.get("harvest_weeks") or 3) - 1))]
    if stall is not None:
        picked = [w for w in picked if cl.t_max[w] <= stall + 3]
    out["harvest"].update(picked)
    end = max(first, last)
    survives = crop.get("survives_c", -10)
    evergreen = crop.get("evergreen")
    if crop.get("type") == "fruit_tree" and not evergreen:
        dormant = [w for w in _span(cl.coldest - 6, bloom - 2) if cl.mean[w] < 15]
        out["pruning"].update(dormant or _span(cl.coldest - 2, cl.coldest + 2))
        out["plant_out"].update(
            w for w in (dormant or _span(cl.coldest - 4, cl.coldest + 4)) if cl.alive(w, survives)
        )
        out["fertilizing"].update({(bloom - 1) % WEEKS, (end + 1) % WEEKS})
    elif crop.get("type") == "fruit_tree":
        out["pruning"].update(_span(end + 1, end + 4))
        out["fertilizing"].update({bloom % WEEKS, (bloom + 12) % WEEKS, (bloom + 28) % WEEKS})
        out["plant_out"].update(
            w for w in range(WEEKS) if cl.alive(w, survives + 2) and cl.t_max[w] <= 35 and cl.mean[w] >= 15
        )
    else:
        out["plant_out"].update(_mild(crop, cl))
        out["fertilizing"].add((bloom - 1) % WEEKS)
    damaged = crop.get("bloom_damaged_below_c")
    out["bloom_frost_risk"] = damaged is not None and any(cl.low[w] <= damaged for w in out["flowering"])
    return out


def _mild(crop: dict[str, Any], cl: Climate) -> set[int]:
    """Weeks to plant a perennial out: not frozen, not hot."""
    survives = crop.get("survives_c")
    return {
        w
        for w in range(WEEKS)
        if (survives is None or cl.alive(w, survives)) and cl.t_max[w] <= 32 and cl.mean[w] >= 7
    }


def _perennial(crop: dict[str, Any], cl: Climate) -> dict[str, Any] | None:
    kind = crop.get("type")
    out: dict[str, Any] = {k: set() for k in CALENDAR}
    if kind in ("tree", "shrub", "vine", "fruit_tree"):
        survives = crop.get("survives_c", -10)
        dormant = {
            w for w in _span(cl.coldest - 6, cl.coldest + 6) if cl.mean[w] < 15 and cl.alive(w, survives)
        }
        out["plant_out"].update(dormant)
        if kind in ("shrub", "vine", "fruit_tree"):
            out["pruning"].update(w for w in _span(cl.coldest - 3, cl.coldest + 3) if cl.mean[w] < 15)
    elif "estimated" not in crop or "survives_c" not in crop.get("estimated", []):
        out["plant_out"].update(_mild(crop, cl))
        if kind == "herb":
            out["harvest"].update(w for w in range(WEEKS) if cl.mean[w] >= 10 and cl.t_max[w] <= 38)
    return out if out["plant_out"] else None


def climate_traits(crop: dict[str, Any], weeks: list[dict[str, Any]] | None) -> dict[str, Any] | None:
    """Weeks and months for this garden from its weekly normals; None when crop or climate lacks data."""
    if not weeks or len(weeks) != WEEKS:
        return None
    cl = Climate(weeks)
    if crop.get("bloom_gdd"):
        found = _blooming(crop, cl)
    elif crop.get("life") == "perennial" and crop.get("grown_as") != "annual":
        found = _perennial(crop, cl)
    else:
        found = _annual(crop, cl)
    if not found:
        return None
    risk = found.pop("bloom_frost_risk", None)
    out: dict[str, Any] = {k: to_months(v) for k, v in found.items() if v}
    out["weeks"] = {k: sorted(w + 1 for w in v) for k, v in found.items() if v}
    if risk:
        out["bloom_frost_risk"] = True
    out["calendar"] = "climate"
    return out


# --- Fallback: CropGraph's frost-anchored windows ----------------------------------------------


def _months(start: date, end: date) -> set[int]:
    months, day = set(), start.replace(day=1)
    while day <= end and len(months) < 12:
        months.add(day.month)
        day = (day + timedelta(days=32)).replace(day=1)
    return months


def frost_traits(
    crop: dict[str, Any], frost: dict[str, str | None] | None, weeks: list | None = None
) -> dict[str, Any]:
    """Months from frost-anchored windows: sowing indoors/outdoors, planting out, harvest (annuals).

    With weekly normals, weeks hotter than 35 °C are left out of planting out (CropGraph knows no heat).
    """
    frost = {**FALLBACK_FROST, **{k: v for k, v in (frost or {}).items() if v}}
    year = 2025
    anchors = {
        "s": date.fromisoformat(f"{year}-{frost['last_spring']}"),
        "f": date.fromisoformat(f"{year}-{frost['first_fall']}"),
    }
    keys = {"i": "sow_indoor", "s": "sow_outdoor", "t": "plant_out"}
    months: dict[str, set[int]] = {key: set() for key in keys.values()}
    harvest: set[int] = set()
    annual = crop.get("life") != "perennial" and crop.get("season") in ("warm", "cool")
    info = crop.get("days_to_harvest") or {}
    days = info.get("days")
    for action, anchor, start, end in crop.get("frost_windows") or []:
        first = anchors[anchor] + timedelta(days=start)
        last = anchors[anchor] + timedelta(days=end)
        got = _months(first, last)
        if weeks and action == "t":
            hot = {week_month(i) for i, w in enumerate(weeks) if w["t_max"] > 35}
            got -= hot
        months[keys[action]] |= got
        if annual and days and action in ("s", "t"):
            ripe_from, ripe_to = first + timedelta(days=days[0]), last + timedelta(days=days[1])
            # Warm crops die at the first frost; cool ones last a few weeks longer.
            limit = anchors["f"] + timedelta(days=0 if crop.get("season") == "warm" else 30)
            if ripe_from <= limit:
                harvest |= _months(ripe_from, min(ripe_to, limit))
    out: dict[str, Any] = {key: sorted(value) for key, value in months.items() if value}
    if harvest:
        out["harvest"] = sorted(harvest)
    if out:
        out["calendar"] = "frost"
    return out


def climate_frost(weeks: list[dict[str, Any]] | None) -> dict[str, str | None] | None:
    """Last spring and first fall frost from the weekly normals (nights ≤ 0 °C one year in ten).

    A frost-free garden anchors both on its coldest week, which keeps CropGraph's windows in the cool season.
    """
    if not weeks or len(weeks) != WEEKS:
        return None
    cl = Climate(weeks)
    frosty = [w for w in range(WEEKS) if cl.low[w] <= 0]

    def day(week: int) -> str:
        return (date(2025, 1, 1) + timedelta(days=(week % WEEKS) * 7 + 3)).strftime("%m-%d")

    if not frosty:
        return {"last_spring": day(cl.coldest), "first_fall": day(cl.coldest)}
    spring = [w for w in frosty if w < 26]
    fall = [w for w in frosty if w >= 26]
    return {
        "last_spring": day(max(spring)) if spring else day(cl.coldest),
        "first_fall": day(min(fall)) if fall else day(cl.coldest),
    }


# --- The table the panel and the alerts read ---------------------------------------------------


def _end_month(months: list[int]) -> int | None:
    """End of a season that may cross the new year (e.g. 9-12 then 1-3 → 3)."""
    if not months:
        return None
    ordered = sorted(months)
    gaps = [b - a for a, b in zip(ordered, ordered[1:], strict=False)]
    if gaps and max(gaps) > 1:
        return ordered[gaps.index(max(gaps))]
    return ordered[-1]


def entry_for_garden(
    crop: dict[str, Any], weeks: list[dict[str, Any]] | None, frost: dict[str, str | None] | None
) -> dict[str, Any]:
    """One crop as the panel and the alerts read it: its needs, plus months (and weeks) for this garden."""
    out = dict(crop)
    out["name_en"] = crop.get("name")
    if crop.get("type"):
        out["plant_type"] = crop["type"]
    if crop.get("survives_c") is not None:
        out["hardiness_c"] = crop["survives_c"]
    if crop.get("season") == "cool" and crop.get("stalls_above_c") is not None:
        out["heat_max_c"] = crop["stalls_above_c"]
    if crop.get("season") == "warm":
        out["warm"] = True
    if crop.get("sprouts_soil_c"):
        out["min_soil_c"] = crop["sprouts_soil_c"][0]
    found = climate_traits(crop, weeks)
    if found is None:
        found = frost_traits(crop, frost or climate_frost(weeks), weeks)
        if out.get("warm") and "end" not in found and (last := _end_month(found.get("harvest") or [])):
            found["end"] = [last % 12 + 1]
    out.update(found)
    return out


def full_table(
    crops: dict[str, dict[str, Any]], weeks: list[dict[str, Any]] | None, frost: dict | None = None
) -> dict[str, dict[str, Any]]:
    """Every crop worked out for this garden, keyed like ``normalize``."""
    return {key: entry_for_garden(crop, weeks, frost) for key, crop in crops.items()}
