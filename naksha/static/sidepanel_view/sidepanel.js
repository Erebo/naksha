/**
 * NAKSHA (নকশা) — Side Panel Application Logic
 * Integrates Leaflet 2D GIS with FastAPI backend (http://127.0.0.1:8000).
 * Linear / Stripe Minimalist Cockpit Architecture.
 * Height-Budget Conscious: Slim Header, Auto-Collapsing Hero, Resizable Map, Inline Legend.
 */

const API_BASE = 'http://127.0.0.1:8000';
const DEFAULT_PARCEL_ID = 'par-8f92-bd04-syn';

const state = {
  activeParcelId: DEFAULT_PARCEL_ID,
  map: null,
  layers: {},
  layerVisibility: {
    ancestral_footprint: true,
    deed_claim: true,
    ground_truth: true,
    restricted_khas: true,
    conflict_zone: true,
  },
  neighborsGeoJSON: null,
  targetBounds: null,
  conflictBounds: null,
  currentRequestSeq: 0,
  currentVerification: null,
  currentLayers: null,
  currentNeighbors: null,
  context: {
    portal: 'ld_tax',
    dag: '402',
    khatian: '120',
    mouza: 'কাশিমপুর',
    area: '৬.০০',
  },
};

const LAYER_CONFIG = {
  ancestral_footprint: {
    color: '#A78BFA',
    weight: 1.5,
    dashArray: '8, 4',
    fillColor: '#A78BFA',
    fillOpacity: 0.10,
    name: '১. সিএস পৈত্রিক সীমানা (CS 88)',
    shortName: 'সিএস ৮৮',
  },
  deed_claim: {
    color: '#FB923C',
    weight: 2,
    dashArray: null,
    fillColor: '#FB923C',
    fillOpacity: 0.15,
    name: '২. দলিলে দাবিকৃত জমি (Deed Claim)',
    shortName: 'দলিল দাবি',
  },
  ground_truth: {
    color: '#3B82F6',
    weight: 3,
    dashArray: null,
    fillColor: '#3B82F6',
    fillOpacity: 0.30,
    name: '৩. ডিএলআরএস জরিপকৃত জমি (DLRS Survey)',
    shortName: 'ডিএলআরএস',
  },
  restricted_khas: {
    color: '#22D3EE',
    weight: 0,
    dashArray: null,
    fillColor: '#22D3EE',
    fillOpacity: 0.25,
    stroke: false,
    name: 'সরকারি খাস নিষ্কাশন খাল (Public Khas Canal)',
    shortName: 'খাস খাল',
  },
  conflict_zone: {
    color: '#F43F5E',
    weight: 2.5,
    dashArray: null,
    fillColor: '#F43F5E',
    fillOpacity: 0.65,
    name: '৪. বিরোধপূর্ণ এলাকা (Khas Canal Conflict)',
    shortName: 'বিরোধপূর্ণ',
  },
};

document.addEventListener('DOMContentLoaded', () => {
  injectSvgIcons();
  initTabs();
  initLanguageToggle();
  initThemeToggle();
  initSessionTimer();
  initMapResizer();
  initMapControlButtons();
  initTabScrollCollapse();
  initLayersPopover();

  const mapOk = initMap();
  initSidePanelListeners();
  if (mapOk) {
    loadContextAndPlotData();
  }
});

// 1. Inject SVG Icons
function injectSvgIcons() {
  const mapIcon = (id, svg) => {
    const el = document.getElementById(id);
    if (el) el.innerHTML = svg;
  };

  mapIcon('sp-icon-layers', ICONS.layers);
  mapIcon('sp-icon-recenter', ICONS.crosshair);
  mapIcon('sp-icon-reset', ICONS.rotateCcw);
  mapIcon('sp-icon-compass', ICONS.compass);
  mapIcon('tab-icon-overview', ICONS.overview);
  mapIcon('tab-icon-history', ICONS.history);
  mapIcon('tab-icon-tax', ICONS.tax);
  mapIcon('tab-icon-liens', ICONS.shield);
  mapIcon('tab-icon-audit', ICONS.link);
}

// 2. Language & Theme Toggles
function initLanguageToggle() {
  const btn = document.getElementById('sp-btn-lang');
  if (!btn) return;
  btn.addEventListener('click', () => {
    const newLang = toggleLanguage();
    btn.textContent = newLang === 'bn' ? 'EN' : 'বাং';
    updateLanguageStrings();
    reRenderActiveViews();
  });
}

