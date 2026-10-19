/**
 * NAKSHA (নকশা) — 2D GIS Interactive Side Panel Logic
 * Bangla-First Land Cadastral & Survey Reconciliation Engine
 */

// Application State
const state = {
    targetParcelId: 'par-8f92-bd04-syn',
    map: null,
    layers: {},
    layerVisibility: {},
    conflictBounds: null,
    targetBounds: null,
};

// Layer Color & Styling Definitions
const LAYER_STYLES = {
    ancestral_footprint: {
        color: '#8b5cf6',
        weight: 2,
        dashArray: '6, 6',
        fillColor: '#8b5cf6',
        fillOpacity: 0.15,
        name: '১. পূর্ববর্তী সিএস পৈত্রিক সীমানা (CS 88)',
    },
    deed_claim: {
        color: '#3b82f6',
        weight: 2,
        fillColor: '#3b82f6',
        fillOpacity: 0.25,
        name: '২. দলিলে দাবিকৃত সীমানা (Deed Claim)',
    },
    ground_truth: {
        color: '#10b981',
        weight: 3,
        fillColor: '#10b981',
        fillOpacity: 0.35,
        name: '৩. ডিএলআরএস জরিপ নকশা (DLRS Ground Truth)',
    },
    conflict_zone: {
        color: '#ef4444',
        weight: 2,
        fillColor: '#ef4444',
        fillOpacity: 0.70,
        name: '৪. সম্ভাব্য বিরোধপূর্ণ এলাকা (Khas Conflict)',
    },
    restricted_khas: {
        color: '#0ea5e9',
        weight: 2,
        fillColor: '#0ea5e9',
        fillOpacity: 0.35,
        name: 'সরকারি খাস নিষ্কাশন খাল (Public Khas Canal)',
    },
};

// Initialize Application on DOM Ready
document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initMap();
    loadParcelData();
    initActionButtons();
});

// ==============================================================================
// 1. Map Initialization
// ==============================================================================

function initMap() {
    // Initial coordinates set around Kashimpur, Gazipur
    state.map = L.map('map', {
        center: [23.98506, 90.35035],
        zoom: 19,
        maxZoom: 21,
        minZoom: 15,
        zoomControl: true,
    });

    // OpenStreetMap high-reliability cartographic basemap without watermark
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors | নকশা (NAKSHA) LandTech 2026',
        maxZoom: 19,
        subdomains: ['a', 'b', 'c'],
    }).addTo(state.map);
}

// ==============================================================================
// 2. Fetch Data & Build Layers
// ==============================================================================

async function loadParcelData() {
    const loader = document.getElementById('map-loader');
    const errorEl = document.getElementById('map-error');
    loader.classList.remove('hidden');
    errorEl.classList.add('hidden');

    try {
        let token = sessionStorage.getItem('naksha_jwt_token');
        if (!token) {
            const authRes = await fetch('/auth/verify-officer', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    portal_origin: window.location.origin || 'http://127.0.0.1:8000',
                    officer_id: 'UL-2024-KSH',
                    name: 'মোঃ ফজলুর রহমান',
                    designation: 'ইউনিয়ন ভূমি সহকারী কর্মকর্তা',
                }),
            }).then(r => r.json()).catch(() => null);
            if (authRes && authRes.token) {
                token = authRes.token;
                sessionStorage.setItem('naksha_jwt_token', token);
            }
        }

        const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
        const [layersData, neighborsData, conflictData, demoData] = await Promise.all([
            fetch(`/api/v1/spatial/parcels/${state.targetParcelId}/layers`, { headers }).then(r => r.json()),
            fetch(`/api/v1/spatial/parcels/${state.targetParcelId}/neighbors`, { headers }).then(r => r.json()),
            fetch(`/api/v1/spatial/parcels/${state.targetParcelId}/conflicts`, { headers }).then(r => r.json()),
            fetch(`/api/v1/records/demo`, { headers }).then(r => r.json()),
        ]);

        renderSurveyLayers(layersData);
        renderNeighborLayers(neighborsData);
        populateOverview(layersData, conflictData, demoData);
        populateNeighborsTab(neighborsData);
        populateFindings(demoData);

        loader.classList.add('hidden');
    } catch (err) {
        console.error('Failed to load spatial data:', err);
        loader.classList.add('hidden');
        errorEl.classList.remove('hidden');
        document.getElementById('error-message').textContent = 
            `সার্ভারের সাথে সংযোগ স্থাপন করা যায়নি: ${err.message || 'নেটওয়ার্ক ত্রুটি'}`;
    }
}

