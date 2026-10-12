#!/usr/bin/env python3
"""
build.py - Data Pipeline and Static Site Pre-renderer for AMELAG Wastewater Surveillance Dashboard
Processes RKI/UBA raw TSV files into optimized JSON data files and generates pre-rendered
accessible static SVG charts and HTML components for GitHub Pages.
"""

import csv
import json
import math
import os
import re
from collections import defaultdict
from datetime import datetime

BUNDESLAENDER = {
    "BW": "Baden-Württemberg",
    "BY": "Bayern",
    "BE": "Berlin",
    "BB": "Brandenburg",
    "HB": "Bremen",
    "HH": "Hamburg",
    "HE": "Hessen",
    "MV": "Mecklenburg-Vorpommern",
    "NI": "Niedersachsen",
    "NW": "Nordrhein-Westfalen",
    "RP": "Rheinland-Pfalz",
    "SL": "Saarland",
    "SN": "Sachsen",
    "ST": "Sachsen-Anhalt",
    "SH": "Schleswig-Holstein",
    "TH": "Thüringen"
}

PATHOGEN_NAMES = {
    "SARS-CoV-2": "SARS-CoV-2 (COVID-19)",
    "Influenza A": "Influenza A",
    "Influenza B": "Influenza B",
    "Influenza A+B": "Influenza A+B (Grippe gesamt)",
    "RSV A": "RSV A",
    "RSV B": "RSV B",
    "RSV A+B": "RSV A+B (RS-Virus gesamt)",
    "RSV A/B": "RSV A/B"
}

PATHOGEN_COLORS = {
    "SARS-CoV-2": "#4f46e5",    # Indigo
    "Influenza A": "#f59e0b",   # Amber
    "Influenza B": "#ef4444",   # Red
    "Influenza A+B": "#ea580c", # Orange
    "RSV A": "#06b6d4",         # Cyan
    "RSV B": "#8b5cf6",         # Purple
    "RSV A+B": "#ec4899",       # Pink
    "RSV A/B": "#14b8a6"        # Teal
}

def slugify(text):
    text = text.lower()
    text = re.sub(r'[äÄ]', 'ae', text)
    text = re.sub(r'[öÖ]', 'oe', text)
    text = re.sub(r'[üÜ]', 'ue', text)
    text = re.sub(r'[ß]', 'ss', text)
    text = re.sub(r'[^a-z0-9]+', '-', text).strip('-')
    return text

def parse_float(val):
    if val is None or val == "" or val == "NA":
        return None
    try:
        return float(val)
    except ValueError:
        return None

def parse_int(val):
    if val is None or val == "" or val == "NA":
        return None
    try:
        return int(float(val))
    except ValueError:
        return None

