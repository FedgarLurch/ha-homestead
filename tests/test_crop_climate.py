"""Crop weeks worked out from the garden's own climate (fork: FedgarLurch)."""

from datetime import date, timedelta

from custom_components.homestead.climate import weekly_normals
from custom_components.homestead.crops import (
    climate_frost,
    crop_hint,
    full_table,
    load_crops,
    lookup,
    normalize,
)


def _c(f: float) -> float:
    return round((f - 32) * 5 / 9, 1)


def _weeks(monthly: list[tuple[float, float, float]]) -> list[dict]:
    """52 weeks interpolated from 12 monthly (mean max, mean min, 1-in-10 coldest night) in °C."""
    out = []
    for week in range(52):
        day = date(2025, 1, 1) + timedelta(days=week * 7 + 3)
        here, frac = day.month - 1, (day.day - 15) / 30
        there = (here + 1) % 12 if frac > 0 else (here - 1) % 12
        a, b, f = monthly[here], monthly[there], abs(frac)
        out.append({k: round(a[i] * (1 - f) + b[i] * f, 1) for i, k in enumerate(("t_max", "t_min", "low"))})
    return out


PHOENIX = _weeks(
    [
        tuple(_c(x) for x in m)
        for m in [
            (67, 45, 33),
            (71, 49, 36),
            (77, 54, 41),
            (85, 60, 47),
            (95, 69, 55),
            (104, 78, 66),
            (106, 84, 74),
            (105, 83, 73),
            (100, 77, 64),
            (89, 65, 50),
            (76, 52, 39),
            (66, 45, 33),
        ]
    ]
)
MILAN = _weeks(
    [
        (6, -2, -8),
        (9, 0, -6),
        (14, 3, -3),
        (18, 7, 1),
        (23, 11, 5),
        (27, 15, 9),
        (30, 17, 12),
        (29, 17, 11),
        (25, 13, 6),
        (18, 9, 1),
        (11, 4, -3),
        (6, -1, -7),
    ]
)


def test_tomato_has_two_seasons_in_the_desert_and_one_in_the_north():
    crops = load_crops()
    phoenix = full_table(crops, PHOENIX)["solanum lycopersicum"]
    milan = full_table(crops, MILAN)["solanum lycopersicum"]
    assert phoenix["calendar"] == milan["calendar"] == "climate"
    # Desert: plant out Feb-Mar and Aug-Sep, never in the summer heat or the winter.
    assert {2, 3, 8, 9} <= set(phoenix["plant_out"]) and not {6, 7, 11, 12} & set(phoenix["plant_out"])
    assert {4, 5, 10, 11} <= set(phoenix["harvest"])
    # North: one season, after the frosts.
    assert set(milan["plant_out"]) <= {4, 5, 6, 7, 8} and 5 in milan["plant_out"]
    assert 8 in milan["harvest"] and not {12, 1, 2} & set(milan["harvest"])
    assert phoenix["warm"] is True and phoenix["hardiness_c"] == 2 and phoenix["min_soil_c"] == 16
    assert phoenix["weeks"]["plant_out"] and all(1 <= w <= 52 for w in phoenix["weeks"]["plant_out"])


def test_cool_crops_follow_the_mild_season():
    table = full_table(load_crops(), PHOENIX)
    lettuce = table["lactuca sativa"]
    assert set(lettuce["harvest"]) <= {11, 12, 1, 2, 3, 4} and lettuce["heat_max_c"] == 27
    assert not {5, 6, 7, 8} & set(lettuce.get("sow_outdoor", []))


def test_crop_groups_split_one_species():
    table = full_table(load_crops(), PHOENIX)
    assert normalize("Brassica oleracea var. italica") == "brassica oleracea italica"
    assert normalize("Brassica oleracea Italica Group") == "brassica oleracea italica"
    broccoli = lookup("Brassica oleracea", table, "Broccoli 1")
    kale = lookup("Brassica oleracea", table, "Kale")
    assert broccoli["name"] == "Broccoli" and kale["name"] == "Kale"
    assert lookup("Brassica oleracea var. italica", table)["name"] == "Broccoli"
    assert broccoli["hardiness_c"] > kale["hardiness_c"]

    class Planting:
        name, variety = "Broccoli 1", None

    assert crop_hint(Planting()) == "Broccoli 1"


def test_fruit_trees_bloom_after_the_cold_and_are_pruned_dormant():
    peach_phx = full_table(load_crops(), PHOENIX)["prunus persica"]
    peach_mil = full_table(load_crops(), MILAN)["prunus persica"]
    assert set(peach_phx["flowering"]) <= {1, 2, 3} and set(peach_mil["flowering"]) <= {3, 4, 5}
    assert min(peach_phx["harvest"]) < min(peach_mil["harvest"])
    assert set(peach_phx["pruning"]) <= {11, 12, 1, 2}
    assert peach_phx["fertilizing"] and peach_phx["chill_hours"] == [150, 1000]


def test_without_history_the_frost_windows_are_used():
    crops = load_crops()
    table = full_table(crops, None)
    assert table["solanum lycopersicum"]["calendar"] == "frost" and table["solanum lycopersicum"]["plant_out"]
    assert table["ficus carica"]["name"] == "Fig"
    # A frost-free garden anchors CropGraph's windows on its coldest week.
    frost = climate_frost(PHOENIX)
    assert frost["last_spring"] == frost["first_fall"]
    assert climate_frost(MILAN)["last_spring"] < "05-01"


def test_needs_are_complete_and_estimates_are_marked():
    crops = load_crops()
    assert len(crops) > 1300
    curated = [c for c in crops.values() if c["source"] == "curated"]
    assert len(curated) >= 40 and not any("estimated" in c for c in curated)
    for crop in crops.values():
        assert crop.get("frost") in (None, "tender", "half-hardy", "hardy")
        assert crop["life"] in ("annual", "biennial", "perennial")
    assert crops["capsicum annuum"]["name"] == "Pepper" and crops["capsicum annuum"]["grown_as"] == "annual"


def test_weekly_normals_need_three_years():
    days = []
    for year in (2021, 2022, 2023):
        day = date(year, 1, 1)
        while day.year == year:
            cold = day.month in (12, 1, 2)
            days.append(
                {"date": day.isoformat(), "t_max": 10 if cold else 30, "t_min": -1 - year % 3 if cold else 15}
            )
            day += timedelta(days=1)
    weeks = weekly_normals(days)
    assert weeks and len(weeks) == 52
    assert weeks[0]["t_max"] == 10 and weeks[0]["low"] == -3 and weeks[26]["t_min"] == 15
    assert weekly_normals(days[:400]) is None
