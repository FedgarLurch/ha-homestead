# FedgarLurch fork of HA Homestead

Tracks [arozoire/ha-homestead](https://github.com/arozoire/ha-homestead) and adds one change, meant to go
upstream once it has run in a real garden. Version = upstream's plus a fourth number (0.20.1.1).

## Crop calendars from the garden's own climate (0.20.1.1)

**Why.** The built-in crop table gave fixed months for a temperate climate (northern/central Italy). In a
hot desert garden (Phoenix, Arizona) most of them are wrong: tomatoes go in in February and again in
August, lettuce and broccoli are winter crops, peaches ripen in May. Frost dates alone cannot fix it,
because there the limit is summer heat, not frost, and the garden is frost-free in most years.

**What changed.**
- `data/crops.json` now stores what each crop needs, not when to plant it: the cold it survives
  (`survives_c`, plus a `frost` class tender / half-hardy / hardy), the soil its seed sprouts in
  (`sprouts_soil_c`), the heat that stops fruit set or makes it bolt (`stalls_above_c`), days to harvest
  and from what (`days_to_harvest`), how it is started (`start`, `indoor_weeks`), life (`annual`,
  `biennial`, `perennial`, `grown_as`), and for fruit trees chill hours, bloom warmth (`bloom_gdd`) and
  bloom to harvest days. Care is tied to the plant's events (prune when dormant, feed at bud break).
- It is built by `scripts/build_crops.py` from CropGraph (1,355 crops, CC-BY-4.0) plus a curated list of
  45 common garden crops. Values a source does not give are filled from the crop's season and listed in
  `estimated`; curated crops have none. The old Italian months are gone; its 16 species missing from
  CropGraph are kept with their cold limit, exposure and spacing.
- Crop groups of one species are separate entries (broccoli, cabbage, cauliflower, Brussels sprouts,
  kale under *Brassica oleracea*), picked by the species with `var.`/`Group`, or by the planting's name or
  variety.
- `climate.weekly_normals`: 52 weekly normals (mean max, mean min, coldest night in 9 years of 10) from
  the weather history Homestead already loads (sensors, then Open-Meteo archive).
- `crops.py` works out the weeks to sow indoors, sow outside, plant out, flower, harvest, prune and feed:
  a start week is good when the plant survives every night until harvest and its first fruit (or head)
  forms in weeks below its heat limit; direct sowing also needs the soil in range. Fruit trees bloom when
  the warmth after the coldest week reaches their `bloom_gdd`, and are pruned while dormant. Months are
  filled from the weeks, so the panel, alerts and work lists keep working; `weeks` holds the detail.
- Without enough history (under 3 years) the CropGraph frost-anchored windows are used as before; a
  frost-free garden anchors them on its coldest week instead of falling back to Italian dates.
- The user's corrections (crop profiles) still win.

Tests: `tests/test_crop_climate.py` (Phoenix and Milan normals give the right seasons).
