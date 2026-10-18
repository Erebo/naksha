"""NAKSHA (নকশা) — Automated End-to-End Screenshot Capture Pipeline
Uses Playwright with Chromium (headed persistent context with extension loaded).
Device Scale Factor: 2 for sharp, high-DPI retina rendering.
Output Directory: docs/screenshots/final/
"""

import os
import re
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT_DIR = Path(__file__).resolve().parent.parent
EXT_PATH = ROOT_DIR / "extension"
OUT_DIR = ROOT_DIR / "docs" / "screenshots" / "final"
BASE_URL = "http://127.0.0.1:8000"

OUT_DIR.mkdir(parents=True, exist_ok=True)


def get_extension_id(context):
    """Retrieves the dynamic unpacked extension ID from Chrome service worker."""
    if context.service_workers:
        match = re.search(r"chrome-extension://([a-z0-9]+)/", context.service_workers[0].url)
        if match:
            return match.group(1)

    # Trigger background service worker via portal page interaction
    page = context.new_page()
    page.goto(f"{BASE_URL}/portals/ld-tax", wait_until="networkidle")
    try:
        page.wait_for_selector("#naksha-floating-pill", timeout=4000)
        page.click("#naksha-pill-open-btn")
    except Exception:
        pass
    page.wait_for_timeout(600)
    page.close()

    if context.service_workers:
        match = re.search(r"chrome-extension://([a-z0-9]+)/", context.service_workers[0].url)
        if match:
            return match.group(1)

    raise RuntimeError("Could not determine Naksha Extension ID from service worker.")