def build_data(root_dir="."):
    agg_file = os.path.join(root_dir, "amelag_aggregierte_kurve.tsv")
    sites_file = os.path.join(root_dir, "amelag_einzelstandorte.tsv")
    data_dir = os.path.join(root_dir, "data")
    sites_dir = os.path.join(data_dir, "sites")
    os.makedirs(sites_dir, exist_ok=True)

    if not os.path.exists(sites_file):
        national_json = os.path.join(data_dir, "national.json")
        states_json = os.path.join(data_dir, "states_summary.json")
        sites_json = os.path.join(data_dir, "sites_index.json")
        if os.path.exists(national_json) and os.path.exists(states_json) and os.path.exists(sites_json):
            print("--- Reusing pre-generated JSON datasets (sites TSV not present) ---")
            with open(national_json, "r", encoding="utf-8") as f:
                national_data = json.load(f)
            with open(states_json, "r", encoding="utf-8") as f:
                states_summary = json.load(f)
            with open(sites_json, "r", encoding="utf-8") as f:
                sites_index = json.load(f)
            return national_data, states_summary, sites_index
        else:
            print("Downloading amelag_einzelstandorte.tsv from RKI...")
            import urllib.request
            url = "https://raw.githubusercontent.com/robert-koch-institut/Abwassersurveillance_AMELAG/main/amelag_einzelstandorte.tsv"
            urllib.request.urlretrieve(url, sites_file)

    if not os.path.exists(agg_file):
        print("Downloading amelag_aggregierte_kurve.tsv from RKI...")
        import urllib.request
        url = "https://raw.githubusercontent.com/robert-koch-institut/Abwassersurveillance_AMELAG/main/amelag_aggregierte_kurve.tsv"
        urllib.request.urlretrieve(url, agg_file)

    print("--- 1. Processing National Aggregated Data ---")
    national_series = defaultdict(list)
    with open(agg_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for r in reader:
            typ = r["typ"]
            d = r["datum"]
            n = parse_int(r["n"])
            cov = parse_float(r["anteil_bev"])
            vl = parse_float(r["viruslast"])
            vln = parse_float(r["viruslast_normalisiert"])
            pred = parse_float(r["vorhersage"])
            upper = parse_float(r["obere_schranke"])
            lower = parse_float(r["untere_schranke"])

            national_series[typ].append({
                "date": d,
                "n": n,
                "cov": round(cov, 4) if cov is not None else None,
                "vl": round(vl, 2) if vl is not None else None,
                "norm": round(vln, 2) if vln is not None else None,
                "pred": round(pred, 2) if pred is not None else None,
                "upper": round(upper, 2) if upper is not None else None,
                "lower": round(lower, 2) if lower is not None else None,
            })

    # Sort each pathogen series by date
    for typ in national_series:
        national_series[typ].sort(key=lambda x: x["date"])

    # Calculate statistics for each pathogen
    pathogen_stats = {}
    latest_global_date = ""
    for typ, rows in national_series.items():
        if not rows:
            continue
        last = rows[-1]
        prev_7d = rows[-2] if len(rows) > 1 else last
        prev_28d = rows[-5] if len(rows) > 4 else rows[0]
        
        if last["date"] > latest_global_date:
            latest_global_date = last["date"]

        curr_p = last["pred"] or last["norm"] or 0
        p7_p = prev_7d["pred"] or prev_7d["norm"] or 0
        p28_p = prev_28d["pred"] or prev_28d["norm"] or 0

        chg_7d = ((curr_p - p7_p) / p7_p * 100) if p7_p > 0 else 0
        chg_28d = ((curr_p - p28_p) / p28_p * 100) if p28_p > 0 else 0

        peak_row = max(rows, key=lambda x: x["pred"] or 0)
        min_row = min((r for r in rows if (r["pred"] or 0) > 0), key=lambda x: x["pred"] or 0, default=rows[0])

        pathogen_stats[typ] = {
            "latest_date": last["date"],
            "latest_pred": curr_p,
            "latest_norm": last["norm"],
            "latest_n": last["n"],
            "latest_cov": last["cov"],
            "chg_7d_pct": round(chg_7d, 1),
            "chg_28d_pct": round(chg_28d, 1),
            "peak_date": peak_row["date"],
            "peak_value": peak_row["pred"],
            "min_date": min_row["date"],
            "min_value": min_row["pred"],
            "total_points": len(rows),
            "start_date": rows[0]["date"],
        }

    print("--- 2. Processing Single Sites and State Aggregations ---")
    site_metadata = {}
    site_series = defaultdict(lambda: defaultdict(list))
    # State daily weighted aggregation: bl -> typ -> date -> {weighted_pred, weighted_norm, weight, n}
    bl_daily = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {"w_p": 0.0, "w_norm": 0.0, "weight": 0, "n": 0})))
    bl_sites_map = defaultdict(set)
    bl_population_map = defaultdict(int)

    with open(sites_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for r in reader:
            s_name = r["standort"]
            bl = r["bundesland"]
            pop = parse_int(r["einwohner"]) or 0
            slug = slugify(s_name)

            if slug not in site_metadata:
                site_metadata[slug] = {
                    "id": slug,
                    "name": s_name,
                    "bl": bl,
                    "bl_name": BUNDESLAENDER.get(bl, bl),
                    "pop": pop,
                    "typs": set(),
                    "first_date": r["datum"],
                    "last_date": r["datum"],
                    "latest_sars_pred": None,
                    "latest_sars_date": None
                }
                bl_sites_map[bl].add(slug)
                bl_population_map[bl] += pop

            meta = site_metadata[slug]
            typ = r["typ"]
            meta["typs"].add(typ)
            d = r["datum"]
            if d > meta["last_date"]:
                meta["last_date"] = d

            vl = parse_float(r["viruslast"])
            vln = parse_float(r["viruslast_normalisiert"])
            pred = parse_float(r["vorhersage"])
            upper = parse_float(r["obere_schranke"])
            lower = parse_float(r["untere_schranke"])
            bg = 1 if r["unter_bg"] == "ja" else 0

            # Store compact point: [date, raw, norm, pred, upper, lower, bg]
            site_series[slug][typ].append([
                d,
                round(vl, 1) if vl is not None else None,
                round(vln, 1) if vln is not None else None,
                round(pred, 1) if pred is not None else None,
                round(upper, 1) if upper is not None else None,
                round(lower, 1) if lower is not None else None,
                bg
            ])

            if typ == "SARS-CoV-2" and pred is not None:
                if meta["latest_sars_date"] is None or d >= meta["latest_sars_date"]:
                    meta["latest_sars_date"] = d
                    meta["latest_sars_pred"] = round(pred, 1)

            # State aggregation accumulation
            if pop > 0 and pred is not None:
                cell = bl_daily[bl][typ][d]
                cell["w_p"] += pred * pop
                cell["weight"] += pop
                cell["n"] += 1
                if vln is not None:
                    cell["w_norm"] += vln * pop

    # Save per-site files and finalize site index
    sites_index = []
    print(f"Writing {len(site_metadata)} site data files...")
    for slug, meta in site_metadata.items():
        # Sort each pathogen series
        for typ in site_series[slug]:
            site_series[slug][typ].sort(key=lambda x: x[0])

        # Write site json
        site_data_obj = {
            "info": {
                "id": slug,
                "name": meta["name"],
                "bl": meta["bl"],
                "bl_name": meta["bl_name"],
                "population": meta["pop"],
                "last_date": meta["last_date"],
                "typs": sorted(list(meta["typs"])),
            },
            "series": site_series[slug]
        }
        site_file_path = os.path.join(sites_dir, f"{slug}.json")
        with open(site_file_path, "w", encoding="utf-8") as sf:
            json.dump(site_data_obj, sf, separators=(",", ":"))

        # Calculate site recent trend (last 14 days change)
        sars_series = site_series[slug].get("SARS-CoV-2", [])
        trend_14d = 0.0
        if len(sars_series) >= 15:
            curr_val = sars_series[-1][3] or sars_series[-1][2] or 0
            prev_val = sars_series[-15][3] or sars_series[-15][2] or 0
            if prev_val > 0:
                trend_14d = round((curr_val - prev_val) / prev_val * 100, 1)

        sites_index.append({
            "id": slug,
            "name": meta["name"],
            "bl": meta["bl"],
            "bl_name": meta["bl_name"],
            "pop": meta["pop"],
            "typs": sorted(list(meta["typs"])),
            "last_date": meta["last_date"],
            "latest_sars": meta["latest_sars_pred"],
            "trend_14d": trend_14d,
            "data_file": f"data/sites/{slug}.json"
        })

    sites_index.sort(key=lambda x: (x["bl"], x["name"]))
    with open(os.path.join(data_dir, "sites_index.json"), "w", encoding="utf-8") as f:
        json.dump(sites_index, f, separators=(",", ":"))

    print("--- 3. Processing State-Level Aggregates ---")
    states_dir = os.path.join(data_dir, "states")
    os.makedirs(states_dir, exist_ok=True)

    states_summary = {
        "meta": {
            "generated_at": datetime.now().isoformat(),
            "latest_date": latest_global_date,
        },
        "states": {}
    }

    for bl_code, bl_name in sorted(BUNDESLAENDER.items()):
        total_bl_pop = bl_population_map[bl_code]
        sites_in_bl = len(bl_sites_map[bl_code])
        state_obj = {
            "code": bl_code,
            "name": bl_name,
            "sites_count": sites_in_bl,
            "population": total_bl_pop,
            "latest_sars": None,
            "trend_7d": None,
            "trend_status": "stable",
            "file": f"data/states/{bl_code.lower()}.json"
        }
        state_series = {}

        for typ, dates_map in bl_daily[bl_code].items():
            sorted_dates = sorted(dates_map.keys())
            if not sorted_dates:
                continue
            curve = []
            for d in sorted_dates:
                c = dates_map[d]
                if c["weight"] > 0:
                    wp = round(c["w_p"] / c["weight"], 1)
                    wn = round(c["w_norm"] / c["weight"], 1) if c["w_norm"] > 0 else None
                    curve.append([d, wp, wn, c["n"], c["weight"]])
            state_series[typ] = curve

            if typ == "SARS-CoV-2" and len(curve) > 0:
                last_pt = curve[-1]
                state_obj["latest_sars"] = last_pt[1]
                if len(curve) >= 8:
                    prev_pt = curve[-8]
                    p_curr = last_pt[1]
                    p_prev = prev_pt[1]
                    if p_prev > 0:
                        t7 = round((p_curr - p_prev) / p_prev * 100, 1)
                        state_obj["trend_7d"] = t7
                        if t7 > 10:
                            state_obj["trend_status"] = "rising"
                        elif t7 < -10:
                            state_obj["trend_status"] = "falling"
                        else:
                            state_obj["trend_status"] = "stable"

        states_summary["states"][bl_code] = state_obj
        
        # Save individual state file
        with open(os.path.join(states_dir, f"{bl_code.lower()}.json"), "w", encoding="utf-8") as stf:
            json.dump({"info": state_obj, "series": state_series}, stf, separators=(",", ":"))

    with open(os.path.join(data_dir, "states_summary.json"), "w", encoding="utf-8") as f:
        json.dump(states_summary, f, separators=(",", ":"))


    print("--- 4. Writing National Summary & Curves ---")
    national_data = {
        "meta": {
            "title": "AMELAG Abwassersurveillance Deutschland",
            "source": "Robert Koch-Institut (RKI) und Umweltbundesamt (UBA)",
            "license": "CC BY 4.0 / dl-de/by-2-0",
            "generated_at": datetime.now().isoformat(),
            "latest_date": latest_global_date,
            "total_sites": len(site_metadata),
            "total_population": sum(bl_population_map.values()),
            "pathogens": pathogen_stats,
        },
        "series": {typ: [[r["date"], r["n"], r["cov"], r["vl"], r["norm"], r["pred"], r["upper"], r["lower"]] for r in rows] for typ, rows in national_series.items()}
    }
    with open(os.path.join(data_dir, "national.json"), "w", encoding="utf-8") as f:
        json.dump(national_data, f, separators=(",", ":"))

    print(f"Data generation complete! Latest date: {latest_global_date}. Total sites: {len(site_metadata)}.")
    return national_data, states_summary, sites_index

def generate_svg_chart(national_data, scale="linear", width=960, height=480):
    """
    Generates a crisp, accessible, standalone SVG chart of the national SARS-CoV-2 curve
    with confidence intervals and comparison with Influenza A+B and RSV A+B.
    Works without any JavaScript.
    """
    sars = national_data["series"].get("SARS-CoV-2", [])
    flu = national_data["series"].get("Influenza A+B", [])
    rsv = national_data["series"].get("RSV A+B", [])

    if not sars:
        return "<svg></svg>"

    # Margins & dimensions
    margin_l = 80
    margin_r = 40
    margin_t = 50
    margin_b = 60
    plot_w = width - margin_l - margin_r
    plot_h = height - margin_t - margin_b

    # Date range
    all_dates = [r[0] for r in sars]
    min_date = all_dates[0]
    max_date = all_dates[-1]

    d_start = datetime.strptime(min_date, "%Y-%m-%d")
    d_end = datetime.strptime(max_date, "%Y-%m-%d")
    total_days = max((d_end - d_start).days, 1)

    def x_coord(d_str):
        d = datetime.strptime(d_str, "%Y-%m-%d")
        frac = (d - d_start).days / total_days
        return margin_l + frac * plot_w

    # Determine Y bounds
    if scale == "log":
        y_min_val = 100.0  # 10^2
        max_val = 1000000.0 # 10^6
        for r in sars:
            if r[6] and r[6] > max_val: # upper bound
                max_val = r[6]
        log_min = math.log10(y_min_val)
        log_max = math.ceil(math.log10(max_val * 1.2))
        log_range = log_max - log_min

        def y_coord(val):
            if val is None or val <= 0:
                v = y_min_val
            else:
                v = max(val, y_min_val)
            log_v = math.log10(v)
            frac = (log_v - log_min) / log_range
            return margin_t + (1.0 - frac) * plot_h

        # Ticks for log scale: powers of 10
        y_ticks = []
        for p in range(int(log_min), int(log_max) + 1):
            val = 10 ** p
            label = f"10{chr(0x2070 + p)}" if p < 10 else f"10^{p}"
            if val >= 1_000_000:
                label_fmt = f"{val/1_000_000:.0f}M"
            elif val >= 1_000:
                label_fmt = f"{val/1_000:.0f}k"
            else:
                label_fmt = str(val)
            y_ticks.append((val, y_coord(val), f"{label_fmt} ({label})"))
    else:
        # Linear scale
        max_val = 0
        for r in sars:
            u = r[6] or r[5] or 0
            if u > max_val:
                max_val = u
        y_max = math.ceil(max_val * 1.1 / 100000) * 100000
        if y_max <= 0:
            y_max = 500000

        def y_coord(val):
            if val is None or val < 0:
                val = 0
            frac = val / y_max
            return margin_t + (1.0 - frac) * plot_h

        y_ticks = []
        step = y_max / 5
        for i in range(6):
            val = i * step
            label = f"{val/1000:.0f}k" if val < 1000000 else f"{val/1000000:.1f}M"
            if val == 0:
                label = "0"
            y_ticks.append((val, y_coord(val), label))

    # X-axis ticks (Year marks & Quarter marks)
    x_ticks = []
    curr_year = d_start.year
    while curr_year <= d_end.year + 1:
        for month in (1, 7):
            tick_date_str = f"{curr_year:04d}-{month:02d}-01"
            try:
                td = datetime.strptime(tick_date_str, "%Y-%m-%d")
                if d_start <= td <= d_end:
                    xc = x_coord(tick_date_str)
                    label = f"{curr_year}" if month == 1 else f"Jul '{str(curr_year)[2:]}"
                    x_ticks.append((xc, label, month == 1))
            except ValueError:
                pass
        curr_year += 1

    # Build SVG paths
    # 1. SARS CI Ribbon (upper & lower bounds)
    ci_points_top = []
    ci_points_bottom = []
    pred_points = []
    norm_points = []

    for r in sars:
        d_str = r[0]
        xc = round(x_coord(d_str), 1)
        pred = r[5]
        norm = r[4]
        upper = r[6]
        lower = r[7]

        if pred is not None:
            yc = round(y_coord(pred), 1)
            pred_points.append(f"{xc},{yc}")

        if norm is not None:
            yn = round(y_coord(norm), 1)
            norm_points.append(f"{xc},{yn}")

        if upper is not None and lower is not None:
            yu = round(y_coord(upper), 1)
            yl = round(y_coord(lower), 1)
            ci_points_top.append(f"{xc},{yu}")
            ci_points_bottom.insert(0, f"{xc},{yl}")

    ci_path_d = ""
    if ci_points_top and ci_points_bottom:
        ci_path_d = f"M {ci_points_top[0]} " + " ".join([f"L {pt}" for pt in ci_points_top[1:]]) + " " + " ".join([f"L {pt}" for pt in ci_points_bottom]) + " Z"

    pred_path_d = f"M {pred_points[0]} " + " ".join([f"L {pt}" for pt in pred_points[1:]]) if pred_points else ""
    norm_path_d = f"M {norm_points[0]} " + " ".join([f"L {pt}" for pt in norm_points[1:]]) if norm_points else ""

    # Flu Path
    flu_points = []
    for r in flu:
        pred = r[5]
        if pred is not None:
            xc = round(x_coord(r[0]), 1)
            yc = round(y_coord(pred), 1)
            flu_points.append(f"{xc},{yc}")
    flu_path_d = f"M {flu_points[0]} " + " ".join([f"L {pt}" for pt in flu_points[1:]]) if flu_points else ""

    # RSV Path
    rsv_points = []
    for r in rsv:
        pred = r[5]
        if pred is not None:
            xc = round(x_coord(r[0]), 1)
            yc = round(y_coord(pred), 1)
            rsv_points.append(f"{xc},{yc}")
    rsv_path_d = f"M {rsv_points[0]} " + " ".join([f"L {pt}" for pt in rsv_points[1:]]) if rsv_points else ""

    scale_title = "Logarithmische Skala (Log₁₀)" if scale == "log" else "Lineare Skala (Genkopien / Liter)"

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" class="amelag-chart-svg" role="img" aria-label="Bundesweite Abwassersurveillance Zeitreihe ({scale_title})">',
        f'  <title>AMELAG Abwassersurveillance Deutschland - {scale_title}</title>',
        f'  <desc>Zeitreihe der SARS-CoV-2, Influenza und RSV Viruslast im Abwasser (Deutschland, {min_date} bis {max_date}).</desc>',
        '  <defs>',
        '    <linearGradient id="ciGrad" x1="0%" y1="0%" x2="0%" y2="100%">',
        '      <stop offset="0%" stop-color="#4f46e5" stop-opacity="0.25" />',
        '      <stop offset="100%" stop-color="#4f46e5" stop-opacity="0.08" />',
        '    </linearGradient>',
        '    <clipPath id="plotClip">',
        f'      <rect x="{margin_l}" y="{margin_t}" width="{plot_w}" height="{plot_h}" />',
        '    </clipPath>',
        '  </defs>',
        # Background & Plot Area
        f'  <rect x="0" y="0" width="{width}" height="{height}" fill="var(--card-bg, #ffffff)" rx="8" />',
        f'  <rect x="{margin_l}" y="{margin_t}" width="{plot_w}" height="{plot_h}" fill="var(--plot-bg, #f8fafc)" stroke="var(--border-color, #e2e8f0)" stroke-width="1" />',
        # Gridlines and Y Ticks
        '  <g class="grid-y">'
    ]

    for val, yc, label in y_ticks:
        svg.append(f'    <line x1="{margin_l}" y1="{yc:.1f}" x2="{margin_l + plot_w}" y2="{yc:.1f}" stroke="var(--grid-color, #e2e8f0)" stroke-width="1" stroke-dasharray="3,3" />')
        svg.append(f'    <text x="{margin_l - 10}" y="{yc + 4:.1f}" text-anchor="end" font-size="11" fill="var(--text-muted, #64748b)" font-family="system-ui, sans-serif">{label}</text>')
    svg.append('  </g>')

    # Gridlines and X Ticks
    svg.append('  <g class="grid-x">')
    for xc, label, is_major in x_ticks:
        stroke_color = "var(--grid-major, #cbd5e1)" if is_major else "var(--grid-color, #f1f5f9)"
        svg.append(f'    <line x1="{xc:.1f}" y1="{margin_t}" x2="{xc:.1f}" y2="{margin_t + plot_h}" stroke="{stroke_color}" stroke-width="1" />')
        font_weight = "bold" if is_major else "normal"
        svg.append(f'    <text x="{xc:.1f}" y="{margin_t + plot_h + 18}" text-anchor="middle" font-size="11" font-weight="{font_weight}" fill="var(--text-muted, #64748b)" font-family="system-ui, sans-serif">{label}</text>')
    svg.append('  </g>')

    # Chart Lines clipped to plot area
    svg.append('  <g clip-path="url(#plotClip)">')
    # Shaded CI Ribbon
    if ci_path_d:
        svg.append(f'    <path d="{ci_path_d}" fill="url(#ciGrad)" />')
    # Normalized measurement line (thinner, dashed or subtle)
    if norm_path_d:
        svg.append(f'    <path d="{norm_path_d}" fill="none" stroke="#93c5fd" stroke-width="1" stroke-dasharray="2,2" opacity="0.75" />')
    # Influenza path
    if flu_path_d:
        svg.append(f'    <path d="{flu_path_d}" fill="none" stroke="#ea580c" stroke-width="2" opacity="0.9" />')
    # RSV path
    if rsv_path_d:
        svg.append(f'    <path d="{rsv_path_d}" fill="none" stroke="#ec4899" stroke-width="2" opacity="0.9" />')
    # SARS GAM Prediction (main curve)
    if pred_path_d:
        svg.append(f'    <path d="{pred_path_d}" fill="none" stroke="#4f46e5" stroke-width="3" />')
    svg.append('  </g>')

    # Chart Header / Legend
    svg.append(f'  <text x="{margin_l}" y="{margin_t - 22}" font-size="14" font-weight="700" fill="var(--text-color, #0f172a)" font-family="system-ui, sans-serif">Bundesweite Viruslast im Abwasser ({scale_title})</text>')
    svg.append(f'  <text x="{margin_l}" y="{margin_t - 6}" font-size="11" fill="var(--text-muted, #64748b)" font-family="system-ui, sans-serif">GAM-Modellierte Trends &amp; 95%-Konfidenzintervall • Quelle: RKI/UBA AMELAG</text>')

    # Legend items in top right
    leg_x = width - margin_r - 420
    leg_y = margin_t - 14
    svg.extend([
        f'  <g transform="translate({leg_x}, {leg_y})" font-family="system-ui, sans-serif" font-size="11">',
        '    <line x1="0" y1="0" x2="16" y2="0" stroke="#4f46e5" stroke-width="3" />',
        '    <text x="22" y="3" fill="var(--text-color, #1e293b)" font-weight="600">SARS-CoV-2</text>',
        '    <line x1="110" y1="0" x2="126" y2="0" stroke="#ea580c" stroke-width="2" />',
        '    <text x="132" y="3" fill="var(--text-color, #1e293b)">Grippe (Flu A+B)</text>',
        '    <line x1="240" y1="0" x2="256" y2="0" stroke="#ec4899" stroke-width="2" />',
        '    <text x="262" y="3" fill="var(--text-color, #1e293b)">RSV (A+B)</text>',
        '    <rect x="340" y="-5" width="12" height="10" fill="#4f46e5" fill-opacity="0.25" />',
        '    <text x="358" y="3" fill="var(--text-muted, #64748b)">95% KI</text>',
        '  </g>'
    ])

    # Y-axis label
    svg.append(f'  <text transform="rotate(-90)" x="{-margin_t - plot_h/2}" y="20" text-anchor="middle" font-size="11" font-weight="500" fill="var(--text-muted, #64748b)" font-family="system-ui, sans-serif">Genkopien / Liter ({scale_title})</text>')
    svg.append('</svg>')

    return "\n".join(svg)

