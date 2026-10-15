"""Twolight — a clock of the two lights.

The sun rules the day, the moon rules the night.
The moon is shared by everyone on Earth; the sun is your own.

This one file holds everything: the moon engine, the clock face, and the page.

Moon time: each moon has 30 moon-days (the moon gaining 12 degrees on the sun,
like the ancient tithi), and each moon-day has 24 moon-hours of 60 moon-minutes
of 60 moon-seconds. Sun and moon positions follow Meeus, Astronomical Algorithms.
"""
from datetime import datetime, timezone
import math
import time

import streamlit as st
import streamlit.components.v1 as components

# ---------------------------------------------------------------- moon engine
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


# ----------------------------------------------------------------- clock face
FACE_HTML = r'''<!-- Twolight clock face.
     Shared layer: the moon (same for everyone on Earth at once).
     Personal layer: the sun (your own daylight, where you stand). -->
<style>
  @import url('https://fonts.googleapis.com/css2?family=Jost:wght@300;400&family=Chakra+Petch:wght@400;500&display=swap');
  :root {
    --night: #0B1030;
    --deep: #05071A;
    --pearl: #ECE7DA;
    --sun: #F2B14A;
    --glass: #9CC3D3;
    --faint: #26305E;
  }
  html, body { margin: 0; padding: 0; background: var(--deep); overflow: hidden; }
  .wrap { display: flex; flex-direction: column; align-items: center; font-family: 'Jost', system-ui, sans-serif; }
  canvas { display: block; width: 100%; max-width: 620px; height: auto; touch-action: manipulation; }
  .line { color: var(--pearl); opacity: .82; font-weight: 300; font-size: 17px; letter-spacing: .02em; margin-top: 6px; text-align: center; }
  .sub { color: var(--glass); opacity: .7; font-weight: 300; font-size: 13px; margin-top: 4px; text-align: center; }
  .digital { display: flex; justify-content: center; align-items: flex-end; gap: 10px; margin-top: 10px; }
  .unit { display: flex; flex-direction: column; align-items: center; }
  .num { font-family: 'Chakra Petch', ui-monospace, monospace; font-variant-numeric: tabular-nums; font-weight: 500;
         font-size: clamp(26px, 8.5vw, 44px); line-height: 1; color: var(--pearl);
         text-shadow: 0 0 14px rgba(156,195,211,.55), 0 0 2px rgba(236,231,218,.9); }
  .num.sec { color: #DDEFF5; }
  .num.day { color: var(--sun); text-shadow: 0 0 14px rgba(242,177,74,.45); }
  .gap { width: 14px; }
  .wheelrow { font-size: 13px; color: var(--glass); opacity: .8; margin-top: 8px; text-align: center; letter-spacing: .03em; }
  .lab { font-size: 11px; font-weight: 400; color: var(--glass); opacity: .75; margin-top: 6px; letter-spacing: .04em; }
  .sep { font-family: 'Chakra Petch', monospace; font-size: clamp(20px, 6vw, 32px); color: var(--glass); opacity: .45; padding-bottom: 20px; }
  .sync { font-size: 11px; color: var(--glass); opacity: .55; margin-top: 8px; text-align: center; }
</style>
<div class="wrap">
  <canvas id="face" width="1240" height="1240" aria-label="Twolight clock face"></canvas>
  <div class="wheelrow" id="wheel">year -- of 19, moon --- of 235</div>
  <div class="digital" aria-label="Twolight time">
    <div class="unit"><div class="num day" id="dD">--</div><div class="lab">moon-day</div></div>
    <div class="gap"></div>
    <div class="unit"><div class="num" id="dH">--</div><div class="lab">hours</div></div>
    <div class="sep">:</div>
    <div class="unit"><div class="num" id="dMi">--</div><div class="lab">minutes</div></div>
    <div class="sep">:</div>
    <div class="unit"><div class="num sec" id="dS">--</div><div class="lab">seconds</div></div>
  </div>
  <div class="sync" id="sync"></div>
  <div class="line" id="line"></div>
  <div class="sub" id="sub"></div>
</div>
<script>
(() => {
  const TEST = new URLSearchParams(location.search).get('t');
  // Server time from Streamlit (kept on atomic time over the internet). Offset corrects the phone's clock.
  const SERVER_MS = Number('__SERVER_MS__');
  const OFFSET = Number.isFinite(SERVER_MS) ? SERVER_MS - Date.now() : 0;
  const SYNCED = Number.isFinite(SERVER_MS);
  const SYNODIC = 29.530588853;
  const REF = Date.UTC(2000, 0, 6, 18, 14);
  const METONIC = 235;
  const NAMES = ["New moon","Waxing crescent","First quarter","Waxing gibbous",
                 "Full moon","Waning gibbous","Last quarter","Waning crescent"];

  const cv = document.getElementById('face');
  const ctx = cv.getContext('2d');
  const S = cv.width, C = S / 2;
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // --- personal layer: where you stand (optional) ---
  let lat = null, lon = null;
  try {
    navigator.geolocation && navigator.geolocation.getCurrentPosition(
      p => { lat = p.coords.latitude; lon = p.coords.longitude; }, () => {}, { timeout: 4000 });
  } catch (e) {}

  // True sun and moon positions (Meeus, Astronomical Algorithms ch. 25 and 47).
  // Elongation = the moon's angle ahead of the sun: 0 new, 180 full.
  const MOON_TERMS = [[0,0,1,0,6288774],[2,0,-1,0,1274027],[2,0,0,0,658314],[0,0,2,0,213618],[0,1,0,0,-185116],[0,0,0,2,-114332],[2,0,-2,0,58793],[2,-1,-1,0,57066],[2,0,1,0,53322],[2,-1,0,0,45758],[0,1,-1,0,-40923],[1,0,0,0,-34720],[0,1,1,0,-30383],[2,0,0,-2,15327],[0,0,1,2,-12528],[0,0,1,-2,10980],[4,0,-1,0,10675],[0,0,3,0,10034],[4,0,-2,0,8548],[2,1,-1,0,-7888],[2,1,0,0,-6766],[1,0,-1,0,-5163],[1,1,0,0,4987],[2,-1,1,0,4036],[2,0,2,0,3994],[4,0,0,0,3861],[2,0,-3,0,3665],[0,1,-2,0,-2689],[2,0,-1,2,-2602],[2,-1,-2,0,2390],[1,0,1,0,-2348],[2,-2,0,0,2236],[0,1,2,0,-2120],[0,2,0,0,-2069],[2,-2,-1,0,2048],[2,0,1,-2,-1773],[2,0,0,2,-1595],[4,-1,-1,0,1215],[0,0,2,2,-1110],[3,0,-1,0,-892],[2,1,1,0,-810],[4,-1,-2,0,759],[0,2,-1,0,-713],[2,2,-1,0,-700],[2,1,-2,0,691],[2,-1,0,-2,596],[4,0,1,0,549],[0,0,4,0,537],[4,-1,0,0,520],[1,0,-2,0,-487]];
  const R = Math.PI / 180;
  function elongation(ms) {
    const jd = ms / 86400000 + 2440587.5 + 69 / 86400;
    const t = (jd - 2451545) / 36525;
    const lp = 218.3164477 + 481267.88123421 * t, d = 297.8501921 + 445267.1114034 * t,
          m = 357.5291092 + 35999.0502909 * t, mp = 134.9633964 + 477198.8675055 * t,
          f = 93.2720950 + 483202.0175233 * t, a1 = 119.75 + 131.849 * t, e = 1 - 0.002516 * t;
    let sig = 0;
    for (const [cd, cm, cmp, cf, amp] of MOON_TERMS) {
      let term = amp * Math.sin((cd * d + cm * m + cmp * mp + cf * f) * R);
      if (Math.abs(cm) === 1) term *= e; else if (Math.abs(cm) === 2) term *= e * e;
      sig += term;
    }
    sig += 3958 * Math.sin(a1 * R) + 1962 * Math.sin((lp - f) * R);
    const moonLon = lp + sig / 1e6;
    const c = (1.914602 - 0.004817 * t) * Math.sin(m * R) + (0.019993 - 0.000101 * t) * Math.sin(2 * m * R)
            + 0.000289 * Math.sin(3 * m * R);
    const sunLon = 280.46646 + 36000.76983 * t + c - 0.00569;
    return (((moonLon - sunLon) % 360) + 360) % 360;
  }
  function moonCount(ms) {
    const el = elongation(ms), cycle = el / 360;
    const meanLun = (ms - REF) / 86400000 / SYNODIC;
    const n = Math.round(meanLun - cycle);
    const inWheel = (((n % METONIC) + METONIC) % METONIC) + cycle;
    return { el, cycle, n, inWheel };
  }

  function moon(now) {
    const k = moonCount(now);
    return {
      cycle: k.cycle,
      lit: (1 - Math.cos(k.el * R)) / 2,
      name: NAMES[Math.floor(k.cycle * 8 + 0.5) % 8],
      met: k.inWheel / METONIC,
    };
  }

  // Sun height: -1 (deep night) .. 1 (high noon)
  function sunHeight(d) {
    const hrs = d.getHours() + d.getMinutes() / 60;
    if (lat === null) return Math.sin(Math.PI * (hrs - 6) / 12);
    const day = Math.floor((d - new Date(d.getFullYear(), 0, 0)) / 86400000);
    const decl = 23.44 * Math.sin(2 * Math.PI * (284 + day) / 365) * Math.PI / 180;
    const utcH = d.getUTCHours() + d.getUTCMinutes() / 60;
    const solar = utcH + lon / 15;
    const ha = (solar - 12) * 15 * Math.PI / 180;
    const la = lat * Math.PI / 180;
    const alt = Math.asin(Math.sin(la) * Math.sin(decl) + Math.cos(la) * Math.cos(decl) * Math.cos(ha));
    return Math.max(-1, Math.min(1, alt / (Math.PI / 2.4)));
  }
  // Fraction of the day for the sun's orbit: noon at top, midnight at bottom
  function dayFrac(d) {
    if (lon === null) return (d.getHours() + d.getMinutes() / 60 + d.getSeconds() / 3600) / 24;
    const utcH = d.getUTCHours() + d.getUTCMinutes() / 60 + d.getUTCSeconds() / 3600;
    return (((utcH + lon / 15) % 24) + 24) % 24 / 24;
  }

  // Fixed star field
  const stars = [];
  let seed = 7;
  const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
  for (let i = 0; i < 220; i++) stars.push({ x: rnd() * S, y: rnd() * S, r: rnd() * 1.6 + .3, t: rnd() * 6.28, s: rnd() * .6 + .2 });
  const craters = [];
  for (let i = 0; i < 14; i++) craters.push({ a: rnd() * 6.28, d: Math.sqrt(rnd()) * .78, r: rnd() * .12 + .03, o: rnd() * .10 + .04 });

  function mix(a, b, t) { return a.map((v, i) => Math.round(v + (b[i] - v) * t)); }

  function drawSky(h, t) {
    const day = Math.max(0, (h + .15) / 1.15);
    const top = mix([5, 7, 26], [32, 58, 104], day);
    const mid = mix([11, 16, 48], [70, 104, 150], day);
    const g = ctx.createRadialGradient(C, C, 0, C, C, C * 1.05);
    g.addColorStop(0, `rgb(${mid})`);
    g.addColorStop(1, `rgb(${top})`);
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, S, S);
    const starA = Math.max(0, 1 - day * 1.6);
    for (const s of stars) {
      const tw = reduce ? 1 : .65 + .35 * Math.sin(t * s.s * 0.002 + s.t);
      ctx.fillStyle = `rgba(236,231,218,${starA * tw * .8})`;
      ctx.beginPath(); ctx.arc(s.x, s.y, s.r, 0, 6.283); ctx.fill();
    }
  }

  // Outer ring: the 19-year wheel (235 moons). Long ticks mark the 19 years.
  function drawMetonic(met) {
    const R = C * .86, done = Math.floor(met * METONIC);
    for (let i = 0; i < METONIC; i++) {
      const a = -Math.PI / 2 + (i / METONIC) * Math.PI * 2;
      const yearMark = Math.abs((i * 19 / METONIC) % 1) < 19 / METONIC - 1e-9;
      const len = yearMark ? 26 : 11;
      const lit = i < done, now = i === done;
      ctx.strokeStyle = now ? 'rgba(236,231,218,1)' : lit ? 'rgba(156,195,211,.75)' : 'rgba(156,195,211,.16)';
      ctx.lineWidth = now ? 4 : yearMark ? 2.6 : 1.6;
      ctx.beginPath();
      ctx.moveTo(C + Math.cos(a) * R, C + Math.sin(a) * R);
      ctx.lineTo(C + Math.cos(a) * (R - len), C + Math.sin(a) * (R - len));
      ctx.stroke();
    }
    // thin glass track
    ctx.strokeStyle = 'rgba(156,195,211,.18)'; ctx.lineWidth = 1.2;
    ctx.beginPath(); ctx.arc(C, C, R + 10, 0, 6.283); ctx.stroke();
  }

  // A lit moon disc drawn on its own small canvas, so erasing the dark side never touches the sky
  function litDisc(r, cyc, fillFor, texture) {
    const off = document.createElement('canvas');
    off.width = off.height = Math.ceil(r * 2 + 4);
    const g = off.getContext('2d'), c = off.width / 2;
    const k = Math.cos(cyc * Math.PI * 2), waxing = cyc < .5;
    g.save();
    g.beginPath(); g.arc(c, c, r, 0, 6.283); g.clip();
    g.fillStyle = fillFor(g, c);
    g.beginPath();
    if (waxing) g.arc(c, c, r, -Math.PI / 2, Math.PI / 2); else g.arc(c, c, r, Math.PI / 2, Math.PI * 1.5);
    g.closePath(); g.fill();
    g.beginPath(); g.ellipse(c, c, Math.max(Math.abs(k) * r, .01), r, 0, 0, 6.283);
    if (k > 0) { g.globalCompositeOperation = 'destination-out'; g.fill(); } else g.fill();
    g.restore();
    if (texture) {
      g.globalCompositeOperation = 'source-atop';
      for (const t of craters) {
        g.fillStyle = `rgba(110,104,90,${t.o})`;
        g.beginPath(); g.arc(c + Math.cos(t.a) * t.d * r, c + Math.sin(t.a) * t.d * r, t.r * r, 0, 6.283); g.fill();
      }
    }
    return off;
  }

  // Middle ring: this moon's cycle, marked by eight little moons (symbols, not numbers)
  const tinyCache = {};
  function tinyMoon(x, y, r, cyc, bright) {
    ctx.fillStyle = bright ? 'rgba(43,52,99,.95)' : 'rgba(38,48,94,.7)';
    ctx.beginPath(); ctx.arc(x, y, r, 0, 6.283); ctx.fill();
    const key = r + ':' + cyc + ':' + bright;
    const img = tinyCache[key] || (tinyCache[key] = litDisc(r, cyc, () => bright ? 'rgba(236,231,218,1)' : 'rgba(236,231,218,.45)'));
    ctx.drawImage(img, x - img.width / 2, y - img.height / 2);
    if (bright) {
      ctx.strokeStyle = 'rgba(236,231,218,.6)'; ctx.lineWidth = 1.5;
      ctx.beginPath(); ctx.arc(x, y, r + 9, 0, 6.283); ctx.stroke();
    }
  }
  function drawPhaseRing(cyc) {
    const R = C * .64;
    ctx.strokeStyle = 'rgba(156,195,211,.14)'; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.arc(C, C, R, 0, 6.283); ctx.stroke();
    const a0 = -Math.PI / 2, a1 = a0 + cyc * Math.PI * 2;
    ctx.strokeStyle = 'rgba(236,231,218,.7)'; ctx.lineWidth = 3.5; ctx.lineCap = 'round';
    ctx.beginPath(); ctx.arc(C, C, R, a0, a1); ctx.stroke();
    const cur = Math.floor(cyc * 8 + .5) % 8;
    for (let i = 0; i < 8; i++) {
      const a = -Math.PI / 2 + i / 8 * Math.PI * 2;
      tinyMoon(C + Math.cos(a) * (R + 62), C + Math.sin(a) * (R + 62), i === cur ? 30 : 22, i / 8, i === cur);
    }
    ctx.fillStyle = 'rgba(236,231,218,1)';
    ctx.shadowColor = 'rgba(236,231,218,.9)'; ctx.shadowBlur = 18;
    ctx.beginPath(); ctx.arc(C + Math.cos(a1) * R, C + Math.sin(a1) * R, 6, 0, 6.283); ctx.fill();
    ctx.shadowBlur = 0;
  }

  // The big moon at the center: the shared layer
  let moonCache = { key: null, img: null };
  function drawMoon(cyc, lit) {
    const r = C * .36;
    const halo = ctx.createRadialGradient(C, C, r * .9, C, C, r * 1.9);
    halo.addColorStop(0, `rgba(236,231,218,${.10 + lit * .22})`);
    halo.addColorStop(1, 'rgba(236,231,218,0)');
    ctx.fillStyle = halo; ctx.beginPath(); ctx.arc(C, C, r * 1.9, 0, 6.283); ctx.fill();
    const body = ctx.createRadialGradient(C - r * .3, C - r * .3, r * .1, C, C, r);
    body.addColorStop(0, '#2B3463'); body.addColorStop(1, '#141A3C');
    ctx.fillStyle = body; ctx.beginPath(); ctx.arc(C, C, r, 0, 6.283); ctx.fill();
    const key = cyc.toFixed(4);
    if (moonCache.key !== key) {
      moonCache = { key, img: litDisc(r, cyc, (g, c) => {
        const s = g.createRadialGradient(c - r * .35, c - r * .35, r * .1, c, c, r);
        s.addColorStop(0, '#FBF8EF'); s.addColorStop(.7, '#E4DECD'); s.addColorStop(1, '#BDB6A3');
        return s;
      }, true) };
    }
    const img = moonCache.img;
    ctx.save(); ctx.shadowColor = 'rgba(236,231,218,.55)'; ctx.shadowBlur = 40;
    ctx.drawImage(img, C - img.width / 2, C - img.height / 2); ctx.restore();
    ctx.strokeStyle = 'rgba(156,195,211,.25)'; ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.arc(C, C, r + 1, 0, 6.283); ctx.stroke();
  }

  // The sun: your own day. Travels the outermost orbit, noon at top.
  function drawSun(frac, h) {
    const R = C * .955;
    const a = Math.PI / 2 + frac * Math.PI * 2;   // midnight bottom, noon top
    const x = C + Math.cos(a) * R, y = C + Math.sin(a) * R;
    // daylight arc above the horizon line
    ctx.strokeStyle = 'rgba(242,177,74,.18)'; ctx.lineWidth = 1.2;
    ctx.setLineDash([2, 10]);
    ctx.beginPath(); ctx.arc(C, C, R, 0, 6.283); ctx.stroke();
    ctx.setLineDash([]);
    const strength = Math.max(.25, (h + 1) / 2);
    const glow = ctx.createRadialGradient(x, y, 0, x, y, 70);
    glow.addColorStop(0, `rgba(255,214,140,${.9 * strength})`);
    glow.addColorStop(.25, `rgba(242,177,74,${.55 * strength})`);
    glow.addColorStop(1, 'rgba(242,177,74,0)');
    ctx.fillStyle = glow; ctx.beginPath(); ctx.arc(x, y, 70, 0, 6.283); ctx.fill();
    ctx.fillStyle = `rgba(255,232,190,${.6 + .4 * strength})`;
    ctx.beginPath(); ctx.arc(x, y, 14, 0, 6.283); ctx.fill();
  }

  const line = document.getElementById('line');
  const sub = document.getElementById('sub');
  let lastText = '';
  const         dD = document.getElementById('dD');
  document.getElementById('sync').textContent = SYNCED
    ? `Set from atomic time. Your device clock was ${Math.abs(OFFSET / 1000).toFixed(1)}s ${OFFSET >= 0 ? 'behind' : 'ahead'}.`
    : 'Running on your device clock.';
  const pad = (n, w) => String(n).padStart(w, '0');
  // Moon time: each moon is split into 30 moon-days (like the ancient tithi).
  // Each moon-day is split into 24 moon-hours, 60 moon-minutes, 60 moon-seconds.
  // A moon-day is the moon gaining 12 degrees on the sun, so its length follows the real moon.
  const dH = document.getElementById('dH'), dMi = document.getElementById('dMi'),
        dS = document.getElementById('dS'), wheel = document.getElementById('wheel');
  function twolightTime(ms) {
    const k = moonCount(ms);
    const md = k.el / 12;                       // 30 moon-days of 12 degrees each
    const secs = Math.floor((md % 1) * 86400);  // 24 x 60 x 60 moon-seconds per moon-day
    return {
      year: Math.floor(k.inWheel / METONIC * 19) + 1,
      moon: Math.floor(k.inWheel) + 1,
      day: Math.floor(md) + 1,
      h: Math.floor(secs / 3600), m: Math.floor(secs / 60) % 60, s: secs % 60,
    };
  }
  let lastWheel = '';
  function tickDigital() {
    const tt = twolightTime(TEST ? new Date(TEST).getTime() : Date.now() + OFFSET);
    dD.textContent = pad(tt.day, 2);
    dH.textContent = pad(tt.h, 2);
    dMi.textContent = pad(tt.m, 2);
    dS.textContent = pad(tt.s, 2);
    const w = `year ${tt.year} of 19, moon ${tt.moon} of 235`;
    if (w !== lastWheel) { wheel.textContent = w; lastWheel = w; }
  }
  tickDigital();
  setInterval(tickDigital, 100);

  function frame(t) {
    const now = TEST ? new Date(TEST) : new Date(Date.now() + OFFSET);
    const m = moon(now.getTime());
    const h = sunHeight(now);
    drawSky(h, t);
    drawMetonic(m.met);
    drawPhaseRing(m.cycle);
    drawSun(dayFrac(now), h);
    drawMoon(m.cycle, m.lit);
    const year = Math.floor(m.met * 19) + 1;
    const text = `${m.name}, ${Math.round(m.lit * 100)}% lit`;
    const s2 = `The same moon, the same time, for everyone on Earth.`;
    if (text !== lastText) { line.textContent = text; sub.textContent = s2; lastText = text; }
    if (!reduce) requestAnimationFrame(frame); else setTimeout(() => frame(0), 60000);
  }
  frame(0);
})();
</script>
'''