// ==============================================================================
// 3. Render Multi-Era Survey Layers
// ==============================================================================

function renderSurveyLayers(layers) {
    const toggleContainer = document.getElementById('layer-toggles');
    toggleContainer.innerHTML = '';

    layers.forEach((layerItem, idx) => {
        const layerKey = layerItem.layer_type;
        const style = LAYER_STYLES[layerKey] || {
            color: '#94a3b8',
            weight: 2,
            fillOpacity: 0.2,
            name: layerItem.layer_name,
        };

        // Create Leaflet GeoJSON layer
        const geoLayer = L.geoJSON(layerItem.geometry, {
            style: {
                color: style.color,
                weight: style.weight,
                dashArray: style.dashArray || null,
                fillColor: style.fillColor || style.color,
                fillOpacity: style.fillOpacity,
            },
            onEachFeature: (feature, layer) => {
                const props = layerItem.properties || {};
                const areaDec = props.calculated_area_decimals || props.area_in_decimals || '—';
                const areaSqm = props.calculated_area_sqm || props.area_in_sq_meters || '—';
                
                const popupContent = `
                    <div style="font-family: 'Hind Siliguri', sans-serif; font-size: 13px; line-height: 1.5;">
                        <h4 style="margin: 0 0 6px 0; color: ${style.color}; font-size: 14px; font-weight: 700;">
                            ${layerItem.layer_name}
                        </h4>
                        <table style="width: 100%; border-collapse: collapse; font-size: 12px;">
                            <tr><td style="color: #64748b;">দাগ নম্বর:</td><td><strong>${props.dag_number || '—'}</strong></td></tr>
                            <tr><td style="color: #64748b;">জরিপের যুগ:</td><td><strong>${props.survey_era || '—'}</strong></td></tr>
                            <tr><td style="color: #64748b;">পরিমাপিত আয়তন:</td><td><strong>${areaDec} শতক (${areaSqm} বর্গমি.)</strong></td></tr>
                            <tr><td style="color: #64748b;">বিবরণ:</td><td>${props.description || '—'}</td></tr>
                        </table>
                    </div>
                `;
                layer.bindPopup(popupContent);

                // Track bounds
                if (layerKey === 'ground_truth') {
                    state.targetBounds = layer.getBounds();
                    state.map.fitBounds(state.targetBounds, { padding: [50, 50] });
                } else if (layerKey === 'conflict_zone') {
                    state.conflictBounds = layer.getBounds();
                }
            }
        });

        // Add to map by default
        geoLayer.addTo(state.map);
        state.layers[layerKey] = geoLayer;
        state.layerVisibility[layerKey] = true;

        // Create Layer Control Checkbox
        const row = document.createElement('label');
        row.className = 'layer-checkbox-label';
        row.innerHTML = `
            <input type="checkbox" checked data-layer="${layerKey}">
            <span class="layer-swatch" style="background-color: ${style.color};"></span>
            <span>${style.name}</span>
        `;
        row.querySelector('input').addEventListener('change', (e) => {
            const key = e.target.dataset.layer;
            if (e.target.checked) {
                state.map.addLayer(state.layers[key]);
                state.layerVisibility[key] = true;
            } else {
                state.map.removeLayer(state.layers[key]);
                state.layerVisibility[key] = false;
            }
        });
        toggleContainer.appendChild(row);
    });
}

// ==============================================================================
// 4. Render Neighbor Parcels
// ==============================================================================