function initThemeToggle() {
  const btn = document.getElementById('sp-btn-theme');
  const icon = document.getElementById('sp-theme-icon');
  if (!btn) return;
  btn.addEventListener('click', () => {
    const theme = toggleTheme();
    if (icon) icon.textContent = theme === 'dark' ? '☀️' : '🌙';
  });
}

function updateLanguageStrings() {
  const isEn = currentLang === 'en';
  const roleEl = document.getElementById('sp-role-chip');
  if (roleEl) roleEl.textContent = isEn ? 'AC Land' : 'এসি ল্যান্ড';

  const demoEl = document.getElementById('sp-demo-pill');
  if (demoEl) demoEl.textContent = isEn ? 'DEMO' : 'ডেমো';

  const tabOverview = document.getElementById('tab-lbl-overview');
  if (tabOverview) tabOverview.textContent = isEn ? 'Overview' : 'সারসংক্ষেপ';
  const tabHistory = document.getElementById('tab-lbl-history');
  if (tabHistory) tabHistory.textContent = isEn ? 'Lineage' : 'ইতিহাস';
  const tabTax = document.getElementById('tab-lbl-tax');
  if (tabTax) tabTax.textContent = isEn ? 'Tax' : 'কর স্থিতি';
  const tabLiens = document.getElementById('tab-lbl-liens');
  if (tabLiens) tabLiens.textContent = isEn ? 'Liens' : 'দায় ও লিয়েন';
  const tabAudit = document.getElementById('tab-lbl-audit');
  if (tabAudit) tabAudit.textContent = isEn ? 'Audit' : 'অডিট লেজার';

  const ctxKhatian = document.getElementById('sp-ctx-khatian-lbl');
  if (ctxKhatian) ctxKhatian.textContent = isEn ? 'Khatian' : 'খতিয়ান';
  const ctxDag = document.getElementById('sp-ctx-dag-lbl');
  if (ctxDag) ctxDag.textContent = isEn ? 'Dag' : 'দাগ';

  const dagEl = document.getElementById('sp-detected-dag');
  if (dagEl) dagEl.textContent = isEn ? state.context.dag : toBnDigits(state.context.dag);
  const khatEl = document.getElementById('sp-detected-khatian');
  if (khatEl) khatEl.textContent = isEn ? state.context.khatian : toBnDigits(state.context.khatian);
  const portalEl = document.getElementById('sp-detected-portal');
  if (portalEl) {
    portalEl.textContent = isEn
      ? (state.context.portal === 'e_mutation' ? 'e-Mutation' : 'LD Tax Portal')
      : (state.context.portal === 'e_mutation' ? 'ই-নামজারি' : 'ভূমি কর পোর্টাল');
  }

  const lblLayers = document.getElementById('sp-lbl-layers');
  if (lblLayers) lblLayers.textContent = isEn ? 'Layers' : 'স্তরসমূহ';

  const popoverTitle = document.getElementById('sp-popover-title');
  if (popoverTitle) popoverTitle.textContent = isEn ? 'Cadastral Layers' : 'ক্যাডাস্ট্রাল স্তরসমূহ';

  const lblCs = document.getElementById('lbl-l-cs');
  if (lblCs) lblCs.textContent = isEn ? '1. Ancestral Footprint' : '১. সিএস পৈত্রিক সীমানা';
  const areaCs = document.getElementById('area-l-cs');
  if (areaCs) areaCs.textContent = isEn ? '18.00 dec' : '১৮.০০ শতক';

  const lblDeed = document.getElementById('lbl-l-deed');
  if (lblDeed) lblDeed.textContent = isEn ? '2. Deed Claim' : '২. দলিল দাবিকৃত জমি';
  const areaDeed = document.getElementById('area-l-deed');
  if (areaDeed) areaDeed.textContent = isEn ? '6.00 dec' : '৬.০০ শতক';

  const lblDlrs = document.getElementById('lbl-l-dlrs');
  if (lblDlrs) lblDlrs.textContent = isEn ? '3. DLRS Ground Truth' : '৩. ডিএলআরএস জরিপকৃত';
  const areaDlrs = document.getElementById('area-l-dlrs');
  if (areaDlrs) areaDlrs.textContent = isEn ? '5.10 dec' : '৫.১০ শতক';

  const lblKhas = document.getElementById('lbl-l-khas');
  if (lblKhas) lblKhas.textContent = isEn ? '4. Public Khas Canal' : '৪. সরকারি খাস নিষ্কাশন খাল';
  const areaKhas = document.getElementById('area-l-khas');
  if (areaKhas) areaKhas.textContent = isEn ? '4.48 dec' : '৪.৪৮ শতক';

  const lblConflict = document.getElementById('lbl-l-conflict');
  if (lblConflict) lblConflict.textContent = isEn ? '5. Conflict Zone' : '৫. বিরোধপূর্ণ এলাকা';
  const areaConflict = document.getElementById('area-l-conflict');
  if (areaConflict) areaConflict.textContent = isEn ? '0.90 dec' : '০.৯০ শতক';
}

