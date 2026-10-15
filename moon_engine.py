"""The engine of Twolight.

Everything here is the SHARED layer: the same answer for every person on Earth
at the same moment, because there is only one moon.
"""
from datetime import datetime, timezone
import math

# Length of one moon cycle (new moon to new moon), in days.
SYNODIC_MONTH = 29.530588853

# A known new moon to count from: 6 Jan 2000, 18:14 UTC.
REFERENCE_NEW_MOON = datetime(2000, 1, 6, 18, 14, tzinfo=timezone.utc)

# The Metonic cycle: 235 moon cycles fit almost exactly into 19 years.
METONIC_LUNATIONS = 235

PHASE_NAMES = [
    "New Moon", "Waxing Crescent", "First Quarter", "Waxing Gibbous",
    "Full Moon", "Waning Gibbous", "Last Quarter", "Waning Crescent",
]


def moon_state(now: datetime | None = None) -> dict:
    """Where the one shared moon is right now."""
    now = now or datetime.now(timezone.utc)
    days = (now - REFERENCE_NEW_MOON).total_seconds() / 86400.0
    lunations = days / SYNODIC_MONTH

    cycle = lunations % 1.0                      # 0 = new, 0.5 = full
    age_days = cycle * SYNODIC_MONTH
    illumination = (1 - math.cos(2 * math.pi * cycle)) / 2
    phase_index = int((cycle * 8) + 0.5) % 8

    lunation_number = math.floor(lunations)       # moons since the reference
    metonic_moon = lunation_number % METONIC_LUNATIONS + 1   # 1..235
    metonic_fraction = ((lunations % METONIC_LUNATIONS) / METONIC_LUNATIONS)

    return {
        "utc": now,
        "cycle": cycle,
        "age_days": age_days,
        "illumination": illumination,
        "phase_name": PHASE_NAMES[phase_index],
        "waxing": cycle < 0.5,
        "lunation_number": lunation_number,
        "metonic_moon": metonic_moon,
        "metonic_fraction": metonic_fraction,
        "metonic_year": int(metonic_fraction * 19) + 1,   # 1..19
    }


if __name__ == "__main__":
    s = moon_state()
    print(f"{s['phase_name']}  {s['illumination']*100:.0f}% lit  "
          f"day {s['age_days']:.1f} of 29.5  |  moon {s['metonic_moon']} of 235, "
          f"year {s['metonic_year']} of 19")