function renderNeighborLayers(neighborCollection) {
    if (!neighborCollection || !neighborCollection.features) return;

    const neighborLayer = L.geoJSON(neighborCollection, {
        filter: (feature) => !feature.properties.is_target_parcel,
        style: (feature) => {
            const isPaid = feature.properties.tax_status === 'paid';
            return {
                color: isPaid ? '#10b981' : '#f59e0b',
                weight: 1.5,
                dashArray: '3, 4',
                fillColor: isPaid ? '#10b981' : '#f59e0b',
                fillOpacity: 0.15,
            };
        },
        onEachFeature: (feature, layer) => {
            const p = feature.properties;
            layer.bindPopup(`
                <div style="font-family: 'Hind Siliguri', sans-serif; font-size: 13px;">
                    <h4 style="margin: 0 0 4px 0; color: #38bdf8;">প্রতিবেশী প্লট: দাগ ${p.dag_number}</h4>
                    <p style="margin: 0;"><strong>খতিয়ান:</strong> ${p.khatian_number} | <strong>আয়তন:</strong> ${p.area_decimals} শতক</p>
                    <p style="margin: 4px 0;"><strong>মালিক:</strong> ${p.owner_name}</p>
                    <p style="margin: 0;"><strong>ভূমি কর:</strong> <span style="color: ${p.tax_status === 'paid' ? '#10b981' : '#f59e0b'}; font-weight: bold;">${p.tax_status_label}</span></p>
                </div>
            `);
        }
    });

    neighborLayer.addTo(state.map);
    state.layers['neighbors'] = neighborLayer;
    state.layerVisibility['neighbors'] = true;

    // Add toggle for neighbors
    const toggleContainer = document.getElementById('layer-toggles');
    const row = document.createElement('label');
    row.className = 'layer-checkbox-label';
    row.innerHTML = `
        <input type="checkbox" checked data-layer="neighbors">
        <span class="layer-swatch" style="background-color: #f59e0b;"></span>
        <span>প্রতিবেশী প্লটসমূহ (কর অবস্থা)</span>
    `;
    row.querySelector('input').addEventListener('change', (e) => {
        if (e.target.checked) {
            state.map.addLayer(state.layers['neighbors']);
            state.layerVisibility['neighbors'] = true;
        } else {
            state.map.removeLayer(state.layers['neighbors']);
            state.layerVisibility['neighbors'] = false;
        }
    });
    toggleContainer.appendChild(row);

    document.getElementById('layer-count').textContent = `${Object.keys(state.layers).length}টি স্তর`;
}

// ==============================================================================
// 5. Populate Side Panel Overview & Findings
// ==============================================================================

function populateOverview(layers, conflict, demoData) {
    // Fill area stats
    const deedLayer = layers.find(l => l.layer_type === 'deed_claim');
    const dlrsLayer = layers.find(l => l.layer_type === 'ground_truth');

    if (deedLayer && deedLayer.properties) {
        document.getElementById('stat-recorded-area').textContent = 
            `${deedLayer.properties.claimed_area_decimals.toFixed(2)} শতক`;
    }
    if (dlrsLayer && dlrsLayer.properties) {
        document.getElementById('stat-measured-area').textContent = 
            `${dlrsLayer.properties.calculated_area_decimals.toFixed(2)} শতক`;
    }

    if (conflict) {
        document.getElementById('area-diff-tag').textContent = 
            `ঘাটতি: ${conflict.area_in_decimals.toFixed(2)} শতক`;
    }
}

function populateFindings(demoData) {
    const list = document.getElementById('findings-list');
    list.innerHTML = '';

    // Static explainable findings corresponding to Scenario 3 + Concept Note
    const findings = [
        {
            title: '🛑 সরকারি খাস খাল দখল বিরোধ (Khas Overlap)',
            desc: 'দলিলের দাবিকৃত ৬.০০ শতকের মধ্যে ০.৯০ শতক (৩৬.৪ বর্গমি.) উত্তরদিকের কাশিমপুর সরকারি নিষ্কাশন খালের সীমানার উপর অননুমোদিত বিস্তার ঘটিয়েছে।',
            severity: 'block',
        },
        {
            title: '⚠️ জমির পরিমাণের ঘাটতি (Area Deficit)',
            desc: 'দলিলে দাবিকৃত জমি (৬.০০ শতক) ডিএলআরএস জরিপকৃত প্রকৃত পরিমাপের (৫.১০ শতক) তুলনায় ০.৯০ শতক বেশি, যা সংবিধিবদ্ধ সীমা (±০.২০ শতক) অতিক্রম করেছে।',
            severity: 'block',
        },
        {
            title: '⚠️ নামজারিবিহীন দলিল (Unmutated Deed Hazard)',
            desc: 'সাব-রেজিস্ট্রি অফিসে ১২৪ দিন পূর্বে দলিল সম্পাদিত হলেও সহকারী কমিশনার (ভূমি) অফিসে কোনো ই-নামজারি নথি খোলা হয়নি। দ্বৈত বিক্রয়ের ঝুঁকি বিদ্যমান।',
            severity: 'warning',
        },
    ];

    findings.forEach(f => {
        const item = document.createElement('div');
        item.className = `finding-item ${f.severity === 'warning' ? 'warning' : ''}`;
        item.innerHTML = `
            <div class="finding-title">${f.title}</div>
            <div class="finding-desc">${f.desc}</div>
        `;
        list.appendChild(item);
    });

    document.getElementById('findings-count').textContent = `${findings.length}টি অসংগতি`;
}

