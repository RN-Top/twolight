"""The engine of Twolight.

Everything here is the SHARED layer: the same answer for every person on Earth
at the same moment, because there is only one moon.

Precision: the true positions of the sun and moon are computed with the
standard astronomical series (Meeus, "Astronomical Algorithms", ch. 25 and 47).
The phase is the moon's true angle ahead of the sun (its elongation), so new
moon, full moon and every moon-day land within a couple of minutes of the real sky.

Moon time:
- a moon (new moon to new moon) averages 29.53 days
- each moon has 30 moon-days; a moon-day is the moon gaining 12 degrees on the
  sun (the ancient tithi), so their real lengths vary with the moon's speed
- each moon-day has 24 moon-hours of 60 moon-minutes of 60 moon-seconds
"""
from datetime import datetime, timezone
import math

SYNODIC_MONTH = 29.530588853          # average length of one moon, in days
REFERENCE_NEW_MOON = datetime(2000, 1, 6, 18, 14, tzinfo=timezone.utc)
METONIC_LUNATIONS = 235               # 235 moons fit almost exactly into 19 years
DELTA_T_SECONDS = 69.0                # Terrestrial Time minus UTC, about 69 s in the 2020s

PHASE_NAMES = [
    "New Moon", "Waxing Crescent", "First Quarter", "Waxing Gibbous",
    "Full Moon", "Waning Gibbous", "Last Quarter", "Waning Crescent",
]

# Largest terms of the moon's longitude series: D, M, M', F, amplitude (1e-6 deg)
MOON_TERMS = [
    (0, 0, 1, 0, 6288774), (2, 0, -1, 0, 1274027), (2, 0, 0, 0, 658314),
    (0, 0, 2, 0, 213618), (0, 1, 0, 0, -185116), (0, 0, 0, 2, -114332),
    (2, 0, -2, 0, 58793), (2, -1, -1, 0, 57066), (2, 0, 1, 0, 53322),
    (2, -1, 0, 0, 45758), (0, 1, -1, 0, -40923), (1, 0, 0, 0, -34720),
    (0, 1, 1, 0, -30383), (2, 0, 0, -2, 15327), (0, 0, 1, 2, -12528),
    (0, 0, 1, -2, 10980), (4, 0, -1, 0, 10675), (0, 0, 3, 0, 10034),
    (4, 0, -2, 0, 8548), (2, 1, -1, 0, -7888), (2, 1, 0, 0, -6766),
    (1, 0, -1, 0, -5163), (1, 1, 0, 0, 4987), (2, -1, 1, 0, 4036),
    (2, 0, 2, 0, 3994), (4, 0, 0, 0, 3861), (2, 0, -3, 0, 3665),
    (0, 1, -2, 0, -2689), (2, 0, -1, 2, -2602), (2, -1, -2, 0, 2390),
    (1, 0, 1, 0, -2348), (2, -2, 0, 0, 2236), (0, 1, 2, 0, -2120),
    (0, 2, 0, 0, -2069), (2, -2, -1, 0, 2048), (2, 0, 1, -2, -1773),
    (2, 0, 0, 2, -1595), (4, -1, -1, 0, 1215), (0, 0, 2, 2, -1110),
    (3, 0, -1, 0, -892), (2, 1, 1, 0, -810), (4, -1, -2, 0, 759),
    (0, 2, -1, 0, -713), (2, 2, -1, 0, -700), (2, 1, -2, 0, 691),
    (2, -1, 0, -2, 596), (4, 0, 1, 0, 549), (0, 0, 4, 0, 537),
    (4, -1, 0, 0, 520), (1, 0, -2, 0, -487),
]


def _rad(deg: float) -> float:
    return math.radians(deg % 360.0)


def elongation_deg(now: datetime) -> float:
    """True angle of the moon ahead of the sun, 0..360 (0 = new, 180 = full)."""
    jd = now.timestamp() / 86400.0 + 2440587.5 + DELTA_T_SECONDS / 86400.0
    t = (jd - 2451545.0) / 36525.0

    lp = 218.3164477 + 481267.88123421 * t
    d = 297.8501921 + 445267.1114034 * t
    m = 357.5291092 + 35999.0502909 * t
    mp = 134.9633964 + 477198.8675055 * t
    f = 93.2720950 + 483202.0175233 * t
    a1 = 119.75 + 131.849 * t
    e = 1 - 0.002516 * t

    sigma = 0.0
    for cd, cm, cmp_, cf, amp in MOON_TERMS:
        term = amp * math.sin(_rad(cd * d + cm * m + cmp_ * mp + cf * f))
        if abs(cm) == 1:
            term *= e
        elif abs(cm) == 2:
            term *= e * e
        sigma += term
    sigma += 3958 * math.sin(_rad(a1)) + 1962 * math.sin(_rad(lp - f))
    moon_lon = lp + sigma / 1e6

    sun_l0 = 280.46646 + 36000.76983 * t
    c = ((1.914602 - 0.004817 * t) * math.sin(_rad(m))
         + (0.019993 - 0.000101 * t) * math.sin(_rad(2 * m))
         + 0.000289 * math.sin(_rad(3 * m)))
    sun_lon = sun_l0 + c - 0.00569          # aberration; nutation cancels in the difference

    return (moon_lon - sun_lon) % 360.0


def divmod_hms(secs: int) -> tuple[int, int, int]:
    return secs // 3600, (secs // 60) % 60, secs % 60


def moon_state(now: datetime | None = None) -> dict:
    """Where the one shared moon is right now."""
    now = now or datetime.now(timezone.utc)
    elong = elongation_deg(now)
    cycle = elong / 360.0                                   # 0 = new, 0.5 = full

    mean_lunations = (now - REFERENCE_NEW_MOON).total_seconds() / 86400.0 / SYNODIC_MONTH
    lunation_number = round(mean_lunations - cycle)         # whole moons since the reference
    in_wheel = (lunation_number % METONIC_LUNATIONS) + cycle

    moon_days = elong / 12.0                                # 0..30, each 12 degrees
    return {
        "utc": now,
        "elongation": elong,
        "cycle": cycle,
        "illumination": (1 - math.cos(math.radians(elong))) / 2,
        "phase_name": PHASE_NAMES[int(cycle * 8 + 0.5) % 8],
        "waxing": cycle < 0.5,
        "lunation_number": lunation_number,
        "metonic_moon": lunation_number % METONIC_LUNATIONS + 1,       # 1..235
        "metonic_fraction": in_wheel / METONIC_LUNATIONS,
        "year": int(in_wheel / METONIC_LUNATIONS * 19) + 1,            # 1..19
        "moon_day": int(moon_days) + 1,                                 # 1..30
        "moon_hms": divmod_hms(int((moon_days % 1) * 86400)),
    }


if __name__ == "__main__":
    s = moon_state()
    h, m, sec = s["moon_hms"]
    print(f"{s['phase_name']}, {s['illumination']*100:.0f}% lit | moon-day {s['moon_day']:02d} "
          f"{h:02d}:{m:02d}:{sec:02d} | year {s['year']} of 19, moon {s['metonic_moon']} of 235")