function initSessionTimer() {
  const timerEl = document.getElementById('sp-session-timer');
  if (!timerEl) return;
  let sec = 258;
  setInterval(() => {
    sec++;
    const m = String(Math.floor(sec / 60)).padStart(2, '0');
    const s = String(sec % 60).padStart(2, '0');
    const isEn = currentLang === 'en';
    timerEl.textContent = `⏱ ${isEn ? m : toBnDigits(m)}:${isEn ? s : toBnDigits(s)}`;
  }, 1000);
}

// 3. Tab Switching & Auto-Collapsing Hero on Tab Switch
function initTabs() {
  const tabs = document.querySelectorAll('.sp-tab-item');
  tabs.forEach((tab) => {
    tab.addEventListener('click', () => {
      tabs.forEach((t) => t.classList.remove('active'));
      document.querySelectorAll('.sp-panel').forEach((c) => c.classList.remove('active'));
      tab.classList.add('active');
      const target = document.getElementById(tab.dataset.tab);
      if (target) target.classList.add('active');

      // Auto-collapse Verdict Hero if switching to any tab other than Overview
      const vContainer = document.getElementById('sp-verdict-hero-container');
      if (vContainer) {
        if (tab.dataset.tab !== 'tab-overview') {
          collapseVerdictHero(vContainer);
        }
      }
    });
  });
}

// Auto-collapse Verdict Hero on scrolling tab content
function initTabScrollCollapse() {
  const tabContainer = document.getElementById('sp-tab-container');
  if (!tabContainer) return;

  tabContainer.addEventListener('scroll', () => {
    if (tabContainer.scrollTop > 25) {
      const vContainer = document.getElementById('sp-verdict-hero-container');
      if (vContainer) collapseVerdictHero(vContainer);
    }
  }, { passive: true });
}

function collapseVerdictHero(container) {
  if (!container || container.classList.contains('collapsed')) return;
  container.classList.add('collapsed');
  const exp = container.querySelector('.vh-expanded-box');
  const col = container.querySelector('.vh-collapsed-bar');
  if (exp) exp.classList.add('hidden');
  if (col) col.classList.remove('hidden');
}

// 4. Map Resizer & View Buttons
function initMapResizer() {
  const resizer = document.getElementById('sp-map-resizer');
  const mapPanel = document.getElementById('sp-map-panel');
  if (!resizer || !mapPanel) return;

  // Restore remembered height from session state
  const savedHeight = sessionStorage.getItem('naksha_map_height');
  if (savedHeight) {
    mapPanel.style.height = savedHeight;
  }

  let startY = 0;
  let startHeight = 0;

  const onMouseMove = (e) => {
    const delta = e.clientY - startY;
    const newHeight = Math.max(120, Math.min(window.innerHeight * 0.65, startHeight + delta));
    mapPanel.style.height = `${newHeight}px`;
    if (state.map) state.map.invalidateSize();
  };

  const onMouseUp = () => {
    resizer.classList.remove('active');
    document.removeEventListener('mousemove', onMouseMove);
    document.removeEventListener('mouseup', onMouseUp);
    sessionStorage.setItem('naksha_map_height', mapPanel.style.height);
    if (state.map) state.map.invalidateSize();
  };

  resizer.addEventListener('mousedown', (e) => {
    e.preventDefault();
    startY = e.clientY;
    startHeight = mapPanel.getBoundingClientRect().height;
    resizer.classList.add('active');
    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
  });
}

function initMapControlButtons() {
  const mapPanel = document.getElementById('sp-map-panel');
  const btnCollapse = document.getElementById('sp-btn-map-collapse');
  const btnExpand = document.getElementById('sp-btn-map-expand');

  if (btnCollapse && mapPanel) {
    btnCollapse.addEventListener('click', () => {
      mapPanel.classList.remove('map-expanded');
      mapPanel.classList.toggle('map-collapsed');
      setTimeout(() => { if (state.map) state.map.invalidateSize(); }, 180);
    });
  }

  if (btnExpand && mapPanel) {
    btnExpand.addEventListener('click', () => {
      mapPanel.classList.remove('map-collapsed');
      mapPanel.classList.toggle('map-expanded');
      setTimeout(() => { if (state.map) state.map.invalidateSize(); }, 180);
    });
  }

  const recenterBtn = document.getElementById('sp-btn-recenter');
  if (recenterBtn) {
    recenterBtn.addEventListener('click', () => {
      if (state.targetBounds && state.map) {
        state.map.fitBounds(state.targetBounds, { padding: [35, 35] });
      }
    });
  }

  const resetBtn = document.getElementById('sp-btn-reset-zoom');
  if (resetBtn) {
    resetBtn.addEventListener('click', () => {
      if (state.map) state.map.setView([23.98506, 90.35035], 19);
    });
  }

  const retryBtn = document.getElementById('sp-retry-btn');
  if (retryBtn) {
    retryBtn.addEventListener('click', () => {
      loadPlotData(state.activeParcelId);
    });
  }
}

