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
import time

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
    "de": {
        "SARS-CoV-2": "SARS-CoV-2 (COVID-19)",
        "Influenza A": "Influenza A",
        "Influenza B": "Influenza B",
        "Influenza A+B": "Influenza A+B (Grippe gesamt)",
        "RSV A": "RSV A",
        "RSV B": "RSV B",
        "RSV A+B": "RSV A+B (RS-Virus gesamt)",
        "RSV A/B": "RSV A/B",
        "COMPARE_ALL": "⚡ Multi-Vergleich (SARS + Flu + RSV)"
    },
    "en": {
        "SARS-CoV-2": "SARS-CoV-2 (COVID-19)",
        "Influenza A": "Influenza A",
        "Influenza B": "Influenza B",
        "Influenza A+B": "Influenza A+B (Flu total)",
        "RSV A": "RSV A",
        "RSV B": "RSV B",
        "RSV A+B": "RSV A+B (RSV total)",
        "RSV A/B": "RSV A/B",
        "COMPARE_ALL": "⚡ Multi-Comparison (SARS + Flu + RSV)"
    }
}

I18N = {
    "de": {
        "lang": "de",
        "doc_title": "Inoffizieller Abwassermonitor Deutschland | Private Open-Data-Visualisierung",
        "doc_desc": "Inoffizielle, rein private Visualisierung der öffentlich zugänglichen AMELAG-Abwasserdaten. Keine Anbindung an das Robert Koch-Institut oder Behörden.",
        "keywords": "Abwassersurveillance, SARS-CoV-2, Corona, Grippe, Influenza, RSV, Viruslast, Klärwerk, Deutschland, Open Data",
        "og_title": "Inoffizieller Abwassermonitor - Deutschland",
        "og_desc": "Inoffizielle, unüberprüfte Visualisierung von Viruslasten aus 169 Kläranlagen in Deutschland auf Basis öffentlicher RKI/UBA Open Data.",
        "brand_badge": "Inoffiziell",
        "brand_title": "Abwassermonitor Deutschland",
        "brand_sub": "Inoffizielles Dashboard • Datenquelle: RKI &amp; UBA Open Data • Stand:",
        "rki_dataset": "RKI Originaldaten (GitHub)",
        "theme_toggle": "Farbschema wechseln",
        "skip_link": "Zum Hauptinhalt springen",
        "disclaimer_aria": "Wichtiger Hinweis und Haftungsausschluss",
        "disclaimer_badge": "⚠️ WICHTIGER HINWEIS &amp; HAFTUNGSAUSSCHLUSS",
        "disclaimer_title": "Inoffizielles, unüberprüftes Freizeitprojekt – Keine Anbindung an Behörden oder Institute",
        "disclaimer_p1": "<strong>Dieses Dashboard ist ein rein privates, unüberprüftes Freizeitprojekt von Manuel Gómez und steht in KEINERLEI Verbindung oder Partnerschaft zum Robert Koch-Institut (RKI), dem Umweltbundesamt (UBA) oder sonstigen Behörden oder Institutionen.</strong>",
        "disclaimer_p2": "Der Betreiber übernimmt keinerlei Gewähr für die Richtigkeit, Aktualität, Vollständigkeit oder Verlässlichkeit der hier dargestellten Grafiken, Berechnungen und Daten. <strong>Niemand sollte sich auf die Inhalte dieser Seite stützen</strong> (weder für medizinische, gesundheitliche, behördliche, rechtliche noch sonstige Entscheidungen).",
        "disclaimer_p3": "Für verlässliche epidemiologische Informationen, offizielle Bewertungen und validierte Auswertungen <strong>konsultieren Sie bitte ausschließlich die Primärquellen der zuständigen Fachbehörden</strong>: das offizielle <a href=\"https://github.com/robert-koch-institut/Abwassersurveillance_AMELAG\" target=\"_blank\" rel=\"noopener noreferrer\">RKI AMELAG GitHub-Repository</a> und das <a href=\"https://www.rki.de/abwassersurveillance\" target=\"_blank\" rel=\"noopener noreferrer\">Webangebot der RKI-Abwassersurveillance</a>. <strong>Vertrauen Sie diesem inoffiziellen Dashboard nicht.</strong>",
        "kpi_unit": "Genkopien/L",
        "vs_prev_week": "vs. Vorwoche",
        "peak": "Peak:",
        "surveillance_net": "Überwachungsnetz",
        "nationwide": "Deutschlandweit",
        "plants": "Kläranlagen",
        "covered_pop": "Versorgte Bevölkerung:",
        "active_rep": "Aktive Berichterstattung:",
        "sites": "Standorte",
        "filter_pathogen": "Erreger:",
        "filter_scale": "Skalierung:",
        "scale_linear": "Linear",
        "scale_log": "Log₁₀",
        "scale_linear_title": "Lineare Darstellung (absolute Virusmenge)",
        "scale_log_title": "Logarithmische Darstellung (Exponentielles Wachstum &amp; Dynamik)",
        "filter_time": "Zeitraum:",
        "preset_all": "Alle Daten (Gesamt 2022–heute)",
        "preset_30d": "Letzte 30 Tage",
        "preset_90d": "Letzte 90 Tage (3 Monate)",
        "preset_6m": "Letzte 6 Monate",
        "preset_1y": "Letztes Jahr (12 Monate)",
        "preset_2y": "Letzte 2 Jahre",
        "preset_custom": "Benutzerdefiniert (Schieberegler)",
        "slider_label": "Zeitfenster Schieberegler:",
        "slider_from": "Von:",
        "slider_to": "Bis:",
        "filter_state": "Bundesland:",
        "all_states": "Deutschlandweit (Gesamt)",
        "filter_site": "Klärwerk (Standort):",
        "all_sites": "Alle Standorte (Aggregiert)",
        "filter_metric": "Messwert:",
        "metric_pred": "GAM-Regression (Glättung + 95% KI)",
        "metric_norm": "Durchfluss-normalisierte Viruslast",
        "metric_raw": "Gemessene Viruslast (Rohwert)",
        "export_csv": "💾 CSV Export",
        "export_svg": "📊 SVG Export",
        "reset_filters": "↺ Reset",
        "chart_title_prefix": "Bundesweite Viruslast im Abwasser",
        "chart_sub": "GAM-Modellierte Trends &amp; 95%-Konfidenzintervall • Datenquelle: RKI/UBA AMELAG Open Data",
        "chart_scale_linear": "Lineare Skala (Genkopien / Liter)",
        "chart_scale_log": "Logarithmische Skala (Log₁₀)",
        "legend_flu": "Grippe (Flu A+B)",
        "legend_rsv": "RSV (A+B)",
        "ci_band": "95% KI",
        "unit_y": "Genkopien / Liter",
        "no_js_note": "Hinweis: Sie betrachten die statische barrierefreie Version des Dashboards (ohne JavaScript). Alle bundesweiten Daten, Grafiken und Tabellen sind vollständig geladen und lesbar.",
        "desc_linear": "Lineare Skala zeigt die absolute physikalische Viruslast im Abwasser.",
        "desc_log": "Logarithmische Skala verdeutlicht Vervielfachungsraten und exponentielle Dynamik bei niedrigen und hohen Werten gleichermaßen.",
        "chart_expl": "Erklärung: Die durchgezogene Linie repräsentiert den GAM-Regressionswert (generalisiertes additives Modell mit adaptiver Glättung). Das schattierte Band stellt das punktweise 95%-Konfidenzintervall dar. Alle Angaben in Genkopien pro Liter Abwasser.",
        "download_svg_lin": "SVG (Linear) herunterladen",
        "download_svg_log": "SVG (Logarithmisch) herunterladen",
        "download_json": "JSON-Rohdaten",
        "states_overview": "Bundesländer Übersicht",
        "states_sub": "SARS-CoV-2 Viruslast &amp; 7-Tage-Trend nach Bundesland",
        "th_state": "Bundesland",
        "th_plants": "Kläranlagen",
        "th_population": "Bevölkerung",
        "th_sars": "SARS-CoV-2",
        "th_trend": "Trend (7d)",
        "pathogen_comp": "Erreger-Vergleich (Deutschlandweit)",
        "pathogen_comp_sub": "Aktuelle Werte im Vergleich zu historischen Höchstständen",
        "th_pathogen": "Erreger",
        "th_current_val": "Aktuell (Kopien/L)",
        "th_sites_cov": "Klärwerke (Abdeckung)",
        "th_hist_peak": "Historischer Peak",
        "method_heading": "Über die Datenquelle &amp; Inoffizielles Projekt",
        "method_intro": "Die hier visualisierten Messdaten stammen aus dem Open-Data-Projekt <strong>AMELAG</strong> (<em>Abwassersurveillance zur epidemiologischen Lageerfassung</em>), einer gemeinsamen Initiative des <strong>Robert Koch-Instituts (RKI)</strong> und des <strong>Umweltbundesamts (UBA)</strong>. <strong>Wichtig:</strong> Diese Website ist ein rein privates, unüberprüftes Freizeitprojekt von Manuel Gómez und steht in <em>keinerlei</em> geschäftlicher, organisatorischer oder offizieller Beziehung zum Robert Koch-Institut oder dem Umweltbundesamt. Die Darstellung der Daten erfolgt ohne Gewähr und stellt keine offizielle Information dar.",
        "why_scales_heading": "Warum lineare und logarithmische Darstellung?",
        "why_scales_li1": "<strong>Lineare Skala:</strong> Zeigt die tatsächliche physikalische Konzentration der Viren im Abwasser. Dies verdeutlicht das absolute Ausmaß großer Infektionswellen im Vergleich zu ruhigen Sommerphasen.",
        "why_scales_li2": "<strong>Logarithmische Skala (Log₁₀):</strong> Da sich Viren in der Anfangsphase einer Welle exponentiell vermehren, entspricht eine exponentielle Zunahme auf der logarithmischen Achse einer Geraden. Dies erlaubt die frühe Erkennung von Trendwechseln und den gleichzeitigen Vergleich von Erregern mit unterschiedlichen Grundlasten (z. B. SARS-CoV-2 vs. RSV).",
        "norm_gam_heading": "Normalisierung und GAM-Modellierung",
        "norm_gam_p": "Um Schwankungen durch Niederschläge, Schmelzwasser oder gewerbliche Einleitungen auszugleichen, wird die gemessene Viruslast über den Abwasserdurchfluss der Kläranlage normalisiert. Anschließend wird eine GAM-Regression (Generalized Additive Model) mit adaptiver Spline-Glättung berechnet, um den übergeordneten epidemiologischen Trend robuster gegenüber einzelnen Messtoleranzen abzubilden.",
        "license_text": "<strong>Datenquelle &amp; Lizenzierung:</strong> Die zugrundeliegenden Rohdaten stammen aus dem öffentlichen Open-Data-Repositorium des RKI/UBA und sind lizenziert unter <a href=\"https://creativecommons.org/licenses/by/4.0/deed.de\" target=\"_blank\" rel=\"noopener noreferrer\">Creative Commons Namensnennung 4.0 International (CC BY 4.0)</a> bzw. dl-de/by-2-0. Dieses Web-Dashboard ist eine separate, inoffizielle Visualisierung und wird weder von den Datenurhebern herausgegeben noch geprüft.",
        "footer_text": "Inoffizieller Abwassermonitor Deutschland • Privates, unüberprüftes Freizeitprojekt von Manuel Gómez • Keine Anbindung an das Robert Koch-Institut, Umweltbundesamt oder Behörden.",
        "footer_orig": "Original RKI Daten-Repository (GitHub)",
        "footer_info": "Offizielle RKI Fachseite",
        "footer_uba": "Umweltbundesamt (UBA)",
        "lang_switch_aria": "Sprache auswählen / Select Language"
    },
    "en": {
        "lang": "en",
        "doc_title": "Unofficial Wastewater Monitor Germany | Private Open Data Visualization",
        "doc_desc": "Unofficial, purely personal visualization of public AMELAG wastewater open data. No affiliation with the Robert Koch Institute or government agencies.",
        "keywords": "Wastewater surveillance, SARS-CoV-2, COVID-19, Flu, Influenza, RSV, viral load, wastewater treatment plant, Germany, Open Data",
        "og_title": "Unofficial Wastewater Monitor - Germany",
        "og_desc": "Unofficial, unverified visualization of viral loads from 169 wastewater treatment plants across Germany based on public RKI/UBA Open Data.",
        "brand_badge": "Unofficial",
        "brand_title": "Wastewater Monitor Germany",
        "brand_sub": "Unofficial Dashboard • Data Source: RKI &amp; UBA Open Data • As of:",
        "rki_dataset": "RKI Original Data (GitHub)",
        "theme_toggle": "Switch Theme",
        "skip_link": "Skip to main content",
        "disclaimer_aria": "Important Notice and Disclaimer",
        "disclaimer_badge": "⚠️ IMPORTANT NOTICE &amp; DISCLAIMER",
        "disclaimer_title": "Unofficial, Unverified Hobby Project – Not Affiliated with Any Institution",
        "disclaimer_p1": "<strong>This dashboard is an entirely private, unverified personal project by Manuel Gómez and is in NO WAY affiliated with, endorsed by, or operated by the Robert Koch Institute (RKI), the German Environment Agency (UBA), or any official health authority or institution.</strong>",
        "disclaimer_p2": "No warranty or guarantee whatsoever is provided regarding the accuracy, timeliness, completeness, or reliability of any visualisations, numbers, or calculations shown here. <strong>Nobody should rely on the contents of this website</strong> for medical, health, public policy, legal, or other decision-making purposes.",
        "disclaimer_p3": "For reliable epidemiological information, official assessments, or decision-making, <strong>please consult the original primary sources published by the official authorities</strong>: specifically the official <a href=\"https://github.com/robert-koch-institut/Abwassersurveillance_AMELAG\" target=\"_blank\" rel=\"noopener noreferrer\">RKI AMELAG GitHub repository</a> and the <a href=\"https://www.rki.de/abwassersurveillance\" target=\"_blank\" rel=\"noopener noreferrer\">RKI Wastewater Surveillance page</a>. <strong>Do not rely on or trust this unofficial dashboard.</strong>",
        "kpi_unit": "Gene copies/L",
        "vs_prev_week": "vs. previous week",
        "peak": "Peak:",
        "surveillance_net": "Surveillance Network",
        "nationwide": "Nationwide (Germany)",
        "plants": "Treatment Plants",
        "covered_pop": "Covered Population:",
        "active_rep": "Active Reporting:",
        "sites": "Sites",
        "filter_pathogen": "Pathogen:",
        "filter_scale": "Scale:",
        "scale_linear": "Linear",
        "scale_log": "Log₁₀",
        "scale_linear_title": "Linear scale (absolute viral concentration)",
        "scale_log_title": "Logarithmic scale (exponential growth &amp; dynamics)",
        "filter_time": "Time Range:",
        "preset_all": "All Data (2022–present)",
        "preset_30d": "Last 30 Days",
        "preset_90d": "Last 90 Days (3 Months)",
        "preset_6m": "Last 6 Months",
        "preset_1y": "Last 1 Year (12 Months)",
        "preset_2y": "Last 2 Years",
        "preset_custom": "Custom (Slider)",
        "slider_label": "Time Window Slider:",
        "slider_from": "From:",
        "slider_to": "To:",
        "filter_state": "Federal State:",
        "all_states": "Germany (Nationwide)",
        "filter_site": "Wastewater Plant (Site):",
        "all_sites": "All Sites (Aggregated)",
        "filter_metric": "Metric:",
        "metric_pred": "GAM Regression (Smoothed + 95% CI)",
        "metric_norm": "Flow-Normalized Viral Load",
        "metric_raw": "Measured Viral Load (Raw)",
        "export_csv": "💾 Export CSV",
        "export_svg": "📊 Export SVG",
        "reset_filters": "↺ Reset",
        "chart_title_prefix": "National Viral Load in Wastewater",
        "chart_sub": "GAM-Modeled Trends &amp; 95% Confidence Interval • Data Source: RKI/UBA AMELAG Open Data",
        "chart_scale_linear": "Linear Scale (Gene copies / Liter)",
        "chart_scale_log": "Logarithmic Scale (Log₁₀)",
        "legend_flu": "Influenza (Flu A+B)",
        "legend_rsv": "RSV (A+B)",
        "ci_band": "95% CI",
        "unit_y": "Gene copies / Liter",
        "no_js_note": "Note: You are viewing the static accessible version of the dashboard (without JavaScript). All nationwide data, charts, and tables are fully loaded and readable.",
        "desc_linear": "Linear scale shows the absolute physical viral load in wastewater.",
        "desc_log": "Logarithmic scale highlights multiplication rates and exponential dynamics across both low and high values.",
        "chart_expl": "Explanation: The solid line represents the GAM regression value (Generalized Additive Model with adaptive smoothing). The shaded band represents the pointwise 95% confidence interval. All values in gene copies per liter of wastewater.",
        "download_svg_lin": "Download SVG (Linear)",
        "download_svg_log": "Download SVG (Logarithmic)",
        "download_json": "Raw JSON Data",
        "states_overview": "Federal States Overview",
        "states_sub": "SARS-CoV-2 Viral Load &amp; 7-Day Trend by Federal State",
        "th_state": "Federal State",
        "th_plants": "Treatment Plants",
        "th_population": "Population",
        "th_sars": "SARS-CoV-2",
        "th_trend": "Trend (7d)",
        "pathogen_comp": "Pathogen Comparison (Nationwide)",
        "pathogen_comp_sub": "Current values compared to historical peaks",
        "th_pathogen": "Pathogen",
        "th_current_val": "Current (copies/L)",
        "th_sites_cov": "Plants (Coverage)",
        "th_hist_peak": "Historical Peak",
        "method_heading": "About the Data Source &amp; Unofficial Project",
        "method_intro": "The measurements visualized here originate from the public open data of the <strong>AMELAG</strong> project (<em>Wastewater Surveillance for Epidemiological Situation Assessment</em>), a joint initiative by the <strong>Robert Koch Institute (RKI)</strong> and the <strong>German Environment Agency (UBA)</strong>. <strong>Important:</strong> This website is an entirely private, unverified hobby project by Manuel Gómez and has <em>no affiliation</em>, endorsement, or connection with the Robert Koch Institute or the German Environment Agency. Visualisations are provided as-is without any warranty and do not represent official statements or assessments.",
        "why_scales_heading": "Why Linear and Logarithmic Visualization?",
        "why_scales_li1": "<strong>Linear Scale:</strong> Shows the actual physical concentration of viruses in wastewater, illustrating the absolute scale of major infection waves compared to low baseline periods.",
        "why_scales_li2": "<strong>Logarithmic Scale (Log₁₀):</strong> Because viruses replicate exponentially during the early phase of an outbreak, exponential growth appears as a straight line with constant slope. This facilitates early trend detection and enables simultaneous comparison of pathogens with widely differing baselines (e.g. SARS-CoV-2 vs. RSV).",
        "norm_gam_heading": "Normalization and GAM Modeling",
        "norm_gam_p": "To compensate for variations caused by precipitation, snowmelt, or industrial inflows, measured viral loads are normalized by plant wastewater flow. A Generalized Additive Model (GAM) with adaptive spline smoothing is then applied to extract the underlying epidemiological trend with high resilience against individual measurement noise.",
        "license_text": "<strong>Data Source &amp; Licensing:</strong> The underlying raw data originates from the public open-data repository of RKI/UBA and is licensed under <a href=\"https://creativecommons.org/licenses/by/4.0/\" target=\"_blank\" rel=\"noopener noreferrer\">Creative Commons Attribution 4.0 International (CC BY 4.0)</a> / dl-de/by-2-0. This web dashboard is a completely independent, unofficial visualization and is neither published nor vetted by the data authors.",
        "footer_text": "Unofficial Wastewater Monitor Germany • Private, unverified personal project by Manuel Gómez • Not affiliated with the Robert Koch Institute, Federal Environment Agency, or government authorities.",
        "footer_orig": "Original RKI Data Repository (GitHub)",
        "footer_info": "Official RKI Web Page",
        "footer_uba": "German Environment Agency (UBA)",
        "lang_switch_aria": "Select Language / Sprache auswählen"
    }
}

