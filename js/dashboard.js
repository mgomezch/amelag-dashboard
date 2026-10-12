/**
 * AMELAG Wastewater Surveillance Dashboard SPA
 * High-performance, zero-dependency interactive data visualization engine.
 * Supports Linear & Logarithmic scaling, temporal sub-slicing,
 * dynamic English/German bilingual switching, multi-pathogen comparison,
 * geographic drilling (national, state, individual wastewater site), and data export.
 */

(function () {
  'use strict';

  // Constants & Dictionaries
  const PATHOGEN_CONFIG = {
    'SARS-CoV-2': { name: 'SARS-CoV-2 (COVID-19)', color: '#4f46e5', lightColor: '#818cf8', bg: 'rgba(79, 70, 229, 0.18)' },
    'Influenza A+B': { name: 'Influenza A+B (Grippe gesamt)', color: '#ea580c', lightColor: '#fb923c', bg: 'rgba(234, 88, 12, 0.18)' },
    'Influenza A': { name: 'Influenza A', color: '#f59e0b', lightColor: '#fcd34d', bg: 'rgba(245, 158, 11, 0.18)' },
    'Influenza B': { name: 'Influenza B', color: '#ef4444', lightColor: '#f87171', bg: 'rgba(239, 68, 68, 0.18)' },
    'RSV A+B': { name: 'RSV A+B (RS-Virus gesamt)', color: '#ec4899', lightColor: '#f472b6', bg: 'rgba(236, 72, 153, 0.18)' },
    'RSV A': { name: 'RSV A', color: '#06b6d4', lightColor: '#67e8f9', bg: 'rgba(6, 182, 212, 0.18)' },
    'RSV B': { name: 'RSV B', color: '#8b5cf6', lightColor: '#c084fc', bg: 'rgba(139, 92, 246, 0.18)' },
    'RSV A/B': { name: 'RSV A/B', color: '#14b8a6', lightColor: '#5eead4', bg: 'rgba(20, 184, 166, 0.18)' }
  };

  const STATE_NAMES = {
    'BW': 'Baden-Württemberg', 'BY': 'Bayern', 'BE': 'Berlin', 'BB': 'Brandenburg',
    'HB': 'Bremen', 'HH': 'Hamburg', 'HE': 'Hessen', 'MV': 'Mecklenburg-Vorpommern',
    'NI': 'Niedersachsen', 'NW': 'Nordrhein-Westfalen', 'RP': 'Rheinland-Pfalz',
    'SL': 'Saarland', 'SN': 'Sachsen', 'ST': 'Sachsen-Anhalt', 'SH': 'Schleswig-Holstein',
    'TH': 'Thüringen'
  };

  const I18N = {
    de: {
      docTitle: 'AMELAG Abwassermonitor | Robert Koch-Institut & UBA Abwassersurveillance',
      brandTitle: 'Abwassersurveillance Deutschland',
      brandSub: 'Robert Koch-Institut &amp; Umweltbundesamt • Datenstand:',
      rkiDataset: 'RKI Datensatz',
      themeToggle: 'Farbschema wechseln',
      skipLink: 'Zum Hauptinhalt springen',
      kpiUnit: 'Genkopien/L',
      vsPrevWeek: 'vs. Vorwoche',
      peak: 'Peak:',
      surveillanceNet: 'Überwachungsnetz',
      nationwide: 'Deutschlandweit',
      plants: 'Kläranlagen',
      coveredPop: 'Versorgte Bevölkerung:',
      activeRep: 'Aktive Berichterstattung:',
      sites: 'Standorte',
      filterPathogen: 'Erreger:',
      filterScale: 'Skalierung:',
      scaleLinear: 'Linear',
      scaleLog: 'Log₁₀',
      scaleLinearTitle: 'Lineare Darstellung (absolute Virusmenge)',
      scaleLogTitle: 'Logarithmische Darstellung (Exponentielles Wachstum &amp; Dynamik)',
      filterTime: 'Zeitraum:',
      timePresets: {
        'all': 'Alle Daten (Gesamt 2022–heute)',
        '30d': 'Letzte 30 Tage',
        '90d': 'Letzte 90 Tage (3 Monate)',
        '6m': 'Letzte 6 Monate',
        '1y': 'Letztes Jahr (12 Monate)',
        '2y': 'Letzte 2 Jahre',
        'custom': 'Benutzerdefiniert (Schieberegler)'
      },
      sliderLabel: 'Zeitfenster Schieberegler:',
      sliderFrom: 'Von:',
      sliderTo: 'Bis:',
      days: 'Tage',
      filterState: 'Bundesland:',
      allStates: 'Deutschlandweit (Gesamt)',
      filterSite: 'Klärwerk (Standort):',
      allSites: 'Alle Standorte (Aggregiert)',
      inhabitants: 'Einw.',
      filterMetric: 'Messwert:',
      metrics: {
        'pred': 'GAM-Regression (Glättung + 95% KI)',
        'norm': 'Durchfluss-normalisierte Viruslast',
        'raw': 'Gemessene Viruslast (Rohwert)'
      },
      exportCsv: '💾 CSV Export',
      exportSvg: '📊 SVG Export',
      resetFilters: '↺ Reset',
      pathogenNames: {
        'SARS-CoV-2': 'SARS-CoV-2 (COVID-19)',
        'Influenza A+B': 'Influenza A+B (Grippe gesamt)',
        'Influenza A': 'Influenza A',
        'Influenza B': 'Influenza B',
        'RSV A+B': 'RSV A+B (RS-Virus gesamt)',
        'RSV A': 'RSV A',
        'RSV B': 'RSV B',
        'COMPARE_ALL': '⚡ Multi-Vergleich (SARS + Flu + RSV)'
      },
      chartTitlePrefix: 'Bundesweite Viruslast im Abwasser',
      chartSub: 'GAM-Modellierte Trends &amp; 95%-Konfidenzintervall • Quelle: RKI/UBA AMELAG',
      chartScaleLinear: 'Lineare Skala (Genkopien / Liter)',
      chartScaleLog: 'Logarithmische Skala (Log₁₀)',
      legendFlu: 'Grippe (Flu A+B)',
      legendRsv: 'RSV (A+B)',
      ciBand: '95% KI',
      unitY: 'Genkopien / Liter',
      viralLoadY: 'Viruslast',
      tooltipCopies: 'Kopien/L',
      tooltipCi: '95% KI:',
      tooltipActivePlants: 'Kläranlagen aktiv:',
      tooltipPop: 'Bev.',
      noData: 'Keine Daten für diese Filterkombination verfügbar.',
      exportNoData: 'Keine Daten für den Export verfügbar.',
      statesOverview: 'Bundesländer Übersicht',
      statesSub: 'SARS-CoV-2 Viruslast &amp; 7-Tage-Trend nach Bundesland',
      thState: 'Bundesland',
      thPlants: 'Kläranlagen',
      thPopulation: 'Bevölkerung',
      thSars: 'SARS-CoV-2',
      thTrend: 'Trend (7d)',
      pathogenComp: 'Erreger-Vergleich (Deutschlandweit)',
      pathogenCompSub: 'Aktuelle Werte im Vergleich zu historischen Höchstständen',
      thPathogen: 'Erreger',
      thCurrentVal: 'Aktuell (Kopien/L)',
      thSitesCov: 'Klärwerke (Abdeckung)',
      thHistPeak: 'Historischer Peak',
      methodHeading: 'Über den AMELAG-Datensatz &amp; Methodik',
      whyScalesHeading: 'Warum lineare und logarithmische Darstellung?',
      normGamHeading: 'Normalisierung und GAM-Modellierung',
      licenseText: '<strong>Datenlizenz:</strong> Die Rohdaten stehen unter der Lizenz <a href="https://creativecommons.org/licenses/by/4.0/deed.de" target="_blank" rel="noopener noreferrer">Creative Commons Namensnennung 4.0 International (CC BY 4.0)</a> bzw. Datenlizenz Deutschland – Namensnennung – Version 2.0. Quelle: Robert Koch-Institut (RKI) &amp; Umweltbundesamt (UBA), Zenodo Datensatz AMELAG.',
      footerText: 'AMELAG Abwassermonitor • Statische Webapplikation für GitHub Pages • Entwickelt mit barrierefreiem Fallback für Low-Performance &amp; Terminal-Browser.',
      footerOrig: 'Original RKI Repository',
      footerInfo: 'RKI Fachinformation',
      footerUba: 'Umweltbundesamt'
    },
    en: {
      docTitle: 'AMELAG Wastewater Monitor | Robert Koch Institute & UBA Wastewater Surveillance',
      brandTitle: 'Wastewater Surveillance Germany',
      brandSub: 'Robert Koch Institute &amp; Federal Environment Agency • As of:',
      rkiDataset: 'RKI Dataset',
      themeToggle: 'Switch Theme',
      skipLink: 'Skip to main content',
      kpiUnit: 'Gene copies/L',
      vsPrevWeek: 'vs. previous week',
      peak: 'Peak:',
      surveillanceNet: 'Surveillance Network',
      nationwide: 'Nationwide (Germany)',
      plants: 'Treatment Plants',
      coveredPop: 'Covered Population:',
      activeRep: 'Active Reporting:',
      sites: 'Sites',
      filterPathogen: 'Pathogen:',
      filterScale: 'Scale:',
      scaleLinear: 'Linear',
      scaleLog: 'Log₁₀',
      scaleLinearTitle: 'Linear scale (absolute viral concentration)',
      scaleLogTitle: 'Logarithmic scale (exponential growth &amp; dynamics)',
      filterTime: 'Time Range:',
      timePresets: {
        'all': 'All Data (2022–present)',
        '30d': 'Last 30 Days',
        '90d': 'Last 90 Days (3 Months)',
        '6m': 'Last 6 Months',
        '1y': 'Last 1 Year (12 Months)',
        '2y': 'Last 2 Years',
        'custom': 'Custom (Slider)'
      },
      sliderLabel: 'Time Window Slider:',
      sliderFrom: 'From:',
      sliderTo: 'To:',
      days: 'days',
      filterState: 'Federal State:',
      allStates: 'Germany (Nationwide)',
      filterSite: 'Wastewater Plant (Site):',
      allSites: 'All Sites (Aggregated)',
      inhabitants: 'inh.',
      filterMetric: 'Metric:',
      metrics: {
        'pred': 'GAM Regression (Smoothed + 95% CI)',
        'norm': 'Flow-Normalized Viral Load',
        'raw': 'Measured Viral Load (Raw)'
      },
      exportCsv: '💾 Export CSV',
      exportSvg: '📊 Export SVG',
      resetFilters: '↺ Reset',
      pathogenNames: {
        'SARS-CoV-2': 'SARS-CoV-2 (COVID-19)',
        'Influenza A+B': 'Influenza A+B (Flu total)',
        'Influenza A': 'Influenza A',
        'Influenza B': 'Influenza B',
        'RSV A+B': 'RSV A+B (RSV total)',
        'RSV A': 'RSV A',
        'RSV B': 'RSV B',
        'COMPARE_ALL': '⚡ Multi-Comparison (SARS + Flu + RSV)'
      },
      chartTitlePrefix: 'National Viral Load in Wastewater',
      chartSub: 'GAM-Modeled Trends &amp; 95% Confidence Interval • Source: RKI/UBA AMELAG',
      chartScaleLinear: 'Linear Scale (Gene copies / Liter)',
      chartScaleLog: 'Logarithmic Scale (Log₁₀)',
      legendFlu: 'Influenza (Flu A+B)',
      legendRsv: 'RSV (A+B)',
      ciBand: '95% CI',
      unitY: 'Gene copies / Liter',
      viralLoadY: 'Viral Load',
      tooltipCopies: 'copies/L',
      tooltipCi: '95% CI:',
      tooltipActivePlants: 'Active plants:',
      tooltipPop: 'Pop.',
      noData: 'No data available for this filter combination.',
      exportNoData: 'No data available for export.',
      statesOverview: 'Federal States Overview',
      statesSub: 'SARS-CoV-2 Viral Load &amp; 7-Day Trend by Federal State',
      thState: 'Federal State',
      thPlants: 'Treatment Plants',
      thPopulation: 'Population',
      thSars: 'SARS-CoV-2',
      thTrend: 'Trend (7d)',
      pathogenComp: 'Pathogen Comparison (Nationwide)',
      pathogenCompSub: 'Current values compared to historical peaks',
      thPathogen: 'Pathogen',
      thCurrentVal: 'Current (copies/L)',
      thSitesCov: 'Plants (Coverage)',
      thHistPeak: 'Historical Peak',
      methodHeading: 'About the AMELAG Dataset &amp; Methodology',
      whyScalesHeading: 'Why Linear and Logarithmic Visualization?',
      normGamHeading: 'Normalization and GAM Modeling',
      licenseText: '<strong>Data License:</strong> Raw data is licensed under <a href="https://creativecommons.org/licenses/by/4.0/" target="_blank" rel="noopener noreferrer">Creative Commons Attribution 4.0 International (CC BY 4.0)</a> / Data License Germany – Attribution – Version 2.0. Source: Robert Koch Institute (RKI) &amp; Federal Environment Agency (UBA), Zenodo AMELAG dataset.',
      footerText: 'AMELAG Wastewater Monitor • Static Web Application for GitHub Pages • Built with accessible fallback for low-performance &amp; terminal browsers.',
      footerOrig: 'Original RKI Repository',
      footerInfo: 'RKI Technical Information',
      footerUba: 'German Environment Agency (UBA)'
    }
  };

  // Application State
  const AppState = {
    lang: 'de',
    pathogen: 'SARS-CoV-2',
    scale: 'linear',        // 'linear' | 'log'
    timePreset: '1y',       // 'all' | '30d' | '90d' | '6m' | '1y' | '2y' | 'custom'
    startDate: null,        // 'YYYY-MM-DD'
    endDate: null,          // 'YYYY-MM-DD'
    globalMinDate: null,    // Earliest date in data
    globalMaxDate: null,    // Latest date in data
    totalDays: 0,
    state: 'ALL',           // 'ALL' | state code (e.g. 'BY')
    site: 'ALL',            // 'ALL' | site slug (e.g. 'aachen')
    metric: 'pred',         // 'pred' | 'norm' | 'raw'
    data: {
      national: null,
      sitesIndex: null,
      statesSummary: null,
      stateCache: {},
      siteCache: {}
    }
  };

  // DOM Elements
  const DOM = {
    filterPathogen: document.getElementById('filter-pathogen'),
    btnScaleLinear: document.getElementById('btn-scale-linear'),
    btnScaleLog: document.getElementById('btn-scale-log'),
    filterTimePreset: document.getElementById('filter-time-preset'),
    sliderStart: document.getElementById('slider-start'),
    sliderEnd: document.getElementById('slider-end'),
    sliderHighlight: document.getElementById('slider-highlight'),
    slicerLabelStart: document.getElementById('slicer-label-start'),
    slicerLabelEnd: document.getElementById('slicer-label-end'),
    slicerSpanDays: document.getElementById('slicer-span-days'),
    filterState: document.getElementById('filter-state'),
    filterSite: document.getElementById('filter-site'),
    filterMetric: document.getElementById('filter-metric'),
    btnResetFilters: document.getElementById('btn-reset-filters'),
    btnExportCsv: document.getElementById('btn-export-csv'),
    btnExportSvg: document.getElementById('btn-export-svg'),
    themeToggle: document.getElementById('theme-toggle'),
    chartViewport: document.getElementById('chart-viewport'),
    chartContainer: document.getElementById('chart-svg-container'),
    chartTooltip: document.getElementById('chart-tooltip'),
    kpiSarsVal: document.getElementById('kpi-sars-val'),
    kpiSarsTrend: document.getElementById('kpi-sars-trend'),
    kpiFluVal: document.getElementById('kpi-flu-val'),
    kpiFluTrend: document.getElementById('kpi-flu-trend'),
    kpiRsvVal: document.getElementById('kpi-rsv-val'),
    kpiRsvTrend: document.getElementById('kpi-rsv-trend'),
    statesTable: document.getElementById('states-table')
  };

  // Helper Functions
  function formatNumber(num, decimals = 0, lang = (AppState.lang || 'de')) {
    if (num === null || num === undefined || isNaN(num)) return '—';
    const locale = lang === 'en' ? 'en-US' : 'de-DE';
    return Number(num).toLocaleString(locale, {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    });
  }

  function formatDate(dateStr, lang = (AppState.lang || 'de')) {
    if (!dateStr) return '';
    const parts = dateStr.split('-');
    if (parts.length !== 3) return dateStr;
    const d = new Date(Date.UTC(parts[0], parts[1] - 1, parts[2]));
    const locale = lang === 'en' ? 'en-US' : 'de-DE';
    return d.toLocaleDateString(locale, { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' });
  }

  function trendBadge(pct) {
    if (pct === null || pct === undefined || isNaN(pct)) {
      return '<span class="badge badge-neutral">—</span>';
    }
    const val = Number(pct);
    if (val > 10) {
      return `<span class="badge badge-rising">↗ +${val.toFixed(1)}%</span>`;
    } else if (val < -10) {
      return `<span class="badge badge-falling">↘ ${val.toFixed(1)}%</span>`;
    } else {
      return `<span class="badge badge-stable">→ ${val >= 0 ? '+' : ''}${val.toFixed(1)}%</span>`;
    }
  }

  // URL Hash State Management
  function syncStateToURL() {
    const params = new URLSearchParams();
    if (AppState.lang !== 'de') params.set('lang', AppState.lang);
    if (AppState.pathogen !== 'SARS-CoV-2') params.set('p', AppState.pathogen);
    if (AppState.scale !== 'linear') params.set('s', AppState.scale);
    if (AppState.timePreset !== '1y') params.set('t', AppState.timePreset);
    if (AppState.startDate && AppState.timePreset === 'custom') params.set('from', AppState.startDate);
    if (AppState.endDate && AppState.timePreset === 'custom') params.set('to', AppState.endDate);
    if (AppState.state !== 'ALL') params.set('bl', AppState.state);
    if (AppState.site !== 'ALL') params.set('site', AppState.site);
    if (AppState.metric !== 'pred') params.set('m', AppState.metric);
    const hashStr = params.toString();
    history.replaceState(null, '', hashStr ? `#${hashStr}` : window.location.pathname);
  }

  function parseStateFromURL() {
    if (!window.location.hash || window.location.hash.length <= 1) return;
    const params = new URLSearchParams(window.location.hash.substring(1));
    if (params.has('lang')) AppState.lang = params.get('lang');
    if (params.has('p')) AppState.pathogen = params.get('p');
    if (params.has('s')) AppState.scale = params.get('s');
    if (params.has('t')) AppState.timePreset = params.get('t');
    if (params.has('from')) AppState.startDate = params.get('from');
    if (params.has('to')) AppState.endDate = params.get('to');
    if (params.has('bl')) AppState.state = params.get('bl');
    if (params.has('site')) AppState.site = params.get('site');
    if (params.has('m')) AppState.metric = params.get('m');
  }

  // Theme Management
  function initTheme() {
    const savedTheme = localStorage.getItem('amelag-theme');
    if (savedTheme) {
      document.documentElement.setAttribute('data-theme', savedTheme);
    }
    DOM.themeToggle?.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-theme');
      const next = current === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('amelag-theme', next);
    });
  }

  // Dynamic Language Switcher (SPA)
  function setLanguage(lang) {
    if (!I18N[lang]) return;
    AppState.lang = lang;
    try {
      localStorage.setItem('amelag_lang', lang);
    } catch (e) {}

    document.documentElement.lang = lang;
    const t = I18N[lang];

    // Document title
    document.title = t.docTitle;

    // Header Date
    const headerDateEl = document.getElementById('header-data-date');
    if (headerDateEl && headerDateEl.dateTime) {
      headerDateEl.textContent = formatDate(headerDateEl.dateTime, lang);
    }

    // Language buttons
    document.querySelectorAll('.lang-btn').forEach(btn => {
      if (btn.dataset.lang === lang) {
        btn.classList.add('active');
        btn.setAttribute('aria-current', 'true');
      } else {
        btn.classList.remove('active');
        btn.removeAttribute('aria-current');
      }
    });

    // Theme toggle
    if (DOM.themeToggle) {
      DOM.themeToggle.setAttribute('aria-label', t.themeToggle);
      DOM.themeToggle.setAttribute('title', t.themeToggle);
    }

    // All elements with data-i18n
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.dataset.i18n;
      if (t[key] !== undefined) {
        el.innerHTML = t[key];
      }
    });

    // Dropdown labels
    if (DOM.filterPathogen) {
      Array.from(DOM.filterPathogen.options).forEach(opt => {
        if (t.pathogenNames[opt.value]) opt.textContent = t.pathogenNames[opt.value];
      });
    }

    if (DOM.filterTimePreset) {
      Array.from(DOM.filterTimePreset.options).forEach(opt => {
        if (t.timePresets[opt.value]) opt.textContent = t.timePresets[opt.value];
      });
    }

    if (DOM.filterState) {
      const firstOpt = DOM.filterState.options[0];
      if (firstOpt && firstOpt.value === 'ALL') firstOpt.textContent = t.allStates;
    }

    if (DOM.filterSite) {
      populateSiteDropdown();
    }

    if (DOM.filterMetric) {
      Array.from(DOM.filterMetric.options).forEach(opt => {
        if (t.metrics[opt.value]) opt.textContent = t.metrics[opt.value];
      });
    }

    // Scale buttons
    if (DOM.btnScaleLinear) DOM.btnScaleLinear.title = t.scaleLinearTitle;
    if (DOM.btnScaleLog) DOM.btnScaleLog.title = t.scaleLogTitle;

    // Slicer UI & dates
    updateSlicerUI();

    // KPI Cards & Tables
    updateKPICards();
    renderStatesTable();
    renderChart();
  }

  // Date and Range Slider Utilities
  function dateToDays(dateStr) {
    if (!AppState.globalMinDate || !dateStr) return 0;
    const d0 = new Date(AppState.globalMinDate);
    const d = new Date(dateStr);
    return Math.max(0, Math.min(AppState.totalDays, Math.round((d - d0) / 86400000)));
  }

  function daysToDateStr(days) {
    if (!AppState.globalMinDate) return '';
    const d0 = new Date(AppState.globalMinDate);
    const target = new Date(d0.getTime() + days * 86400000);
    return target.toISOString().slice(0, 10);
  }

  function updateSlicerUI() {
    if (!DOM.sliderStart || !DOM.sliderEnd || AppState.totalDays <= 0) return;

    const startVal = Number(DOM.sliderStart.value);
    const endVal = Number(DOM.sliderEnd.value);
    const pctStart = (startVal / AppState.totalDays) * 100;
    const pctEnd = (endVal / AppState.totalDays) * 100;

    if (DOM.sliderHighlight) {
      DOM.sliderHighlight.style.left = `${pctStart}%`;
      DOM.sliderHighlight.style.width = `${Math.max(0, pctEnd - pctStart)}%`;
    }
    if (DOM.slicerLabelStart) {
      DOM.slicerLabelStart.textContent = formatDate(AppState.startDate, AppState.lang);
    }
    if (DOM.slicerLabelEnd) {
      DOM.slicerLabelEnd.textContent = formatDate(AppState.endDate, AppState.lang);
    }
    if (DOM.slicerSpanDays) {
      const diffDays = Math.max(endVal - startVal, 1);
      const dayUnit = AppState.lang === 'en' ? 'days' : 'Tage';
      DOM.slicerSpanDays.textContent = `(${diffDays} ${dayUnit})`;
    }
    if (DOM.filterTimePreset) {
      DOM.filterTimePreset.value = AppState.timePreset;
    }
  }

  function applyTimePreset(preset, triggerRender = true) {
    AppState.timePreset = preset;
    const total = AppState.totalDays;
    let startDays = 0;
    let endDays = total;

    if (preset === '30d') {
      startDays = Math.max(0, total - 30);
    } else if (preset === '90d') {
      startDays = Math.max(0, total - 90);
    } else if (preset === '6m') {
      startDays = Math.max(0, total - 182);
    } else if (preset === '1y') {
      startDays = Math.max(0, total - 365);
    } else if (preset === '2y') {
      startDays = Math.max(0, total - 730);
    } else if (preset === 'all') {
      startDays = 0;
      endDays = total;
    }

    if (DOM.sliderStart && DOM.sliderEnd) {
      DOM.sliderStart.value = startDays;
      DOM.sliderEnd.value = endDays;
    }

    AppState.startDate = daysToDateStr(startDays);
    AppState.endDate = daysToDateStr(endDays);

    updateSlicerUI();

    if (triggerRender) {
      renderChart();
      syncStateToURL();
    }
  }

  function initTimelineSlicer() {
    if (!AppState.data.national) return;
    const sars = AppState.data.national.series['SARS-CoV-2'] || [];
    if (sars.length === 0) return;

    AppState.globalMinDate = sars[0][0];
    AppState.globalMaxDate = sars[sars.length - 1][0];

    const dMin = new Date(AppState.globalMinDate);
    const dMax = new Date(AppState.globalMaxDate);
    AppState.totalDays = Math.max(Math.round((dMax - dMin) / 86400000), 1);

    if (DOM.sliderStart && DOM.sliderEnd) {
      DOM.sliderStart.min = 0;
      DOM.sliderStart.max = AppState.totalDays;
      DOM.sliderEnd.min = 0;
      DOM.sliderEnd.max = AppState.totalDays;

      if (AppState.startDate && AppState.endDate) {
        DOM.sliderStart.value = dateToDays(AppState.startDate);
        DOM.sliderEnd.value = dateToDays(AppState.endDate);
        AppState.timePreset = 'custom';
        updateSlicerUI();
      } else {
        applyTimePreset(AppState.timePreset, false);
      }
    }
  }

  // Data Loading
  async function loadInitialData() {
    try {
      const [natRes, sitesRes, statesRes] = await Promise.all([
        fetch('data/national.json').then(r => r.json()),
        fetch('data/sites_index.json').then(r => r.json()),
        fetch('data/states_summary.json').then(r => r.json())
      ]);

      AppState.data.national = natRes;
      AppState.data.sitesIndex = sitesRes;
      AppState.data.statesSummary = statesRes;

      initTimelineSlicer();
      populateSiteDropdown();
      applyStateToInputs();
      renderStatesTable();
      await updateActiveDataAndRender();
    } catch (err) {
      console.error('Error loading initial data:', err);
    }
  }

  async function loadStateData(blCode) {
    if (AppState.data.stateCache[blCode]) {
      return AppState.data.stateCache[blCode];
    }
    try {
      const res = await fetch(`data/states/${blCode.toLowerCase()}.json`).then(r => r.json());
      AppState.data.stateCache[blCode] = res;
      return res;
    } catch (e) {
      console.error(`Failed to load data for state ${blCode}`, e);
      return null;
    }
  }

  async function loadSiteData(siteSlug) {
    if (AppState.data.siteCache[siteSlug]) {
      return AppState.data.siteCache[siteSlug];
    }
    try {
      const res = await fetch(`data/sites/${siteSlug}.json`).then(r => r.json());
      AppState.data.siteCache[siteSlug] = res;
      return res;
    } catch (e) {
      console.error(`Failed to load data for site ${siteSlug}`, e);
      return null;
    }
  }

  function populateSiteDropdown() {
    if (!DOM.filterSite || !AppState.data.sitesIndex) return;
    const currentSite = AppState.site;
    const currentState = AppState.state;
    const t = I18N[AppState.lang || 'de'];

    const filteredSites = currentState === 'ALL'
      ? AppState.data.sitesIndex
      : AppState.data.sitesIndex.filter(s => s.bl === currentState);

    let html = `<option value="ALL">${t.allSites}</option>`;
    let currentBl = '';

    filteredSites.forEach(s => {
      if (currentState === 'ALL' && s.bl !== currentBl) {
        if (currentBl !== '') html += '</optgroup>';
        currentBl = s.bl;
        html += `<optgroup label="${STATE_NAMES[currentBl] || currentBl}">`;
      }
      const selected = s.id === currentSite ? ' selected' : '';
      const popStr = s.pop ? ` (${formatNumber(s.pop, 0, AppState.lang)} ${t.inhabitants})` : '';
      html += `<option value="${s.id}"${selected}>${s.name}${popStr}</option>`;
    });

    if (currentState === 'ALL' && currentBl !== '') {
      html += '</optgroup>';
    }

    DOM.filterSite.innerHTML = html;
  }

  function applyStateToInputs() {
    if (DOM.filterPathogen) DOM.filterPathogen.value = AppState.pathogen;
    if (DOM.filterState) DOM.filterState.value = AppState.state;
    if (DOM.filterSite) DOM.filterSite.value = AppState.site;
    if (DOM.filterMetric) DOM.filterMetric.value = AppState.metric;
    if (DOM.filterTimePreset) DOM.filterTimePreset.value = AppState.timePreset;

    if (DOM.btnScaleLinear && DOM.btnScaleLog) {
      DOM.btnScaleLinear.classList.toggle('active', AppState.scale === 'linear');
      DOM.btnScaleLog.classList.toggle('active', AppState.scale === 'log');
    }
  }

  // Update Data and Re-render View
  async function updateActiveDataAndRender() {
    if (AppState.site !== 'ALL') {
      await loadSiteData(AppState.site);
    } else if (AppState.state !== 'ALL') {
      await loadStateData(AppState.state);
    }

    updateKPICards();
    renderChart();
    syncStateToURL();
  }

  // Update KPI Cards depending on current geographic selection
  function updateKPICards() {
    if (!AppState.data.national) return;
    const t = I18N[AppState.lang || 'de'];

    if (AppState.site !== 'ALL') {
      const siteData = AppState.data.siteCache[AppState.site];
      if (siteData && siteData.info) {
        const sarsSeries = siteData.series['SARS-CoV-2'] || [];
        const lastPt = sarsSeries.length > 0 ? sarsSeries[sarsSeries.length - 1] : null;
        if (lastPt) {
          DOM.kpiSarsVal.textContent = formatNumber(lastPt[3] || lastPt[2], 0, AppState.lang);
        }
      }
      return;
    }

    if (AppState.state !== 'ALL') {
      const stInfo = AppState.data.statesSummary?.states?.[AppState.state];
      if (stInfo) {
        DOM.kpiSarsVal.textContent = formatNumber(stInfo.latest_sars, 0, AppState.lang);
        DOM.kpiSarsTrend.innerHTML = trendBadge(stInfo.trend_7d) + ' ' + t.vsPrevWeek;
      }
      return;
    }

    // Default: National KPIs
    const pStats = AppState.data.national.meta.pathogens;
    if (pStats['SARS-CoV-2']) {
      DOM.kpiSarsVal.textContent = formatNumber(pStats['SARS-CoV-2'].latest_pred, 0, AppState.lang);
      DOM.kpiSarsTrend.innerHTML = trendBadge(pStats['SARS-CoV-2'].chg_7d_pct) + ' ' + t.vsPrevWeek;
    }
    if (pStats['Influenza A+B']) {
      DOM.kpiFluVal.textContent = formatNumber(pStats['Influenza A+B'].latest_pred, 0, AppState.lang);
      DOM.kpiFluTrend.innerHTML = trendBadge(pStats['Influenza A+B'].chg_7d_pct) + ' ' + t.vsPrevWeek;
    }
    if (pStats['RSV A+B']) {
      DOM.kpiRsvVal.textContent = formatNumber(pStats['RSV A+B'].latest_pred, 0, AppState.lang);
      DOM.kpiRsvTrend.innerHTML = trendBadge(pStats['RSV A+B'].chg_7d_pct) + ' ' + t.vsPrevWeek;
    }
  }

  // Render State Breakdown Table
  function renderStatesTable() {
    if (!DOM.statesTable || !AppState.data.statesSummary) return;
    const t = I18N[AppState.lang || 'de'];
    const thead = DOM.statesTable.querySelector('thead');
    if (thead) {
      thead.innerHTML = `
        <tr>
          <th scope="col">${t.thState}</th>
          <th scope="col" class="text-right">${t.thPlants}</th>
          <th scope="col" class="text-right">${t.thPopulation}</th>
          <th scope="col" class="text-right">${t.thSars}</th>
          <th scope="col" class="text-center">${t.thTrend}</th>
        </tr>
      `;
    }
    const tbody = DOM.statesTable.querySelector('tbody');
    if (!tbody) return;
    const states = AppState.data.statesSummary.states;
    const sortedStates = Object.entries(states).sort((a, b) => b[1].population - a[1].population);
    tbody.innerHTML = sortedStates.map(([code, s]) => {
      const popFmt = formatNumber(s.population, 0, AppState.lang);
      const sarsFmt = s.latest_sars ? formatNumber(s.latest_sars, 0, AppState.lang) : '—';
      const badge = trendBadge(s.trend_7d);
      return `
        <tr data-state="${code}">
          <td><strong><a href="#state-${code}" class="state-link" data-bl="${code}">${s.name} (${code})</a></strong></td>
          <td class="text-right">${s.sites_count}</td>
          <td class="text-right">${popFmt}</td>
          <td class="text-right font-mono">${sarsFmt}</td>
          <td class="text-center">${badge}</td>
        </tr>
      `;
    }).join('');
  }

  // Filter series data by active temporal sub-slice [startDate, endDate]
  function filterByTime(series) {
    if (!series || series.length === 0) return series;
    const start = AppState.startDate || '0000-00-00';
    const end = AppState.endDate || '9999-99-99';
    return series.filter(pt => pt[0] >= start && pt[0] <= end);
  }

  // High-performance dynamic SVG chart rendering
  function renderChart() {
    if (!DOM.chartContainer || !AppState.data.national) return;
    const t = I18N[AppState.lang || 'de'];

    const width = DOM.chartContainer.clientWidth || 960;
    const isMobile = width < 500;
    const height = isMobile ? 340 : Math.min(Math.max(width * 0.46, 320), 480);
    const margin = {
      top: 40,
      right: isMobile ? 15 : 30,
      bottom: 50,
      left: isMobile ? (AppState.scale === 'log' ? 50 : 58) : 75
    };
    const plotW = Math.max(width - margin.left - margin.right, 100);
    const plotH = Math.max(height - margin.top - margin.bottom, 100);

    // Determine what series to plot
    let datasetsToPlot = [];
    const isMultiCompare = AppState.pathogen === 'COMPARE_ALL';

    if (AppState.site !== 'ALL') {
      const siteData = AppState.data.siteCache[AppState.site];
      if (siteData && siteData.series) {
        if (isMultiCompare) {
          ['SARS-CoV-2', 'Influenza A+B', 'RSV A+B'].forEach(p => {
            if (siteData.series[p]) {
              datasetsToPlot.push({
                pathogen: p,
                series: filterByTime(siteData.series[p]),
                isSite: true
              });
            }
          });
        } else if (siteData.series[AppState.pathogen]) {
          datasetsToPlot.push({
            pathogen: AppState.pathogen,
            series: filterByTime(siteData.series[AppState.pathogen]),
            isSite: true
          });
        }
      }
    } else if (AppState.state !== 'ALL') {
      const stData = AppState.data.stateCache[AppState.state];
      if (stData && stData.series) {
        if (isMultiCompare) {
          ['SARS-CoV-2', 'Influenza A+B', 'RSV A+B'].forEach(p => {
            if (stData.series[p]) {
              datasetsToPlot.push({
                pathogen: p,
                series: filterByTime(stData.series[p]),
                isState: true
              });
            }
          });
        } else if (stData.series[AppState.pathogen]) {
          datasetsToPlot.push({
            pathogen: AppState.pathogen,
            series: filterByTime(stData.series[AppState.pathogen]),
            isState: true
          });
        }
      }
    } else {
      // National
      if (isMultiCompare) {
        ['SARS-CoV-2', 'Influenza A+B', 'RSV A+B'].forEach(p => {
          if (AppState.data.national.series[p]) {
            datasetsToPlot.push({
              pathogen: p,
              series: filterByTime(AppState.data.national.series[p]),
              isNational: true
            });
          }
        });
      } else {
        const natSeries = AppState.data.national.series[AppState.pathogen] || [];
        datasetsToPlot.push({
          pathogen: AppState.pathogen,
          series: filterByTime(natSeries),
          isNational: true
        });
      }
    }

    if (datasetsToPlot.length === 0 || datasetsToPlot[0].series.length === 0) {
      DOM.chartContainer.innerHTML = `<div style="padding: 4rem; text-align: center; color: var(--text-muted);">${t.noData}</div>`;
      return;
    }

    // Determine Global Date Bounds from primary dataset
    const primarySeries = datasetsToPlot[0].series;
    const minDateStr = primarySeries[0][0];
    const maxDateStr = primarySeries[primarySeries.length - 1][0];
    const dStart = new Date(minDateStr);
    const dEnd = new Date(maxDateStr);
    const dateSpanMs = Math.max(dEnd - dStart, 86400000);

    function getX(dateStr) {
      const d = new Date(dateStr);
      const frac = (d - dStart) / dateSpanMs;
      return margin.left + frac * plotW;
    }

    // Determine Y Bounds
    let maxYVal = 0;
    datasetsToPlot.forEach(ds => {
      ds.series.forEach(pt => {
        let u = null;
        if (ds.isNational) {
          u = pt[6] || pt[5] || pt[4];
        } else if (ds.isSite) {
          u = pt[4] || pt[3] || pt[2];
        } else if (ds.isState) {
          u = pt[1] || pt[2];
        }
        if (u && u > maxYVal) maxYVal = u;
      });
    });

    if (maxYVal <= 0) maxYVal = 10000;

    let getY;
    let yTicks = [];

    if (AppState.scale === 'log') {
      const logMin = 2.0; // 10^2 = 100
      let logMax = Math.ceil(Math.log10(maxYVal * 1.15));
      if (logMax <= logMin) logMax = logMin + 2;
      const logSpan = logMax - logMin;

      getY = function (val) {
        if (!val || val <= 0) val = 100;
        const clamped = Math.max(val, 100);
        const logV = Math.log10(clamped);
        const frac = (logV - logMin) / logSpan;
        return margin.top + (1.0 - Math.min(Math.max(frac, 0), 1)) * plotH;
      };

      for (let p = Math.ceil(logMin); p <= Math.floor(logMax); p++) {
        const val = Math.pow(10, p);
        const yPos = getY(val);
        const lbl = p >= 6 ? `${val / 1000000}M` : p >= 3 ? `${val / 1000}k` : `${val}`;
        yTicks.push({ val, y: yPos, label: `${lbl} (10^${p})` });
      }
    } else {
      // Linear Scale
      const niceMax = Math.ceil(maxYVal * 1.1 / 10000) * 10000;
      getY = function (val) {
        if (!val || val < 0) val = 0;
        const frac = val / niceMax;
        return margin.top + (1.0 - Math.min(Math.max(frac, 0), 1)) * plotH;
      };

      const step = niceMax / 5;
      for (let i = 0; i <= 5; i++) {
        const val = i * step;
        const yPos = getY(val);
        const lbl = val === 0 ? '0' : val >= 1000000 ? `${(val / 1000000).toFixed(1)}M` : `${Math.round(val / 1000)}k`;
        yTicks.push({ val, y: yPos, label: lbl });
      }
    }

    // X Axis Ticks (Months / Quarters)
    const xTicks = [];
    let curDate = new Date(dStart.getFullYear(), dStart.getMonth(), 1);
    const spanMonths = Math.round(dateSpanMs / (86400000 * 30));
    const monthStep = spanMonths > 36 ? 6 : spanMonths > 18 ? 3 : spanMonths > 6 ? 2 : 1;

    while (curDate <= dEnd) {
      if (curDate >= dStart) {
        const dateStr = curDate.toISOString().slice(0, 10);
        const xPos = getX(dateStr);
        const isJan = curDate.getMonth() === 0;
        const monthLabel = curDate.toLocaleDateString(AppState.lang === 'en' ? 'en-US' : 'de-DE', { month: 'short' });
        const lbl = isJan ? `${curDate.getFullYear()}` : `${monthLabel}`;
        xTicks.push({ x: xPos, label: lbl, isMajor: isJan });
      }
      curDate.setMonth(curDate.getMonth() + monthStep);
    }

    // Render SVG Strings
    const svgParts = [];
    svgParts.push(`<svg viewBox="0 0 ${width} ${height}" class="amelag-chart-svg" role="img" aria-label="${t.chartTitlePrefix}">`);
    svgParts.push(`  <defs>`);
    svgParts.push(`    <clipPath id="chartPlotClip"><rect x="${margin.left}" y="${margin.top}" width="${plotW}" height="${plotH}" /></clipPath>`);
    svgParts.push(`  </defs>`);

    // Backgrounds
    svgParts.push(`  <rect x="0" y="0" width="${width}" height="${height}" fill="var(--card-bg)" rx="8" />`);
    svgParts.push(`  <rect x="${margin.left}" y="${margin.top}" width="${plotW}" height="${plotH}" fill="var(--plot-bg)" stroke="var(--border-color)" stroke-width="1" />`);

    // Gridlines Y
    svgParts.push(`  <g class="chart-grid-y">`);
    yTicks.forEach(tick => {
      svgParts.push(`    <line x1="${margin.left}" y1="${tick.y.toFixed(1)}" x2="${margin.left + plotW}" y2="${tick.y.toFixed(1)}" stroke="var(--grid-color)" stroke-width="1" stroke-dasharray="3,3" />`);
      svgParts.push(`    <text x="${margin.left - 8}" y="${(tick.y + 4).toFixed(1)}" text-anchor="end" font-size="11" fill="var(--text-muted)" font-family="system-ui, sans-serif">${tick.label}</text>`);
    });
    svgParts.push(`  </g>`);

    // Gridlines X
    svgParts.push(`  <g class="chart-grid-x">`);
    xTicks.forEach(tick => {
      const strokeColor = tick.isMajor ? 'var(--grid-major)' : 'var(--grid-color)';
      const fontWeight = tick.isMajor ? 'bold' : 'normal';
      svgParts.push(`    <line x1="${tick.x.toFixed(1)}" y1="${margin.top}" x2="${tick.x.toFixed(1)}" y2="${margin.top + plotH}" stroke="${strokeColor}" stroke-width="1" />`);
      svgParts.push(`    <text x="${tick.x.toFixed(1)}" y="${margin.top + plotH + 18}" text-anchor="middle" font-size="11" font-weight="${fontWeight}" fill="var(--text-muted)" font-family="system-ui, sans-serif">${tick.label}</text>`);
    });
    svgParts.push(`  </g>`);

    // Series Data Lines & CI Ribbons
    svgParts.push(`  <g clip-path="url(#chartPlotClip)">`);

    datasetsToPlot.forEach(ds => {
      const pConf = PATHOGEN_CONFIG[ds.pathogen] || { color: '#4f46e5', bg: 'rgba(79, 70, 229, 0.2)' };
      const pts = ds.series;

      // Extract coordinates
      const predCoords = [];
      const normCoords = [];
      const topCiCoords = [];
      const botCiCoords = [];

      pts.forEach(pt => {
        const xc = getX(pt[0]);
        let predVal = null;
        let normVal = null;
        let upperVal = null;
        let lowerVal = null;

        if (ds.isNational) {
          normVal = pt[4];
          predVal = pt[5];
          upperVal = pt[6];
          lowerVal = pt[7];
        } else if (ds.isSite) {
          normVal = pt[2];
          predVal = pt[3];
          upperVal = pt[4];
          lowerVal = pt[5];
        } else if (ds.isState) {
          predVal = pt[1];
          normVal = pt[2];
        }

        if (predVal !== null && predVal !== undefined) {
          predCoords.push(`${xc.toFixed(1)},${getY(predVal).toFixed(1)}`);
        }
        if (normVal !== null && normVal !== undefined) {
          normCoords.push(`${xc.toFixed(1)},${getY(normVal).toFixed(1)}`);
        }
        if (upperVal !== null && lowerVal !== null) {
          topCiCoords.push(`${xc.toFixed(1)},${getY(upperVal).toFixed(1)}`);
          botCiCoords.unshift(`${xc.toFixed(1)},${getY(lowerVal).toFixed(1)}`);
        }
      });

      // Draw CI ribbon if not in multi-compare mode
      if (!isMultiCompare && topCiCoords.length > 0 && botCiCoords.length > 0) {
        const ciD = `M ${topCiCoords[0]} ` + topCiCoords.slice(1).map(c => `L ${c}`).join(' ') + ' ' + botCiCoords.map(c => `L ${c}`).join(' ') + ' Z';
        svgParts.push(`    <path d="${ciD}" fill="${pConf.bg}" class="chart-ci-area" />`);
      }

      // Draw Norm Line (dots / subtle line)
      if (normCoords.length > 1 && (AppState.metric === 'norm' || !isMultiCompare)) {
        const normD = `M ${normCoords[0]} ` + normCoords.slice(1).map(c => `L ${c}`).join(' ');
        svgParts.push(`    <path d="${normD}" fill="none" stroke="${pConf.lightColor || '#93c5fd'}" stroke-width="1.2" stroke-dasharray="2,2" opacity="0.65" />`);
      }

      // Draw Main Trend Line (GAM Prediction)
      if (predCoords.length > 1) {
        const predD = `M ${predCoords[0]} ` + predCoords.slice(1).map(c => `L ${c}`).join(' ');
        const strokeW = isMultiCompare ? 2.5 : 3.0;
        svgParts.push(`    <path d="${predD}" fill="none" stroke="${pConf.color}" stroke-width="${strokeW}" class="chart-svg-line" />`);
      }
    });

    // Crosshair and Hover elements placeholder
    svgParts.push(`    <line id="interactive-crosshair" class="chart-crosshair" x1="-10" y1="${margin.top}" x2="-10" y2="${margin.top + plotH}" stroke="var(--text-muted)" stroke-width="1" />`);
    svgParts.push(`    <circle id="interactive-dot" class="chart-hover-dot" cx="-10" cy="-10" r="5" fill="#ffffff" stroke="var(--primary)" />`);
    svgParts.push(`  </g>`);

    // Y Axis Title
    const scaleText = AppState.scale === 'log' ? 'Log₁₀' : t.unitY;
    svgParts.push(`  <text transform="rotate(-90)" x="${-margin.top - plotH / 2}" y="20" text-anchor="middle" font-size="11" font-weight="600" fill="var(--text-muted)" font-family="system-ui, sans-serif">${t.viralLoadY} (${scaleText})</text>`);

    // Legend on top
    svgParts.push(`  <g transform="translate(${margin.left}, 22)" font-size="11" font-family="system-ui, sans-serif">`);
    if (isMultiCompare) {
      let legOffset = 0;
      ['SARS-CoV-2', 'Influenza A+B', 'RSV A+B'].forEach(p => {
        const pConf = PATHOGEN_CONFIG[p] || { color: '#4f46e5' };
        const label = t.pathogenNames[p] || p;
        svgParts.push(`    <line x1="${legOffset}" y1="0" x2="${legOffset + 14}" y2="0" stroke="${pConf.color}" stroke-width="3" />`);
        svgParts.push(`    <text x="${legOffset + 18}" y="3" fill="var(--text-color)" font-weight="600">${label}</text>`);
        legOffset += isMobile ? 85 : 140;
      });
    } else {
      const pConf = PATHOGEN_CONFIG[AppState.pathogen] || { color: '#4f46e5' };
      const label = t.pathogenNames[AppState.pathogen] || AppState.pathogen;
      svgParts.push(`    <line x1="0" y1="0" x2="16" y2="0" stroke="${pConf.color}" stroke-width="3" />`);
      svgParts.push(`    <text x="22" y="3" fill="var(--text-color)" font-weight="600">${label}</text>`);
      svgParts.push(`    <rect x="${isMobile ? 120 : 170}" y="-5" width="12" height="10" fill="${pConf.bg}" />`);
      svgParts.push(`    <text x="${isMobile ? 138 : 188}" y="3" fill="var(--text-muted)">${t.ciBand}</text>`);
    }
    svgParts.push(`  </g>`);

    svgParts.push(`</svg>`);

    DOM.chartContainer.innerHTML = svgParts.join('
');
    attachChartInteractivity(datasetsToPlot, getX, getY, margin, plotW, plotH);
  }

  // Mouse & Touch Interactivity (Crosshair, Tooltips)
  function attachChartInteractivity(datasets, getX, getY, margin, plotW, plotH) {
    const svgEl = DOM.chartContainer.querySelector('svg');
    const crosshair = DOM.chartContainer.querySelector('#interactive-crosshair');
    const dot = DOM.chartContainer.querySelector('#interactive-dot');
    if (!svgEl || !crosshair || !dot) return;

    const primaryDS = datasets[0];
    const points = primaryDS.series;
    const t = I18N[AppState.lang || 'de'];

    function handlePointer(e) {
      const rect = svgEl.getBoundingClientRect();
      const clientX = e.touches ? e.touches[0].clientX : e.clientX;
      const clientY = e.touches ? e.touches[0].clientY : e.clientY;
      const mouseX = clientX - rect.left;
      const mouseY = clientY - rect.top;

      const scaleX = (svgEl.viewBox.baseVal.width || rect.width) / rect.width;
      const svgX = mouseX * scaleX;

      if (svgX < margin.left || svgX > margin.left + plotW) {
        hideTooltip();
        return;
      }

      let closestPt = null;
      let minDistance = Infinity;

      points.forEach(pt => {
        const ptX = getX(pt[0]);
        const dist = Math.abs(ptX - svgX);
        if (dist < minDistance) {
          minDistance = dist;
          closestPt = pt;
        }
      });

      if (!closestPt) return;

      const ptX = getX(closestPt[0]);
      let primaryVal = primaryDS.isNational ? closestPt[5] : primaryDS.isSite ? closestPt[3] : closestPt[1];
      if (primaryVal === null || primaryVal === undefined) {
        primaryVal = primaryDS.isNational ? closestPt[4] : closestPt[2];
      }
      const ptY = getY(primaryVal);

      crosshair.setAttribute('x1', ptX.toFixed(1));
      crosshair.setAttribute('x2', ptX.toFixed(1));
      dot.setAttribute('cx', ptX.toFixed(1));
      dot.setAttribute('cy', ptY.toFixed(1));

      // Build Tooltip Content
      const dateStr = closestPt[0];
      let tooltipContent = `<div class="tooltip-title">${formatDate(dateStr, AppState.lang)}</div>`;

      datasets.forEach(ds => {
        const conf = PATHOGEN_CONFIG[ds.pathogen] || { color: '#4f46e5', name: ds.pathogen };
        const matchingPt = ds.series.find(p => p[0] === dateStr);
        if (matchingPt) {
          let pVal = ds.isNational ? matchingPt[5] : ds.isSite ? matchingPt[3] : matchingPt[1];
          let nVal = ds.isNational ? matchingPt[4] : ds.isSite ? matchingPt[2] : matchingPt[2];
          let upper = ds.isNational ? matchingPt[6] : ds.isSite ? matchingPt[4] : null;
          let lower = ds.isNational ? matchingPt[7] : ds.isSite ? matchingPt[5] : null;

          const pLabel = t.pathogenNames[ds.pathogen] || conf.name;
          tooltipContent += `
            <div class="tooltip-row">
              <span><span class="tooltip-swatch" style="background:${conf.color};"></span> <strong>${pLabel}</strong>:</span>
              <span class="font-mono font-bold">${formatNumber(pVal || nVal, 0, AppState.lang)} ${t.tooltipCopies}</span>
            </div>`;
          if (upper !== null && lower !== null) {
            tooltipContent += `
              <div class="tooltip-row text-muted" style="font-size:0.75rem;">
                <span>${t.tooltipCi}</span>
                <span>[${formatNumber(lower, 0, AppState.lang)} – ${formatNumber(upper, 0, AppState.lang)}]</span>
              </div>`;
          }
        }
      });

      if (primaryDS.isNational) {
        tooltipContent += `
          <div class="tooltip-row text-muted" style="font-size:0.75rem; border-top:1px solid var(--border-light); margin-top:0.3rem; padding-top:0.3rem;">
            <span>${t.tooltipActivePlants}</span>
            <span>${closestPt[1]} (${formatNumber((closestPt[2] || 0) * 100, 1, AppState.lang)}% ${t.tooltipPop})</span>
          </div>`;
      }

      DOM.chartTooltip.innerHTML = tooltipContent;
      DOM.chartTooltip.classList.add('visible');
      DOM.chartTooltip.style.left = `${(ptX / (svgEl.viewBox.baseVal.width || rect.width)) * rect.width}px`;
      DOM.chartTooltip.style.top = `${(ptY / (svgEl.viewBox.baseVal.height || rect.height)) * rect.height}px`;
    }

    function hideTooltip() {
      DOM.chartTooltip.classList.remove('visible');
      crosshair.setAttribute('x1', '-10');
      crosshair.setAttribute('x2', '-10');
      dot.setAttribute('cx', '-10');
      dot.setAttribute('cy', '-10');
    }

    svgEl.addEventListener('mousemove', handlePointer);
    svgEl.addEventListener('mouseleave', hideTooltip);
    svgEl.addEventListener('touchstart', handlePointer, { passive: true });
    svgEl.addEventListener('touchmove', handlePointer, { passive: true });
    svgEl.addEventListener('touchend', hideTooltip);
  }

  // Export Data as CSV
  function exportCSV() {
    if (!AppState.data.national) return;
    const t = I18N[AppState.lang || 'de'];
    let rows = [];
    const p = AppState.pathogen;

    if (AppState.site !== 'ALL') {
      const sData = AppState.data.siteCache[AppState.site];
      if (sData && sData.series[p]) {
        rows.push(['standort', 'datum', 'viruslast_roh', 'viruslast_normalisiert', 'vorhersage_gam', 'obere_schranke', 'untere_schranke', 'unter_bestimmungsgrenze']);
        sData.series[p].forEach(pt => {
          rows.push([sData.info.name, pt[0], pt[1] ?? '', pt[2] ?? '', pt[3] ?? '', pt[4] ?? '', pt[5] ?? '', pt[6] ?? '']);
        });
      }
    } else if (AppState.state !== 'ALL') {
      const stData = AppState.data.stateCache[AppState.state];
      if (stData && stData.series[p]) {
        rows.push(['bundesland', 'datum', 'vorhersage_gewichtet', 'normalisiert_gewichtet', 'klaeranlagen_aktiv', 'bevoelkerung_erfasst']);
        stData.series[p].forEach(pt => {
          rows.push([AppState.state, pt[0], pt[1] ?? '', pt[2] ?? '', pt[3] ?? '', pt[4] ?? '']);
        });
      }
    } else {
      const nat = AppState.data.national.series[p] || [];
      rows.push(['datum', 'anzahl_klaeranlagen', 'anteil_bevoelkerung', 'viruslast_roh', 'viruslast_normalisiert', 'vorhersage_gam', 'obere_schranke', 'untere_schranke']);
      nat.forEach(pt => {
        rows.push([pt[0], pt[1] ?? '', pt[2] ?? '', pt[3] ?? '', pt[4] ?? '', pt[5] ?? '', pt[6] ?? '', pt[7] ?? '']);
      });
    }

    if (rows.length <= 1) {
      alert(t.exportNoData);
      return;
    }

    const csvContent = 'data:text/csv;charset=utf-8,' + rows.map(e => e.join(';')).join('
');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `amelag_${p.toLowerCase()}_${AppState.state.toLowerCase()}_${AppState.site.toLowerCase()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  // Export Chart as SVG
  function exportSVG() {
    const svgEl = DOM.chartContainer.querySelector('svg');
    if (!svgEl) return;
    const serializer = new XMLSerializer();
    const svgString = serializer.serializeToString(svgEl);
    const blob = new Blob([svgString], { type: 'image/svg+xml;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `amelag_chart_${AppState.pathogen.toLowerCase()}_${AppState.scale}.svg`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }

  // Event Listeners Initialization
  function initEventListeners() {
    // Language Switcher Controls
    document.querySelectorAll('.lang-btn').forEach(btn => {
      btn.addEventListener('click', e => {
        e.preventDefault();
        const targetLang = btn.dataset.lang;
        if (targetLang && targetLang !== AppState.lang) {
          setLanguage(targetLang);
          syncStateToURL();
        }
      });
    });

    // Pathogen Select
    DOM.filterPathogen?.addEventListener('change', e => {
      AppState.pathogen = e.target.value;
      updateActiveDataAndRender();
    });

    // Scale Buttons
    DOM.btnScaleLinear?.addEventListener('click', () => {
      AppState.scale = 'linear';
      DOM.btnScaleLinear.classList.add('active');
      DOM.btnScaleLog.classList.remove('active');
      renderChart();
      syncStateToURL();
    });

    DOM.btnScaleLog?.addEventListener('click', () => {
      AppState.scale = 'log';
      DOM.btnScaleLog.classList.add('active');
      DOM.btnScaleLinear.classList.remove('active');
      renderChart();
      syncStateToURL();
    });

    // Time Preset Dropdown
    DOM.filterTimePreset?.addEventListener('change', e => {
      applyTimePreset(e.target.value, true);
    });

    // Dual Range Slider Inputs
    DOM.sliderStart?.addEventListener('input', e => {
      let val = Number(e.target.value);
      const endVal = Number(DOM.sliderEnd?.value || AppState.totalDays);
      if (val >= endVal) {
        val = Math.max(0, endVal - 1);
        e.target.value = val;
      }
      AppState.startDate = daysToDateStr(val);
      AppState.timePreset = 'custom';
      updateSlicerUI();
      renderChart();
      syncStateToURL();
    });

    DOM.sliderEnd?.addEventListener('input', e => {
      let val = Number(e.target.value);
      const startVal = Number(DOM.sliderStart?.value || 0);
      if (val <= startVal) {
        val = Math.min(AppState.totalDays, startVal + 1);
        e.target.value = val;
      }
      AppState.endDate = daysToDateStr(val);
      AppState.timePreset = 'custom';
      updateSlicerUI();
      renderChart();
      syncStateToURL();
    });

    DOM.filterState?.addEventListener('change', e => {
      AppState.state = e.target.value;
      AppState.site = 'ALL';
      populateSiteDropdown();
      updateActiveDataAndRender();
    });

    DOM.filterSite?.addEventListener('change', e => {
      AppState.site = e.target.value;
      if (AppState.site !== 'ALL' && AppState.data.sitesIndex) {
        const found = AppState.data.sitesIndex.find(s => s.id === AppState.site);
        if (found) {
          AppState.state = found.bl;
          DOM.filterState.value = found.bl;
        }
      }
      updateActiveDataAndRender();
    });

    DOM.filterMetric?.addEventListener('change', e => {
      AppState.metric = e.target.value;
      renderChart();
      syncStateToURL();
    });

    DOM.btnResetFilters?.addEventListener('click', () => {
      AppState.pathogen = 'SARS-CoV-2';
      AppState.scale = 'linear';
      AppState.state = 'ALL';
      AppState.site = 'ALL';
      AppState.metric = 'pred';
      populateSiteDropdown();
      applyStateToInputs();
      applyTimePreset('1y', false);
      updateActiveDataAndRender();
    });

    DOM.btnExportCsv?.addEventListener('click', exportCSV);
    DOM.btnExportSvg?.addEventListener('click', exportSVG);

    // State table row clickability
    DOM.statesTable?.addEventListener('click', e => {
      const link = e.target.closest('.state-link');
      if (link && link.dataset.bl) {
        e.preventDefault();
        AppState.state = link.dataset.bl;
        AppState.site = 'ALL';
        populateSiteDropdown();
        applyStateToInputs();
        updateActiveDataAndRender();
        document.getElementById('main-content')?.scrollIntoView({ behavior: 'smooth' });
      }
    });

    // Window Resize Observer for responsive chart redraw
    let resizeTimer = null;
    window.addEventListener('resize', () => {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(() => {
        renderChart();
      }, 150);
    });
  }

  // App Initialization
  function init() {
    initTheme();
    
    // Detect preferred or current language
    const docLang = document.documentElement.lang === 'en' ? 'en' : 'de';
    let preferredLang = docLang;
    try {
      const stored = localStorage.getItem('amelag_lang');
      if (stored && (stored === 'de' || stored === 'en')) {
        preferredLang = stored;
      }
    } catch (e) {}

    parseStateFromURL();
    if (AppState.lang && (AppState.lang === 'de' || AppState.lang === 'en')) {
      preferredLang = AppState.lang;
    }
    
    AppState.lang = preferredLang;
    initEventListeners();
    setLanguage(preferredLang);
    loadInitialData();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