// Layers Popover Menu Toggle (Top-Left of Map)
function initLayersPopover() {
  const btn = document.getElementById('sp-btn-layers-toggle');
  const popover = document.getElementById('sp-layers-popover');
  if (!btn || !popover) return;

  btn.addEventListener('click', (e) => {
    e.stopPropagation();
    popover.classList.toggle('hidden');
  });

  document.addEventListener('click', (e) => {
    if (!popover.contains(e.target) && e.target !== btn) {
      popover.classList.add('hidden');
    }
  });

  // Wire checkboxes
  popover.querySelectorAll('input[type="checkbox"]').forEach((chk) => {
    chk.addEventListener('change', (e) => {
      const type = chk.dataset.layerType;
      const isChecked = e.target.checked;
      state.layerVisibility[type] = isChecked;
      const layer = state.layers[type];
      if (layer && state.map) {
        if (isChecked) state.map.addLayer(layer);
        else state.map.removeLayer(layer);
      }
    });
  });
}

// 5. Initialize Leaflet Map
function initMap() {
  if (typeof L === 'undefined') {
    const errorEl = document.getElementById('sp-map-error');
    if (errorEl) errorEl.classList.remove('hidden');
    return false;
  }

  const mapContainer = document.getElementById('sp-map');
  if (!mapContainer) return false;

  try {
    state.map = L.map('sp-map', {
      center: [23.98506, 90.35035],
      zoom: 19,
      maxZoom: 21,
      minZoom: 14,
      zoomControl: false,
      attributionControl: false,
    });

    const tileLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      subdomains: ['a', 'b', 'c'],
    });

    tileLayer.on('tileerror', () => {
      const warnEl = document.getElementById('sp-tile-warning');
      if (warnEl) {
        warnEl.classList.remove('hidden');
        setTimeout(() => warnEl.classList.add('hidden'), 5000);
      }
    });

    tileLayer.addTo(state.map);

    setTimeout(() => {
      if (state.map) {
        state.map.invalidateSize();
        injectSvgMapPatterns();
      }
    }, 120);

    window.addEventListener('resize', () => {
      if (state.map) state.map.invalidateSize();
    });

    return true;
  } catch (mapErr) {
    console.error('[NAKSHA SidePanel] Map initialization error:', mapErr);
    return false;
  }
}

// Inject SVG Hatch & Wave Patterns into Leaflet Overlay Pane
function injectSvgMapPatterns() {
  const svg = document.querySelector('#sp-map svg');
  if (!svg) return;

  let defs = svg.querySelector('defs');
  if (!defs) {
    defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
    svg.prepend(defs);
  }

  if (!document.getElementById('pattern-hatch-red')) {
    const hatch = document.createElementNS('http://www.w3.org/2000/svg', 'pattern');
    hatch.setAttribute('id', 'pattern-hatch-red');
    hatch.setAttribute('patternUnits', 'userSpaceOnUse');
    hatch.setAttribute('width', '8');
    hatch.setAttribute('height', '8');
    hatch.setAttribute('patternTransform', 'rotate(45 0 0)');
    hatch.innerHTML = `
      <rect width="8" height="8" fill="#F43F5E" fill-opacity="0.25" />
      <line x1="0" y1="0" x2="0" y2="8" stroke="#F43F5E" stroke-width="2.5" />
    `;
    defs.appendChild(hatch);
  }

  if (!document.getElementById('pattern-wave-cyan')) {
    const wave = document.createElementNS('http://www.w3.org/2000/svg', 'pattern');
    wave.setAttribute('id', 'pattern-wave-cyan');
    wave.setAttribute('patternUnits', 'userSpaceOnUse');
    wave.setAttribute('width', '8');
    wave.setAttribute('height', '8');
    wave.innerHTML = `
      <rect width="8" height="8" fill="#22D3EE" fill-opacity="0.15" />
      <circle cx="4" cy="4" r="1.5" fill="#22D3EE" fill-opacity="0.75" />
    `;
    defs.appendChild(wave);
  }
}

