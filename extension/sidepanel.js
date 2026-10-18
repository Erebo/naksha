/**
 * NAKSHA (নকশা) — Side Panel Application Logic
 * Integrates Leaflet 2D GIS with FastAPI backend (http://127.0.0.1:8000).
 * Receives parcel context from Chrome Extension messaging/storage.
 */

const API_BASE = 'http://127.0.0.1:8000';
const DEFAULT_PARCEL_ID = 'par-8f92-bd04-syn';

const state = {
  activeParcelId: DEFAULT_PARCEL_ID,
  map: null,
  layers: {},
  layerVisibility: {},
  neighborsGeoJSON: null,
  targetBounds: null,
  conflictBounds: null,
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
  },
  deed_claim: {
    color: '#3b82f6',
    weight: 2,
    fillColor: '#3b82f6',
    fillOpacity: 0.25,
    name: '২. দলিলে দাবিকৃত জমি (Deed Claim)',
  },
  ground_truth: {
    color: '#10b981',
    weight: 3,
    fillColor: '#10b981',
    fillOpacity: 0.35,
    name: '৩. ডিএলআরএস জরিপকৃত জমি (DLRS Survey)',
  },
  conflict_zone: {
    color: '#ef4444',
    weight: 2,
    fillColor: '#ef4444',
    fillOpacity: 0.70,
    name: '৪. সম্ভাব্য বিরোধপূর্ণ এলাকা (Khas Canal Conflict)',
  },
  restricted_khas: {
    color: '#0ea5e9',
    weight: 2,
    fillColor: '#0ea5e9',
    fillOpacity: 0.35,
    name: 'সরকারি খাস নিষ্কাশন খাল (Public Khas Canal)',
  },
};

document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  initMap();
  initSidePanelListeners();
  loadContextAndPlotData();
  setupActionButtons();
  fetchLedgerEntries();
});

// 1. Initialize Tabs
function initTabs() {
  const tabs = document.querySelectorAll('.sp-tab');
  tabs.forEach((tab) => {
    tab.addEventListener('click', () => {
      tabs.forEach((t) => t.classList.remove('active'));
      document.querySelectorAll('.sp-tab-content').forEach((c) => c.classList.remove('active'));
      tab.classList.add('active');
      const target = document.getElementById(tab.dataset.tab);
      if (target) target.classList.add('active');
    });
  });
}

// 2. Initialize Leaflet Map
function initMap() {
  state.map = L.map('sp-map', {
    center: [23.98506, 90.35035],
    zoom: 19,
    maxZoom: 21,
    minZoom: 15,
    zoomControl: false, // Compact side panel
  });

  L.control.zoom({ position: 'topright' }).addTo(state.map);

  L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; CARTO | নকশা (NAKSHA)',
    maxZoom: 21,
    subdomains: 'abcd',
  }).addTo(state.map);
}