def generate_static_html(national_data, states_data, sites_index, root_dir="."):
    """
    Renders index.html containing full semantic pre-rendered data, KPI cards,
    state breakdown table, and pre-rendered SVG charts for both Linear and Log scales.
    Enhanced with modern interactive JS SPA.
    """
    meta = national_data["meta"]
    p_stats = meta["pathogens"]
    sars_stat = p_stats.get("SARS-CoV-2", {})
    flu_stat = p_stats.get("Influenza A+B", {})
    rsv_stat = p_stats.get("RSV A+B", {})

    svg_linear = generate_svg_chart(national_data, scale="linear", width=980, height=480)
    svg_log = generate_svg_chart(national_data, scale="log", width=980, height=480)

    # Save standalone SVGs as well for direct download/view
    os.makedirs(os.path.join(root_dir, "assets"), exist_ok=True)
    with open(os.path.join(root_dir, "assets", "national_chart_linear.svg"), "w", encoding="utf-8") as f:
        f.write(svg_linear)
    with open(os.path.join(root_dir, "assets", "national_chart_log.svg"), "w", encoding="utf-8") as f:
        f.write(svg_log)

    # Helper for trend arrow
    def trend_badge(pct):
        if pct is None:
            return '<span class="badge badge-neutral">—</span>'
        if pct > 10:
            return f'<span class="badge badge-rising">↗ +{pct:.1f}%</span>'
        elif pct < -10:
            return f'<span class="badge badge-falling">↘ {pct:.1f}%</span>'
        else:
            return f'<span class="badge badge-stable">→ {pct:+.1f}%</span>'

    # Build State rows for pre-rendered table
    state_rows_html = []
    for code, s_info in sorted(states_data["states"].items(), key=lambda x: x[1]["population"], reverse=True):
        pop_fmt = f"{s_info['population']:,}".replace(",", ".")
        sars_val = f"{s_info['latest_sars']:,.0f}".replace(",", ".") if s_info['latest_sars'] else "—"
        badge = trend_badge(s_info['trend_7d'])
        state_rows_html.append(f"""
        <tr data-state="{code}">
          <td><strong><a href="#state-{code}" class="state-link" data-bl="{code}">{s_info['name']} ({code})</a></strong></td>
          <td class="text-right">{s_info['sites_count']}</td>
          <td class="text-right">{pop_fmt}</td>
          <td class="text-right font-mono">{sars_val}</td>
          <td class="text-center">{badge}</td>
        </tr>""")
    state_table_body = "\n".join(state_rows_html)

    # Build National Summary Table
    pathogen_rows_html = []
    for typ in ["SARS-CoV-2", "Influenza A+B", "Influenza A", "Influenza B", "RSV A+B", "RSV A", "RSV B"]:
        stat = p_stats.get(typ)
        if not stat:
            continue
        p_name = PATHOGEN_NAMES.get(typ, typ)
        val_fmt = f"{stat['latest_pred']:,.0f}".replace(",", ".")
        peak_fmt = f"{stat['peak_value']:,.0f}".replace(",", ".")
        cov_pct = f"{stat['latest_cov']*100:.1f}%" if stat['latest_cov'] else "—"
        badge = trend_badge(stat['chg_7d_pct'])
        pathogen_rows_html.append(f"""
        <tr>
          <td><span class="pathogen-dot" style="background-color: {PATHOGEN_COLORS.get(typ, '#64748b')}"></span> <strong>{p_name}</strong></td>
          <td class="text-right font-mono font-bold">{val_fmt}</td>
          <td class="text-center">{badge}</td>
          <td class="text-right">{stat['latest_n']} ({cov_pct})</td>
          <td class="text-right font-mono text-muted">{peak_fmt} <small>({stat['peak_date']})</small></td>
        </tr>""")
    pathogen_table_body = "\n".join(pathogen_rows_html)

    # HTML template with No-JS support, accessible landmarks, and rich JS SPA
    html_content = f"""<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AMELAG Abwassermonitor | Robert Koch-Institut &amp; UBA Abwassersurveillance</title>
  <meta name="description" content="Interaktives Dashboard zur bundesweiten Abwassersurveillance (AMELAG) von RKI und UBA. Zeitreihen für SARS-CoV-2, Influenza A/B und RSV in linearer und logarithmischer Skalierung.">
  <meta name="keywords" content="Abwassersurveillance, AMELAG, RKI, Robert Koch-Institut, SARS-CoV-2, Corona, Grippe, Influenza, RSV, Viruslast, Klärwerk, Deutschland">
  <meta name="author" content="Robert Koch-Institut &amp; Umweltbundesamt / AMELAG">
  <meta name="theme-color" content="#4f46e5">

  <!-- Open Graph / Social Media Meta Tags -->
  <meta property="og:title" content="AMELAG Abwassermonitor - Deutschland">
  <meta property="og:description" content="Wöchentliche Viruslasten von SARS-CoV-2, Influenza und RSV aus 169 Kläranlagen in ganz Deutschland mit linearer und logarithmischer Visualisierung.">
  <meta property="og:type" content="website">
  <meta property="og:url" content="https://robert-koch-institut.github.io/Abwassersurveillance_AMELAG/">
  <meta property="og:image" content="assets/national_chart_linear.svg">

  <link rel="stylesheet" href="css/dashboard.css">
  
  <noscript>
    <style>
      .js-only {{ display: none !important; }}
      .no-js-tabs {{ display: block; }}
      .chart-toggle-input:checked + .chart-container {{ display: block; }}
    </style>
  </noscript>
</head>
<body>
  <a href="#main-content" class="skip-link">Zum Hauptinhalt springen</a>

  <!-- Header -->
  <header class="app-header" role="banner">
    <div class="container header-container">
      <div class="brand">
        <div class="brand-badge">AMELAG</div>
        <div>
          <h1 class="brand-title">Abwassersurveillance Deutschland</h1>
          <p class="brand-subtitle">Robert Koch-Institut &amp; Umweltbundesamt • Datenstand: <time id="header-data-date" datetime="{meta['latest_date']}">{meta['latest_date']}</time></p>
        </div>
      </div>
      <div class="header-actions">
        <button id="theme-toggle" class="btn btn-icon js-only" aria-label="Farbschema wechseln" title="Hell/Dunkel umschalten">
          <span class="icon-sun">☀️</span><span class="icon-moon">🌙</span>
        </button>
        <a href="https://github.com/robert-koch-institut/Abwassersurveillance_AMELAG" target="_blank" rel="noopener noreferrer" class="btn btn-outline" title="GitHub Repository öffnen">
          <svg class="icon-github" viewBox="0 0 16 16" width="16" height="16" fill="currentColor" aria-hidden="true"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>
          <span>RKI Datensatz</span>
        </a>
      </div>
    </div>
  </header>

  <!-- Main Container -->
  <main id="main-content" class="container" role="main">
    
    <!-- KPI Hero Summary Cards -->
    <section class="kpi-grid" aria-label="Wichtigste Kennzahlen">
      <div class="kpi-card" id="kpi-sars">
        <div class="kpi-header">
          <span class="pathogen-pill pathogen-sars">SARS-CoV-2</span>
          <span class="kpi-date">{sars_stat.get('latest_date', '')}</span>
        </div>
        <div class="kpi-value-row">
          <span class="kpi-value" id="kpi-sars-val">{sars_stat.get('latest_pred', 0):,.0f}</span>
          <span class="kpi-unit">Genkopien/L</span>
        </div>
        <div class="kpi-footer">
          <span class="kpi-trend" id="kpi-sars-trend">{trend_badge(sars_stat.get('chg_7d_pct'))} vs. Vorwoche</span>
          <span class="kpi-sub">Peak: {sars_stat.get('peak_value', 0):,.0f} ({sars_stat.get('peak_date', '')})</span>
        </div>
      </div>

      <div class="kpi-card" id="kpi-flu">
        <div class="kpi-header">
          <span class="pathogen-pill pathogen-flu">Influenza A+B (Grippe)</span>
          <span class="kpi-date">{flu_stat.get('latest_date', '')}</span>
        </div>
        <div class="kpi-value-row">
          <span class="kpi-value" id="kpi-flu-val">{flu_stat.get('latest_pred', 0):,.0f}</span>
          <span class="kpi-unit">Genkopien/L</span>
        </div>
        <div class="kpi-footer">
          <span class="kpi-trend" id="kpi-flu-trend">{trend_badge(flu_stat.get('chg_7d_pct'))} vs. Vorwoche</span>
          <span class="kpi-sub">Peak: {flu_stat.get('peak_value', 0):,.0f} ({flu_stat.get('peak_date', '')})</span>
        </div>
      </div>

      <div class="kpi-card" id="kpi-rsv">
        <div class="kpi-header">
          <span class="pathogen-pill pathogen-rsv">RSV (A+B)</span>
          <span class="kpi-date">{rsv_stat.get('latest_date', '')}</span>
        </div>
        <div class="kpi-value-row">
          <span class="kpi-value" id="kpi-rsv-val">{rsv_stat.get('latest_pred', 0):,.0f}</span>
          <span class="kpi-unit">Genkopien/L</span>
        </div>
        <div class="kpi-footer">
          <span class="kpi-trend" id="kpi-rsv-trend">{trend_badge(rsv_stat.get('chg_7d_pct'))} vs. Vorwoche</span>
          <span class="kpi-sub">Peak: {rsv_stat.get('peak_value', 0):,.0f} ({rsv_stat.get('peak_date', '')})</span>
        </div>
      </div>

      <div class="kpi-card" id="kpi-coverage">
        <div class="kpi-header">
          <span class="pathogen-pill pathogen-neutral">Überwachungsnetz</span>
          <span class="kpi-date">Deutschlandweit</span>
        </div>
        <div class="kpi-value-row">
          <span class="kpi-value">{meta['total_sites']}</span>
          <span class="kpi-unit">Kläranlagen</span>
        </div>
        <div class="kpi-footer">
          <span class="kpi-sub">Versorgte Bevölkerung: <strong>{meta['total_population']:,}</strong></span>
          <span class="kpi-sub">Aktive Berichterstattung: {sars_stat.get('latest_n', 0)} Standorte</span>
        </div>
      </div>
    </section>

    <!-- Main Chart Section -->
    <section class="card chart-card" aria-label="Hauptgrafik Viruslast">
      
      <!-- Interactive Filter Controls (Enhanced via JS) -->
      <div class="chart-controls js-only">
        
        <!-- Row 1: Pathogen & Scale Toggles -->
        <div class="controls-row">
          <div class="control-group">
            <label class="control-label" for="filter-pathogen">Erreger:</label>
            <select id="filter-pathogen" class="select-input" aria-label="Erreger auswählen">
              <option value="SARS-CoV-2" selected>SARS-CoV-2 (COVID-19)</option>
              <option value="Influenza A+B">Influenza A+B (Grippe gesamt)</option>
              <option value="Influenza A">Influenza A</option>
              <option value="Influenza B">Influenza B</option>
              <option value="RSV A+B">RSV A+B (RS-Virus gesamt)</option>
              <option value="RSV A">RSV A</option>
              <option value="RSV B">RSV B</option>
              <option value="COMPARE_ALL">⚡ Multi-Vergleich (SARS + Flu + RSV)</option>
            </select>
          </div>

          <div class="control-group">
            <span class="control-label">Skalierung:</span>
            <div class="btn-group" role="group" aria-label="Skalierung">
              <button type="button" id="btn-scale-linear" class="btn btn-toggle active" data-scale="linear" title="Lineare Darstellung (absolute Virusmenge)">Linear</button>
              <button type="button" id="btn-scale-log" class="btn btn-toggle" data-scale="log" title="Logarithmische Darstellung (Exponentielles Wachstum &amp; Dynamik)">Log₁₀</button>
            </div>
          </div>

          <div class="control-group">
            <label class="control-label" for="filter-time-preset">Zeitraum:</label>
            <select id="filter-time-preset" class="select-input" aria-label="Zeitraum auswählen">
              <option value="all">Alle Daten (Gesamt 2022–heute)</option>
              <option value="30d">Letzte 30 Tage</option>
              <option value="90d">Letzte 90 Tage (3 Monate)</option>
              <option value="6m">Letzte 6 Monate</option>
              <option value="1y" selected>Letztes Jahr (12 Monate)</option>
              <option value="2y">Letzte 2 Jahre</option>
              <option value="custom">Benutzerdefiniert (Schieberegler)</option>
            </select>
          </div>
        </div>

        <!-- Row 2: Geographic & Metric Filters -->
        <div class="controls-row">
          <div class="control-group">
            <label class="control-label" for="filter-state">Bundesland:</label>
            <select id="filter-state" class="select-input" aria-label="Bundesland filtern">
              <option value="ALL" selected>Deutschlandweit (Gesamt)</option>
              <option value="BW">Baden-Württemberg (BW)</option>
              <option value="BY">Bayern (BY)</option>
              <option value="BE">Berlin (BE)</option>
              <option value="BB">Brandenburg (BB)</option>
              <option value="HB">Bremen (HB)</option>
              <option value="HH">Hamburg (HH)</option>
              <option value="HE">Hessen (HE)</option>
              <option value="MV">Mecklenburg-Vorpommern (MV)</option>
              <option value="NI">Niedersachsen (NI)</option>
              <option value="NW">Nordrhein-Westfalen (NW)</option>
              <option value="RP">Rheinland-Pfalz (RP)</option>
              <option value="SL">Saarland (SL)</option>
              <option value="SN">Sachsen (SN)</option>
              <option value="ST">Sachsen-Anhalt (ST)</option>
              <option value="SH">Schleswig-Holstein (SH)</option>
              <option value="TH">Thüringen (TH)</option>
            </select>
          </div>

          <div class="control-group">
            <label class="control-label" for="filter-site">Klärwerk (Standort):</label>
            <select id="filter-site" class="select-input select-searchable" aria-label="Einzelstandort auswählen">
              <option value="ALL" selected>Alle Standorte (Aggregiert)</option>
            </select>
          </div>

          <div class="control-group">
            <label class="control-label" for="filter-metric">Messwert:</label>
            <select id="filter-metric" class="select-input" aria-label="Messwert Metrik">
              <option value="pred" selected>GAM-Regression (Glättung + 95% KI)</option>
              <option value="norm">Durchfluss-normalisierte Viruslast</option>
              <option value="raw">Gemessene Viruslast (Rohwert)</option>
            </select>
          </div>

          <div class="control-group export-group">
            <button id="btn-export-csv" class="btn btn-outline btn-sm" title="Aktuell gefilterte Daten als CSV herunterladen">💾 CSV Export</button>
            <button id="btn-export-svg" class="btn btn-outline btn-sm" title="Grafik als SVG Vektorgrafik speichern">📊 SVG Export</button>
            <button id="btn-reset-filters" class="btn btn-ghost btn-sm" title="Filter zurücksetzen">↺ Reset</button>
          </div>
        </div>

        <!-- Row 3: Interactive Dual-Slider Temporal Slicer -->
        <div class="timeline-slicer" id="timeline-slicer-container">
          <div class="slicer-header">
            <div class="slicer-presets">
              <span class="control-label">Zeitfenster Schieberegler:</span>
            </div>
            <div class="slicer-labels">
              <span class="slicer-date-badge"><span class="badge-label">Von:</span> <strong id="slicer-label-start">—</strong></span>
              <span class="slicer-arrow">→</span>
              <span class="slicer-date-badge"><span class="badge-label">Bis:</span> <strong id="slicer-label-end">—</strong></span>
              <span class="slicer-span-text text-muted" id="slicer-span-days"></span>
            </div>
          </div>
          <div class="dual-slider-wrapper">
            <div class="dual-slider-track"></div>
            <div class="dual-slider-highlight" id="slider-highlight"></div>
            <input type="range" id="slider-start" class="range-input" min="0" max="100" value="70" step="1" aria-label="Startdatum eingrenzen">
            <input type="range" id="slider-end" class="range-input" min="0" max="100" value="100" step="1" aria-label="Enddatum eingrenzen">
          </div>
        </div>

      </div>

      <!-- Live Dynamic Chart Container (Pre-rendered for instant paint & hydrated via JS) -->
      <div id="chart-viewport" class="chart-viewport js-only">
        <div id="chart-svg-container" class="chart-svg-container">
          {svg_linear}
        </div>
        <!-- Tooltip overlay -->
        <div id="chart-tooltip" class="chart-tooltip" role="tooltip" aria-hidden="true"></div>
      </div>

      <!-- NO-JAVASCRIPT FALLBACK VIEW: Fully Pre-rendered Visualizations -->
      <noscript>
        <div class="no-js-banner alert alert-info">
          <strong>Hinweis:</strong> Sie betrachten die statische barrierefreie Version des Dashboards (ohne JavaScript). Alle bundesweiten Daten, Grafiken und Tabellen sind vollständig geladen und lesbar.
        </div>
        
        <div class="no-js-tabs">
          <details open class="chart-details">
            <summary class="chart-summary"><strong>📊 Grafik: Lineare Skala (Genkopien / Liter)</strong></summary>
            <div class="static-svg-wrapper">
              {svg_linear}
            </div>
            <p class="text-muted"><small>Lineare Skala zeigt die absolute physikalische Viruslast im Abwasser.</small></p>
          </details>

          <details class="chart-details">
            <summary class="chart-summary"><strong>📈 Grafik: Logarithmische Skala (Log₁₀)</strong></summary>
            <div class="static-svg-wrapper">
              {svg_log}
            </div>
            <p class="text-muted"><small>Logarithmische Skala verdeutlicht Vervielfachungsraten und exponentielle Dynamik bei niedrigen und hohen Werten gleichermaßen.</small></p>
          </details>
        </div>
      </noscript>

      <!-- Chart Metadata & Caption -->
      <div class="chart-caption">
        <p><strong>Erklärung:</strong> Die durchgezogene Linie repräsentiert den GAM-Regressionswert (generalisiertes additives Modell mit adaptiver Glättung). Das schattierte Band stellt das punktweise 95%-Konfidenzintervall dar. Alle Angaben in Genkopien pro Liter Abwasser.</p>
        <div class="chart-links">
          <a href="assets/national_chart_linear.svg" download="amelag_linear_deutschland.svg" class="btn-link">SVG (Linear) herunterladen</a> • 
          <a href="assets/national_chart_log.svg" download="amelag_log_deutschland.svg" class="btn-link">SVG (Logarithmisch) herunterladen</a> •
          <a href="data/national.json" download="national.json" class="btn-link">JSON-Rohdaten</a>
        </div>
      </div>
    </section>

    <!-- Content Split: State Overview & Pathogen Comparison -->
    <div class="dashboard-grid">
      
      <!-- Bundesländer Comparison Table -->
      <section class="card" aria-label="Bundesländer Übersicht">
        <div class="card-header">
          <h2 class="card-title">Bundesländer Übersicht</h2>
          <span class="card-subtitle">SARS-CoV-2 Viruslast &amp; 7-Tage-Trend nach Bundesland</span>
        </div>
        <div class="table-container">
          <table class="data-table" id="states-table">
            <thead>
              <tr>
                <th scope="col">Bundesland</th>
                <th scope="col" class="text-right">Kläranlagen</th>
                <th scope="col" class="text-right">Bevölkerung</th>
                <th scope="col" class="text-right">SARS-CoV-2</th>
                <th scope="col" class="text-center">Trend (7d)</th>
              </tr>
            </thead>
            <tbody>
              {state_table_body}
            </tbody>
          </table>
        </div>
      </section>

      <!-- Pathogen Comparison Table -->
      <section class="card" aria-label="Erreger-Vergleich">
        <div class="card-header">
          <h2 class="card-title">Erreger-Vergleich (Deutschlandweit)</h2>
          <span class="card-subtitle">Aktuelle Werte im Vergleich zu historischen Höchstständen</span>
        </div>
        <div class="table-container">
          <table class="data-table" id="pathogen-table">
            <thead>
              <tr>
                <th scope="col">Erreger</th>
                <th scope="col" class="text-right">Aktuell (Kopien/L)</th>
                <th scope="col" class="text-center">Trend (7d)</th>
                <th scope="col" class="text-right">Klärwerke (Abdeckung)</th>
                <th scope="col" class="text-right">Historischer Peak</th>
              </tr>
            </thead>
            <tbody>
              {pathogen_table_body}
            </tbody>
          </table>
        </div>
      </section>

    </div>

    <!-- Methodology & Data Notes -->
    <section class="card info-card" aria-label="Methodik und Datenquelle">
      <h2 class="card-title">Über den AMELAG-Datensatz &amp; Methodik</h2>
      <div class="info-content">
        <p>Das Projekt <strong>AMELAG</strong> (<em>Abwassersurveillance zur epidemiologischen Lageerfassung</em>) ist eine gemeinsame Initiative des <strong>Robert Koch-Instituts (RKI)</strong> und des <strong>Umweltbundesamts (UBA)</strong>. Seit Februar 2022 wird in einem bundesweiten Verbund aus Kläranlagen, Laboren und Fachbehörden die Konzentration von Krankheitserregern im Rohabwasser fortlaufend überwacht.</p>
        
        <h3>Warum lineare und logarithmische Darstellung?</h3>
        <ul>
          <li><strong>Lineare Skala:</strong> Zeigt die tatsächliche physikalische Konzentration der Viren im Abwasser. Dies verdeutlicht das absolute Ausmaß großer Infektionswellen im Vergleich zu ruhigen Sommerphasen.</li>
          <li><strong>Logarithmische Skala (Log₁₀):</strong> Da sich Viren in der Anfangsphase einer Welle exponentiell vermehren, entspricht eine exponentielle Zunahme auf der logarithmischen Achse einer Geraden. Dies erlaubt die frühe Erkennung von Trendwechseln und den gleichzeitigen Vergleich von Erregern mit unterschiedlichen Grundlasten (z. B. SARS-CoV-2 vs. RSV).</li>
        </ul>

        <h3>Normalisierung und GAM-Modellierung</h3>
        <p>Um Schwankungen durch Niederschläge, Schmelzwasser oder gewerbliche Einleitungen auszugleichen, wird die gemessene Viruslast über den Abwasserdurchfluss der Kläranlage normalisiert. Anschließend wird eine GAM-Regression (Generalized Additive Model) mit adaptiver Spline-Glättung berechnet, um den übergeordneten epidemiologischen Trend robuster gegenüber einzelnen Messtoleranzen abzubilden.</p>
        
        <div class="license-box">
          <p><strong>Datenlizenz:</strong> Die Rohdaten stehen unter der Lizenz <a href="https://creativecommons.org/licenses/by/4.0/deed.de" target="_blank" rel="noopener noreferrer">Creative Commons Namensnennung 4.0 International (CC BY 4.0)</a> bzw. Datenlizenz Deutschland – Namensnennung – Version 2.0. Quelle: Robert Koch-Institut (RKI) &amp; Umweltbundesamt (UBA), Zenodo Datensatz AMELAG.</p>
        </div>
      </div>
    </section>

  </main>

  <!-- Footer -->
  <footer class="app-footer" role="contentinfo">
    <div class="container footer-container">
      <p>AMELAG Abwassermonitor • Statische Webapplikation für GitHub Pages • Entwickelt mit barrierefreiem Fallback für Low-Performance &amp; Terminal-Browser.</p>
      <p class="footer-links">
        <a href="https://github.com/robert-koch-institut/Abwassersurveillance_AMELAG" target="_blank" rel="noopener noreferrer">Original RKI Repository</a> •
        <a href="https://www.rki.de/DE/Content/InfAZ/A/Abwassersurveillance/abwassersurveillance_node.html" target="_blank" rel="noopener noreferrer">RKI Fachinformation</a> •
        <a href="https://www.umweltbundesamt.de/" target="_blank" rel="noopener noreferrer">Umweltbundesamt</a>
      </p>
    </div>
  </footer>

  <!-- SPA Hydration Script -->
  <script src="js/dashboard.js"></script>
</body>
</html>
"""

    with open(os.path.join(root_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html_content)
    print("index.html successfully written with pre-rendered data and charts.")

if __name__ == "__main__":
    import sys
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    nat, states, sites = build_data(root)
    generate_static_html(nat, states, sites, root)