// 6. Connect to Chrome Extension messaging & storage
function initSidePanelListeners() {
  if (chrome.runtime && chrome.runtime.onMessage) {
    chrome.runtime.onMessage.addListener((message) => {
      if (message.type === 'NAKSHA_CONTEXT_UPDATED' || message.type === 'NAKSHA_PLOT_CHANGED') {
        applyDetectedContext(message.payload);
      }
    });
  }

  if (chrome.storage && chrome.storage.local) {
    chrome.storage.local.get(['activeParcelContext'], (result) => {
      if (result.activeParcelContext) {
        applyDetectedContext(result.activeParcelContext);
      }
    });
  }
}

function resolveParcelId(dag) {
  if (!dag) return state.activeParcelId || DEFAULT_PARCEL_ID;
  const clean = String(dag).trim();
  if (clean === '402') return 'par-8f92-bd04-syn';
  if (clean === '401') return 'BS-401';
  if (clean === '403') return 'BS-403';
  return clean;
}

function applyDetectedContext(ctx) {
  if (!ctx) return;
  state.context = ctx;

  const isEn = currentLang === 'en';
  const dagEl = document.getElementById('sp-detected-dag');
  const khatianEl = document.getElementById('sp-detected-khatian');
  const mouzaEl = document.getElementById('sp-detected-mouza');
  const portalEl = document.getElementById('sp-detected-portal');

  if (dagEl) dagEl.textContent = isEn ? (ctx.dag || '402') : toBnDigits(ctx.dag || '৪০২');
  if (khatianEl) khatianEl.textContent = isEn ? (ctx.khatian || '120') : toBnDigits(ctx.khatian || '১২০');
  if (mouzaEl) mouzaEl.textContent = ctx.mouza || (isEn ? 'Kashimpur' : 'কাশিমপুর');
  if (portalEl) {
    portalEl.textContent = isEn
      ? (ctx.portal === 'e_mutation' ? 'e-Mutation' : 'LD Tax Portal')
      : (ctx.portal === 'e_mutation' ? 'ই-নামজারি' : 'ভূমি কর পোর্টাল');
  }

  const targetId = resolveParcelId(ctx.dag);
  state.activeParcelId = targetId;
  loadPlotData(targetId);
}

// 7. Load context & plot data
async function loadContextAndPlotData() {
  if (window.location && window.location.search) {
    const params = new URLSearchParams(window.location.search);
    const langParam = params.get('lang');
    if (langParam && (langParam === 'en' || langParam === 'bn') && langParam !== currentLang) {
      currentLang = langParam;
      const btn = document.getElementById('sp-btn-lang');
      if (btn) btn.textContent = currentLang === 'bn' ? 'EN' : 'বাং';
      updateLanguageStrings();
    }

    const dagParam = params.get('dag');
    if (dagParam) {
      state.context.dag = dagParam;
      if (dagParam === '401') state.context.khatian = '88';
      else if (dagParam === '403') state.context.khatian = '125';
      state.activeParcelId = resolveParcelId(dagParam);

      const isEn = currentLang === 'en';
      const dagEl = document.getElementById('sp-detected-dag');
      if (dagEl) dagEl.textContent = isEn ? dagParam : toBnDigits(dagParam);
      const khatEl = document.getElementById('sp-detected-khatian');
      if (khatEl) khatEl.textContent = isEn ? state.context.khatian : toBnDigits(state.context.khatian);
    }

    const tabParam = params.get('tab');
    if (tabParam) {
      setTimeout(() => {
        const tabBtn = document.querySelector(`.sp-tab-item[data-tab="${tabParam}"]`);
        if (tabBtn) tabBtn.click();
      }, 350);
    }

    const openLayers = params.get('open_layers');
    if (openLayers === 'true') {
      setTimeout(() => {
        const popover = document.getElementById('sp-layers-popover');
        if (popover) popover.classList.remove('hidden');
      }, 450);
    }
  }
  await loadPlotData(state.activeParcelId);
}