# ----------------------------------------------------------------------- page
st.set_page_config(page_title="Twolight", page_icon="🌙", layout="centered")

st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Jost:wght@300;400&display=swap');
      .stApp { background: #05071A; }
      html, body, [class*="css"] { font-family: 'Jost', system-ui, sans-serif; }
      header[data-testid="stHeader"] { background: transparent; }
      .block-container { padding-top: 1.2rem; max-width: 680px; }
      h1.title { color: #ECE7DA; font-weight: 300; font-size: 1.9rem; text-align: center;
                 letter-spacing: .04em; margin: 0 0 .2rem 0; }
      p.tag { color: #9CC3D3; opacity: .75; text-align: center; font-weight: 300; margin: 0 0 .6rem 0; }
    </style>
    <h1 class="title">Twolight</h1>
    <p class="tag">One moon over the whole world. Your own sun where you stand.</p>
    """,
    unsafe_allow_html=True,
)

face = FACE_HTML
# Hand the face this server's clock (synced to atomic time) so phones with drifting clocks stay exact.
face = face.replace("__SERVER_MS__", str(int(time.time() * 1000)))
components.html(face, height=880, scrolling=False)

s = moon_state()
with st.expander("The numbers behind the face"):
    h, m, sec = s["moon_hms"]
    st.write(f"**Twolight time:** moon-day {s['moon_day']:02d}, {h:02d}:{m:02d}:{sec:02d} "
             f"(year {s['year']} of 19, moon {s['metonic_moon']} of 235)")
    st.write(f"**Phase:** {s['phase_name']} — {s['illumination'] * 100:.0f}% lit")
    st.write(f"**Moon's angle ahead of the sun:** {s['elongation']:.2f}°")
    st.write(f"**Shared moment (UTC):** {s['utc']:%Y-%m-%d %H:%M}")
    st.caption(
        "The moon's phase is the same everywhere on Earth at once — that is the shared layer. "
        "The sun on the outer ring follows your own day: allow location for your true sun, "
        "otherwise it follows your device clock."
    )