def format_date_str(date_str, lang="de"):
    if not date_str:
        return ""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        if lang == "en":
            return dt.strftime("%b %d, %Y")
        else:
            months_de = ["", "Jan.", "Feb.", "März", "Apr.", "Mai", "Juni", "Juli", "Aug.", "Sept.", "Okt.", "Nov.", "Dez."]
            return f"{dt.day}. {months_de[dt.month]} {dt.year}"
    except Exception:
        return date_str

def format_num_str(val, decimals=0, lang="de"):
    if val is None:
        return "—"
    if decimals == 0:
        val = round(val)
        if lang == "de":
            return f"{val:,}".replace(",", ".")
        else:
            return f"{val:,}"
    else:
        if lang == "de":
            return f"{val:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")
        else:
            return f"{val:,.{decimals}f}"

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

def generate_svg_chart(national_data, scale="linear", width=960, height=480, lang="de"):
    """
    Generates a crisp, accessible, standalone SVG chart of the national SARS-CoV-2 curve
    with confidence intervals and comparison with Influenza A+B and RSV A+B.
    Works without any JavaScript.
    """
    t = I18N.get(lang, I18N["de"])
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

    scale_title = t["chart_scale_log"] if scale == "log" else t["chart_scale_linear"]
    desc_text = (f"Time series of SARS-CoV-2, Influenza, and RSV viral load in wastewater (Germany, {min_date} to {max_date})."
                 if lang == "en" else
                 f"Zeitreihe der SARS-CoV-2, Influenza und RSV Viruslast im Abwasser (Deutschland, {min_date} bis {max_date}).")

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" class="amelag-chart-svg" role="img" aria-label="{t["chart_title_prefix"]} ({scale_title})">',
        f'  <title>{t["brand_title"]} - {scale_title}</title>',
        f'  <desc>{desc_text}</desc>',
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
    svg.append(f'  <text x="{margin_l}" y="{margin_t - 22}" font-size="14" font-weight="700" fill="var(--text-color, #0f172a)" font-family="system-ui, sans-serif">{t["chart_title_prefix"]} ({scale_title})</text>')
    svg.append(f'  <text x="{margin_l}" y="{margin_t - 6}" font-size="11" fill="var(--text-muted, #64748b)" font-family="system-ui, sans-serif">{t["chart_sub"]}</text>')

    # Legend items in top right
    leg_x = width - margin_r - 420
    leg_y = margin_t - 14
    svg.extend([
        f'  <g transform="translate({leg_x}, {leg_y})" font-family="system-ui, sans-serif" font-size="11">',
        '    <line x1="0" y1="0" x2="16" y2="0" stroke="#4f46e5" stroke-width="3" />',
        '    <text x="22" y="3" fill="var(--text-color, #1e293b)" font-weight="600">SARS-CoV-2</text>',
        '    <line x1="110" y1="0" x2="126" y2="0" stroke="#ea580c" stroke-width="2" />',
        f'    <text x="132" y="3" fill="var(--text-color, #1e293b)">{t["legend_flu"]}</text>',
        '    <line x1="240" y1="0" x2="256" y2="0" stroke="#ec4899" stroke-width="2" />',
        f'    <text x="262" y="3" fill="var(--text-color, #1e293b)">{t["legend_rsv"]}</text>',
        '    <rect x="340" y="-5" width="12" height="10" fill="#4f46e5" fill-opacity="0.25" />',
        f'    <text x="358" y="3" fill="var(--text-muted, #64748b)">{t["ci_band"]}</text>',
        '  </g>'
    ])

    # Y-axis label
    svg.append(f'  <text transform="rotate(-90)" x="{-margin_t - plot_h/2}" y="20" text-anchor="middle" font-size="11" font-weight="500" fill="var(--text-muted, #64748b)" font-family="system-ui, sans-serif">{t["unit_y"]} ({scale_title})</text>')
    svg.append('</svg>')

    return "\n".join(svg)