async function loadPlotData(parcelId) {
  const reqSeq = ++state.currentRequestSeq;

  const loader = document.getElementById('sp-map-loader');
  const loaderText = document.getElementById('sp-map-loader-text');
  const errorEl = document.getElementById('sp-map-error');

  if (loader) {
    loader.classList.remove('hidden');
    if (loaderText) {
      const isEn = currentLang === 'en';
      loaderText.textContent = isEn
        ? `Loading Plot ${state.context.dag || '402'} layers...`
        : `দাগ ${toBnDigits(state.context.dag || '৪০২')} এর স্তরসমূহ লোড হচ্ছে...`;
    }
  }
  if (errorEl) errorEl.classList.add('hidden');

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 8000);

  try {
    const fetchOpts = { signal: controller.signal };
    const [layersRes, neighborsRes, conflictsRes, verifRes, ledgerRes, integRes] = await Promise.allSettled([
      fetch(`${API_BASE}/api/v1/spatial/parcels/${parcelId}/layers`, fetchOpts),
      fetch(`${API_BASE}/api/v1/spatial/parcels/${parcelId}/neighbors`, fetchOpts),
      fetch(`${API_BASE}/api/v1/spatial/parcels/${parcelId}/conflicts`, fetchOpts),
      fetch(`${API_BASE}/api/v1/spatial/parcels/${parcelId}/verification`, fetchOpts),
      fetch(`${API_BASE}/api/v1/ledger?limit=10`, fetchOpts),
      fetch(`${API_BASE}/api/v1/ledger/verify`, fetchOpts),
    ]);

    clearTimeout(timeoutId);

    if (reqSeq !== state.currentRequestSeq) return;

    if (layersRes.status !== 'fulfilled' || !layersRes.value.ok) {
      throw new Error('Spatial layers unavailable');
    }

    const layersData = await layersRes.value.json();
    state.currentLayers = layersData;
    renderLayers(layersData);

    let conflictData = null;
    if (conflictsRes.status === 'fulfilled' && conflictsRes.value.ok) {
      conflictData = await conflictsRes.value.json();
    }

    let neighborsData = null;
    if (neighborsRes.status === 'fulfilled' && neighborsRes.value.ok) {
      neighborsData = await neighborsRes.value.json();
      state.currentNeighbors = neighborsData;
      renderNeighborOutlines(neighborsData);
    }

    let verifData = null;
    if (verifRes.status === 'fulfilled' && verifRes.value.ok) {
      verifData = await verifRes.value.json();
      state.currentVerification = verifData;
    }

    let ledgerData = [];
    if (ledgerRes.status === 'fulfilled' && ledgerRes.value.ok) {
      ledgerData = await ledgerRes.value.json();
    }

    let integData = { is_valid: true };
    if (integRes.status === 'fulfilled' && integRes.value.ok) {
      integData = await integRes.value.json();
    }

    renderAllComponents(verifData, layersData, conflictData, neighborsData, ledgerData, integData);

    if (loader) loader.classList.add('hidden');
    if (state.map) {
      setTimeout(() => {
        state.map.invalidateSize();
        injectSvgMapPatterns();
      }, 80);
    }
  } catch (err) {
    clearTimeout(timeoutId);
    if (reqSeq !== state.currentRequestSeq) return;

    console.error('[NAKSHA SidePanel] Fetch failed:', err);
    if (loader) loader.classList.add('hidden');
    if (errorEl) errorEl.classList.remove('hidden');
  }
}