def capture_all():
    print("=" * 70)
    print("NAKSHA — Automated Screenshot Capture Pipeline (Playwright Chromium)")
    print(f"Output Directory: {OUT_DIR}")
    print("=" * 70)

    with sync_playwright() as p:
        # Launch persistent context with the Naksha extension loaded
        context = p.chromium.launch_persistent_context(
            user_data_dir="",
            headless=False,
            device_scale_factor=2,
            args=[
                f"--disable-extensions-except={EXT_PATH}",
                f"--load-extension={EXT_PATH}",
                "--no-sandbox",
                "--disable-gpu",
            ],
        )

        ext_id = get_extension_id(context)
        print(f"[OK] Naksha Extension ID: {ext_id}")
        sp_base = f"chrome-extension://{ext_id}/sidepanel.html"

        captured = []
        skipped = []

        # =====================================================================
        # 1. Portal Screenshots (1440x900)
        # =====================================================================
        print("\n--- Portal Integration (1440x900) ---")

        # 01: Portal logged in, officer UL-2024-KSH, pill visible
        p1 = context.new_page()
        p1.set_viewport_size({"width": 1440, "height": 900})
        p1.goto(f"{BASE_URL}/portals/ld-tax", wait_until="networkidle")
        p1.wait_for_selector("#naksha-floating-pill", state="visible", timeout=6000)
        p1.wait_for_selector(".tax-status-pill", state="visible")
        p1.wait_for_timeout(300)
        shot_01 = OUT_DIR / "01_portal_logged_in.png"
        p1.screenshot(path=str(shot_01))
        print("  [01] 01_portal_logged_in.png")
        captured.append("01_portal_logged_in.png")

        # 02: Pill close-up (clip to element)
        shot_02 = OUT_DIR / "02_portal_pill_closeup.png"
        pill_elem = p1.locator("#naksha-floating-pill")
        pill_elem.screenshot(path=str(shot_02))
        print("  [02] 02_portal_pill_closeup.png")
        captured.append("02_portal_pill_closeup.png")

        # 03: "Demo: officer" dropdown open in yellow banner
        shot_03 = OUT_DIR / "03_portal_demo_officer_dropdown.png"
        select_elem = p1.locator("#demo-officer-select")
        select_elem.scroll_into_view_if_needed()
        select_elem.evaluate("el => el.setAttribute('size', '4')")
        p1.wait_for_timeout(200)
        p1.screenshot(path=str(shot_03))
        select_elem.evaluate("el => el.removeAttribute('size')")
        print("  [03] 03_portal_demo_officer_dropdown.png")
        captured.append("03_portal_demo_officer_dropdown.png")
        p1.close()

        # =====================================================================
        # 2. Verification Screen (420x800)
        # =====================================================================
        print("\n--- Security Verification Gate (420x800) ---")

        # 04: Verification screen, checks running (mid-check)
        p_sp = context.new_page()
        p_sp.set_viewport_size({"width": 420, "height": 800})
        p_sp.goto(f"{sp_base}?mock_mid_check=true", wait_until="networkidle")
        p_sp.wait_for_selector(".sp-identity-card", state="visible")
        p_sp.wait_for_selector(".sp-spinner", state="visible")
        p_sp.wait_for_timeout(300)
        shot_04 = OUT_DIR / "04_verify_checks_running.png"
        p_sp.screenshot(path=str(shot_04))
        print("  [04] 04_verify_checks_running.png")
        captured.append("04_verify_checks_running.png")

        # 05: Identity card with metadata + verified tick
        p_sp.goto(f"{sp_base}?mock_verified=true", wait_until="networkidle")
        p_sp.wait_for_selector(".sp-identity-card", state="visible")
        p_sp.wait_for_selector(".sp-res-success", state="visible")
        p_sp.wait_for_timeout(300)
        shot_05 = OUT_DIR / "05_verify_identity_card_verified.png"
        p_sp.screenshot(path=str(shot_05))
        print("  [05] 05_verify_identity_card_verified.png")
        captured.append("05_verify_identity_card_verified.png")

        # 06: Denial: officer ID not in registry
        p_sp.goto(f"{sp_base}?mock_denied=true", wait_until="networkidle")
        p_sp.wait_for_selector(".sp-res-denied", state="visible")
        p_sp.wait_for_timeout(300)
        shot_06 = OUT_DIR / "06_verify_denial_unlisted_officer.png"
        p_sp.screenshot(path=str(shot_06))
        print("  [06] 06_verify_denial_unlisted_officer.png")
        captured.append("06_verify_denial_unlisted_officer.png")

        # =====================================================================
        # 3. Cockpit Scenario BLOCK Khas Encroachment (Dag 402)
        # =====================================================================
        print("\n--- Cockpit: Scenario BLOCK (Dag 402) ---")

        # 07: Cockpit full view, default state
        p_sp.goto(f"{sp_base}?bypass_verify=true&dag=402", wait_until="networkidle")
        p_sp.wait_for_selector("#sp-map", state="visible")
        p_sp.wait_for_selector(".vh-expanded-box", state="visible")
        p_sp.wait_for_timeout(500)
        shot_07 = OUT_DIR / "07_cockpit_block_khas_default.png"
        p_sp.screenshot(path=str(shot_07))
        print("  [07] 07_cockpit_block_khas_default.png")
        captured.append("07_cockpit_block_khas_default.png")

        # 08: Layers popover open, all layers on
        p_sp.click("#sp-btn-layers-toggle")
        p_sp.wait_for_selector("#sp-layers-popover:not(.hidden)", state="visible")
        p_sp.wait_for_timeout(300)
        shot_08 = OUT_DIR / "08_map_layers_popover_all_active.png"
        p_sp.screenshot(path=str(shot_08))
        print("  [08] 08_map_layers_popover_all_active.png")
        captured.append("08_map_layers_popover_all_active.png")

        # 09: Layers popover with only Deed claim + DLRS on
        p_sp.uncheck('input[data-layer-type="ancestral_footprint"]')
        p_sp.uncheck('input[data-layer-type="restricted_khas"]')
        p_sp.uncheck('input[data-layer-type="conflict_zone"]')
        p_sp.wait_for_timeout(400)
        shot_09 = OUT_DIR / "09_map_layers_popover_deed_dlrs.png"
        p_sp.screenshot(path=str(shot_09))
        print("  [09] 09_map_layers_popover_deed_dlrs.png")
        captured.append("09_map_layers_popover_deed_dlrs.png")

        # Restore layers and close popover
        p_sp.check('input[data-layer-type="ancestral_footprint"]')
        p_sp.check('input[data-layer-type="restricted_khas"]')
        p_sp.check('input[data-layer-type="conflict_zone"]')
        p_sp.click("#sp-btn-layers-toggle")
        p_sp.wait_for_timeout(300)

        # 10: Map expanded to full panel
        p_sp.click("#sp-btn-map-expand")
        p_sp.wait_for_timeout(400)
        shot_10 = OUT_DIR / "10_map_expanded_full_panel.png"
        p_sp.screenshot(path=str(shot_10))
        print("  [10] 10_map_expanded_full_panel.png")
        captured.append("10_map_expanded_full_panel.png")

        # Reset map size
        p_sp.click("#sp-btn-map-collapse")
        p_sp.wait_for_timeout(300)

        # 11: Overview tab (area bars, overlap ring, failed rules)
        p_sp.click('.sp-tab-item[data-tab="tab-overview"]')
        p_sp.wait_for_selector("#overview-chart-container .bento-card", state="visible")
        p_sp.wait_for_timeout(300)
        shot_11 = OUT_DIR / "11_tab_overview_khas_conflict.png"
        p_sp.screenshot(path=str(shot_11))
        print("  [11] 11_tab_overview_khas_conflict.png")
        captured.append("11_tab_overview_khas_conflict.png")

        # 12: History tab (lineage graph, name-match meter)
        p_sp.click('.sp-tab-item[data-tab="tab-history"]')
        p_sp.wait_for_selector(".lineage-minimal-track", state="visible")
        p_sp.wait_for_selector(".lineage-phonetic-box", state="visible")
        p_sp.wait_for_timeout(300)
        shot_12 = OUT_DIR / "12_tab_history_lineage_graph.png"
        p_sp.screenshot(path=str(shot_12))
        print("  [12] 12_tab_history_lineage_graph.png")
        captured.append("12_tab_history_lineage_graph.png")

        # 13: Tax tab
        p_sp.click('.sp-tab-item[data-tab="tab-tax"]')
        p_sp.wait_for_selector(".tax-status-metric-row", state="visible")
        p_sp.wait_for_timeout(300)
        shot_13 = OUT_DIR / "13_tab_tax_records_arrears.png"
        p_sp.screenshot(path=str(shot_13))
        print("  [13] 13_tab_tax_records_arrears.png")
        captured.append("13_tab_tax_records_arrears.png")

        # 14: Liens tab
        p_sp.click('.sp-tab-item[data-tab="tab-liens"]')
        p_sp.wait_for_selector(".bento-empty-center", state="visible")
        p_sp.wait_for_timeout(300)
        shot_14 = OUT_DIR / "14_tab_liens_encumbrance_status.png"
        p_sp.screenshot(path=str(shot_14))
        print("  [14] 14_tab_liens_encumbrance_status.png")
        captured.append("14_tab_liens_encumbrance_status.png")

        # 15: Audit tab with ACCESS_GRANTED and "Chain intact" badge
        p_sp.click('.sp-tab-item[data-tab="tab-audit"]')
        p_sp.wait_for_selector(".audit-pinned-banner", state="visible")
        p_sp.wait_for_selector(".audit-block-card", state="visible")
        p_sp.wait_for_timeout(300)
        shot_15 = OUT_DIR / "15_tab_audit_access_granted_intact.png"
        p_sp.screenshot(path=str(shot_15))
        print("  [15] 15_tab_audit_access_granted_intact.png")
        captured.append("15_tab_audit_access_granted_intact.png")

        # 16: Audit tab after tamper demo (chain break) -> Feature not implemented
        print("  [16] 16_tab_audit_tamper_demo_break.png -> SKIPPED (tamper simulation endpoint does not exist)")
        skipped.append(("16_tab_audit_tamper_demo_break.png", "Tamper demo / cryptographic corruption simulation endpoint does not exist."))

        # =====================================================================
        # 4. Other Scenarios (Cockpit + Overview Tab)
        # =====================================================================
        print("\n--- Additional Decision Scenarios ---")

        # 17: CLEAR (dag 401)
        p_sp.goto(f"{sp_base}?bypass_verify=true&dag=401&tab=tab-overview", wait_until="networkidle")
        p_sp.wait_for_selector("#sp-map", state="visible")
        p_sp.wait_for_selector(".vh-expanded-box", state="visible")
        p_sp.wait_for_timeout(500)
        shot_17 = OUT_DIR / "17_scenario_401_clear.png"
        p_sp.screenshot(path=str(shot_17))
        print("  [17] 17_scenario_401_clear.png")
        captured.append("17_scenario_401_clear.png")

        # 18: REVIEW tax mismatch (dag 403)
        p_sp.goto(f"{sp_base}?bypass_verify=true&dag=403&tab=tab-overview", wait_until="networkidle")
        p_sp.wait_for_selector("#sp-map", state="visible")
        p_sp.wait_for_selector(".vh-expanded-box", state="visible")
        p_sp.wait_for_timeout(500)
        shot_18 = OUT_DIR / "18_scenario_403_review.png"
        p_sp.screenshot(path=str(shot_18))
        print("  [18] 18_scenario_403_review.png")
        captured.append("18_scenario_403_review.png")

        # 19: BLOCK unmutated deed + bank lien -> Not seeded as separate scenario
        print("  [19] 19_scenario_block_unmutated_deed.png -> SKIPPED (no 4th scenario seeded in database)")
        skipped.append(("19_scenario_block_unmutated_deed.png", "A separate 4th seeded parcel combining unmutated deed + bank lien does not exist in the spatial database; seeded cohorts are Dag 401 (CLEAR), Dag 402 (BLOCK), and Dag 403 (REVIEW)."))

        # =====================================================================
        # 5. Responsive and Settings
        # =====================================================================
        print("\n--- Responsive & Settings ---")

        # 20: English mode (cockpit)
        p_sp.goto(f"{sp_base}?bypass_verify=true&dag=402&lang=en", wait_until="networkidle")
        p_sp.wait_for_selector("#sp-map", state="visible")
        p_sp.wait_for_selector(".vh-expanded-box", state="visible")
        p_sp.wait_for_timeout(500)
        shot_20 = OUT_DIR / "20_cockpit_english_mode.png"
        p_sp.screenshot(path=str(shot_20))
        print("  [20] 20_cockpit_english_mode.png")
        captured.append("20_cockpit_english_mode.png")

        # 21: Light theme (cockpit)
        p_sp.goto(f"{sp_base}?bypass_verify=true&dag=402&theme=light", wait_until="networkidle")
        p_sp.wait_for_selector("#sp-map", state="visible")
        p_sp.wait_for_selector(".vh-expanded-box", state="visible")
        p_sp.wait_for_timeout(500)
        shot_21 = OUT_DIR / "21_cockpit_light_theme.png"
        p_sp.screenshot(path=str(shot_21))
        print("  [21] 21_cockpit_light_theme.png")
        captured.append("21_cockpit_light_theme.png")

        # 22: Narrow 380px width
        p_sp.set_viewport_size({"width": 380, "height": 800})
        p_sp.goto(f"{sp_base}?bypass_verify=true&dag=402&theme=dark", wait_until="networkidle")
        p_sp.wait_for_selector("#sp-map", state="visible")
        p_sp.wait_for_timeout(500)
        shot_22 = OUT_DIR / "22_cockpit_narrow_380px.png"
        p_sp.screenshot(path=str(shot_22))
        print("  [22] 22_cockpit_narrow_380px.png")
        captured.append("22_cockpit_narrow_380px.png")

        # 23: Wide 800px width (2-column layout)
        p_sp.set_viewport_size({"width": 800, "height": 800})
        p_sp.goto(f"{sp_base}?bypass_verify=true&dag=402&theme=dark", wait_until="networkidle")
        p_sp.wait_for_selector("#sp-map", state="visible")
        p_sp.wait_for_timeout(500)
        shot_23 = OUT_DIR / "23_cockpit_wide_800px.png"
        p_sp.screenshot(path=str(shot_23))
        print("  [23] 23_cockpit_wide_800px.png")
        captured.append("23_cockpit_wide_800px.png")

        # 24: Wide 1000px width with History tab
        p_sp.set_viewport_size({"width": 1000, "height": 800})
        p_sp.goto(f"{sp_base}?bypass_verify=true&dag=402&tab=tab-history&theme=dark", wait_until="networkidle")
        p_sp.wait_for_selector(".lineage-minimal-track", state="visible")
        p_sp.wait_for_timeout(500)
        shot_24 = OUT_DIR / "24_cockpit_wide_1000px_history.png"
        p_sp.screenshot(path=str(shot_24))
        print("  [24] 24_cockpit_wide_1000px_history.png")
        captured.append("24_cockpit_wide_1000px_history.png")
        p_sp.close()

        # =====================================================================
        # 6. Security
        # =====================================================================
        print("\n--- Security Verification ---")

        # 25: Non-allowlisted website: extension shows nothing (neutral page)
        p_sec = context.new_page()
        p_sec.set_viewport_size({"width": 1440, "height": 900})
        p_sec.goto(f"{BASE_URL}/docs", wait_until="networkidle")
        p_sec.wait_for_timeout(800)
        assert not p_sec.locator("#naksha-floating-pill").is_visible(), "Pill must not inject on non-allowlisted pages!"
        shot_25 = OUT_DIR / "25_security_non_allowlisted_page.png"
        p_sec.screenshot(path=str(shot_25))
        print("  [25] 25_security_non_allowlisted_page.png")
        captured.append("25_security_non_allowlisted_page.png")
        p_sec.close()

        # 26: Portal logged out: panel locked / pill disabled -> Feature not implemented
        print("  [26] 26_security_portal_logged_out.png -> SKIPPED (logged-out state not implemented in mock portal)")
        skipped.append(("26_security_portal_logged_out.png", "Mock portal does not have a logged-out toggle or locked-pill state."))

        # 27: Audit tab with an ACCESS_DENIED entry
        p_audit = context.new_page()
        p_audit.set_viewport_size({"width": 420, "height": 800})
        # Trigger an ACCESS_DENIED in audit ledger by calling verification with unlisted officer
        p_audit.goto(f"{sp_base}?mock_denied=true", wait_until="networkidle")
        p_audit.wait_for_selector(".sp-res-denied", state="visible")
        p_audit.wait_for_timeout(300)
        # Now open the cockpit audit tab to view the recorded ACCESS_DENIED block
        p_audit.goto(f"{sp_base}?bypass_verify=true&tab=tab-audit", wait_until="networkidle")
        p_audit.wait_for_selector(".audit-pinned-banner", state="visible")
        p_audit.wait_for_selector(".audit-block-card", state="visible")
        p_audit.wait_for_timeout(500)
        shot_27 = OUT_DIR / "27_security_audit_access_denied.png"
        p_audit.screenshot(path=str(shot_27))
        print("  [27] 27_security_audit_access_denied.png")
        captured.append("27_security_audit_access_denied.png")
        p_audit.close()

        context.close()

    print("\n" + "=" * 70)
    print(f"CAPTURE COMPLETE: {len(captured)} captured, {len(skipped)} skipped.")
    print("=" * 70)

    # Write INDEX.md
    write_index_md(captured, skipped)


