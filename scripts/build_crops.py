"""Build data/crops.json (crop needs, not calendars) from CropGraph plus a curated garden list.

    python scripts/build_crops.py

Months are never stored: crops.py works them out from the garden's own climate (weekly normals from
the weather history), so the same file is right in Phoenix and in Milan. A value the sources do not
give is filled from the crop's season and listed in ``estimated``; curated crops have none.

Sources: data/cropgraph.json (CropGraph 2, CC-BY-4.0, see the README), the curated table below
(typical extension-service values for the common garden crops), and climate.CHILL_NEEDS.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "custom_components" / "homestead" / "data"
sys.path.insert(0, str(ROOT / "custom_components" / "homestead"))

from climate import CHILL_NEEDS  # noqa: E402

FORMAT = 2

# Season defaults for values a source does not give (marked as estimated).
WARM = {"survives_c": 2, "sprouts_soil_c": [16, 35], "stalls_above_c": 35}
COOL = {"survives_c": -4, "sprouts_soil_c": [7, 27], "stalls_above_c": 27}
PERENNIAL = {"survives_c": -10}

# Care by plant type: tied to the plant's own events, not to calendar months.
CARE = {
    "fruit_tree": {"prune": {"when": "dormant"}, "fertilize": {"at": ["bud_break", "after_harvest"]}},
    "shrub": {"prune": {"when": "dormant"}},
    "vine": {"prune": {"when": "dormant"}},
    "vegetable": {"fertilize": {"from": "start", "every_weeks": 3}},
    "herb": {"fertilize": {"from": "start", "every_weeks": 6}},
}
EVERGREEN_FRUIT = {
    "prune": {"when": "after_harvest"},
    "fertilize": {"at": ["bud_break", "bud_break+12w", "bud_break+28w"]},
}

# Curated garden crops: (key, fields). Values from US extension guides; replace any of them per variety
# with a correction in the panel. Keys are "genus species" or "genus species group".
C = "curated"
CURATED: dict[str, dict] = {
    # Warm annuals: frost kills them, heat stops fruit set.
    "solanum lycopersicum": dict(
        name="Tomato",
        type="vegetable",
        life="perennial",
        grown_as="annual",
        season="warm",
        survives_c=2,
        sprouts_soil_c=[16, 35],
        stalls_above_c=35,
        start=["indoor", "transplant"],
        indoor_weeks=[6, 8],
        days_to_harvest={"days": [60, 85], "from": "plant_out"},
        harvest_weeks=8,
        fruiting=True,
    ),
    "capsicum annuum": dict(
        name="Pepper",
        type="vegetable",
        life="perennial",
        grown_as="annual",
        season="warm",
        survives_c=4,
        sprouts_soil_c=[21, 35],
        stalls_above_c=35,
        start=["indoor", "transplant"],
        indoor_weeks=[8, 10],
        days_to_harvest={"days": [60, 90], "from": "plant_out"},
        harvest_weeks=12,
        fruiting=True,
        family="Solanaceae",
    ),
    "solanum melongena": dict(
        name="Eggplant",
        type="vegetable",
        life="perennial",
        grown_as="annual",
        season="warm",
        survives_c=4,
        sprouts_soil_c=[21, 35],
        stalls_above_c=38,
        start=["indoor", "transplant"],
        indoor_weeks=[8, 10],
        days_to_harvest={"days": [65, 85], "from": "plant_out"},
        harvest_weeks=10,
        fruiting=True,
    ),
    "cucurbita pepo": dict(
        name="Zucchini",
        type="vegetable",
        life="annual",
        season="warm",
        survives_c=4,
        sprouts_soil_c=[21, 35],
        stalls_above_c=38,
        start=["direct"],
        days_to_harvest={"days": [45, 60], "from": "sow"},
        harvest_weeks=8,
        fruiting=True,
    ),
    "cucumis sativus": dict(
        name="Cucumber",
        type="vegetable",
        life="annual",
        season="warm",
        survives_c=4,
        sprouts_soil_c=[18, 35],
        stalls_above_c=35,
        start=["direct"],
        days_to_harvest={"days": [50, 70], "from": "sow"},
        harvest_weeks=6,
        fruiting=True,
    ),
    "citrullus lanatus": dict(
        name="Watermelon",
        type="vegetable",
        life="annual",
        season="warm",
        survives_c=4,
        sprouts_soil_c=[21, 35],
        stalls_above_c=40,
        start=["direct"],
        days_to_harvest={"days": [75, 95], "from": "sow"},
        harvest_weeks=4,
        fruiting=True,
    ),
    "cucumis melo": dict(
        name="Melon",
        type="vegetable",
        life="annual",
        season="warm",
        survives_c=4,
        sprouts_soil_c=[21, 35],
        stalls_above_c=40,
        start=["direct"],
        days_to_harvest={"days": [75, 95], "from": "sow"},
        harvest_weeks=4,
        fruiting=True,
    ),
    "zea mays": dict(
        name="Sweet corn",
        type="vegetable",
        life="annual",
        season="warm",
        survives_c=2,
        sprouts_soil_c=[16, 35],
        stalls_above_c=38,
        start=["direct"],
        days_to_harvest={"days": [70, 90], "from": "sow"},
        harvest_weeks=2,
        fruiting=True,
    ),
    "phaseolus vulgaris": dict(
        name="Bean",
        type="vegetable",
        life="annual",
        season="warm",
        survives_c=2,
        sprouts_soil_c=[16, 30],
        stalls_above_c=32,
        start=["direct"],
        days_to_harvest={"days": [55, 70], "from": "sow"},
        harvest_weeks=6,
        fruiting=True,
    ),
    "abelmoschus esculentus": dict(
        name="Okra",
        type="vegetable",
        life="annual",
        season="warm",
        survives_c=4,
        sprouts_soil_c=[21, 35],
        stalls_above_c=42,
        start=["direct"],
        days_to_harvest={"days": [50, 65], "from": "sow"},
        harvest_weeks=12,
        fruiting=True,
    ),
    "ocimum basilicum": dict(
        name="Basil",
        type="herb",
        life="annual",
        season="warm",
        survives_c=4,
        sprouts_soil_c=[21, 32],
        stalls_above_c=40,
        start=["indoor", "transplant", "direct"],
        indoor_weeks=[4, 6],
        days_to_harvest={"days": [50, 75], "from": "sow"},
        harvest_weeks=16,
    ),
    # Cool annuals: take frost, bolt or stop in heat.
    "lactuca sativa": dict(
        name="Lettuce",
        type="vegetable",
        life="annual",
        season="cool",
        survives_c=-4,
        sprouts_soil_c=[4, 27],
        stalls_above_c=27,
        start=["direct", "indoor", "transplant"],
        indoor_weeks=[3, 4],
        days_to_harvest={"days": [45, 65], "from": "sow"},
        harvest_weeks=4,
        succession_weeks=2,
    ),
    "spinacia oleracea": dict(
        name="Spinach",
        type="vegetable",
        life="annual",
        season="cool",
        survives_c=-9,
        sprouts_soil_c=[4, 24],
        stalls_above_c=24,
        start=["direct"],
        days_to_harvest={"days": [40, 50], "from": "sow"},
        harvest_weeks=4,
        succession_weeks=2,
    ),
    "brassica oleracea": dict(
        name="Kale",
        type="vegetable",
        life="biennial",
        grown_as="annual",
        season="cool",
        survives_c=-10,
        sprouts_soil_c=[7, 30],
        stalls_above_c=29,
        start=["indoor", "transplant", "direct"],
        indoor_weeks=[5, 7],
        days_to_harvest={"days": [50, 65], "from": "plant_out"},
        harvest_weeks=12,
    ),
    "brassica oleracea italica": dict(
        name="Broccoli",
        group="Italica",
        group_names=["broccoli"],
        type="vegetable",
        life="biennial",
        grown_as="annual",
        season="cool",
        survives_c=-4,
        sprouts_soil_c=[7, 30],
        stalls_above_c=27,
        start=["indoor", "transplant"],
        indoor_weeks=[5, 7],
        days_to_harvest={"days": [55, 80], "from": "plant_out"},
        harvest_weeks=5,
    ),
    "brassica oleracea capitata": dict(
        name="Cabbage",
        group="Capitata",
        group_names=["cabbage"],
        type="vegetable",
        life="biennial",
        grown_as="annual",
        season="cool",
        survives_c=-7,
        sprouts_soil_c=[7, 30],
        stalls_above_c=27,
        start=["indoor", "transplant"],
        indoor_weeks=[5, 7],
        days_to_harvest={"days": [70, 100], "from": "plant_out"},
        harvest_weeks=4,
    ),
    "brassica oleracea botrytis": dict(
        name="Cauliflower",
        group="Botrytis",
        group_names=["cauliflower"],
        type="vegetable",
        life="biennial",
        grown_as="annual",
        season="cool",
        survives_c=-2,
        sprouts_soil_c=[7, 30],
        stalls_above_c=24,
        start=["indoor", "transplant"],
        indoor_weeks=[5, 7],
        days_to_harvest={"days": [60, 90], "from": "plant_out"},
        harvest_weeks=2,
    ),
    "brassica oleracea gemmifera": dict(
        name="Brussels sprouts",
        group="Gemmifera",
        group_names=["brussels sprout", "brussels sprouts"],
        type="vegetable",
        life="biennial",
        grown_as="annual",
        season="cool",
        survives_c=-9,
        sprouts_soil_c=[7, 30],
        stalls_above_c=24,
        start=["indoor", "transplant"],
        indoor_weeks=[5, 7],
        days_to_harvest={"days": [90, 110], "from": "plant_out"},
        harvest_weeks=6,
    ),
    "solanum tuberosum": dict(
        name="Potato",
        type="vegetable",
        life="perennial",
        grown_as="annual",
        season="cool",
        survives_c=-1,
        sprouts_soil_c=[7, 27],
        stalls_above_c=29,
        start=["direct"],
        days_to_harvest={"days": [80, 110], "from": "sow"},
        harvest_weeks=3,
    ),
    "daucus carota": dict(
        name="Carrot",
        type="vegetable",
        life="biennial",
        grown_as="annual",
        season="cool",
        survives_c=-6,
        sprouts_soil_c=[7, 30],
        stalls_above_c=30,
        start=["direct"],
        days_to_harvest={"days": [60, 80], "from": "sow"},
        harvest_weeks=6,
    ),
    "beta vulgaris": dict(
        name="Beet",
        type="vegetable",
        life="biennial",
        grown_as="annual",
        season="cool",
        survives_c=-4,
        sprouts_soil_c=[10, 30],
        stalls_above_c=30,
        start=["direct"],
        days_to_harvest={"days": [50, 70], "from": "sow"},
        harvest_weeks=4,
    ),
    "raphanus sativus": dict(
        name="Radish",
        type="vegetable",
        life="annual",
        season="cool",
        survives_c=-4,
        sprouts_soil_c=[7, 30],
        stalls_above_c=27,
        start=["direct"],
        days_to_harvest={"days": [22, 35], "from": "sow"},
        harvest_weeks=2,
        succession_weeks=2,
    ),
    "pisum sativum": dict(
        name="Pea",
        type="vegetable",
        life="annual",
        season="cool",
        survives_c=-4,
        sprouts_soil_c=[4, 24],
        stalls_above_c=27,
        start=["direct"],
        days_to_harvest={"days": [60, 75], "from": "sow"},
        harvest_weeks=4,
        fruiting=True,
    ),
    "allium cepa": dict(
        name="Onion",
        type="vegetable",
        life="biennial",
        grown_as="annual",
        season="cool",
        survives_c=-7,
        sprouts_soil_c=[7, 30],
        stalls_above_c=38,
        start=["direct", "indoor", "transplant"],
        indoor_weeks=[8, 10],
        days_to_harvest={"days": [110, 150], "from": "sow"},
        harvest_weeks=4,
    ),
    "allium porrum": dict(
        name="Leek",
        species="Allium porrum",
        type="vegetable",
        life="biennial",
        grown_as="annual",
        season="cool",
        survives_c=-12,
        sprouts_soil_c=[10, 30],
        stalls_above_c=32,
        start=["indoor", "transplant"],
        indoor_weeks=[8, 10],
        days_to_harvest={"days": [90, 120], "from": "plant_out"},
        harvest_weeks=8,
        family="Amaryllidaceae",
        exposure=["sun"],
        spacing_cm=15,
    ),
    "coriandrum sativum": dict(
        name="Cilantro",
        type="herb",
        life="annual",
        season="cool",
        survives_c=-6,
        sprouts_soil_c=[10, 27],
        stalls_above_c=27,
        start=["direct"],
        days_to_harvest={"days": [40, 55], "from": "sow"},
        harvest_weeks=4,
        succession_weeks=3,
    ),
    "anethum graveolens": dict(
        name="Dill",
        type="herb",
        life="annual",
        season="cool",
        survives_c=-2,
        sprouts_soil_c=[10, 27],
        stalls_above_c=30,
        start=["direct"],
        days_to_harvest={"days": [40, 60], "from": "sow"},
        harvest_weeks=6,
    ),
    "petroselinum crispum": dict(
        name="Parsley",
        type="herb",
        life="biennial",
        grown_as="annual",
        season="cool",
        survives_c=-9,
        sprouts_soil_c=[10, 27],
        stalls_above_c=32,
        start=["direct", "indoor", "transplant"],
        indoor_weeks=[8, 10],
        days_to_harvest={"days": [70, 90], "from": "sow"},
        harvest_weeks=20,
    ),
    # Perennial herbs and strawberry: planted out when it is neither frozen nor hot.
    "salvia rosmarinus": dict(name="Rosemary", type="herb", life="perennial", survives_c=-10),
    "thymus vulgaris": dict(name="Thyme", type="herb", life="perennial", survives_c=-20),
    "salvia officinalis": dict(name="Sage", type="herb", life="perennial", survives_c=-20),
    "origanum vulgare": dict(name="Oregano", type="herb", life="perennial", survives_c=-20),
    "allium schoenoprasum": dict(name="Chives", type="herb", life="perennial", survives_c=-30),
    "mentha spicata": dict(name="Mint", type="herb", life="perennial", survives_c=-30),
    "mentha": dict(name="Mint", species="Mentha", type="herb", life="perennial", survives_c=-30),
    "fragaria ananassa": dict(
        name="Strawberry",
        type="vegetable",
        life="perennial",
        survives_c=-15,
        bloom_damaged_below_c=-2,
        bloom_gdd=200,
        bloom_to_harvest=[30, 75],
        harvest_weeks=6,
        stalls_above_c=32,
    ),
    # Fruit trees: bloom from the warmth after the coldest week, harvest from bloom.
    "prunus persica": dict(
        name="Peach",
        type="fruit_tree",
        life="perennial",
        survives_c=-23,
        bloom_damaged_below_c=-2,
        chill_hours=[150, 1000],
        bloom_gdd=330,
        bloom_to_harvest=[90, 120],
        harvest_weeks=3,
        thin_fruit_days=[30, 45],
    ),
    "prunus armeniaca": dict(
        name="Apricot",
        type="fruit_tree",
        life="perennial",
        survives_c=-25,
        bloom_damaged_below_c=-2,
        chill_hours=[300, 900],
        bloom_gdd=280,
        bloom_to_harvest=[90, 110],
        harvest_weeks=3,
    ),
    "prunus domestica": dict(
        name="Plum",
        type="fruit_tree",
        life="perennial",
        survives_c=-30,
        bloom_damaged_below_c=-2,
        chill_hours=[400, 1000],
        bloom_gdd=350,
        bloom_to_harvest=[100, 140],
        harvest_weeks=3,
    ),
    "prunus avium": dict(
        name="Sweet cherry",
        type="fruit_tree",
        life="perennial",
        survives_c=-30,
        bloom_damaged_below_c=-2,
        chill_hours=[700, 1300],
        bloom_gdd=380,
        bloom_to_harvest=[55, 75],
        harvest_weeks=3,
    ),
    "malus domestica": dict(
        name="Apple",
        type="fruit_tree",
        life="perennial",
        survives_c=-35,
        bloom_damaged_below_c=-2,
        chill_hours=[200, 1500],
        bloom_gdd=450,
        bloom_to_harvest=[100, 160],
        harvest_weeks=4,
    ),
    "pyrus communis": dict(
        name="Pear",
        type="fruit_tree",
        life="perennial",
        survives_c=-30,
        bloom_damaged_below_c=-2,
        chill_hours=[300, 1200],
        bloom_gdd=400,
        bloom_to_harvest=[110, 150],
        harvest_weeks=4,
    ),
    "ficus carica": dict(
        name="Fig",
        type="fruit_tree",
        life="perennial",
        survives_c=-9,
        chill_hours=[100, 300],
        bloom_gdd=450,
        bloom_to_harvest=[60, 90],
        harvest_weeks=8,
    ),
    "citrus limon": dict(
        name="Lemon",
        type="fruit_tree",
        life="perennial",
        evergreen=True,
        survives_c=-3,
        bloom_damaged_below_c=-1,
        bloom_gdd=550,
        bloom_to_harvest=[240, 300],
        harvest_weeks=16,
        exposure=["sun"],
        spacing_cm=300,
    ),
    "citrus sinensis": dict(
        name="Orange",
        type="fruit_tree",
        life="perennial",
        evergreen=True,
        survives_c=-4,
        bloom_damaged_below_c=-1,
        bloom_gdd=550,
        bloom_to_harvest=[270, 360],
        harvest_weeks=16,
    ),
}

# Old built-in species that are not in CropGraph: kept with their cold limit, exposure and spacing.
LEGACY_ONLY = {
    "citrus limon": None,  # curated above
    "allium porrum": None,  # curated above
    "fragaria ananassa": None,  # curated above
    "quercus robur": ("Pedunculate oak", "tree", -30, ["sun"], 1000),
    "quercus cerris": ("Turkey oak", "tree", -25, ["sun"], 1000),
    "quercus pubescens": ("Downy oak", "tree", -25, ["sun"], 1000),
    "fraxinus excelsior": ("Ash", "tree", -30, ["sun"], 1000),
    "acer campestre": ("Field maple", "tree", -30, ["sun", "partial"], 600),
    "ostrya carpinifolia": ("Hop hornbeam", "tree", -25, ["sun", "partial"], 600),
    "rosa": ("Rose", "shrub", -20, ["sun"], 80),
    "hydrangea": ("Hydrangea", "shrub", -15, ["partial"], 120),
    "tulipa": ("Tulip", "flower", -25, ["sun"], 10),
    "narcissus": ("Daffodil", "flower", -25, ["sun", "partial"], 10),
    "dahlia": ("Dahlia", "flower", 0, ["sun"], 60),
    "tagetes": ("Marigold", "flower", 2, ["sun"], 25),
    "zinnia": ("Zinnia", "flower", 2, ["sun"], 30),
}


def species_name(key: str) -> str:
    words = key.split()
    return " ".join([words[0].capitalize(), *words[1:2]])


def frost_class(survives: float | None) -> str | None:
    if survives is None:
        return None
    return "tender" if survives > 0 else "half-hardy" if survives > -4 else "hardy"


def starts(windows: list) -> list[str]:
    acts = {w[0] for w in windows}
    out = []
    if "i" in acts:
        out.append("indoor")
    if "t" in acts:
        out.append("transplant")
    if "s" in acts:
        out.append("direct")
    return out


def indoor_lead(windows: list) -> list[int] | None:
    """Weeks from sowing indoors to planting out, from the two frost-anchored windows."""
    sow = next((w for w in windows if w[0] == "i"), None)
    out = next((w for w in windows if w[0] == "t"), None)
    if not sow or not out or sow[1] != out[1]:
        return None
    low, high = round((out[2] - sow[3]) / 7), round((out[2] - sow[2]) / 7)
    return [max(2, min(low, high)), max(low, high)]


def from_cropgraph(key: str, v: dict, legacy: dict) -> dict:
    """One CropGraph entry in the new shape; gaps filled from the season and listed as estimated."""
    from crops import plant_type  # noqa: PLC0415

    season = v.get("s")
    life = {"perennial": "perennial", "biennial": "biennial"}.get(season, "annual")
    out: dict = {"name": v.get("n"), "species": species_name(key), "category": v.get("c"), "life": life}
    kind = plant_type(key, v.get("c"))
    if kind:
        out["type"] = kind
    estimated: list[str] = []
    if season in ("warm", "cool"):
        out["season"] = season
        base = WARM if season == "warm" else COOL
    elif life == "biennial" and v.get("c") in ("vegetable", "root", "herb"):
        out["season"], out["grown_as"], base = "cool", "annual", COOL
    else:
        base = PERENNIAL
    old = legacy.get(key) or {}
    if old.get("hardiness_c") is not None:
        out["survives_c"] = old["hardiness_c"]
    else:
        out["survives_c"] = base["survives_c"]
        estimated.append("survives_c")
    if "sprouts_soil_c" in base:
        top = base["sprouts_soil_c"][1]
        if v.get("t") is not None:
            out["sprouts_soil_c"] = [v["t"], top]
            estimated.append("sprouts_soil_c[1]")
        else:
            out["sprouts_soil_c"] = list(base["sprouts_soil_c"])
            estimated.append("sprouts_soil_c")
        if old.get("heat_max_c") is not None:
            out["stalls_above_c"] = old["heat_max_c"]
        else:
            out["stalls_above_c"] = base["stalls_above_c"]
            estimated.append("stalls_above_c")
    windows = v.get("w") or []
    out["start"] = starts(windows)
    if lead := indoor_lead(windows):
        out["indoor_weeks"] = lead
    if v.get("d"):
        if life == "perennial":
            out["first_harvest_days"] = v["d"]
        else:
            planted = any(w[0] == "t" for w in windows)
            out["days_to_harvest"] = {"days": v["d"], "from": "plant_out" if planted else "sow"}
            out["harvest_weeks"] = max(2, round((v["d"][1] - v["d"][0]) / 7) + 2)
            estimated.append("harvest_weeks")
    for field in ("exposure", "spacing_cm"):
        if old.get(field) is not None:
            out[field] = old[field]
    if v.get("f") and v["f"] != "Various":
        out["family"] = v["f"]
    if v.get("g"):
        out["good"] = v["g"]
    if windows:
        out["frost_windows"] = windows
    if key in CHILL_NEEDS:
        out["chill_hours"] = [CHILL_NEEDS[key], CHILL_NEEDS[key]]
    if care := CARE.get(out.get("type") or ""):
        out["care"] = care
    out["frost"] = frost_class(out.get("survives_c"))
    if estimated:
        out["estimated"] = estimated
    out["source"] = "cropgraph"
    return out


def curated(key: str, fields: dict, base: dict | None) -> dict:
    out = dict(base or {})
    for drop in ("estimated", "first_harvest_days", "category", "season", "grown_as", "fruiting"):
        out.pop(drop, None)
    out.update({k: v for k, v in fields.items()})
    out.setdefault("species", species_name(key))
    if out.get("life") == "perennial" and out.get("type") == "fruit_tree":
        out.pop("days_to_harvest", None)
        out.pop("start", None)
        out["care"] = EVERGREEN_FRUIT if out.get("evergreen") else CARE["fruit_tree"]
    elif out.get("type") in CARE and "care" not in fields and out.get("life") != "perennial":
        out["care"] = CARE[out["type"]]
    elif out.get("life") == "perennial" and out.get("type") == "herb":
        out.pop("care", None)
    out["frost"] = frost_class(out.get("survives_c"))
    out["source"] = C
    return out


def main() -> None:
    graph = json.loads((DATA / "cropgraph.json").read_text(encoding="utf-8"))["crops"]
    legacy_path = DATA / "crops.json"
    legacy_raw = json.loads(legacy_path.read_text(encoding="utf-8"))
    if legacy_raw.get("format") == FORMAT:
        legacy = legacy_raw.get("legacy_traits", {})
    else:  # first run: the old Italian table, by normalized key
        legacy = {
            " ".join(k.lower().replace("×", " ").split()[:2]): v for k, v in legacy_raw["crops"].items()
        }
    crops: dict[str, dict] = {key: from_cropgraph(key, v, legacy) for key, v in graph.items()}
    for key, row in LEGACY_ONLY.items():
        if row is None or key in crops:
            continue
        name, kind, survives, exposure, spacing = row
        crops[key] = {
            "name": name,
            "species": species_name(key),
            "type": kind,
            "life": "annual" if key in ("tagetes", "zinnia") else "perennial",
            "survives_c": survives,
            "frost": frost_class(survives),
            "exposure": exposure,
            "spacing_cm": spacing,
            "source": "legacy",
            **({"care": CARE[kind]} if kind in CARE else {}),
        }
    for key, fields in CURATED.items():
        base = crops.get(key) or crops.get(" ".join(key.split()[:2]))
        crops[key] = curated(key, fields, base)
    keep = {
        k: {f: v[f] for f in ("hardiness_c", "heat_max_c", "exposure", "spacing_cm") if f in v}
        for k, v in legacy.items()
    }
    doc = {
        "format": FORMAT,
        "_note": (
            "What each crop needs, not when to plant it: crops.py works out the weeks from the garden's own "
            "weather history. Temperatures in °C. 'estimated' lists values filled from the crop's season. "
            "Built by scripts/build_crops.py from CropGraph 2 (CC-BY-4.0) and a curated garden list."
        ),
        "crops": dict(sorted(crops.items())),
        "legacy_traits": keep,
    }
    legacy_path.write_text(
        json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8"
    )
    curated_n = sum(1 for v in crops.values() if v["source"] == C)
    print(f"{len(crops)} crops ({curated_n} curated) -> {legacy_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
