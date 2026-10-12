# 🦠 AMELAG Abwassermonitor Deutschland

[![Deploy Static Dashboard to GitHub Pages](https://github.com/mgomezch/amelag-dashboard/actions/workflows/deploy.yml/badge.svg)](https://github.com/mgomezch/amelag-dashboard/actions)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC_BY_4.0-blue.svg)](https://creativecommons.org/licenses/by/4.0/deed.de)
[![Accessibility: Lynx & Links Verified](https://img.shields.io/badge/Accessibility-No--JS%20%26%20Terminal%20Ready-success.svg)](#barrierefreiheit--terminal-browser)

Ein modernes, barrierefreies und performantes **Single-Page-Dashboard (SPA)** zur Visualisierung der bundesweiten Abwassersurveillance des **Robert Koch-Instituts (RKI)** und des **Umweltbundesamts (UBA)** aus dem Projekt **AMELAG** (*Abwassersurveillance zur epidemiologischen Lageerfassung*).

Das Dashboard überwacht kontinuierlich die Viruslasten von:
- **SARS-CoV-2** (COVID-19)
- **Influenza A & B** (sowie Influenza A+B gesamt)
- **RSV A & B** (sowie RSV A+B gesamt)

aus **169 Kläranlagen** in allen **16 deutschen Bundesländern**, die über **31 Millionen Einwohner** abdecken.

---

## ✨ Hauptfunktionen

### 1. 📈 Lineare und Logarithmische Visualisierung
- **Lineare Skala (Genkopien / Liter):** Zeigt das reale physikalische Volumen der Viren im Abwasser. Verdeutlicht das Ausmaß von Infektionswellen im Vergleich zu sommerlichen Niedrigphasen.
- **Logarithmische Skala ($\text{Log}_{10}$):** Exponentielle Vervielfachungsraten in frühen Wachstumsphasen von Infektionswellen erscheinen als Geraden mit konstanter Steigung. Ermöglicht den direkten Vergleich zwischen Erregern mit stark unterschiedlichen Grundkonzentrationen (z. B. SARS-CoV-2 vs. RSV).
- **Statische No-JS-Ansicht:** Beide Diagramme sind zusätzlich als barrierefreie, statische Vektorgrafiken (SVG) direkt im HTML vorgerendert.

### 2. 🎛️ Interaktive Filter & Erregervergleich
- **Erreger-Auswahl:** Umschalten zwischen SARS-CoV-2, Influenza A, Influenza B, Influenza A+B, RSV A, RSV B, RSV A+B.
- **⚡ Multi-Erreger-Vergleich:** Gleichzeitige Einblendung von SARS-CoV-2, Grippe (Flu A+B) und RSV (A+B) auf einer gemeinsamen Zeitachse zur Analyse von Doppelwellen und saisonalen Überlappungen.
- **Geografische Filterung:**
  - Deutschlandweit (Gesamtüberblick)
  - 16 Bundesländer (mit bevölkerungsgewichteten Trends)
  - 169 Einzelklärwerke (z. B. Berlin-Ruhleben, Köln-Stammheim, München-Großlappen, Hamburg, Frankfurt-Niederrad etc.)
- **Temporales Slicing & Doppel-Schieberegler:**
  - Schnell-Auswahl über Preset-Dropdown: *Gesamtzeitraum (2022–heute)*, *Letzte 30 Tage*, *Letzte 90 Tage*, *Letzte 6 Monate*, *Letztes Jahr (12 Monate)*, *Letzte 2 Jahre*.
  - Synchronisierter Doppel-Schieberegler (Dual-Handle Slider) für beliebige zeitliche Teilabschnitte mit dynamischer Neuberechnung lokaler Peaks und Kennzahlen.
  - Deep-Linking & URL-State-Hash (`#p=sars-cov-2&s=log&t=6m&from=...&to=...`).
- **Metrik-Auswahl:** GAM-Spline-Regression (adaptive Glättung mit 95%-Konfidenzintervall), durchfluss-normalisierte Viruslast oder Rohmesswerte.
- **Daten- & Grafik-Export:** 1-Klick-Export der aktuell gefilterten Daten als CSV oder als Vektorgrafik (SVG).

### 3. 🌐 Zweisprachig (Deutsch / English)
- **Dynamischer Sprachwechsel:** Im Header kann mit einem Klick zwischen Deutsch (**DE**) und Englisch (**EN**) gewechselt werden. Die gesamte Benutzeroberfläche, Grafiken, Legenden, Tabellen und Achsenbeschriftungen schalten ohne Neuladen der Seite sofort um.
- **Vollwertige No-JS Multi-Page Fallbacks:**
  - Deutsche Version: [`index.html`](index.html)
  - Englische Version: [`en.html`](en.html) bzw. [`en/index.html`](en/index.html)
  - Auch in Lynx und Links/Links2 kann direkt über die oberen Hyperlinks `[DE]` und `[EN]` zwischen den Sprachen gewechselt werden.

### 4. ♿ Barrierefreiheit & Robuste No-JavaScript-Fallbacks
- Funktioniert vollständig ohne JavaScript: Alle Kennzahlen, Daten der Bundesländer, Erregervergleiche und SVG-Grafiken (linear & logarithmisch) sind statisch im HTML vorgerendert.
- Vollständig navigierbar mit Screenreadern und Tastatur (`Skip Links`, ARIA-Landmarks, semantische Tabellen).
- Getestet in textbasierten Terminal-Browsern wie **Lynx** und **Links/Links2**.

### 5. 📱 Responsives Design für alle Bildschirmgrößen
- Flüssiges Layout von extrem schmalen Bildschirmen (**320px** iPhone SE / KaiOS) über Smartphones (**375px**) und Tablets (**768px**) bis hin zu Desktop-Displays (**1280px+**).
- Automatische Unterstützung für Hell- und Dunkelmodus (`prefers-color-scheme` sowie manueller Umschalter mit Speicherung in `localStorage`).
- Optimierte Ladezeit: Initiale Ladezeit unter 50ms, da keine externen JavaScript-Frameworks oder schwere Bibliotheken verwendet werden (0 KB externe Runtime-Dependencies).

---

## 📸 Screenshots & Validierung

Automatisierte Headless-Browser-Tests (Firefox Headless) verifizieren das Layout über alle Displayauflösungen:

| Ansicht | Auflösung | Status |
| :--- | :--- | :--- |
| **Desktop** | 1280 × 800 px / 1280 × 1600 px | ✅ Verifiziert |
| **Tablet** | 768 × 1024 px | ✅ Verifiziert |
| **Mobile Standard** | 375 × 667 px / 375 × 1800 px | ✅ Verifiziert |
| **Mobile Narrow** | 320 × 568 px / 320 × 1600 px | ✅ Verifiziert |
| **Terminal (Lynx)** | Text-Only Terminal (UTF-8) | ✅ Verifiziert |
| **Terminal (Links2)** | Text-Only Terminal | ✅ Verifiziert |

---

## 🖥️ Barrierefreiheit & Terminal-Browser

Das Dashboard wurde speziell dafür entwickelt, auch auf ressourcenschwachen Geräten und in reinen Terminal-Browsern verständlich und übersichtlich zu sein:

```bash
# Test in Lynx (UTF-8)
nix shell nixpkgs#lynx --command lynx -display_charset=utf-8 -dump index.html

# Test in Links / Links2
nix shell nixpkgs#links2 --command links -dump index.html
```

---

## 🚀 Lokale Ausführung & Bauprozess

### 1. Voraussetzungen
- Python 3.8+
- Optional: Nix (für Lynx/Links2 und Browser-Tools)

### 2. Daten aktualisieren und HTML vorrendern
```bash
python3 scripts/build.py .
```

Das Skript liest die TSV-Dateien ein, erzeugt aggregierte JSON-Daten in `data/`, rendert die linearen und logarithmischen SVG-Grafiken in `assets/` und generiert die statische `index.html`.

### 3. Lokalen Webserver starten
```bash
python3 -m http.server 8080
```
Öffne anschließend [http://localhost:8080](http://localhost:8080) im Browser.

### 4. Headless-Browser-Tests ausführen
```bash
python3 scripts/test_headless.py
```

---

## 🌐 Veröffentlichung auf GitHub Pages

Das Repository enthält zwei vollautomatisierte GitHub Actions Workflows:

1. **`.github/workflows/deploy.yml`**:
   Baut und veröffentlicht die statische Website bei jedem Push auf den `main`-Branch automatisch auf **GitHub Pages**.
   
   *Aktivierung in den Repository-Einstellungen:*
   - Gehe zu `Settings` -> `Pages`.
   - Wähle als Source: **GitHub Actions**.

2. **`.github/workflows/update_data.yml`**:
   Lädt jeden Donnerstag automatisch die neuesten Messdaten aus dem RKI-Repository herunter, baut das Dashboard neu und committet die Aktualisierung.

---

## 📊 Datenquelle & Lizenz

Die Daten stammen aus der bundesweiten Abwassersurveillance des **Robert Koch-Instituts (RKI)** und des **Umweltbundesamts (UBA)**:
- Original-Repository: [https://github.com/robert-koch-institut/Abwassersurveillance_AMELAG](https://github.com/robert-koch-institut/Abwassersurveillance_AMELAG)
- Datensatz: Robert Koch-Institut & Umweltbundesamt. *Abwassersurveillance AMELAG*. Zenodo. [DOI: 10.5281/zenodo.23210544](https://doi.org/10.5281/zenodo.23210544)
- **Nutzungslizenz:** [Creative Commons Namensnennung 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/deed.de) / Datenlizenz Deutschland – Namensnennung – Version 2.0.