def generate_static_html(national_data, states_data, sites_index, root_dir=".", lang="de", filename="index.html", path_prefix=""):
    """
    Renders static HTML containing full semantic pre-rendered data, KPI cards,
    state breakdown table, and pre-rendered SVG charts for both Linear and Log scales.
    Enhanced with modern interactive JS SPA. Supports bilingual pre-rendering (de/en).
    """
    t = I18N.get(lang, I18N["de"])
    meta = national_data["meta"]
    p_stats = meta["pathogens"]
    sars_stat = p_stats.get("SARS-CoV-2", {})
    flu_stat = p_stats.get("Influenza A+B", {})
    rsv_stat = p_stats.get("RSV A+B", {})

    svg_linear = generate_svg_chart(national_data, scale="linear", width=980, height=480, lang=lang)
    svg_log = generate_svg_chart(national_data, scale="log", width=980, height=480, lang=lang)

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
        pop_fmt = format_num_str(s_info['population'], 0, lang)
        sars_val = format_num_str(s_info['latest_sars'], 0, lang) if s_info['latest_sars'] else "—"
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
        p_name = PATHOGEN_NAMES[lang].get(typ, typ)
        val_fmt = format_num_str(stat['latest_pred'], 0, lang)
        peak_fmt = format_num_str(stat['peak_value'], 0, lang)
        cov_pct = f"{stat['latest_cov']*100:.1f}%" if stat['latest_cov'] else "—"
        badge = trend_badge(stat['chg_7d_pct'])
        peak_date_fmt = format_date_str(stat['peak_date'], lang)
        pathogen_rows_html.append(f"""
        <tr>
          <td><span class="pathogen-dot" style="background-color: {PATHOGEN_COLORS.get(typ, '#64748b')}"></span> <strong>{p_name}</strong></td>
          <td class="text-right font-mono font-bold">{val_fmt}</td>
          <td class="text-center">{badge}</td>
          <td class="text-right">{stat['latest_n']} ({cov_pct})</td>
          <td class="text-right font-mono text-muted">{peak_fmt} <small>({peak_date_fmt})</small></td>
        </tr>""")
    pathogen_table_body = "\n".join(pathogen_rows_html)

    de_href = f"{path_prefix}index.html"
    en_href = f"{path_prefix}en.html"
    active_de = "active" if lang == "de" else ""
    active_en = "active" if lang == "en" else ""
    build_ver = int(time.time())
    css_path = f"{path_prefix}css/dashboard.css?v={build_ver}"
    js_path = f"{path_prefix}js/dashboard.js?v={build_ver}"
    assets_prefix = f"{path_prefix}assets/"
    data_prefix = f"{path_prefix}data/"

    formatted_latest_date = format_date_str(meta['latest_date'], lang)
    total_pop_fmt = format_num_str(meta['total_population'], 0, lang)

    sars_val_fmt = format_num_str(sars_stat.get('latest_pred', 0), 0, lang)
    sars_peak_fmt = format_num_str(sars_stat.get('peak_value', 0), 0, lang)
    sars_peak_date = format_date_str(sars_stat.get('peak_date', ''), lang)
    sars_latest_date = format_date_str(sars_stat.get('latest_date', ''), lang)

    flu_val_fmt = format_num_str(flu_stat.get('latest_pred', 0), 0, lang)
    flu_peak_fmt = format_num_str(flu_stat.get('peak_value', 0), 0, lang)
    flu_peak_date = format_date_str(flu_stat.get('peak_date', ''), lang)
    flu_latest_date = format_date_str(flu_stat.get('latest_date', ''), lang)

    rsv_val_fmt = format_num_str(rsv_stat.get('latest_pred', 0), 0, lang)
    rsv_peak_fmt = format_num_str(rsv_stat.get('peak_value', 0), 0, lang)
    rsv_peak_date = format_date_str(rsv_stat.get('peak_date', ''), lang)
    rsv_latest_date = format_date_str(rsv_stat.get('latest_date', ''), lang)

    # HTML template with No-JS support, accessible landmarks, and rich JS SPA
    html_content = f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{t['doc_title']}</title>
  <meta name="description" content="{t['doc_desc']}">
  <meta name="keywords" content="{t['keywords']}">
  <meta name="author" content="Manuel Gómez (Inoffizielles Privatprojekt)">
  <meta name="theme-color" content="#4f46e5">

  <!-- Open Graph / Social Media Meta Tags -->
  <meta property="og:title" content="{t['og_title']}">
  <meta property="og:description" content="{t['og_desc']}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="https://mgomezch.github.io/amelag-dashboard/">
  <meta property="og:image" content="{assets_prefix}national_chart_linear.svg">

  <link rel="stylesheet" href="{css_path}">
  
  <noscript>
    <style>
      .js-only {{ display: none !important; }}
      .no-js-tabs {{ display: block; }}
      .chart-toggle-input:checked + .chart-container {{ display: block; }}
    </style>
  </noscript>