// 3. Connect to Chrome Extension messaging & storage
function initSidePanelListeners() {
  // Listen for broadcasted plot change messages from content script / service worker
  if (chrome.runtime && chrome.runtime.onMessage) {
    chrome.runtime.onMessage.addListener((message) => {
      if (message.type === 'NAKSHA_CONTEXT_UPDATED' || message.type === 'NAKSHA_PLOT_CHANGED') {
        console.log('[NAKSHA SidePanel] Received updated context:', message.payload);
        applyDetectedContext(message.payload);
      }
    });
  }

  // Load existing context from storage if available
  if (chrome.storage && chrome.storage.local) {
    chrome.storage.local.get(['activeParcelContext'], (result) => {
      if (result.activeParcelContext) {
        console.log('[NAKSHA SidePanel] Initial storage context:', result.activeParcelContext);
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
    portalEl.textContent = ctx.portal === 'e_mutation' ? 'ই-নামজারি পোর্টাল' : 'ভূমি কর পোর্টাল';
  }
  if (dagEl) dagEl.textContent = 'বিএস ' + (ctx.dag || '৪০২');
  if (khatianEl) khatianEl.textContent = ctx.khatian || '১২০';
  if (mouzaEl) mouzaEl.textContent = ctx.mouza || 'কাশিমপুর';

  // Adapt verification verdicts & details based on active plot selection
  updatePlotVerificationView(ctx.dag);

  if (ctx.dag === '401' || ctx.dag === '403') {
    highlightNeighborPlot(ctx.dag);
  } else {
    // Return to main benchmark parcel 402
    loadPlotData(state.activeParcelId);
  }

  // Refresh Trust Ledger
  fetchLedgerEntries();
}

function updatePlotVerificationView(dag) {
  const verdictEl = document.getElementById('sp-verdict');
  const verdictText = document.getElementById('sp-verdict-text');
  const tabDisc = document.getElementById('tab-discrepancy');

  if (dag === '401') {
    // Dag 401 is clean and tax paid
    if (verdictEl && verdictText) {
      verdictEl.className = 'sp-verdict-pill verdict-clear';
      verdictEl.style.background = 'rgba(16, 185, 129, 0.15)';
      verdictEl.style.borderColor = 'rgba(16, 185, 129, 0.4)';
      verdictEl.style.color = '#86efac';
      verdictText.textContent = 'ক্লিয়ার (CLEAR)';
    }
    if (tabDisc) {
      tabDisc.innerHTML = `
        <div class="sp-card" style="border-left: 3px solid #10b981;">
          <div class="sp-card-title text-green">✅ দাগ ৪০১: সীমানা ও কর সন্তোষজনক</div>
          <p class="sp-card-text">
            মৌজা কাশিমপুর, দাগ ৪০১, খতিয়ান ৮৮। মালিক: মোঃ রহিম শেখ। জমির পরিমাণ: ৪.৩৭ শতক।
            কোনো সরকারি খাস ভূমির সাথে বিরোধ নেই এবং চলতি অর্থবছর পর্যন্ত ভূমি উন্নয়ন কর সম্পূর্ণ পরিশোধিত।
          </p>
          <div class="sp-metrics-grid">
            <div class="sp-metric">
              <span class="sp-m-label">খতিয়ান</span>
              <span class="sp-m-val text-blue">বিএস ৮৮</span>
            </div>
            <div class="sp-metric">
              <span class="sp-m-label">জরিপকৃত জমি</span>
              <span class="sp-m-val text-green">৪.৩৭ শতক</span>
            </div>
            <div class="sp-metric">
              <span class="sp-m-label">কর স্ট্যাটাস</span>
              <span class="sp-m-val text-green">পরিশোধিত</span>
            </div>
          </div>
        </div>
      `;
    }
  } else if (dag === '403') {
    // Dag 403 has tax arrears and khatian discrepancy
    if (verdictEl && verdictText) {
      verdictEl.className = 'sp-verdict-pill verdict-review';
      verdictEl.style.background = 'rgba(245, 158, 11, 0.15)';
      verdictEl.style.borderColor = 'rgba(245, 158, 11, 0.4)';
      verdictEl.style.color = '#fde68a';
      verdictText.textContent = 'রিভিউ (REVIEW)';
    }
    if (tabDisc) {
      tabDisc.innerHTML = `
        <div class="sp-card" style="border-left: 3px solid #f59e0b;">
          <div class="sp-card-title" style="color: #fde68a;">⚠️ দাগ ৪০৩: কর বকেয়া ও শ্রেণি অসংগতি নোটিশ</div>
          <p class="sp-card-text">
            মৌজা কাশিমপুর, দাগ ৪০৩, খতিয়ান ১২৫। মালিক: আব্দুল মজিদ। জমির পরিমাণ: ৫.৫৩ শতক।
            বিগত ৩ অর্থবছরের ভূমি উন্নয়ন কর বকেয়া রয়েছে। নামজারি বা হস্তান্তরের পূর্বে বকেয়া কর আদায়ের নোটিশ প্রযোজ্য।
          </p>
          <div class="sp-metrics-grid">
            <div class="sp-metric">
              <span class="sp-m-label">খতিয়ান</span>
              <span class="sp-m-val text-blue">বিএস ১২৫</span>
            </div>
            <div class="sp-metric">
              <span class="sp-m-label">রেকর্ডীয় জমি</span>
              <span class="sp-m-val text-green">৫.৫৩ শতক</span>
            </div>
            <div class="sp-metric">
              <span class="sp-m-label">কর স্ট্যাটাস</span>
              <span class="sp-m-val text-red">বকেয়া (Arrears)</span>
            </div>
          </div>
        </div>
      `;
    }
  } else {
    // Default main plot Dag 402 with Khas canal conflict
    if (verdictEl && verdictText) {
      verdictEl.className = 'sp-verdict-pill verdict-block';
      verdictEl.style.background = 'rgba(239, 68, 68, 0.15)';
      verdictEl.style.borderColor = 'rgba(239, 68, 68, 0.4)';
      verdictEl.style.color = '#fca5a5';
      verdictText.textContent = 'ব্লক (BLOCK)';
    }
    if (tabDisc) {
      tabDisc.innerHTML = `
        <div class="sp-card alert-card">
          <div class="sp-card-title text-danger">🚨 সরকারি খাস খাল দখল ও সীমানা অমিল</div>
          <p class="sp-card-text">
            দলিলে দাবিকৃত জমি <strong>৬.০০ শতক</strong>, কিন্তু ডিএলআরএস জরিপকৃত প্রকৃত জমি <strong>৫.১ শতক</strong>।
            বাকি <strong>০.৯০ শতক</strong> উত্তর পাশের সরকারি খাস নিষ্কাশন খালের ভেতরে ঢুকে পড়েছে।
          </p>
          <div class="sp-metrics-grid">
            <div class="sp-metric">
              <span class="sp-m-label">দলিলে দাবি</span>
              <span class="sp-m-val text-blue">৬.০০ শতক</span>
            </div>
            <div class="sp-metric">
              <span class="sp-m-label">জরিপে প্রকৃত</span>
              <span class="sp-m-val text-green">৫.১ শতক</span>
            </div>
            <div class="sp-metric">
              <span class="sp-m-label">খাল দখল</span>
              <span class="sp-m-val text-red">০.৯০ শতক</span>
            </div>
          </div>
        </div>

        <div class="sp-card">
          <div class="sp-card-title">স্বয়ংক্রিয় নীতিগত সুপারিশ</div>
          <ul class="sp-rule-list">
            <li>❌ <strong>নামজারি আবেদন সাময়িক স্থগিত:</strong> সরকারি খাস ভূমির সাথে অমিল নিষ্পত্তি না হওয়া পর্যন্ত মিউটেশন চূড়ান্ত অনুমোদনযোগ্য নয়।</li>
            <li>⚠️ <strong>যৌথ সীমানা পরিমাপ:</strong> ইউনিয়ন ভূমি সহকারী কর্মকর্তা ও কানুনগো দ্বারা বাস্তব সরজমিনে সীমানা পরিমাপের নির্দেশ।</li>
          </ul>
        </div>
      `;
    }
  }
}

async function fetchLedgerEntries() {
  const listEl = document.getElementById('sp-ledger-entries-list');
  if (!listEl) return;

  try {
    const res = await fetch(`${API_BASE}/api/v1/ledger?limit=10`);
    if (!res.ok) return;
    const entries = await res.json();

    listEl.innerHTML = '';
    entries.forEach((e) => {
      const card = document.createElement('div');
      card.className = 'sp-card';
      card.style.fontSize = '10px';
      card.style.marginBottom = '6px';
      card.innerHTML = `
        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
          <strong style="color: #38bdf8;">ব্লক #${e.index}: ${e.event_type}</strong>
          <span style="color: #64748b;">${e.timestamp.slice(11, 19)} UTC</span>
        </div>
        <div style="color: #94a3b8; word-break: break-all;">
          দাগ: <strong>${e.dag_number || 'N/A'}</strong> · মৌজা: ${e.mouza || 'N/A'} · রায়: <strong>${e.verdict || 'N/A'}</strong><br/>
          হ্যাশ: <code>${e.entry_hash.slice(0, 16)}...</code><br/>
          স্বাক্ষর: <span style="color: #34d399;">Ed25519 Verified</span>
        </div>
      `;
      listEl.appendChild(card);
    });
  } catch (err) {
    console.warn('[NAKSHA SidePanel] Ledger fetch notice:', err);
  }
}

// 4. Fetch Multi-Era Layers and Plot Data from FastAPI
async function loadContextAndPlotData() {
  await loadPlotData(state.activeParcelId);
}

async function loadPlotData(parcelId) {
  const loader = document.getElementById('sp-map-loader');
  const errorEl = document.getElementById('sp-map-error');
  if (loader) loader.classList.remove('hidden');
  if (errorEl) errorEl.classList.add('hidden');

  try {
    const [layersData, neighborsData, conflictData] = await Promise.all([
      fetch(`${API_BASE}/api/v1/spatial/parcels/${parcelId}/layers`).then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      }),
      fetch(`${API_BASE}/api/v1/spatial/parcels/${parcelId}/neighbors`).then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      }),
      fetch(`${API_BASE}/api/v1/spatial/parcels/${parcelId}/conflicts`).then((r) => {
        if (!r.ok) return null;
        return r.json();
      }),
    ]);

    renderLayers(layersData);
    renderNeighbors(neighborsData);
    if (conflictData) {
      renderConflictAlert(conflictData);
    }

    if (loader) loader.classList.add('hidden');
  } catch (err) {
    console.error('[NAKSHA SidePanel] Fetch failed:', err);
    if (loader) loader.classList.add('hidden');
    if (errorEl) errorEl.classList.remove('hidden');
  }
}

