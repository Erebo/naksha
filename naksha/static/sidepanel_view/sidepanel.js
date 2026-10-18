/**
 * NAKSHA (নকশা) — Side Panel Application Logic
 * Integrates Leaflet 2D GIS with FastAPI backend (http://127.0.0.1:8000).
 * Decision-First UI Architecture connecting VerdictHero, AreaChart, RuleGrid, Lineage, Tax, Liens, Audit.
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
    color: '#8b5cf6',
    weight: 2,
    dashArray: '5, 5',
    fillColor: '#8b5cf6',
    fillOpacity: 0.15,
    name: '১. সিএস পৈত্রিক সীমানা (CS 88)',
    shortName: 'সিএস ৮৮',
  },
  deed_claim: {
    color: '#3b82f6',
    weight: 2,
    fillColor: '#3b82f6',
    fillOpacity: 0.25,
    name: '২. দলিলে দাবিকৃত জমি (Deed Claim)',
    shortName: 'দলিল দাবি',
  },
  ground_truth: {
    color: '#10b981',
    weight: 3,
    fillColor: '#10b981',
    fillOpacity: 0.35,
    name: '৩. ডিএলআরএস জরিপকৃত জমি (DLRS Survey)',
    shortName: 'ডিএলআরএস',
  },
  conflict_zone: {
    color: '#ef4444',
    weight: 2,
    fillColor: '#ef4444',
    fillOpacity: 0.70,
    name: '৪. বিরোধপূর্ণ এলাকা (Khas Canal Conflict)',
    shortName: 'বিরোধপূর্ণ',
  },
  restricted_khas: {
    color: '#0ea5e9',
    weight: 2,
    fillColor: '#0ea5e9',
    fillOpacity: 0.35,
    name: 'সরকারি খাস নিষ্কাশন খাল (Public Khas Canal)',
    shortName: 'খাস খাল',
  },
};

document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  initLanguageToggle();
  initSessionTimer();
  const mapOk = initMap();
  initSidePanelListeners();
  if (mapOk) {
    loadContextAndPlotData();
  }
  setupActionButtons();
  initLayerPillToggles();
});

// 1. Language Toggle & Session Timer
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

function updateLanguageStrings() {
  const isEn = currentLang === 'en';
  const roleEl = document.getElementById('sp-role-chip');
  if (roleEl) roleEl.textContent = isEn ? 'AC Land / Kanoongo' : 'এসি ল্যান্ড / কানুনগো';

  const synEl = document.getElementById('sp-syn-tag');
  if (synEl) synEl.textContent = isEn ? 'Synthetic Data' : 'কৃত্রিম ডেমো ডেটা';

  const lblPortal = document.getElementById('sp-lbl-portal');
  if (lblPortal) lblPortal.textContent = isEn ? 'Portal:' : 'পোর্টাল:';
  const lblMouza = document.getElementById('sp-lbl-mouza');
  if (lblMouza) lblMouza.textContent = isEn ? 'Mouza:' : 'মৌজা:';
  const lblKhatian = document.getElementById('sp-lbl-khatian');
  if (lblKhatian) lblKhatian.textContent = isEn ? 'Khatian:' : 'খতিয়ান:';
  const lblDag = document.getElementById('sp-lbl-dag');
  if (lblDag) lblDag.textContent = isEn ? 'Plot:' : 'দাগ:';

  // Update Tab Labels
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
}

function initSessionTimer() {
  const timerEl = document.getElementById('sp-session-timer');
  if (!timerEl) return;
  let sec = 258; // 04:18 starting countdown
  setInterval(() => {
    sec++;
    const m = String(Math.floor(sec / 60)).padStart(2, '0');
    const s = String(sec % 60).padStart(2, '0');
    timerEl.textContent = `⏱ ${m}:${s}`;
  }, 1000);
}

// 2. Initialize Tabs
function initTabs() {
  const tabs = document.querySelectorAll('.sp-tab-btn');
  tabs.forEach((tab) => {
    tab.addEventListener('click', () => {
      tabs.forEach((t) => t.classList.remove('active'));
      document.querySelectorAll('.sp-tab-pane').forEach((c) => c.classList.remove('active'));
      tab.classList.add('active');
      const target = document.getElementById(tab.dataset.tab);
      if (target) target.classList.add('active');
    });
  });
}

// 3. Initialize Leaflet Map
function initMap() {
  if (typeof L === 'undefined') {
    console.error('[NAKSHA SidePanel] Leaflet library L is not loaded.');
    const errorEl = document.getElementById('sp-map-error');
    const errorMsg = document.getElementById('sp-error-message');
    const loader = document.getElementById('sp-map-loader');
    if (loader) loader.classList.add('hidden');
    if (errorEl) {
      errorEl.classList.remove('hidden');
      if (errorMsg) errorMsg.textContent = 'Leaflet library failed to load.';
    }
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
      zoomControl: false, // Clean side panel UI
      attributionControl: false,
    });

    // Muted CartoDB Positron / OSM Basemap without watermark
    const tileLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      subdomains: ['a', 'b', 'c'],
    });

    let tileWarningTriggered = false;
    tileLayer.on('tileerror', () => {
      if (!tileWarningTriggered) {
        tileWarningTriggered = true;
        const warnEl = document.getElementById('sp-tile-warning');
        if (warnEl) {
          warnEl.classList.remove('hidden');
          setTimeout(() => warnEl.classList.add('hidden'), 5000);
        }
      }
    });

    tileLayer.addTo(state.map);

    setTimeout(() => {
      if (state.map) state.map.invalidateSize();
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

// 4. Resolve backend parcel ID from Dag number
function resolveParcelId(dag) {
  if (!dag) return state.activeParcelId || DEFAULT_PARCEL_ID;
  const clean = String(dag).trim();
  if (clean === '402') return 'par-8f92-bd04-syn';
  if (clean === '401') return 'BS-401';
  if (clean === '403') return 'BS-403';
  return clean;
}

// 5. Connect to Chrome Extension messaging & storage
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

function applyDetectedContext(ctx) {
  if (!ctx) return;
  state.context = ctx;

  const portalEl = document.getElementById('sp-detected-portal');
  const dagEl = document.getElementById('sp-detected-dag');
  const khatianEl = document.getElementById('sp-detected-khatian');
  const mouzaEl = document.getElementById('sp-detected-mouza');

  if (portalEl) {
    portalEl.textContent = ctx.portal === 'e_mutation' ? 'ই-নামজারি' : 'ভূমি কর';
  }
  if (dagEl) dagEl.textContent = (ctx.dag || '৪০২');
  if (khatianEl) khatianEl.textContent = (ctx.khatian || '১২০');
  if (mouzaEl) mouzaEl.textContent = (ctx.mouza || 'কাশিমপুর');

  const targetId = resolveParcelId(ctx.dag);
  state.activeParcelId = targetId;
  loadPlotData(targetId);
}

// 6. Fetch Multi-Era Layers and Plot Data from FastAPI
async function loadContextAndPlotData() {
  // Check URL query parameters for standalone preview or automated test
  if (window.location && window.location.search) {
    const params = new URLSearchParams(window.location.search);
    const dagParam = params.get('dag');
    if (dagParam) {
      state.context.dag = dagParam;
      if (dagParam === '401') {
        state.context.khatian = '88';
      } else if (dagParam === '403') {
        state.context.khatian = '125';
      }
      state.activeParcelId = resolveParcelId(dagParam);
      const dagEl = document.getElementById('sp-detected-dag');
      if (dagEl) dagEl.textContent = dagParam;
      const khatEl = document.getElementById('sp-detected-khatian');
      if (khatEl) khatEl.textContent = state.context.khatian;
    }
  }
  await loadPlotData(state.activeParcelId);
}

async function loadPlotData(parcelId) {
  const reqSeq = ++state.currentRequestSeq;

  const loader = document.getElementById('sp-map-loader');
  const loaderText = document.getElementById('sp-map-loader-text');
  const errorEl = document.getElementById('sp-map-error');
  const errorMsg = document.getElementById('sp-error-message');

  if (loader) {
    loader.classList.remove('hidden');
    if (loaderText) {
      loaderText.textContent = `দাগ ${state.context.dag || '৪০২'} এর ক্যাডাস্ট্রাল স্তর লোড হচ্ছে...`;
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

    if (reqSeq !== state.currentRequestSeq) {
      console.log(`[NAKSHA SidePanel] Discarding stale response for request seq #${reqSeq}`);
      return;
    }

    if (layersRes.status !== 'fulfilled' || !layersRes.value.ok) {
      const statusText = layersRes.status === 'fulfilled' ? `HTTP ${layersRes.value.status}` : 'সংযোগ ত্রুটি';
      throw new Error(`ক্যাডাস্ট্রাল স্তর লোড করা যায়নি (${statusText})।`);
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

    // Render All Modern Components
    renderAllComponents(verifData, layersData, conflictData, neighborsData, ledgerData, integData);

    if (loader) loader.classList.add('hidden');
    if (state.map) {
      setTimeout(() => state.map.invalidateSize(), 60);
    }
  } catch (err) {
    clearTimeout(timeoutId);
    if (reqSeq !== state.currentRequestSeq) return;

    console.error('[NAKSHA SidePanel] Fetch failed:', err);
    if (loader) loader.classList.add('hidden');
    if (errorEl) {
      errorEl.classList.remove('hidden');
      if (errorMsg) {
        errorMsg.textContent = err.name === 'AbortError'
          ? 'সার্ভার সংযোগে অতিরিক্ত সময় নিচ্ছে (টাইমআউট)।'
          : (err.message || 'স্প্যাশিয়াল সার্ভার সংযোগ বিচ্ছিন্ন।');
      }
    }
  }
}

// 7. Render All Modular Components
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
  let summaryLine = '';
  const chips = [];

  if (verdict === 'CLEAR') {
    summaryLine = isEn ? 'All titles, boundaries & taxes verified with zero discrepancies.' : 'মৌজা কাশিমপুর, দাগ ৪০১ এর সকল রেকর্ড, সীমানা ও কর পরিশোধিত।';
    chips.push({ label: isEn ? '✓ Title Clean' : '✓ স্বত্ব নির্ভুল', color: 'var(--status-clear)', target: 'rule_area' });
    chips.push({ label: isEn ? '✓ Tax Paid' : '✓ কর পরিশোধিত', color: 'var(--status-clear)', target: 'tab-tax' });
  } else if (verdict === 'REVIEW') {
    summaryLine = isEn ? 'Unmutated deed notice & 3 years of land tax in arrears.' : 'নামজারিহীন দলিল ও বিগত ৩ অর্থবছরের ভূমি উন্নয়ন কর বকেয়া।';
    chips.push({ label: isEn ? '⚠ Unmutated 124d' : '⚠ নামজারিহীন ১২৪ দিন', color: 'var(--status-review)', target: 'rule_mutation' });
    chips.push({ label: isEn ? '⚠ Arrears × 3 Yrs' : '⚠ বকেয়া কর ৩ অর্থবছর', color: 'var(--status-review)', target: 'tab-tax' });
    chips.push({ label: isEn ? '⚠ Class Mismatch' : '⚠ শ্রেণি অমিল', color: 'var(--status-review)', target: 'rule_class' });
  } else {
    summaryLine = isEn ? '0.90 dec Khas canal encroachment & paper claim exceeds field survey.' : '০.৯০ শতক সরকারি খাস খাল দখল ও ৬.০০ শতক দলিলে অতিরিক্ত দাবি।';
    chips.push({ label: isEn ? '🚨 Khas Overlap 0.9 dec' : '🚨 সরকারি খাল দখল ০.৯০ শতক', color: 'var(--status-block)', target: 'conflict_zone' });
    chips.push({ label: isEn ? '🚨 Deficit 0.90 dec' : '🚨 জমির ঘাটতি ০.৯০ শতক', color: 'var(--status-block)', target: 'rule_area' });
    chips.push({ label: isEn ? '🚨 Mutation On Hold' : '🚨 নামজারি সাময়িক স্থগিত', color: 'var(--status-block)', target: 'rule_mutation' });
  }

  renderVerdictHero(vContainer, {
    verdict: verdict,
    summary: summaryLine,
    hasKhasOverlap,
    hasAreaMismatch,
    hasUnmutated,
    hasClassConflict,
    hasOwnerMismatch,
    chips: chips,
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

  renderAreaChart(chartContainer, {
    csArea,
    deedArea,
    dlrsArea,
    conflictArea,
  });

  // C. RuleGrid (Tab 1)
  const rulesContainer = document.getElementById('overview-rules-container');
  renderRuleGrid(rulesContainer, {
    hasKhasOverlap,
    hasAreaMismatch,
    hasUnmutated,
    hasClassConflict,
    hasOwnerMismatch,
    areaDeficit: hasAreaMismatch ? '0.90' : '0.01',
    unmutatedDays: hasUnmutated ? 124 : 0,
    ownerScore: hasOwnerMismatch ? 64 : 98,
    classConflict: hasClassConflict,
  });

  // D. LineageTimeline (Tab 2)
  const lineageContainer = document.getElementById('history-lineage-container');
  renderLineageTimeline(lineageContainer, {
    dag: cleanDag,
    nameMatchScore: hasOwnerMismatch ? 64 : 98,
  });

  // E. TaxChart (Tab 3)
  const taxContainer = document.getElementById('tax-chart-container');
  const neighborsList = neighborsData?.features?.map(f => {
    const p = f.properties || {};
    return {
      dag: p.dag_number,
      khatian: p.khatian_number,
      owner: p.owner_name,
      payer: p.dag_number === '403' ? 'অজ্ঞাত করদাতা (Unknown)' : p.owner_name,
      status: p.tax_status,
      area: String(p.area_decimals || '5.0'),
      mismatch: p.dag_number === '403',
    };
  }) || [];
  renderTaxChart(taxContainer, { neighbors: neighborsList });

  // F. LienTimeline (Tab 4)
  const liensContainer = document.getElementById('liens-timeline-container');
  renderLienTimeline(liensContainer, { liens: [] });

  // G. AuditChain (Tab 5)
  const auditContainer = document.getElementById('audit-chain-container');
  renderAuditChain(auditContainer, ledgerData, integData);
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

// 8. Chip Click to Highlight Feature on Map or Open Tab
function handleChipClickHighlight(targetKey) {
  if (!targetKey) return;

  if (targetKey === 'conflict_zone') {
    if (state.conflictBounds && state.map) {
      state.map.fitBounds(state.conflictBounds, { padding: [40, 40] });
    }
  } else if (targetKey.startsWith('tab-')) {
    const tabBtn = document.querySelector(`.sp-tab-btn[data-tab="${targetKey}"]`);
    if (tabBtn) tabBtn.click();
  } else if (targetKey.startsWith('rule_')) {
    const tabOverviewBtn = document.querySelector('.sp-tab-btn[data-tab="tab-overview"]');
    if (tabOverviewBtn) tabOverviewBtn.click();
    const ruleCard = document.querySelector(`.rule-card[data-rule-id="${targetKey}"]`);
    if (ruleCard) {
      ruleCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
      ruleCard.click();
    }
  }
}

// 9. Render Layers on Leaflet Map
function renderLayers(layerSnapshots) {
  if (!state.map) return;

  Object.values(state.layers).forEach((layer) => {
    try { state.map.removeLayer(layer); } catch (e) {}
  });
  state.layers = {};

  let boundsToFit = null;

  layerSnapshots.forEach((snapshot) => {
    const type = snapshot.layer_type;
    const styleCfg = LAYER_CONFIG[type] || {
      color: '#94a3b8',
      fillColor: '#94a3b8',
      weight: 2,
      fillOpacity: 0.2,
      name: snapshot.layer_name,
    };

    try {
      const isConflict = (type === 'conflict_zone');
      const geoLayer = L.geoJSON(snapshot.geometry, {
        style: {
          color: styleCfg.color,
          weight: isConflict ? 3 : styleCfg.weight,
          dashArray: styleCfg.dashArray || (isConflict ? '4, 4' : null),
          fillColor: styleCfg.fillColor,
          fillOpacity: isConflict ? 0.65 : styleCfg.fillOpacity,
        },
        onEachFeature: (feature, layer) => {
          if (isConflict) {
            // Label conflict zone on map directly
            layer.bindTooltip("0.90 dec overlap", {
              permanent: true,
              direction: 'center',
              className: 'conflict-hatched-label',
            });
          }
          layer.bindPopup(`
            <div style="font-family: var(--font-bn); font-size: 11.5px; line-height: 1.4; color: #0B1220;">
              <strong style="color: ${styleCfg.color}; font-size: 12.5px;">${styleCfg.name}</strong><br/>
              ${snapshot.properties?.description || ''}<br/>
              ${snapshot.properties?.area_in_decimals ? `<strong>পরিমাপ:</strong> ${snapshot.properties.area_in_decimals} শতক` : ''}
            </div>
          `);
        },
      });

      if (state.layerVisibility[type] !== false) {
        geoLayer.addTo(state.map);
      }
      state.layers[type] = geoLayer;

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

  if (boundsToFit && state.map) {
    state.map.fitBounds(boundsToFit, { padding: [35, 35] });
  }
}

// 10. Floating Pill Layer Toggles
function initLayerPillToggles() {
  const pills = document.querySelectorAll('.sp-pill-toggle');
  pills.forEach((pill) => {
    pill.addEventListener('click', () => {
      const type = pill.dataset.layerType;
      const isCurrentlyActive = pill.classList.contains('active');
      const newActive = !isCurrentlyActive;
      pill.classList.toggle('active', newActive);

      state.layerVisibility[type] = newActive;
      const layer = state.layers[type];
      if (layer && state.map) {
        if (newActive) {
          state.map.addLayer(layer);
        } else {
          state.map.removeLayer(layer);
        }
      }
    });
  });
}

// 11. Recenter & Action Buttons
function setupActionButtons() {
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
      if (state.map) {
        state.map.setView([23.98506, 90.35035], 19);
      }
    });
  }

  const retryBtn = document.getElementById('sp-retry-btn');
  if (retryBtn) {
    retryBtn.addEventListener('click', () => {
      loadPlotData(state.activeParcelId);
    });
  }
}