</head>
<body>
  <a href="#main-content" class="skip-link" data-i18n="skip_link">{t['skip_link']}</a>

  <!-- Header -->
  <header class="app-header" role="banner">
    <div class="container header-container">
      <div class="brand">
        <div class="brand-badge brand-badge-unofficial" data-i18n="brand_badge">{t['brand_badge']}</div>
        <div>
          <h1 class="brand-title" data-i18n="brand_title">{t['brand_title']}</h1>
          <p class="brand-subtitle"><span data-i18n="brand_sub">{t['brand_sub']}</span> <time id="header-data-date" datetime="{meta['latest_date']}">{formatted_latest_date}</time></p>
        </div>
      </div>
      <div class="header-actions">
        <div class="lang-switch" role="group" aria-label="{t['lang_switch_aria']}">
          <a href="{de_href}" class="lang-btn {active_de}" data-lang="de" aria-label="Deutsch">DE</a>
          <span class="lang-divider" aria-hidden="true">|</span>
          <a href="{en_href}" class="lang-btn {active_en}" data-lang="en" aria-label="English">EN</a>
        </div>
        <button id="theme-toggle" class="btn btn-icon js-only" aria-label="{t['theme_toggle']}" title="{t['theme_toggle']}">
          <span class="icon-sun">☀️</span><span class="icon-moon">🌙</span>
        </button>
        <a href="https://github.com/robert-koch-institut/Abwassersurveillance_AMELAG" target="_blank" rel="noopener noreferrer" class="btn btn-outline" title="{t['rki_dataset']}">
          <svg class="icon-github" viewBox="0 0 16 16" width="16" height="16" fill="currentColor" aria-hidden="true"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>
          <span data-i18n="rki_dataset">{t['rki_dataset']}</span>
        </a>
      </div>
    </div>
  </header>

  <!-- Main Container -->
  <main id="main-content" class="container" role="main">
    
    <!-- Unofficial Project Disclaimer Banner -->
    <aside class="disclaimer-banner" role="alert" aria-label="{t['disclaimer_aria']}">
      <div class="disclaimer-header">
        <span class="disclaimer-badge" data-i18n="disclaimer_badge">{t['disclaimer_badge']}</span>
        <h2 class="disclaimer-title" data-i18n="disclaimer_title">{t['disclaimer_title']}</h2>
      </div>
      <div class="disclaimer-body">
        <p data-i18n="disclaimer_p1">{t['disclaimer_p1']}</p>
        <p data-i18n="disclaimer_p2">{t['disclaimer_p2']}</p>
        <p data-i18n="disclaimer_p3">{t['disclaimer_p3']}</p>
      </div>
    </aside>

    <!-- KPI Hero Summary Cards -->
    <section class="kpi-grid" aria-label="Wichtigste Kennzahlen / Key Metrics">
      <div class="kpi-card" id="kpi-sars">
        <div class="kpi-header">
          <span class="pathogen-pill pathogen-sars">SARS-CoV-2</span>
          <span class="kpi-date">{sars_latest_date}</span>
        </div>
        <div class="kpi-value-row">
          <span class="kpi-value" id="kpi-sars-val">{sars_val_fmt}</span>
          <span class="kpi-unit" data-i18n="kpi_unit">{t['kpi_unit']}</span>
        </div>
        <div class="kpi-footer">
          <span class="kpi-trend" id="kpi-sars-trend">{trend_badge(sars_stat.get('chg_7d_pct'))} {t['vs_prev_week']}</span>
          <span class="kpi-sub">{t['peak']} {sars_peak_fmt} ({sars_peak_date})</span>
        </div>
      </div>

      <div class="kpi-card" id="kpi-flu">
        <div class="kpi-header">
          <span class="pathogen-pill pathogen-flu">{PATHOGEN_NAMES[lang]['Influenza A+B']}</span>
          <span class="kpi-date">{flu_latest_date}</span>
        </div>
        <div class="kpi-value-row">
          <span class="kpi-value" id="kpi-flu-val">{flu_val_fmt}</span>
          <span class="kpi-unit" data-i18n="kpi_unit">{t['kpi_unit']}</span>
        </div>
        <div class="kpi-footer">
          <span class="kpi-trend" id="kpi-flu-trend">{trend_badge(flu_stat.get('chg_7d_pct'))} {t['vs_prev_week']}</span>
          <span class="kpi-sub">{t['peak']} {flu_peak_fmt} ({flu_peak_date})</span>
        </div>
      </div>

      <div class="kpi-card" id="kpi-rsv">
        <div class="kpi-header">
          <span class="pathogen-pill pathogen-rsv">{PATHOGEN_NAMES[lang]['RSV A+B']}</span>
          <span class="kpi-date">{rsv_latest_date}</span>
        </div>
        <div class="kpi-value-row">
          <span class="kpi-value" id="kpi-rsv-val">{rsv_val_fmt}</span>
          <span class="kpi-unit" data-i18n="kpi_unit">{t['kpi_unit']}</span>
        </div>
        <div class="kpi-footer">
          <span class="kpi-trend" id="kpi-rsv-trend">{trend_badge(rsv_stat.get('chg_7d_pct'))} {t['vs_prev_week']}</span>
          <span class="kpi-sub">{t['peak']} {rsv_peak_fmt} ({rsv_peak_date})</span>
        </div>
      </div>

      <div class="kpi-card" id="kpi-coverage">
        <div class="kpi-header">
          <span class="pathogen-pill pathogen-neutral" data-i18n="surveillance_net">{t['surveillance_net']}</span>
          <span class="kpi-date" data-i18n="nationwide">{t['nationwide']}</span>
        </div>
        <div class="kpi-value-row">
          <span class="kpi-value">{meta['total_sites']}</span>
          <span class="kpi-unit" data-i18n="plants">{t['plants']}</span>
        </div>
        <div class="kpi-footer">
          <span class="kpi-sub"><span data-i18n="covered_pop">{t['covered_pop']}</span> <strong>{total_pop_fmt}</strong></span>
          <span class="kpi-sub"><span data-i18n="active_rep">{t['active_rep']}</span> {sars_stat.get('latest_n', 0)} <span data-i18n="sites">{t['sites']}</span></span>
        </div>
      </div>
    </section>

    <!-- Main Chart Section -->
    <section class="card chart-card" aria-label="Hauptgrafik Viruslast / Main Viral Load Chart">
      
      <!-- Interactive Filter Controls (Enhanced via JS) -->
      <div class="chart-controls js-only">
        
        <!-- Row 1: Pathogen & Scale Toggles -->
        <div class="controls-row">
          <div class="control-group">
            <label class="control-label" for="filter-pathogen" data-i18n="filter_pathogen">{t['filter_pathogen']}</label>
            <select id="filter-pathogen" class="select-input" aria-label="{t['filter_pathogen']}">
              <option value="SARS-CoV-2" selected>{PATHOGEN_NAMES[lang]['SARS-CoV-2']}</option>
              <option value="Influenza A+B">{PATHOGEN_NAMES[lang]['Influenza A+B']}</option>
              <option value="Influenza A">{PATHOGEN_NAMES[lang]['Influenza A']}</option>
              <option value="Influenza B">{PATHOGEN_NAMES[lang]['Influenza B']}</option>
              <option value="RSV A+B">{PATHOGEN_NAMES[lang]['RSV A+B']}</option>
              <option value="RSV A">{PATHOGEN_NAMES[lang]['RSV A']}</option>
              <option value="RSV B">{PATHOGEN_NAMES[lang]['RSV B']}</option>
              <option value="COMPARE_ALL">{PATHOGEN_NAMES[lang]['COMPARE_ALL']}</option>
            </select>
          </div>

          <div class="control-group">
            <span class="control-label" data-i18n="filter_scale">{t['filter_scale']}</span>
            <div class="btn-group" role="group" aria-label="{t['filter_scale']}">
              <button type="button" id="btn-scale-linear" class="btn btn-toggle active" data-scale="linear" title="{t['scale_linear_title']}" data-i18n="scale_linear">{t['scale_linear']}</button>
              <button type="button" id="btn-scale-log" class="btn btn-toggle" data-scale="log" title="{t['scale_log_title']}" data-i18n="scale_log">{t['scale_log']}</button>
            </div>
          </div>

          <div class="control-group">
            <label class="control-label" for="filter-time-preset" data-i18n="filter_time">{t['filter_time']}</label>
            <select id="filter-time-preset" class="select-input" aria-label="{t['filter_time']}">
              <option value="all">{t['preset_all']}</option>
              <option value="30d">{t['preset_30d']}</option>
              <option value="90d">{t['preset_90d']}</option>
              <option value="6m">{t['preset_6m']}</option>
              <option value="1y" selected>{t['preset_1y']}</option>
              <option value="2y">{t['preset_2y']}</option>
              <option value="custom">{t['preset_custom']}</option>
            </select>
          </div>
        </div>

        <!-- Row 2: Geographic & Metric Filters -->
        <div class="controls-row">
          <div class="control-group">
            <label class="control-label" for="filter-state" data-i18n="filter_state">{t['filter_state']}</label>
            <select id="filter-state" class="select-input" aria-label="{t['filter_state']}">
              <option value="ALL" selected>{t['all_states']}</option>
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
            <label class="control-label" for="filter-site" data-i18n="filter_site">{t['filter_site']}</label>
            <select id="filter-site" class="select-input select-searchable" aria-label="{t['filter_site']}">
              <option value="ALL" selected>{t['all_sites']}</option>
            </select>
          </div>

          <div class="control-group">
            <label class="control-label" for="filter-metric" data-i18n="filter_metric">{t['filter_metric']}</label>
            <select id="filter-metric" class="select-input" aria-label="{t['filter_metric']}">
              <option value="pred" selected>{t['metric_pred']}</option>
              <option value="norm">{t['metric_norm']}</option>
              <option value="raw">{t['metric_raw']}</option>
            </select>
          </div>

          <div class="control-group export-group">
            <button id="btn-export-csv" class="btn btn-outline btn-sm" title="{t['export_csv']}" data-i18n="export_csv">{t['export_csv']}</button>
            <button id="btn-export-svg" class="btn btn-outline btn-sm" title="{t['export_svg']}" data-i18n="export_svg">{t['export_svg']}</button>
            <button id="btn-reset-filters" class="btn btn-ghost btn-sm" title="{t['reset_filters']}" data-i18n="reset_filters">{t['reset_filters']}</button>
          </div>
        </div>

        <!-- Row 3: Interactive Dual-Slider Temporal Slicer -->
        <div class="timeline-slicer" id="timeline-slicer-container">
          <div class="slicer-header">
            <div class="slicer-presets">
              <span class="control-label" data-i18n="slider_label">{t['slider_label']}</span>
            </div>
            <div class="slicer-labels">
              <span class="slicer-date-badge"><span class="badge-label" data-i18n="slider_from">{t['slider_from']}</span> <strong id="slicer-label-start">—</strong></span>
              <span class="slicer-arrow">→</span>
              <span class="slicer-date-badge"><span class="badge-label" data-i18n="slider_to">{t['slider_to']}</span> <strong id="slicer-label-end">—</strong></span>
              <span class="slicer-span-text text-muted" id="slicer-span-days"></span>
            </div>
          </div>
          <div class="dual-slider-wrapper">
            <div class="dual-slider-track"></div>
            <div class="dual-slider-highlight" id="slider-highlight"></div>
            <input type="range" id="slider-start" class="range-input" min="0" max="100" value="70" step="1" aria-label="Start date">
            <input type="range" id="slider-end" class="range-input" min="0" max="100" value="100" step="1" aria-label="End date">
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
          <strong>{t['no_js_note']}</strong>
        </div>
        
        <div class="no-js-tabs">
          <details open class="chart-details">
            <summary class="chart-summary"><strong>📊 {t['chart_scale_linear']}</strong></summary>
            <div class="static-svg-wrapper">
              {svg_linear}
            </div>
            <p class="text-muted"><small>{t['desc_linear']}</small></p>
          </details>

          <details class="chart-details">
            <summary class="chart-summary"><strong>📈 {t['chart_scale_log']}</strong></summary>
            <div class="static-svg-wrapper">
              {svg_log}
            </div>
            <p class="text-muted"><small>{t['desc_log']}</small></p>
          </details>
        </div>
      </noscript>

      <!-- Chart Metadata & Caption -->
      <div class="chart-caption">
        <p data-i18n="chart_expl">{t['chart_expl']}</p>
        <div class="chart-links">
          <a href="{assets_prefix}national_chart_linear.svg" download="amelag_linear_{lang}.svg" class="btn-link">{t['download_svg_lin']}</a> • 
          <a href="{assets_prefix}national_chart_log.svg" download="amelag_log_{lang}.svg" class="btn-link">{t['download_svg_log']}</a> •
          <a href="{data_prefix}national.json" download="national.json" class="btn-link">{t['download_json']}</a>
        </div>
      </div>
    </section>

    <!-- Content Split: State Overview & Pathogen Comparison -->
    <div class="dashboard-grid">
      
      <!-- Bundesländer Comparison Table -->
      <section class="card" aria-label="{t['states_overview']}">
        <div class="card-header">
          <h2 class="card-title" data-i18n="states_overview">{t['states_overview']}</h2>
          <span class="card-subtitle" data-i18n="states_sub">{t['states_sub']}</span>
        </div>
        <div class="table-container">
          <table class="data-table" id="states-table">
            <thead>
              <tr>
                <th scope="col" data-i18n="th_state">{t['th_state']}</th>
                <th scope="col" class="text-right" data-i18n="th_plants">{t['th_plants']}</th>
                <th scope="col" class="text-right" data-i18n="th_population">{t['th_population']}</th>
                <th scope="col" class="text-right" data-i18n="th_sars">{t['th_sars']}</th>
                <th scope="col" class="text-center" data-i18n="th_trend">{t['th_trend']}</th>
              </tr>
            </thead>
            <tbody>
              {state_table_body}
            </tbody>
          </table>
        </div>
      </section>

      <!-- Pathogen Comparison Table -->
      <section class="card" aria-label="{t['pathogen_comp']}">
        <div class="card-header">
          <h2 class="card-title" data-i18n="pathogen_comp">{t['pathogen_comp']}</h2>
          <span class="card-subtitle" data-i18n="pathogen_comp_sub">{t['pathogen_comp_sub']}</span>
        </div>
        <div class="table-container">
          <table class="data-table" id="pathogen-table">
            <thead>
              <tr>
                <th scope="col" data-i18n="th_pathogen">{t['th_pathogen']}</th>
                <th scope="col" class="text-right" data-i18n="th_current_val">{t['th_current_val']}</th>
                <th scope="col" class="text-center" data-i18n="th_trend">{t['th_trend']}</th>
                <th scope="col" class="text-right" data-i18n="th_sites_cov">{t['th_sites_cov']}</th>
                <th scope="col" class="text-right" data-i18n="th_hist_peak">{t['th_hist_peak']}</th>
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
    <section class="card info-card" aria-label="{t['method_heading']}">
      <h2 class="card-title" data-i18n="method_heading">{t['method_heading']}</h2>
      <div class="info-content">
        <p data-i18n="method_intro">{t['method_intro']}</p>
        
        <h3 data-i18n="why_scales_heading">{t['why_scales_heading']}</h3>
        <ul>
          <li data-i18n="why_scales_li1">{t['why_scales_li1']}</li>
          <li data-i18n="why_scales_li2">{t['why_scales_li2']}</li>
        </ul>

        <h3 data-i18n="norm_gam_heading">{t['norm_gam_heading']}</h3>
        <p data-i18n="norm_gam_p">{t['norm_gam_p']}</p>
        
        <div class="license-box">
          <p data-i18n="license_text">{t['license_text']}</p>
        </div>
      </div>
    </section>

  </main>

  <!-- Footer -->
  <footer class="app-footer" role="contentinfo">
    <div class="container footer-container">
      <p data-i18n="footer_text">{t['footer_text']}</p>
      <p class="footer-links">
        <a href="https://github.com/robert-koch-institut/Abwassersurveillance_AMELAG" target="_blank" rel="noopener noreferrer" data-i18n="footer_orig">{t['footer_orig']}</a> •
        <a href="https://www.rki.de/DE/Content/InfAZ/A/Abwassersurveillance/abwassersurveillance_node.html" target="_blank" rel="noopener noreferrer" data-i18n="footer_info">{t['footer_info']}</a> •
        <a href="https://www.umweltbundesamt.de/" target="_blank" rel="noopener noreferrer" data-i18n="footer_uba">{t['footer_uba']}</a>
      </p>
    </div>
  </footer>

  <!-- SPA Hydration Script -->
  <script src="{js_path}"></script>