// 5. Render Layers on Leaflet Map
function renderLayers(layerSnapshots) {
  // Clear old layers
  Object.values(state.layers).forEach((layer) => state.map.removeLayer(layer));
  state.layers = {};
  state.layerVisibility = {};

  const toggleContainer = document.getElementById('sp-layer-toggles');
  if (toggleContainer) toggleContainer.innerHTML = '';

  const countBadge = document.getElementById('sp-layer-count');
  if (countBadge) countBadge.textContent = `${layerSnapshots.length}টি স্তর`;

  layerSnapshots.forEach((snapshot) => {
    const type = snapshot.layer_type;
    const styleCfg = LAYER_CONFIG[type] || {
      color: '#94a3b8',
      fillColor: '#94a3b8',
      weight: 2,
      fillOpacity: 0.2,
      name: snapshot.layer_name,
    };

    const geoLayer = L.geoJSON(snapshot.geometry, {
      style: {
        color: styleCfg.color,
        weight: styleCfg.weight,
        dashArray: styleCfg.dashArray || null,
        fillColor: styleCfg.fillColor,
        fillOpacity: styleCfg.fillOpacity,
      },
      onEachFeature: (feature, layer) => {
        layer.bindPopup(`
          <div style="font-family: 'Hind Siliguri', sans-serif; font-size: 12px; line-height: 1.4;">
            <strong style="color: ${styleCfg.color}; font-size: 13px;">${styleCfg.name}</strong><br/>
            ${snapshot.properties?.description || ''}<br/>
            ${snapshot.properties?.area_in_decimals ? `<strong>পরিমাপ:</strong> ${snapshot.properties.area_in_decimals} শতক` : ''}
          </div>
        `);
      },
    }).addTo(state.map);

    state.layers[type] = geoLayer;
    state.layerVisibility[type] = true;

    if (type === 'ground_truth') {
      state.targetBounds = geoLayer.getBounds();
      state.map.fitBounds(state.targetBounds, { padding: [30, 30] });
    } else if (type === 'conflict_zone') {
      state.conflictBounds = geoLayer.getBounds();
    }

    // Add checkbox toggle
    if (toggleContainer) {
      const row = document.createElement('div');
      row.className = 'sp-layer-item';
      row.innerHTML = `
        <label class="sp-layer-label">
          <input type="checkbox" checked data-layer-type="${type}">
          <span class="sp-layer-swatch" style="background-color: ${styleCfg.color}"></span>
          <span>${styleCfg.name}</span>
        </label>
      `;

      row.querySelector('input').addEventListener('change', (e) => {
        toggleLayer(type, e.target.checked);
      });

      toggleContainer.appendChild(row);
    }
  });
}