def write_index_md(captured, skipped):
    index_path = OUT_DIR / "INDEX.md"

    table_data = [
        ("01", "01_portal_logged_in.png", "Mock LD Tax portal logged in as UL-2024-KSH, 'যাচাই করুন' pill visible", "Normal Portal Session", "বাংলা (BN)", "Light (Portal)", "1440x900"),
        ("02", "02_portal_pill_closeup.png", "Close-up bounding box of floating Naksha pill on the portal", "Normal Portal Session", "বাংলা (BN)", "Light (Portal)", "Clip to Element"),
        ("03", "03_portal_demo_officer_dropdown.png", "'Demo: officer' dropdown active in the yellow demo banner", "Officer Switcher", "বাংলা (BN)", "Light (Portal)", "1440x900"),
        ("04", "04_verify_checks_running.png", "Security verification gate mid-check with active step spinners", "Gate in Progress", "বাংলা (BN)", "Dark", "420x800"),
        ("05", "05_verify_identity_card_verified.png", "Identity card with officer metadata + green verified tick", "UL-2024-KSH Verified", "বাংলা (BN)", "Dark", "420x800"),
        ("06", "06_verify_denial_unlisted_officer.png", "Security gate denial state for unlisted officer (EXT-999-HACK)", "Unauthorized Access", "বাংলা (BN)", "Dark", "420x800"),
        ("07", "07_cockpit_block_khas_default.png", "Cockpit full view default state, BLOCK Khas encroachment (Dag 402)", "Dag 402 (BLOCK)", "বাংলা (BN)", "Dark", "420x800"),
        ("08", "08_map_layers_popover_all_active.png", "Floating Layers popover open with all 5 cadastral layers active", "Dag 402 (BLOCK)", "বাংলা (BN)", "Dark", "420x800"),
        ("09", "09_map_layers_popover_deed_dlrs.png", "Layers popover filtered to Deed Claim + DLRS ground truth only", "Dag 402 (BLOCK)", "বাংলা (BN)", "Dark", "420x800"),
        ("10", "10_map_expanded_full_panel.png", "Cadastral 2D GIS map expanded to fill full panel height", "Dag 402 (BLOCK)", "বাংলা (BN)", "Dark", "420x800"),
        ("11", "11_tab_overview_khas_conflict.png", "Overview tab: area comparison, 14% overlap donut, failed rules", "Dag 402 (BLOCK)", "বাংলা (BN)", "Dark", "420x800"),
        ("12", "12_tab_history_lineage_graph.png", "History tab: CS-SA-RS-BS lineage track & phonetic name match", "Dag 402 (BLOCK)", "বাংলা (BN)", "Dark", "420x800"),
        ("13", "13_tab_tax_records_arrears.png", "Tax tab: 3-year holding status metrics & assessment records", "Dag 402 (BLOCK)", "বাংলা (BN)", "Dark", "420x800"),
        ("14", "14_tab_liens_encumbrance_status.png", "Liens tab: CIB / AC Land clean encumbrance empty state", "Dag 402 (BLOCK)", "বাংলা (BN)", "Dark", "420x800"),
        ("15", "15_tab_audit_access_granted_intact.png", "Audit tab: ACCESS_GRANTED entry & '● লেজার সম্পূর্ণ অটুট' badge", "Dag 402 (BLOCK)", "বাংলা (BN)", "Dark", "420x800"),
        ("16", "16_tab_audit_tamper_demo_break.png", "Audit tab after tamper demo (chain break)", "N/A", "N/A", "N/A", "N/A"),
        ("17", "17_scenario_401_clear.png", "Scenario CLEAR (Dag 401, clean records, 5/5 statutory rules passed)", "Dag 401 (CLEAR)", "বাংলা (BN)", "Dark", "420x800"),
        ("18", "18_scenario_403_review.png", "Scenario REVIEW (Dag 403, 3-year tax arrears & unmutated deed gap)", "Dag 403 (REVIEW)", "বাংলা (BN)", "Dark", "420x800"),
        ("19", "19_scenario_block_unmutated_deed.png", "BLOCK unmutated deed + bank lien", "N/A", "N/A", "N/A", "N/A"),
        ("20", "20_cockpit_english_mode.png", "Cockpit rendered in 100% English localization mode (EN)", "Dag 402 (BLOCK)", "English (EN)", "Dark", "420x800"),
        ("21", "21_cockpit_light_theme.png", "Cockpit rendered in complete Soft Grey Light Theme", "Dag 402 (BLOCK)", "বাংলা (BN)", "Light", "420x800"),
        ("22", "22_cockpit_narrow_380px.png", "Cockpit at narrow 380px width, fluid layout without horizontal scroll", "Dag 402 (BLOCK)", "বাংলা (BN)", "Dark", "380x800"),
        ("23", "23_cockpit_wide_800px.png", "Cockpit at wide 800px width (2-column layout: Hero+Map and Tabs)", "Dag 402 (BLOCK)", "বাংলা (BN)", "Dark", "800x800"),
        ("24", "24_cockpit_wide_1000px_history.png", "Cockpit at ultra-wide 1000px width showing History tab", "Dag 402 (BLOCK)", "বাংলা (BN)", "Dark", "1000x800"),
        ("25", "25_security_non_allowlisted_page.png", "Non-allowlisted neutral site (e.g. /docs): extension injects nothing", "Non-Allowlisted Page", "English (EN)", "Light", "1440x900"),
        ("26", "26_security_portal_logged_out.png", "Portal logged out: panel locked / pill disabled", "N/A", "N/A", "N/A", "N/A"),
        ("27", "27_security_audit_access_denied.png", "Audit tab displaying cryptographic ACCESS_DENIED block", "Security Audit", "বাংলা (BN)", "Dark", "420x800"),
    ]

    lines = [
        "# NAKSHA (নকশা) — Visual Verification Index",
        "",
        "> [!NOTE]",
        "> **Methodology Declaration**: Chrome's internal OS side panel container cannot be rendered directly via browser automation. "
        "Side panel views are rendered and captured at side-panel viewports (default `420x800`, with `380px`, `800px`, and `1000px` for responsive verification) "
        "using the extension's unpacked Chrome MV3 runtime (`chrome-extension://<id>/sidepanel.html`). "
        "Portal integration views are captured at `1440x900` on the mock government portal (`http://127.0.0.1:8000/portals/ld-tax`). "
        "All captures use Chromium with high-DPI `device_scale_factor: 2` and strictly synthetic demo data.",
        "",
        "## Captured Visual Index",
        "",
        "| # | File Name | Description | Scenario | Language | Theme | Viewport |",
        "|---|---|---|---|---|---|---|",
    ]

    for item in table_data:
        serial, fname, desc, scen, lang, theme, vp = item
        if any(fname == c for c in captured):
            lines.append(f"| **{serial}** | [`{fname}`](./{fname}) | {desc} | {scen} | {lang} | {theme} | `{vp}` |")
        else:
            lines.append(f"| **{serial}** | *Skipped* | {desc} | *N/A* | *N/A* | *N/A* | *N/A* |")

    lines.extend([
        "",
        "## Not Captured (Architectural Rationale)",
        "",
        "Per project rules, features not implemented or seeded in the current codebase are never faked or mocked:",
        "",
        "1. **`16_tab_audit_tamper_demo_break.png` (Serial 16)**:",
        "   - *Reason*: The cryptographic hash chain verifies integrity against SHA-256 and Ed25519 signatures, but no runtime tamper corruption simulation route is implemented on the server.",
        "",
        "2. **`19_scenario_block_unmutated_deed.png` (Serial 19)**:",
        "   - *Reason*: The seeded spatial dataset contains 3 official benchmark cohorts: Dag 402 (BLOCK: Khas Canal Overlap), Dag 401 (CLEAR: Clean Parcel), and Dag 403 (REVIEW: Tax Arrears & Unmutated Deed Gap). A separate 4th seeded parcel combining unmutated deed + bank lien as a BLOCK is not registered in the database.",
        "",
        "3. **`26_security_portal_logged_out.png` (Serial 26)**:",
        "   - *Reason*: The mock portal presents an active mock officer session by default and does not feature a logged-out toggle or locked-pill state.",
        "",
    ])

    with open(index_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[OK] Generated {index_path}")


if __name__ == "__main__":
    capture_all()
