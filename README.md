# Twolight

**A clock of the two lights.** The sun rules the day, the moon rules the night.

Twolight keeps time by the sky instead of by time zones. The moon's phase is the same for everyone on Earth at the same moment, so Twolight time is one shared time: the same moon, the same moment, wherever you are.

## How Twolight time works

Each moon (one cycle from new moon to new moon) is divided into **30 moon-days**. A moon-day is the time the moon takes to gain 12° on the sun, which is the same unit as the ancient *tithi*. Because it follows the real moon, a moon-day's length changes slightly with the moon's actual motion.

Each moon-day has **24 moon-hours** of 60 moon-minutes of 60 moon-seconds. They are shown as a 12-hour clock in two halves:

| Half | Name | What happens on the face |
|---|---|---|
| **GL** | Greater Light | First half of the moon-day. The face brightens. |
| **LL** | Lesser Light | Second half of the moon-day. The face darkens. |

Moons are counted on a **19-year wheel of 235 moons** (the Metonic cycle). That is the point where moons and years line up almost exactly again.

A Twolight reading looks like this:

```
moon-day 14   07:32:05 GL
year 7 of 19, moon 83 of 235
```

## The clock face

- **Center:** the moon, drawn at its real current phase.
- **Middle ring:** the current moon's cycle, marked with eight small moons from new to full and back, plus a marker showing how far along it is.
- **Outer ring:** the 19-year wheel. There are 235 ticks, one per moon, with longer ticks marking the 19 years.
- **Outermost orbit:** the light, travelling with the moon-day through GL and LL.
- **Below the face:** a digital readout of the moon-day, hours, minutes, seconds and GL/LL, plus the current phase and how much of the moon is lit.

The time is set from the server's clock, which is kept on atomic time, so a phone whose clock has drifted still shows the right moment. The face shows how far off your device was.

Open **"The numbers behind the face"** under the clock to see the exact values: the moon's angle ahead of the sun, the phase, the Twolight reading and the shared moment in UTC.

## The astronomy

Sun and moon positions follow Jean Meeus, *Astronomical Algorithms* (chapters 25 and 47). The moon's longitude uses the 50 largest terms of its series. Everything is calculated from the moon's **elongation**, its angle ahead of the sun (0° is new, 180° is full). No outside data or internet lookups are needed.

## Run it

```bash
pip install -r requirements.txt
streamlit run app.py
```

### Deploy on Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io) and choose **Create app**.
2. Repository: `RN-Top/twolight`, branch: `main`, main file path: `app.py`.
3. Deploy.

## Files

| File | What it is |
|---|---|
| `app.py` | The whole app: moon engine, clock face and page, all in one file. |
| `requirements.txt` | Python dependencies (just Streamlit). |
| `engine.py`, `moon_engine.py`, `face.html` | Earlier separate pieces. `app.py` doesn't use them. |

---

*Created by Erin Rae Toppe.*


