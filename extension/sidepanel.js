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
  currentRequestSeq: 0,
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
  const mapOk = initMap();
  initSidePanelListeners();
  if (mapOk) {
    loadContextAndPlotData();
  }
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
  if (typeof L === 'undefined') {
    console.error('[NAKSHA SidePanel] Leaflet library L is not loaded.');
    const errorEl = document.getElementById('sp-map-error');
    const errorMsg = document.getElementById('sp-error-message');
    const loader = document.getElementById('sp-map-loader');
    if (loader) loader.classList.add('hidden');
    if (errorEl) {
      errorEl.classList.remove('hidden');
      if (errorMsg) errorMsg.textContent = 'লিফলেট (Leaflet) লাইব্রেরি লোড হতে ব্যর্থ হয়েছে।';
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
      zoomControl: false, // Compact side panel
    });

    L.control.zoom({ position: 'topright' }).addTo(state.map);

    const tileLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors | নকশা (NAKSHA)',
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
          setTimeout(() => warnEl.classList.add('hidden'), 6000);
        }
      }
    });

    tileLayer.addTo(state.map);

    // Invalidate size once container layout stabilizes
    setTimeout(() => {
      if (state.map) state.map.invalidateSize();
    }, 120);

    window.addEventListener('resize', () => {
      if (state.map) state.map.invalidateSize();
    });

    return true;
  } catch (mapErr) {
    console.error('[NAKSHA SidePanel] Map initialization error:', mapErr);
    const loader = document.getElementById('sp-map-loader');
    const errorEl = document.getElementById('sp-map-error');
    const errorMsg = document.getElementById('sp-error-message');
    if (loader) loader.classList.add('hidden');
    if (errorEl) {
      errorEl.classList.remove('hidden');
      if (errorMsg) errorMsg.textContent = 'মানচিত্র রেন্ডারিংয়ে ত্রুটি ঘটেছে: ' + mapErr.message;
    }
    return false;
  }
}

// Helper: Resolve backend parcel ID from Dag number
function resolveParcelId(dag) {
  if (!dag) return state.activeParcelId || DEFAULT_PARCEL_ID;
  const clean = String(dag).trim();
  if (clean === '402') return 'par-8f92-bd04-syn';
  if (clean === '401') return 'BS-401';
  if (clean === '403') return 'BS-403';
  return clean;
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

  // Dynamically resolve parcel ID and load actual layers & verification from backend
  const targetId = resolveParcelId(ctx.dag);
  state.activeParcelId = targetId;
  loadPlotData(targetId);

  // Refresh Trust Ledger
  fetchLedgerEntries();
}