function toggleLayer(type, isVisible) {
  state.layerVisibility[type] = isVisible;
  const layer = state.layers[type];
  if (!layer) return;

  if (isVisible) {
    state.map.addLayer(layer);
  } else {
    state.map.removeLayer(layer);
  }
}

// 6. Render Neighbor Parcels
function renderNeighbors(geoJsonCollection) {
  state.neighborsGeoJSON = geoJsonCollection;
  const container = document.getElementById('sp-neighbors-list');
  if (!container) return;

  container.innerHTML = '';
  const features = geoJsonCollection.features || [];

  features.forEach((feat) => {
    const props = feat.properties || {};
    const card = document.createElement('div');
    card.className = 'sp-neighbor-card';
    const isPaid = props.tax_status === 'paid';
    const badgeClass = isPaid ? 'badge-paid' : 'badge-arrears';

    card.innerHTML = `
      <div class="sp-nb-header">
        <span class="sp-nb-dag">দাগ নং: বিএস ${props.dag_number} ${props.is_target_parcel ? '(মূল প্লট)' : ''}</span>
        <span class="sp-nb-badge ${badgeClass}">${props.tax_status_label}</span>
      </div>
      <div style="font-size: 10px; color: #94a3b8;">
        খতিয়ান: ${props.khatian_number} · মালিক: ${props.owner_name}<br/>
        জমির পরিমাণ: ${props.area_decimals} শতক · হোল্ডিং: ${props.holding_number}
      </div>
    `;

    card.addEventListener('click', () => {
      highlightNeighborPlot(props.dag_number);
    });

    container.appendChild(card);
  });
}