// 8. Render All Components
function renderAllComponents(verifData, layersData, conflictData, neighborsData, ledgerData, integData) {
  const cleanDag = String(state.context.dag || '402');
  const verdict = verifData?.verdict || (cleanDag === '401' ? 'CLEAR' : (cleanDag === '403' ? 'REVIEW' : 'BLOCK'));
  const isEn = currentLang === 'en';

  const hasKhasOverlap = !!(conflictData && conflictData.area_in_decimals > 0) || (cleanDag === '402');
  const hasAreaMismatch = (verifData?.discrepancies?.some(d => d.discrepancy_type === 'AREA_MISMATCH')) || (cleanDag === '402');
  const hasUnmutated = (verifData?.discrepancies?.some(d => d.discrepancy_type === 'UNMUTATED_DEED')) || (cleanDag === '403');
  const hasClassConflict = (verifData?.discrepancies?.some(d => d.discrepancy_type === 'CLASS_CONFLICT')) || (cleanDag === '403');
  const hasOwnerMismatch = (verifData?.discrepancies?.some(d => d.discrepancy_type === 'OWNER_MISMATCH'));

  // A. VerdictHero
  const vContainer = document.getElementById('sp-verdict-hero-container');
  const chips = [];

  if (verdict === 'CLEAR') {
    chips.push({ label: isEn ? 'Title clean' : 'স্বত্ব নির্ভুল', color: 'var(--status-clear)', target: 'rule_area' });
    chips.push({ label: isEn ? 'Tax paid' : 'কর পরিশোধিত', color: 'var(--status-clear)', target: 'tab-tax' });
  } else if (verdict === 'REVIEW') {
    chips.push({ label: isEn ? 'Unmutated 124d' : 'নামজারিহীন ১২৪ দিন', color: 'var(--status-review)', target: 'rule_mutation' });
    chips.push({ label: isEn ? 'Arrears × 3 Yrs' : 'বকেয়া কর ৩ অর্থবছর', color: 'var(--status-review)', target: 'tab-tax' });
    chips.push({ label: isEn ? 'Class mismatch' : 'শ্রেণি অমিল', color: 'var(--status-review)', target: 'rule_class' });
  } else {
    chips.push({ label: isEn ? 'Khas overlap 0.90 dec' : 'সরকারি খাল দখল ০.৯০ শতক', color: 'var(--status-block)', target: 'conflict_zone' });
    chips.push({ label: isEn ? 'Area deficit 0.90 dec' : 'জমির ঘাটতি ০.৯০ শতক', color: 'var(--status-block)', target: 'rule_area' });
    chips.push({ label: isEn ? 'Mutation on hold' : 'নামজারি স্থগিত', color: 'var(--status-block)', target: 'rule_mutation' });
  }

  renderVerdictHero(vContainer, {
    verdict,
    hasKhasOverlap,
    hasAreaMismatch,
    hasUnmutated,
    hasClassConflict,
    hasOwnerMismatch,
    chips,
  }, (targetKey) => {
    handleChipClickHighlight(targetKey);
  });

  // B. AreaChart (Tab 1)
  const chartContainer = document.getElementById('overview-chart-container');
  let deedArea = 6.00;
  let dlrsArea = 5.10;
  let csArea = 18.00;
  let conflictArea = hasKhasOverlap ? 0.90 : 0.0;

  if (cleanDag === '401') {
    deedArea = 4.37;
    dlrsArea = 4.37;
    conflictArea = 0.0;
  } else if (cleanDag === '403') {
    deedArea = 5.53;
    dlrsArea = 5.52;
    conflictArea = 0.0;
  }

  renderAreaChart(chartContainer, { csArea, deedArea, dlrsArea, conflictArea });

  // D. RuleGrid (Tab 1)
  const rulesContainer = document.getElementById('overview-rules-container');
  renderRuleGrid(rulesContainer, {
    hasKhasOverlap,
    hasAreaMismatch,
    hasUnmutated,
    hasClassConflict,
    hasOwnerMismatch,
  });

  // E. LineageTimeline (Tab 2)
  const lineageContainer = document.getElementById('history-lineage-container');
  renderLineageTimeline(lineageContainer, {
    dag: cleanDag,
    nameMatchScore: hasOwnerMismatch ? 64 : 98,
  });

  // F. TaxChart (Tab 3)
  const taxContainer = document.getElementById('tax-chart-container');
  const neighborsList = neighborsData?.features?.map(f => {
    const p = f.properties || {};
    return {
      dag: p.dag_number,
      khatian: p.khatian_number,
      owner: p.owner_name,
      payer: p.dag_number === '403' ? (isEn ? 'Unknown Payer' : 'অজ্ঞাত করদাতা') : p.owner_name,
      status: p.tax_status,
      area: String(p.area_decimals || '5.0'),
      mismatch: p.dag_number === '403',
    };
  }) || [];
  renderTaxChart(taxContainer, { neighbors: neighborsList });

  // G. LienTimeline (Tab 4)
  const liensContainer = document.getElementById('liens-timeline-container');
  renderLienTimeline(liensContainer, { liens: [] });

  // H. AuditChain (Tab 5)
  const auditContainer = document.getElementById('audit-chain-container');
  renderAuditChain(auditContainer, ledgerData, integData);
}

function resetLayerStyle(type, layer) {
  const cfg = LAYER_CONFIG[type];
  if (!cfg || !layer) return;
  layer.setStyle({
    color: cfg.color,
    weight: cfg.weight,
    dashArray: cfg.dashArray,
    fillColor: cfg.fillColor,
    fillOpacity: cfg.fillOpacity,
    opacity: 1.0,
    stroke: cfg.stroke !== false,
  });
}

function reRenderActiveViews() {
  if (state.currentLayers) {
    renderAllComponents(
      state.currentVerification,
      state.currentLayers,
      null,
      state.currentNeighbors,
      null,
      null
    );
  }
}