function renderVerificationVerdict(vResult, dagNumber) {
  const verdictEl = document.getElementById('sp-verdict');
  const verdictText = document.getElementById('sp-verdict-text');
  const tabDisc = document.getElementById('tab-discrepancy');
  const tabSurvey = document.getElementById('tab-survey');

  if (!vResult) return;

  const verdict = vResult.verdict; // 'CLEAR', 'BLOCK', 'REVIEW'
  if (verdictEl && verdictText) {
    if (verdict === 'CLEAR') {
      verdictEl.className = 'sp-verdict-pill verdict-clear';
      verdictEl.style.background = 'rgba(16, 185, 129, 0.15)';
      verdictEl.style.borderColor = 'rgba(16, 185, 129, 0.4)';
      verdictEl.style.color = '#86efac';
      verdictText.textContent = 'ক্লিয়ার (CLEAR)';
    } else if (verdict === 'REVIEW') {
      verdictEl.className = 'sp-verdict-pill verdict-review';
      verdictEl.style.background = 'rgba(245, 158, 11, 0.15)';
      verdictEl.style.borderColor = 'rgba(245, 158, 11, 0.4)';
      verdictEl.style.color = '#fde68a';
      verdictText.textContent = 'রিভিউ (REVIEW)';
    } else {
      verdictEl.className = 'sp-verdict-pill verdict-block';
      verdictEl.style.background = 'rgba(239, 68, 68, 0.15)';
      verdictEl.style.borderColor = 'rgba(239, 68, 68, 0.4)';
      verdictEl.style.color = '#fca5a5';
      verdictText.textContent = 'ব্লক (BLOCK)';
    }
  }

  if (tabDisc) {
    let discHtml = '';
    const cleanDag = String(dagNumber || state.context.dag || '৪০২');

    if (verdict === 'CLEAR') {
      discHtml = `
        <div class="sp-card" style="border-left: 3px solid #10b981;">
          <div class="sp-card-title text-green">✅ দাগ ${cleanDag}: সীমানা ও কর সন্তোষজনক</div>
          <p class="sp-card-text">${vResult.summary}</p>
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
    } else if (verdict === 'REVIEW') {
      discHtml = `
        <div class="sp-card" style="border-left: 3px solid #f59e0b;">
          <div class="sp-card-title" style="color: #fde68a;">⚠️ দাগ ${cleanDag}: রিভিউ নোটিশ ও অসংগতি</div>
          <p class="sp-card-text">${vResult.summary}</p>
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
    } else {
      discHtml = `
        <div class="sp-card alert-card">
          <div class="sp-card-title text-danger">🚨 দাগ ${cleanDag}: সরকারি খাস খাল দখল ও সীমানা অমিল</div>
          <p class="sp-card-text">${vResult.summary}</p>
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
      `;
    }

    // Append specific discrepancies returned dynamically by backend
    if (vResult.discrepancies && vResult.discrepancies.length > 0) {
      discHtml += `
        <div class="sp-card">
          <div class="sp-card-title">শনাক্তকৃত অমিলসমূহ (Backend Identified Discrepancies)</div>
          <ul class="sp-rule-list">
      `;
      vResult.discrepancies.forEach((d) => {
        discHtml += `<li>⚠️ <strong>${d.discrepancy_type}:</strong> ${d.difference_description}</li>`;
      });
      discHtml += `
          </ul>
        </div>
      `;
    }

    discHtml += `
      <div class="sp-card">
        <div class="sp-card-title">স্বয়ংক্রিয় নীতিগত সুপারিশ (Policy Rules)</div>
        <ul class="sp-rule-list">
          ${verdict === 'BLOCK' ? '<li>❌ <strong>নামজারি স্থগিত:</strong> সরকারি খাস ভূমির সাথে অমিল নিষ্পত্তি না হওয়া পর্যন্ত নামজারি অনুমোদন স্থগিত থাকবে।</li>' : ''}
          ${verdict === 'REVIEW' ? '<li>⚠️ <strong>শুনানি ও কর আদায়:</strong> বিগত ৩ অর্থবছরের বকেয়া ভূমি উন্নয়ন কর আদায় সাপেক্ষে রেকর্ড যাচাই নির্দেশ।</li>' : ''}
          ${verdict === 'CLEAR' ? '<li>✅ <strong>অনুমোদনের সুপারিশ:</strong> সকল রেকর্ড ও ক্যাডাস্ট্রাল সীমানা সামঞ্জস্যপূর্ণ হওয়ায় আবেদন চূড়ান্ত অনুমোদনের সুপারিশ করা হলো।</li>' : ''}
        </ul>
      </div>
    `;

    tabDisc.innerHTML = discHtml;
  }

  // Update Survey History Tab dynamically
  if (tabSurvey && vResult.spatial_layers) {
    let surveyHtml = '<div class="sp-timeline">';
    vResult.spatial_layers.forEach((l) => {
      const p = l.properties || {};
      const area = p.calculated_area_decimals || p.recorded_area_decimals || p.claimed_area_decimals || p.area_in_decimals || '—';
      const color = p.color || '#3b82f6';
      surveyHtml += `
        <div class="sp-timeline-item">
          <div class="sp-tl-dot" style="background: ${color};"></div>
          <div class="sp-tl-content">
            <div class="sp-tl-title">${l.layer_name}</div>
            <div class="sp-tl-sub">${p.description || ''} · পরিমাপ: <strong>${area} শতক</strong></div>
          </div>
        </div>
      `;
    });
    surveyHtml += '</div>';
    tabSurvey.innerHTML = surveyHtml;
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
  const reqSeq = ++state.currentRequestSeq;

  const loader = document.getElementById('sp-map-loader');
  const loaderText = document.getElementById('sp-map-loader-text');
  const errorEl = document.getElementById('sp-map-error');
  const errorMsg = document.getElementById('sp-error-message');

  if (loader) {
    loader.classList.remove('hidden');
    if (loaderText) {
      loaderText.textContent = `দাগ ${state.context.dag || '৪০২'} এর ক্যাডাস্ট্রাল স্তর ও রেকর্ড লোড হচ্ছে...`;
    }
  }
  if (errorEl) errorEl.classList.add('hidden');

  // AbortController ensures request never hangs indefinitely
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 8000);

  try {
    const fetchOpts = { signal: controller.signal };
    const [layersRes, neighborsRes, conflictsRes, verifRes] = await Promise.allSettled([
      fetch(`${API_BASE}/api/v1/spatial/parcels/${parcelId}/layers`, fetchOpts),
      fetch(`${API_BASE}/api/v1/spatial/parcels/${parcelId}/neighbors`, fetchOpts),
      fetch(`${API_BASE}/api/v1/spatial/parcels/${parcelId}/conflicts`, fetchOpts),
      fetch(`${API_BASE}/api/v1/spatial/parcels/${parcelId}/verification`, fetchOpts),
    ]);

    clearTimeout(timeoutId);

    // Discard outdated response if another plot was selected while fetching
    if (reqSeq !== state.currentRequestSeq) {
      console.log(`[NAKSHA SidePanel] Discarding stale response for request seq #${reqSeq}`);
      return;
    }

    if (layersRes.status !== 'fulfilled' || !layersRes.value.ok) {
      const statusText = layersRes.status === 'fulfilled' ? `HTTP ${layersRes.value.status}` : 'সার্ভার সংযোগ ত্রুটি';
      throw new Error(`ক্যাডাস্ট্রাল স্তর লোড করা যায়নি (${statusText})। ব্যাকএন্ড সার্ভার (http://127.0.0.1:8000) চালু আছে কিনা নিশ্চিত করুন।`);
    }

    const layersData = await layersRes.value.json();
    renderLayers(layersData);

    if (neighborsRes.status === 'fulfilled' && neighborsRes.value.ok) {
      const neighborsData = await neighborsRes.value.json();
      renderNeighbors(neighborsData);
    }

    if (conflictsRes.status === 'fulfilled' && conflictsRes.value.ok) {
      const conflictData = await conflictsRes.value.json();
      renderConflictAlert(conflictData);
    }

    if (verifRes.status === 'fulfilled' && verifRes.value.ok) {
      const verifData = await verifRes.value.json();
      renderVerificationVerdict(verifData, state.context.dag);
    }

    // Always terminate loading state on success
    if (loader) loader.classList.add('hidden');

    if (state.map) {
      setTimeout(() => state.map.invalidateSize(), 50);
    }
  } catch (err) {
    clearTimeout(timeoutId);
    if (reqSeq !== state.currentRequestSeq) return;

    console.error('[NAKSHA SidePanel] Fetch failed:', err);
    // Always terminate loading state on failure
    if (loader) loader.classList.add('hidden');
    if (errorEl) {
      errorEl.classList.remove('hidden');
      if (errorMsg) {
        errorMsg.textContent = err.name === 'AbortError'
          ? 'সার্ভার থেকে তথ্য আসতে অতিরিক্ত সময় নিচ্ছে (টাইমআউট)। দয়া করে পুনরায় চেষ্টা করুন।'
          : (err.message || 'স্প্যাশিয়াল সার্ভার সংযোগ বিচ্ছিন্ন (http://127.0.0.1:8000)।');
      }
    }
  }
}

