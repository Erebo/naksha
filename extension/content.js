/**
 * NAKSHA (নকশা) — Content Script for Bangla-First Mock Land Portals
 * Detects Mouza, Dag, and Khatian identifiers on purpose-built mock pages.
 * Never scrapes or connects to live government websites.
 */

(function () {
  'use strict';

  console.log('[NAKSHA Content Script] Loaded on mock land portal.');

  // Extract identifiers and officer identity from DOM
  function extractPortalContext() {
    const contextEl = document.getElementById('naksha-portal-context');
    if (!contextEl) {
      return null;
    }

    const officerEl = document.getElementById('portal-officer-header');
    const officerData = officerEl ? officerEl.dataset : {};

    const dataset = contextEl.dataset;
    return {
      portal: dataset.portal || 'mock_portal',
      portalName: officerData.portalName || (dataset.portal === 'e_mutation' ? 'ই-নামজারি ও মিউটেশন ব্যবস্থাপনা সিস্টেম' : 'ভূমি উন্নয়ন কর ব্যবস্থাপনা সিস্টেম (LD Tax)'),
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
      officerId: officerData.officerId || 'UL-2024-KSH',
      officerName: officerData.officerName || 'মোঃ ফজলুর রহমান',
      officerRole: officerData.officerRole || 'union_land_officer',
      officerDesignation: officerData.officerDesignation || 'ইউনিয়ন ভূমি সহকারী কর্মকর্তা',
      officerOffice: officerData.officerOffice || 'কাশিমপুর, গাজীপুর সদর',
      timestamp: Date.now(),
      url: window.location.href,
      origin: window.location.origin,
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
        <button id="naksha-pill-open-btn" class="naksha-pill-btn" type="button">যাচাই করুন</button>
      </div>
    `;

    document.body.appendChild(pill);

    const openBtn = pill.querySelector('#naksha-pill-open-btn');
    openBtn.addEventListener('click', () => {
      chrome.runtime.sendMessage({ type: 'NAKSHA_OPEN_SIDEPANEL', payload: extractPortalContext() }, (res) => {
        if (chrome.runtime.lastError || !res || res.status !== 'opened') {
          // If browser requires user action on extension toolbar directly, show clear Bangla guidance
          showPanelGuideToast();
        }
      });
    });
  }

  function showPanelGuideToast() {
    if (document.getElementById('naksha-guide-toast')) return;
    const toast = document.createElement('div');
    toast.id = 'naksha-guide-toast';
    toast.className = 'naksha-toast-container';
    toast.innerHTML = `
      <div class="naksha-toast-header">
        <strong>📌 নকশা (NAKSHA) সাইড প্যানেল নির্দেশিকা</strong>
        <span class="naksha-toast-close" onclick="this.parentElement.parentElement.remove()">✕</span>
      </div>
      <p style="margin: 6px 0; font-size: 12px; line-height: 1.4;">
        ক্রোম ব্রাউজারের সাইড প্যানেল স্বয়ংক্রিয়ভাবে খোলার জন্য ব্রাউজারের উপরের ডানদিকের 
        <strong>এক্সটেনশন (NAKSHA) আইকনটিতে ক্লিক করুন</strong> অথবা ক্রোম সাইড প্যানেল মেন্যু থেকে <strong>নকশা</strong> নির্বাচন করুন।
      </p>
      <div style="font-size: 11px; color: #94a3b8;">
        (সাইড প্যানেল একবার খুললে এটি পোর্টালটির পাশেই দৃশ্যমান থাকবে এবং প্রতিটি দাগ পরিবর্তনের সাথে স্বয়ংক্রিয়ভাবে ম্যাপ হালনাগাদ হবে।)
      </div>
    `;
    document.body.appendChild(toast);
    setTimeout(() => {
      if (toast && toast.parentElement) toast.remove();
    }, 8000);
  }

  function updateFloatingBadgeText(context) {
    const dagEl = document.getElementById('naksha-pill-dag');
    if (dagEl && context) {
      dagEl.textContent = context.dag;
    }
  }

  function initPortalDetection() {
    const ctx = extractPortalContext();
    if (ctx) {
      console.log('[NAKSHA Content Script] Identified plot:', ctx);
      notifyExtension(ctx, 'NAKSHA_PLOT_DETECTED');
      injectFloatingBadge(ctx);
    } else {
      // Retry in 200ms if DOM is still being rendered
      setTimeout(initPortalDetection, 200);
      return;
    }

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
  }

  // Run on DOM ready or immediately if document is already loaded
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPortalDetection);
  } else {
    initPortalDetection();
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

  // Listen for dynamic officer switching events on the mock portal
  window.addEventListener('naksha:officerChanged', (event) => {
    console.log('[NAKSHA Content Script] Custom event naksha:officerChanged caught:', event.detail);
    const updated = extractPortalContext();
    if (updated) {
      notifyExtension(updated, 'NAKSHA_OFFICER_CHANGED');
    }
  });
})();

