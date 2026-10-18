/**
 * NAKSHA (নকশা) — Content Script for Bangla-First Mock Land Portals
 * Detects Mouza, Dag, and Khatian identifiers on purpose-built mock pages.
 * Never scrapes or connects to live government websites.
 */

(function () {
  'use strict';

  console.log('[NAKSHA Content Script] Loaded on mock land portal.');

  // Extract identifiers from DOM element #naksha-portal-context
  function extractPortalContext() {
    const contextEl = document.getElementById('naksha-portal-context');
    if (!contextEl) {
      return null;
    }

    const dataset = contextEl.dataset;
    return {
      portal: dataset.portal || 'mock_portal',
      mouza: dataset.mouza || 'কাশিমপুর',
      jl: dataset.jl || '২৮',
      upazila: dataset.upazila || 'গাজীপুর সদর',
      district: dataset.district || 'গাজীপুর',
      dag: dataset.dag || '402',
      khatian: dataset.khatian || '120',
      holding: dataset.holding || '',
      caseId: dataset.caseId || '',
      deedNo: dataset.deedNo || '',
      owner: dataset.owner || '',
      area: dataset.area || '',
      taxStatus: dataset.taxStatus || '',
      timestamp: Date.now(),
      url: window.location.href,
    };
  }

  // Notify extension service worker with current context
  function notifyExtension(context, eventType = 'NAKSHA_PLOT_DETECTED') {
    if (!context) return;
    try {
      chrome.runtime.sendMessage({
        type: eventType,
        payload: context,
      }, (response) => {
        if (chrome.runtime.lastError) {
          // Extension sidepanel or background may not be listening immediately
        }
      });
    } catch (e) {
      console.warn('[NAKSHA Content Script] Error sending context to extension:', e);
    }
  }

  // Inject floating Bangla badge/button into the mock portal
  function injectFloatingBadge(context) {
    if (document.getElementById('naksha-floating-pill')) {
      updateFloatingBadgeText(context);
      return;
    }

    const pill = document.createElement('div');
    pill.id = 'naksha-floating-pill';
    pill.className = 'naksha-pill-container';
    pill.innerHTML = `
      <div class="naksha-pill-header" title="নকশা সাইড প্যানেল খুলুন">
        <div class="naksha-pill-logo">নকশা</div>
        <div class="naksha-pill-info">
          <span class="naksha-pill-title">প্লট শনাক্ত: দাগ <strong id="naksha-pill-dag">${context.dag}</strong></span>
          <span class="naksha-pill-sub">মৌজা ${context.mouza} · ২ডি জিআইএস সমন্বয়</span>
        </div>
        <button id="naksha-pill-open-btn" class="naksha-pill-btn" type="button">ম্যাপ দেখুন</button>
      </div>
    `;

    document.body.appendChild(pill);

    const openBtn = pill.querySelector('#naksha-pill-open-btn');
    openBtn.addEventListener('click', () => {
      chrome.runtime.sendMessage({ type: 'NAKSHA_OPEN_SIDEPANEL' }, (res) => {
        // Fallback alert for browsers requiring user to click extension icon
        if (chrome.runtime.lastError || !res || res.status !== 'opened') {
          console.log('[NAKSHA] Opening side panel: please click the NAKSHA icon in Chrome toolbar or side panel.');
        }
      });
    });
  }

  function updateFloatingBadgeText(context) {
    const dagEl = document.getElementById('naksha-pill-dag');
    if (dagEl && context) {
      dagEl.textContent = context.dag;
    }
  }

  // Initial detection when page is ready
  const initialContext = extractPortalContext();
  if (initialContext) {
    console.log('[NAKSHA Content Script] Identified plot:', initialContext);
    notifyExtension(initialContext, 'NAKSHA_PLOT_DETECTED');
    injectFloatingBadge(initialContext);
  }

  // Listen for dynamic plot switching events on the mock portal
  window.addEventListener('naksha:plotChanged', (event) => {
    console.log('[NAKSHA Content Script] Custom event naksha:plotChanged caught:', event.detail);
    const updated = extractPortalContext();
    if (updated) {
      notifyExtension(updated, 'NAKSHA_PLOT_CHANGED');
      updateFloatingBadgeText(updated);
    }
  });

  // Observe DOM changes if attributes on #naksha-portal-context change
  const targetNode = document.getElementById('naksha-portal-context');
  if (targetNode) {
    const observer = new MutationObserver(() => {
      const updated = extractPortalContext();
      if (updated) {
        notifyExtension(updated, 'NAKSHA_PLOT_CHANGED');
        updateFloatingBadgeText(updated);
      }
    });
    observer.observe(targetNode, { attributes: true });
  }
})();