</body>
</html>
"""

    out_file = os.path.join(root_dir, filename)
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"{filename} successfully written in [{lang.upper()}].")

if __name__ == "__main__":
    import sys
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    nat, states, sites = build_data(root)

    # 1. Standalone SVG Assets (both DE and EN)
    assets_dir = os.path.join(root, "assets")
    os.makedirs(assets_dir, exist_ok=True)
    with open(os.path.join(assets_dir, "national_chart_linear.svg"), "w", encoding="utf-8") as f:
        f.write(generate_svg_chart(nat, scale="linear", width=980, height=480, lang="de"))
    with open(os.path.join(assets_dir, "national_chart_log.svg"), "w", encoding="utf-8") as f:
        f.write(generate_svg_chart(nat, scale="log", width=980, height=480, lang="de"))
    with open(os.path.join(assets_dir, "national_chart_linear_en.svg"), "w", encoding="utf-8") as f:
        f.write(generate_svg_chart(nat, scale="linear", width=980, height=480, lang="en"))
    with open(os.path.join(assets_dir, "national_chart_log_en.svg"), "w", encoding="utf-8") as f:
        f.write(generate_svg_chart(nat, scale="log", width=980, height=480, lang="en"))

    # 2. Multi-page pre-rendering: German default (index.html)
    generate_static_html(nat, states, sites, root_dir=root, lang="de", filename="index.html", path_prefix="")

    # 3. Multi-page pre-rendering: English version (en.html in root)
    generate_static_html(nat, states, sites, root_dir=root, lang="en", filename="en.html", path_prefix="")

    # 4. Multi-page pre-rendering: English version (en/index.html with ../ path prefix)
    generate_static_html(nat, states, sites, root_dir=root, lang="en", filename="en/index.html", path_prefix="../")

    print("Static build finished: index.html (DE), en.html (EN), en/index.html (EN) generated!")