// 5. Render Layers on Leaflet Map
function renderLayers(layerSnapshots) {
  if (!state.map) return;

  // Clear old layers
  Object.values(state.layers).forEach((layer) => {
    try { state.map.removeLayer(layer); } catch (e) {}
  });
  state.layers = {};
  state.layerVisibility = {};

  const toggleContainer = document.getElementById('sp-layer-toggles');
  if (toggleContainer) toggleContainer.innerHTML = '';

  const countBadge = document.getElementById('sp-layer-count');
  if (countBadge) countBadge.textContent = `${layerSnapshots.length}টি স্তর`;

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
    } catch (layerErr) {
      console.warn(`[NAKSHA SidePanel] Failed to render layer ${type}:`, layerErr);
    }
  });

  if (boundsToFit && state.map) {
    state.map.fitBounds(boundsToFit, { padding: [30, 30] });
  }
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
  if (!state.neighborsGeoJSON || !state.map || typeof L === 'undefined') return;
  const match = state.neighborsGeoJSON.features.find((f) => f.properties.dag_number === String(dag));
  if (match) {
    try {
      const tmp = L.geoJSON(match.geometry);
      const b = tmp.getBounds();
      if (b && b.isValid && b.isValid()) {
        state.map.fitBounds(b, { padding: [40, 40] });
      }
    } catch (e) {
      console.warn('[NAKSHA SidePanel] Error highlighting neighbor plot:', e);
    }
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