function populateNeighborsTab(neighborCollection) {
    const list = document.getElementById('neighbor-list');
    list.innerHTML = '';

    if (!neighborCollection || !neighborCollection.features) return;

    neighborCollection.features.forEach(f => {
        const p = f.properties;
        const isPaid = p.tax_status === 'paid';
        const card = document.createElement('div');
        card.className = 'neighbor-card';
        card.innerHTML = `
            <div class="neighbor-header">
                <span class="neighbor-title">দাগ নং: বিএস ${p.dag_number} ${p.is_target_parcel ? '(বর্তমান প্লট)' : ''}</span>
                <span class="tax-badge ${isPaid ? 'tax-paid' : 'tax-arrears'}">${p.tax_status_label}</span>
            </div>
            <div class="neighbor-meta">
                <span>মালিক: <strong>${p.owner_name}</strong></span> |
                <span>আয়তন: <strong>${p.area_decimals} শতক</strong></span> |
                <span>হোল্ডিং: <strong>${p.holding_number}</strong></span>
            </div>
        `;
        list.appendChild(card);
    });
}

// ==============================================================================
// 6. Action Buttons & Interactivity
// ==============================================================================

function initActionButtons() {
    // Recenter
    document.getElementById('btn-recenter').addEventListener('click', () => {
        if (state.targetBounds) {
            state.map.fitBounds(state.targetBounds, { padding: [60, 60] });
        }
    });

    // Focus on Conflict Zone
    document.getElementById('btn-focus-conflict').addEventListener('click', () => {
        if (state.conflictBounds) {
            state.map.fitBounds(state.conflictBounds, { padding: [100, 100], maxZoom: 21 });
            // Flash conflict layer if visible
            const conflictLayer = state.layers['conflict_zone'];
            if (conflictLayer) {
                if (!state.map.hasLayer(conflictLayer)) {
                    state.map.addLayer(conflictLayer);
                    const cb = document.querySelector('input[data-layer="conflict_zone"]');
                    if (cb) cb.checked = true;
                }
            }
        }
    });

    // Toggle All Layers
    let allOn = true;
    document.getElementById('btn-toggle-all').addEventListener('click', () => {
        allOn = !allOn;
        Object.keys(state.layers).forEach(key => {
            const layer = state.layers[key];
            const cb = document.querySelector(`input[data-layer="${key}"]`);
            if (allOn) {
                if (!state.map.hasLayer(layer)) state.map.addLayer(layer);
                if (cb) cb.checked = true;
                state.layerVisibility[key] = true;
            } else {
                if (state.map.hasLayer(layer)) state.map.removeLayer(layer);
                if (cb) cb.checked = false;
                state.layerVisibility[key] = false;
            }
        });
    });

    // Retry Button on error
    document.getElementById('retry-btn').addEventListener('click', () => {
        loadParcelData();
    });
}

// ==============================================================================
// 7. Tab Switching
// ==============================================================================

function initTabs() {
    const tabs = document.querySelectorAll('.nav-tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

            tab.classList.add('active');
            const targetId = tab.dataset.tab;
            const targetPane = document.getElementById(targetId);
            if (targetPane) targetPane.classList.add('active');
        });
    });
}
