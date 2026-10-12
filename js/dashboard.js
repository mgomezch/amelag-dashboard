/**
 * AMELAG Wastewater Surveillance Dashboard SPA
 * High-performance, zero-dependency interactive data visualization engine.
 * Supports Linear & Logarithmic scaling, multi-pathogen comparison,
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

  // Application State
  const AppState = {
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
  function formatNumber(num, decimals = 0) {
    if (num === null || num === undefined || isNaN(num)) return '—';
    return Number(num).toLocaleString('de-DE', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    });
  }

  function formatDateDE(dateStr) {
    if (!dateStr) return '';
    const parts = dateStr.split('-');
    if (parts.length !== 3) return dateStr;
    const d = new Date(Date.UTC(parts[0], parts[1] - 1, parts[2]));
    return d.toLocaleDateString('de-DE', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' });
  }

  function getWeekNumber(dateStr) {
    const d = new Date(dateStr);
    const date = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()));
    date.setUTCDate(date.getUTCDate() + 4 - (date.getUTCDay() || 7));
    const yearStart = new Date(Date.UTC(date.getUTCFullYear(), 0, 1));
    return Math.ceil((((date - yearStart) / 86400000) + 1) / 7);
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
      renderChart();
    });
  }

  // Slicer Functions
  function dateToDays(dateStr) {
    if (!AppState.globalMinDate || !dateStr) return 0;
    const dMin = new Date(AppState.globalMinDate);
    const d = new Date(dateStr);
    return Math.max(0, Math.round((d.getTime() - dMin.getTime()) / 86400000));
  }

  function daysToDateStr(days) {
    if (!AppState.globalMinDate) return '';
    const dMin = new Date(AppState.globalMinDate);
    const d = new Date(dMin.getTime() + days * 86400000);
    return d.toISOString().substring(0, 10);
  }

  function updateSlicerUI() {
    if (!DOM.sliderStart || !DOM.sliderEnd || AppState.totalDays <= 0) return;
    const startVal = Number(DOM.sliderStart.value);
    const endVal = Number(DOM.sliderEnd.value);

    // Update highlight bar
    if (DOM.sliderHighlight) {
      const leftPct = (startVal / AppState.totalDays) * 100;
      const widthPct = ((endVal - startVal) / AppState.totalDays) * 100;
      DOM.sliderHighlight.style.left = `${leftPct}%`;
      DOM.sliderHighlight.style.width = `${widthPct}%`;
    }

    // Update date badges
    if (DOM.slicerLabelStart) {
      DOM.slicerLabelStart.textContent = formatDateDE(AppState.startDate);
    }
    if (DOM.slicerLabelEnd) {
      DOM.slicerLabelEnd.textContent = formatDateDE(AppState.endDate);
    }
    if (DOM.slicerSpanDays) {
      const diffDays = Math.max(endVal - startVal, 1);
      DOM.slicerSpanDays.textContent = `(${diffDays} Tage)`;
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
      await updateActiveDataAndRender();
    } catch (err) {
      console.error('Error loading initial data:', err);
      // Fallback: the page already has pre-rendered content from server-side build!
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

    // Filter sites by state if state is selected
    const filteredSites = currentState === 'ALL'
      ? AppState.data.sitesIndex
      : AppState.data.sitesIndex.filter(s => s.bl === currentState);

    let html = '<option value="ALL">Alle Standorte (Aggregiert)</option>';
    let currentBl = '';

    filteredSites.forEach(s => {
      if (currentState === 'ALL' && s.bl !== currentBl) {
        if (currentBl !== '') html += '</optgroup>';
        currentBl = s.bl;
        html += `<optgroup label="${STATE_NAMES[currentBl] || currentBl}">`;
      }
      const selected = s.id === currentSite ? ' selected' : '';
      const popStr = s.pop ? ` (${formatNumber(s.pop)} Einw.)` : '';
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
    // If a site is selected, fetch site data
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

    if (AppState.site !== 'ALL') {
      const siteData = AppState.data.siteCache[AppState.site];
      if (siteData && siteData.info) {
        const sarsSeries = siteData.series['SARS-CoV-2'] || [];
        const lastPt = sarsSeries.length > 0 ? sarsSeries[sarsSeries.length - 1] : null;
        if (lastPt) {
          DOM.kpiSarsVal.textContent = formatNumber(lastPt[3] || lastPt[2]);
        }
      }
      return;
    }

    if (AppState.state !== 'ALL') {
      const stInfo = AppState.data.statesSummary?.states?.[AppState.state];
      if (stInfo) {
        DOM.kpiSarsVal.textContent = formatNumber(stInfo.latest_sars);
        DOM.kpiSarsTrend.innerHTML = trendBadge(stInfo.trend_7d) + ' vs. Vorwoche';
      }
      return;
    }

    // Default: National KPIs
    const pStats = AppState.data.national.meta.pathogens;
    if (pStats['SARS-CoV-2']) {
      DOM.kpiSarsVal.textContent = formatNumber(pStats['SARS-CoV-2'].latest_pred);
      DOM.kpiSarsTrend.innerHTML = trendBadge(pStats['SARS-CoV-2'].chg_7d_pct) + ' vs. Vorwoche';
    }
    if (pStats['Influenza A+B']) {
      DOM.kpiFluVal.textContent = formatNumber(pStats['Influenza A+B'].latest_pred);
      DOM.kpiFluTrend.innerHTML = trendBadge(pStats['Influenza A+B'].chg_7d_pct) + ' vs. Vorwoche';
    }
    if (pStats['RSV A+B']) {
      DOM.kpiRsvVal.textContent = formatNumber(pStats['RSV A+B'].latest_pred);
      DOM.kpiRsvTrend.innerHTML = trendBadge(pStats['RSV A+B'].chg_7d_pct) + ' vs. Vorwoche';
    }
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
      DOM.chartContainer.innerHTML = '<div style="padding: 4rem; text-align: center; color: var(--text-muted);">Keine Daten für diese Filterkombination verfügbar.</div>';
      return;
    }

    // Determine Date Range for Chart X-domain
    let minDateStr = AppState.startDate;
    let maxDateStr = AppState.endDate;
    if (!minDateStr || !maxDateStr) {
      datasetsToPlot.forEach(ds => {
        ds.series.forEach(pt => {
          if (!minDateStr || pt[0] < minDateStr) minDateStr = pt[0];
          if (!maxDateStr || pt[0] > maxDateStr) maxDateStr = pt[0];
        });
      });
    }

    const dStart = new Date(minDateStr);
    const dEnd = new Date(maxDateStr);
    const totalMs = Math.max(dEnd.getTime() - dStart.getTime(), 86400000);

    function getX(dateStr) {
      const d = new Date(dateStr);
      const frac = (d.getTime() - dStart.getTime()) / totalMs;
      return margin.left + frac * plotW;
    }

    // Determine Y scale bounds
    let yMax = 0;
    let yMin = AppState.scale === 'log' ? 100 : 0;

    datasetsToPlot.forEach(ds => {
      ds.series.forEach(pt => {
        // Point values:
        // National: [date, n, cov, raw, norm, pred, upper, lower] (indices 3:raw, 4:norm, 5:pred, 6:upper, 7:lower)
        // Site: [date, raw, norm, pred, upper, lower, bg] (indices 1:raw, 2:norm, 3:pred, 4:upper, 5:lower)
        // State: [date, pred, norm, n, pop] (indices 1:pred, 2:norm)
        let valToCheck = 0;
        if (ds.isNational) {
          valToCheck = pt[6] || pt[5] || pt[4] || 0;
        } else if (ds.isSite) {
          valToCheck = pt[4] || pt[3] || pt[2] || 0;
        } else if (ds.isState) {
          valToCheck = pt[1] || pt[2] || 0;
        }
        if (valToCheck > yMax) yMax = valToCheck;
      });
    });

    if (yMax <= 0) yMax = 10000;

    let getY;
    let yTicks = [];

    if (AppState.scale === 'log') {
      const logMin = Math.log10(Math.max(yMin, 10));
      const logMax = Math.ceil(Math.log10(yMax * 1.25));
      const logRange = logMax - logMin;

      getY = function (val) {
        if (val === null || val === undefined || isNaN(val) || val <= 0) {
          return margin.top + plotH;
        }
        const v = Math.max(val, Math.pow(10, logMin));
        const logV = Math.log10(v);
        const frac = (logV - logMin) / logRange;
        return margin.top + (1.0 - Math.min(Math.max(frac, 0), 1)) * plotH;
      };

      for (let p = Math.floor(logMin); p <= logMax; p++) {
        const val = Math.pow(10, p);
        let label = `10^${p}`;
        if (val >= 1000000) label = `${(val / 1000000).toFixed(0)}M`;
        else if (val >= 1000) label = `${(val / 1000).toFixed(0)}k`;
        else label = `${val}`;
        yTicks.push({ val, y: getY(val), label });
      }
    } else {
      // Linear Scale
      const niceStep = Math.pow(10, Math.floor(Math.log10(yMax)));
      let ceiling = Math.ceil((yMax * 1.1) / niceStep) * niceStep;
      if (ceiling <= 0) ceiling = 50000;

      getY = function (val) {
        if (val === null || val === undefined || isNaN(val) || val < 0) {
          return margin.top + plotH;
        }
        const frac = val / ceiling;
        return margin.top + (1.0 - Math.min(Math.max(frac, 0), 1)) * plotH;
      };

      const steps = 5;
      for (let i = 0; i <= steps; i++) {
        const val = (i / steps) * ceiling;
        let label = '0';
        if (val >= 1000000) label = `${(val / 1000000).toFixed(1)}M`;
        else if (val >= 1000) label = `${(val / 1000).toFixed(0)}k`;
        else if (val > 0) label = `${val.toFixed(0)}`;
        yTicks.push({ val, y: getY(val), label });
      }
    }

    // X Ticks (Adaptive dates)
    const xTicks = [];
    const spanDays = totalMs / 86400000;
    let tickIntervalDays = spanDays > 600 ? 180 : spanDays > 250 ? 60 : 30;
    if (isMobile) {
      tickIntervalDays = spanDays > 600 ? 365 : spanDays > 250 ? 120 : 60;
    }

    let currD = new Date(dStart);
    currD.setUTCDate(1); // align to month start
    while (currD <= dEnd) {
      if (currD >= dStart) {
        const dStr = currD.toISOString().substring(0, 10);
        const xc = getX(dStr);
        let label = currD.toLocaleDateString('de-DE', { month: 'short', year: '2-digit', timeZone: 'UTC' });
        if (currD.getUTCMonth() === 0) {
          label = currD.toLocaleDateString('de-DE', { year: 'numeric', timeZone: 'UTC' });
        }
        xTicks.push({ xc, label, isYear: currD.getUTCMonth() === 0 });
      }
      currD = new Date(currD.getTime() + tickIntervalDays * 86400000);
    }

    // Build SVG Elements
    const svgParts = [
      `<svg viewBox="0 0 ${width} ${height}" class="amelag-chart-svg" role="img" preserveAspectRatio="none">`,
      `  <defs>`,
      `    <clipPath id="chartPlotClip">`,
      `      <rect x="${margin.left}" y="${margin.top}" width="${plotW}" height="${plotH}" />`,
      `    </clipPath>`,
      `  </defs>`,
      // Grid & Background
      `  <rect x="${margin.left}" y="${margin.top}" width="${plotW}" height="${plotH}" fill="var(--plot-bg)" stroke="var(--border-color)" stroke-width="1" />`,
      `  <g class="chart-grid">`
    ];

    // Horizontal Y Grid lines
    yTicks.forEach(t => {
      svgParts.push(`    <line x1="${margin.left}" y1="${t.y.toFixed(1)}" x2="${margin.left + plotW}" y2="${t.y.toFixed(1)}" stroke="var(--grid-color)" stroke-width="1" stroke-dasharray="3,3" />`);
      svgParts.push(`    <text x="${margin.left - 10}" y="${(t.y + 4).toFixed(1)}" text-anchor="end" font-size="11" fill="var(--text-muted)" font-family="system-ui, sans-serif">${t.label}</text>`);
    });

    // Vertical X Grid lines
    xTicks.forEach(t => {
      const strokeC = t.isYear ? 'var(--grid-major)' : 'var(--grid-color)';
      svgParts.push(`    <line x1="${t.xc.toFixed(1)}" y1="${margin.top}" x2="${t.xc.toFixed(1)}" y2="${margin.top + plotH}" stroke="${strokeC}" stroke-width="1" stroke-dasharray="2,2" />`);
      svgParts.push(`    <text x="${t.xc.toFixed(1)}" y="${margin.top + plotH + 18}" text-anchor="middle" font-size="11" font-weight="${t.isYear ? '700' : '400'}" fill="var(--text-muted)" font-family="system-ui, sans-serif">${t.label}</text>`);
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
    const scaleText = AppState.scale === 'log' ? 'Log₁₀' : 'Genkopien / L';
    svgParts.push(`  <text transform="rotate(-90)" x="${-margin.top - plotH / 2}" y="20" text-anchor="middle" font-size="11" font-weight="600" fill="var(--text-muted)" font-family="system-ui, sans-serif">Viruslast (${scaleText})</text>`);

    // Legend on top
    svgParts.push(`  <g transform="translate(${margin.left}, 22)" font-size="11" font-family="system-ui, sans-serif">`);
    if (isMultiCompare) {
      let legOffset = 0;
      ['SARS-CoV-2', 'Influenza A+B', 'RSV A+B'].forEach(p => {
        const conf = PATHOGEN_CONFIG[p];
        svgParts.push(`    <line x1="${legOffset}" y1="0" x2="${legOffset + 14}" y2="0" stroke="${conf.color}" stroke-width="3" />`);
        svgParts.push(`    <text x="${legOffset + 20}" y="4" fill="var(--text-color)" font-weight="600">${conf.name}</text>`);
        legOffset += (p === 'SARS-CoV-2' ? 160 : 190);
      });
    } else {
      const conf = PATHOGEN_CONFIG[AppState.pathogen] || { color: '#4f46e5', name: AppState.pathogen };
      svgParts.push(`    <line x1="0" y1="0" x2="16" y2="0" stroke="${conf.color}" stroke-width="3" />`);
      svgParts.push(`    <text x="22" y="4" fill="var(--text-color)" font-weight="700">${conf.name}</text>`);
      svgParts.push(`    <rect x="180" y="-6" width="14" height="12" fill="${conf.bg || 'rgba(79,70,229,0.2)'}" />`);
      svgParts.push(`    <text x="200" y="4" fill="var(--text-muted)">95% Konfidenzintervall</text>`);
    }
    svgParts.push(`  </g>`);

    svgParts.push(`</svg>`);

    DOM.chartContainer.innerHTML = svgParts.join('\n');
    setupChartInteractions(datasetsToPlot, getX, getY, margin, plotW, plotH, dStart, totalMs);
  }

  // Pointer & Touch Interactivity (Tooltip & Crosshair)
  function setupChartInteractions(datasets, getX, getY, margin, plotW, plotH, dStart, totalMs) {
    const svgEl = DOM.chartContainer.querySelector('svg');
    const crosshair = DOM.chartContainer.querySelector('#interactive-crosshair');
    const dot = DOM.chartContainer.querySelector('#interactive-dot');
    if (!svgEl || !crosshair || !dot || !DOM.chartTooltip) return;

    // Flatten primary points for fast nearest-neighbor binary search
    const primaryDS = datasets[0];
    const points = primaryDS.series;
    if (!points || points.length === 0) return;

    function handlePointer(evt) {
      const rect = svgEl.getBoundingClientRect();
      const clientX = evt.touches ? evt.touches[0].clientX : evt.clientX;
      const clientY = evt.touches ? evt.touches[0].clientY : evt.clientY;

      const relX = clientX - rect.left;
      const relY = clientY - rect.top;

      // Scale to SVG coordinates
      const svgX = (relX / rect.width) * (svgEl.viewBox.baseVal.width || rect.width);
      if (svgX < margin.left || svgX > margin.left + plotW) {
        hideTooltip();
        return;
      }

      // Find nearest data point by date
      const dateFrac = (svgX - margin.left) / plotW;
      const targetMs = dStart.getTime() + dateFrac * totalMs;

      let closestPt = points[0];
      let minDiff = Infinity;
      points.forEach(pt => {
        const ptMs = new Date(pt[0]).getTime();
        const diff = Math.abs(ptMs - targetMs);
        if (diff < minDiff) {
          minDiff = diff;
          closestPt = pt;
        }
      });

      if (!closestPt) return;

      const dateStr = closestPt[0];
      const ptX = getX(dateStr);
      let predVal = primaryDS.isNational ? closestPt[5] : primaryDS.isSite ? closestPt[3] : closestPt[1];
      if (predVal === null) predVal = primaryDS.isNational ? closestPt[4] : closestPt[2];
      const ptY = getY(predVal || 0);

      // Move crosshair and dot
      crosshair.setAttribute('x1', ptX.toFixed(1));
      crosshair.setAttribute('x2', ptX.toFixed(1));
      dot.setAttribute('cx', ptX.toFixed(1));
      dot.setAttribute('cy', ptY.toFixed(1));

      // Build Tooltip HTML
      const weekNo = getWeekNumber(dateStr);
      let tooltipContent = `<div class="tooltip-date">${formatDateDE(dateStr)} (KW ${weekNo})</div>`;

      datasets.forEach(ds => {
        const conf = PATHOGEN_CONFIG[ds.pathogen] || { color: '#4f46e5', name: ds.pathogen };
        const matchingPt = ds.series.find(p => p[0] === dateStr);
        if (matchingPt) {
          let pVal = ds.isNational ? matchingPt[5] : ds.isSite ? matchingPt[3] : matchingPt[1];
          let nVal = ds.isNational ? matchingPt[4] : ds.isSite ? matchingPt[2] : matchingPt[2];
          let upper = ds.isNational ? matchingPt[6] : ds.isSite ? matchingPt[4] : null;
          let lower = ds.isNational ? matchingPt[7] : ds.isSite ? matchingPt[5] : null;

          tooltipContent += `
            <div class="tooltip-row">
              <span><span class="tooltip-swatch" style="background:${conf.color};"></span> <strong>${conf.name}</strong>:</span>
              <span class="font-mono font-bold">${formatNumber(pVal || nVal)} Kopien/L</span>
            </div>`;
          if (upper !== null && lower !== null) {
            tooltipContent += `
              <div class="tooltip-row text-muted" style="font-size:0.75rem;">
                <span>95% KI:</span>
                <span>[${formatNumber(lower)} – ${formatNumber(upper)}]</span>
              </div>`;
          }
        }
      });

      if (primaryDS.isNational) {
        tooltipContent += `
          <div class="tooltip-row text-muted" style="font-size:0.75rem; border-top:1px solid var(--border-light); margin-top:0.3rem; padding-top:0.3rem;">
            <span>Kläranlagen aktiv:</span>
            <span>${closestPt[1]} (${formatNumber((closestPt[2] || 0) * 100, 1)}% Bev.)</span>
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
      alert('Keine Daten für den Export verfügbar.');
      return;
    }

    const csvContent = 'data:text/csv;charset=utf-8,' + rows.map(e => e.join(';')).join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `amelag_${AppState.pathogen}_${AppState.state}_${AppState.site}_${AppState.scale}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  // Export Chart as standalone SVG file
  function exportSVG() {
    const svgEl = DOM.chartContainer.querySelector('svg');
    if (!svgEl) return;
    const serializer = new XMLSerializer();
    let source = serializer.serializeToString(svgEl);

    if (!source.match(/^<svg[^>]+xmlns="http\:\/\/www\.w3\.org\/2000\/svg"/)) {
      source = source.replace(/^<svg/, '<svg xmlns="http://www.w3.org/2000/svg"');
    }

    const url = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(source);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `amelag_chart_${AppState.pathogen}_${AppState.scale}.svg`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  // Event Listeners Setup
  function initEventListeners() {
    DOM.filterPathogen?.addEventListener('change', e => {
      AppState.pathogen = e.target.value;
      updateActiveDataAndRender();
    });

    DOM.btnScaleLinear?.addEventListener('click', () => {
      AppState.scale = 'linear';
      applyStateToInputs();
      renderChart();
      syncStateToURL();
    });

    DOM.btnScaleLog?.addEventListener('click', () => {
      AppState.scale = 'log';
      applyStateToInputs();
      renderChart();
      syncStateToURL();
    });

    DOM.filterTimePreset?.addEventListener('change', e => {
      applyTimePreset(e.target.value, true);
    });

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
      AppState.site = 'ALL'; // reset site selection when state changes
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
    parseStateFromURL();
    initEventListeners();
    loadInitialData();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