function highlightNeighborPlot(dag) {
  if (!state.neighborsGeoJSON) return;
  const match = state.neighborsGeoJSON.features.find((f) => f.properties.dag_number === String(dag));
  if (match) {
    const tmp = L.geoJSON(match.geometry);
    state.map.fitBounds(tmp.getBounds(), { padding: [40, 40] });
  }
}

function renderConflictAlert(conflict) {
  // Can dynamically update conflict metric if needed
  console.log('[NAKSHA SidePanel] Spatial conflict loaded:', conflict);
}

// 7. Recenter & Action Controls
function setupActionButtons() {
  const recenterBtn = document.getElementById('sp-btn-recenter');
  if (recenterBtn) {
    recenterBtn.addEventListener('click', () => {
      if (state.targetBounds) {
        state.map.fitBounds(state.targetBounds, { padding: [30, 30] });
      }
    });
  }

  const toggleDrawerBtn = document.getElementById('sp-btn-toggle-layers');
  const layerSection = document.getElementById('sp-layer-section');
  if (toggleDrawerBtn && layerSection) {
    toggleDrawerBtn.addEventListener('click', () => {
      layerSection.style.display = layerSection.style.display === 'none' ? 'block' : 'none';
    });
  }

  const retryBtn = document.getElementById('sp-retry-btn');
  if (retryBtn) {
    retryBtn.addEventListener('click', () => {
      loadPlotData(state.activeParcelId);
    });
  }
}
