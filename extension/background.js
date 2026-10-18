/**
 * NAKSHA (নকশা) — Chrome Extension Background Service Worker (Manifest V3)
 * Manages side panel behavior, storage synchronization, and cross-context messaging.
 */

// Configure Chrome Extension Side Panel behavior on install and startup
function configureSidePanel() {
  if (chrome.sidePanel && chrome.sidePanel.setPanelBehavior) {
    chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true })
      .then(() => console.log('[NAKSHA Background] Side panel behavior configured: open on action click.'))
      .catch((err) => console.error('[NAKSHA Background] Error setting panel behavior:', err));
  }
}

// Call on startup, install, and initial worker evaluation
configureSidePanel();

chrome.runtime.onInstalled.addListener(() => {
  console.log('[NAKSHA Background] Service worker installed.');
  configureSidePanel();
});

chrome.runtime.onStartup.addListener(() => {
  console.log('[NAKSHA Background] Chrome startup.');
  configureSidePanel();
});

// Handle clicking the extension toolbar action icon
chrome.action.onClicked.addListener(async (tab) => {
  console.log('[NAKSHA Background] Action clicked on tab:', tab?.id);
  if (tab?.id && chrome.sidePanel && chrome.sidePanel.open) {
    try {
      await chrome.sidePanel.open({ tabId: tab.id });
      console.log('[NAKSHA Background] Successfully opened side panel for tab:', tab.id);
    } catch (e) {
      console.warn('[NAKSHA Background] sidePanel.open notice:', e);
    }
  }
});

// Listen for messages from content scripts or side panel
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'NAKSHA_PLOT_DETECTED' || message.type === 'NAKSHA_PLOT_CHANGED') {
    const plotData = message.payload;
    console.log('[NAKSHA Background] Plot context received:', plotData);

    // Save active parcel context to chrome.storage.local
    if (chrome.storage && chrome.storage.local) {
      chrome.storage.local.set({ activeParcelContext: plotData }, () => {
        // Broadcast to all extension views (including sidepanel)
        chrome.runtime.sendMessage({
          type: 'NAKSHA_CONTEXT_UPDATED',
          payload: plotData,
        }).catch(() => {
          // It's normal if side panel is not currently open/listening
        });
      });
    }

    sendResponse({ status: 'ok', received: plotData });
    return true;
  }

  if (message.type === 'NAKSHA_OPEN_SIDEPANEL') {
    if (sender?.tab?.id && chrome.sidePanel && chrome.sidePanel.open) {
      chrome.sidePanel.open({ tabId: sender.tab.id })
        .then(() => sendResponse({ status: 'opened' }))
        .catch((err) => sendResponse({ status: 'error', error: err.message }));
      return true;
    }
  }

  if (message.type === 'NAKSHA_GET_CURRENT_CONTEXT') {
    if (chrome.storage && chrome.storage.local) {
      chrome.storage.local.get(['activeParcelContext'], (result) => {
        sendResponse({ status: 'ok', context: result.activeParcelContext || null });
      });
      return true;
    }
  }

  return false;
});