// 9. Chip Click to Highlight Feature
function handleChipClickHighlight(targetKey) {
  if (!targetKey) return;

  if (targetKey === 'conflict_zone') {
    if (state.conflictBounds && state.map) {
      state.map.fitBounds(state.conflictBounds, { padding: [45, 45] });
    }
  } else if (targetKey.startsWith('tab-')) {
    const tabBtn = document.querySelector(`.sp-tab-item[data-tab="${targetKey}"]`);
    if (tabBtn) tabBtn.click();
  } else if (targetKey.startsWith('rule_')) {
    const tabOverviewBtn = document.querySelector('.sp-tab-item[data-tab="tab-overview"]');
    if (tabOverviewBtn) tabOverviewBtn.click();
    const ruleCard = document.querySelector(`.rule-fail-card`);
    if (ruleCard) ruleCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }
}

// 10. Render Layers on Leaflet Map
function renderLayers(layerSnapshots) {
  if (!state.map) return;

  Object.values(state.layers).forEach((layer) => {
    try { state.map.removeLayer(layer); } catch (e) {}
  });
  state.layers = {};

  let boundsToFit = null;
  const isEn = currentLang === 'en';

  layerSnapshots.forEach((snapshot) => {
    const type = snapshot.layer_type;
    const styleCfg = LAYER_CONFIG[type] || {
      color: '#A78BFA',
      fillColor: '#A78BFA',
      weight: 1.5,
      fillOpacity: 0.1,
      name: snapshot.layer_name,
    };

    try {
      const isConflict = (type === 'conflict_zone');
      const isKhas = (type === 'restricted_khas');

      const geoLayer = L.geoJSON(snapshot.geometry, {
        style: {
          color: styleCfg.color,
          weight: styleCfg.weight,
          dashArray: styleCfg.dashArray,
          fillColor: styleCfg.fillColor,
          fillOpacity: styleCfg.fillOpacity,
          stroke: styleCfg.stroke !== false,
        },
        onEachFeature: (feature, layer) => {
          if (isConflict) {
            layer.bindTooltip(isEn ? "0.90 dec overlap" : "০.৯০ শতক দখল", {
              permanent: true,
              direction: 'center',
              className: 'conflict-callout',
            });
          }
        },
      });

      if (state.layerVisibility[type] !== false) {
        geoLayer.addTo(state.map);
      }
      state.layers[type] = geoLayer;

      // Apply SVG pattern textures after rendering
      setTimeout(() => {
        try {
          if (isConflict) {
            geoLayer.eachLayer(l => {
              const el = l.getElement ? l.getElement() : null;
              if (el) el.setAttribute('fill', 'url(#pattern-hatch-red)');
            });
          } else if (isKhas) {
            geoLayer.eachLayer(l => {
              const el = l.getElement ? l.getElement() : null;
              if (el) el.setAttribute('fill', 'url(#pattern-wave-cyan)');
            });
          }
        } catch (e) {}
      }, 50);

      const layerBounds = geoLayer.getBounds();
      if (layerBounds && layerBounds.isValid && layerBounds.isValid()) {
        if (type === 'ground_truth') {
          state.targetBounds = layerBounds;
          boundsToFit = layerBounds;
        } else if (!boundsToFit) {
          boundsToFit = layerBounds;
        }
      }

      if (type === 'conflict_zone') {
        state.conflictBounds = layerBounds;
      }
    } catch (layerErr) {
      console.warn(`[NAKSHA SidePanel] Failed to render layer ${type}:`, layerErr);
    }
  });

  // Ensure conflict zone is always brought to top
  if (state.layers['conflict_zone'] && state.layers['conflict_zone'].bringToFront) {
    state.layers['conflict_zone'].bringToFront();
  }

  if (boundsToFit && state.map) {
    state.map.fitBounds(boundsToFit, { padding: [35, 35] });
  }
}

// 11. Render Neighbor Outlines (Realistic Context with Dag Numbers)
function renderNeighborOutlines(neighborsGeoJSON) {
  if (!state.map || !neighborsGeoJSON || !neighborsGeoJSON.features) return;

  try {
    const isEn = currentLang === 'en';
    const neighborLayer = L.geoJSON(neighborsGeoJSON, {
      filter: (f) => !f.properties.is_target_parcel,
      style: {
        color: '#52525B',
        weight: 1,
        dashArray: '2, 4',
        fill: false,
      },
      onEachFeature: (f, layer) => {
        const p = f.properties || {};
        const dagNum = isEn ? p.dag_number : toBnDigits(p.dag_number);
        layer.bindTooltip(`${isEn ? 'Dag' : 'দাগ'} ${dagNum}`, {
          permanent: true,
          direction: 'center',
          className: 'layer-map-label',
        });
      },
    });

    neighborLayer.addTo(state.map);
  } catch (e) {
    console.warn('[NAKSHA SidePanel] Error rendering neighbor outlines:', e);
  }
}
