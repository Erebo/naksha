# NAKSHA (নকশা) — Visual Verification Index

> [!NOTE]
> **Methodology Declaration**: Chrome's internal OS side panel container cannot be rendered directly via browser automation. Side panel views are rendered and captured at side-panel viewports (default `420x800`, with `380px`, `800px`, and `1000px` for responsive verification) using the extension's unpacked Chrome MV3 runtime (`chrome-extension://<id>/sidepanel.html`). Portal integration views are captured at `1440x900` on the mock government portal (`http://127.0.0.1:8000/portals/ld-tax`). All captures use Chromium with high-DPI `device_scale_factor: 2` and strictly synthetic demo data.

## Captured Visual Index

| # | File Name | Description | Scenario | Language | Theme | Viewport |
|---|---|---|---|---|---|---|
| **01** | [`01_portal_logged_in.png`](./01_portal_logged_in.png) | Mock LD Tax portal logged in as UL-2024-KSH, 'যাচাই করুন' pill visible | Normal Portal Session | বাংলা (BN) | Light (Portal) | `1440x900` |
| **02** | [`02_portal_pill_closeup.png`](./02_portal_pill_closeup.png) | Close-up bounding box of floating Naksha pill on the portal | Normal Portal Session | বাংলা (BN) | Light (Portal) | `Clip to Element` |
| **03** | [`03_portal_demo_officer_dropdown.png`](./03_portal_demo_officer_dropdown.png) | 'Demo: officer' dropdown active in the yellow demo banner | Officer Switcher | বাংলা (BN) | Light (Portal) | `1440x900` |
| **04** | [`04_verify_checks_running.png`](./04_verify_checks_running.png) | Security verification gate mid-check with active step spinners | Gate in Progress | বাংলা (BN) | Dark | `420x800` |
| **05** | [`05_verify_identity_card_verified.png`](./05_verify_identity_card_verified.png) | Identity card with officer metadata + green verified tick | UL-2024-KSH Verified | বাংলা (BN) | Dark | `420x800` |
| **06** | [`06_verify_denial_unlisted_officer.png`](./06_verify_denial_unlisted_officer.png) | Security gate denial state for unlisted officer (EXT-999-HACK) | Unauthorized Access | বাংলা (BN) | Dark | `420x800` |
| **07** | [`07_cockpit_block_khas_default.png`](./07_cockpit_block_khas_default.png) | Cockpit full view default state, BLOCK Khas encroachment (Dag 402) | Dag 402 (BLOCK) | বাংলা (BN) | Dark | `420x800` |
| **08** | [`08_map_layers_popover_all_active.png`](./08_map_layers_popover_all_active.png) | Floating Layers popover open with all 5 cadastral layers active | Dag 402 (BLOCK) | বাংলা (BN) | Dark | `420x800` |
| **09** | [`09_map_layers_popover_deed_dlrs.png`](./09_map_layers_popover_deed_dlrs.png) | Layers popover filtered to Deed Claim + DLRS ground truth only | Dag 402 (BLOCK) | বাংলা (BN) | Dark | `420x800` |
| **10** | [`10_map_expanded_full_panel.png`](./10_map_expanded_full_panel.png) | Cadastral 2D GIS map expanded to fill full panel height | Dag 402 (BLOCK) | বাংলা (BN) | Dark | `420x800` |
| **11** | [`11_tab_overview_khas_conflict.png`](./11_tab_overview_khas_conflict.png) | Overview tab: area comparison, 14% overlap donut, failed rules | Dag 402 (BLOCK) | বাংলা (BN) | Dark | `420x800` |
| **12** | [`12_tab_history_lineage_graph.png`](./12_tab_history_lineage_graph.png) | History tab: CS-SA-RS-BS lineage track & phonetic name match | Dag 402 (BLOCK) | বাংলা (BN) | Dark | `420x800` |
| **13** | [`13_tab_tax_records_arrears.png`](./13_tab_tax_records_arrears.png) | Tax tab: 3-year holding status metrics & assessment records | Dag 402 (BLOCK) | বাংলা (BN) | Dark | `420x800` |
| **14** | [`14_tab_liens_encumbrance_status.png`](./14_tab_liens_encumbrance_status.png) | Liens tab: CIB / AC Land clean encumbrance empty state | Dag 402 (BLOCK) | বাংলা (BN) | Dark | `420x800` |
| **15** | [`15_tab_audit_access_granted_intact.png`](./15_tab_audit_access_granted_intact.png) | Audit tab: ACCESS_GRANTED entry & '● লেজার সম্পূর্ণ অটুট' badge | Dag 402 (BLOCK) | বাংলা (BN) | Dark | `420x800` |
| **16** | *Skipped* | Audit tab after tamper demo (chain break) | *N/A* | *N/A* | *N/A* | *N/A* |
| **17** | [`17_scenario_401_clear.png`](./17_scenario_401_clear.png) | Scenario CLEAR (Dag 401, clean records, 5/5 statutory rules passed) | Dag 401 (CLEAR) | বাংলা (BN) | Dark | `420x800` |
| **18** | [`18_scenario_403_review.png`](./18_scenario_403_review.png) | Scenario REVIEW (Dag 403, 3-year tax arrears & unmutated deed gap) | Dag 403 (REVIEW) | বাংলা (BN) | Dark | `420x800` |
| **19** | *Skipped* | BLOCK unmutated deed + bank lien | *N/A* | *N/A* | *N/A* | *N/A* |
| **20** | [`20_cockpit_english_mode.png`](./20_cockpit_english_mode.png) | Cockpit rendered in 100% English localization mode (EN) | Dag 402 (BLOCK) | English (EN) | Dark | `420x800` |
| **21** | [`21_cockpit_light_theme.png`](./21_cockpit_light_theme.png) | Cockpit rendered in complete Soft Grey Light Theme | Dag 402 (BLOCK) | বাংলা (BN) | Light | `420x800` |
| **22** | [`22_cockpit_narrow_380px.png`](./22_cockpit_narrow_380px.png) | Cockpit at narrow 380px width, fluid layout without horizontal scroll | Dag 402 (BLOCK) | বাংলা (BN) | Dark | `380x800` |
| **23** | [`23_cockpit_wide_800px.png`](./23_cockpit_wide_800px.png) | Cockpit at wide 800px width (2-column layout: Hero+Map and Tabs) | Dag 402 (BLOCK) | বাংলা (BN) | Dark | `800x800` |
| **24** | [`24_cockpit_wide_1000px_history.png`](./24_cockpit_wide_1000px_history.png) | Cockpit at ultra-wide 1000px width showing History tab | Dag 402 (BLOCK) | বাংলা (BN) | Dark | `1000x800` |
| **25** | [`25_security_non_allowlisted_page.png`](./25_security_non_allowlisted_page.png) | Non-allowlisted neutral site (e.g. /docs): extension injects nothing | Non-Allowlisted Page | English (EN) | Light | `1440x900` |
| **26** | *Skipped* | Portal logged out: panel locked / pill disabled | *N/A* | *N/A* | *N/A* | *N/A* |
| **27** | [`27_security_audit_access_denied.png`](./27_security_audit_access_denied.png) | Audit tab displaying cryptographic ACCESS_DENIED block | Security Audit | বাংলা (BN) | Dark | `420x800` |

## Not Captured (Architectural Rationale)

Per project rules, features not implemented or seeded in the current codebase are never faked or mocked:

1. **`16_tab_audit_tamper_demo_break.png` (Serial 16)**:
   - *Reason*: The cryptographic hash chain verifies integrity against SHA-256 and Ed25519 signatures, but no runtime tamper corruption simulation route is implemented on the server.

2. **`19_scenario_block_unmutated_deed.png` (Serial 19)**:
   - *Reason*: The seeded spatial dataset contains 3 official benchmark cohorts: Dag 402 (BLOCK: Khas Canal Overlap), Dag 401 (CLEAR: Clean Parcel), and Dag 403 (REVIEW: Tax Arrears & Unmutated Deed Gap). A separate 4th seeded parcel combining unmutated deed + bank lien as a BLOCK is not registered in the database.

3. **`26_security_portal_logged_out.png` (Serial 26)**:
   - *Reason*: The mock portal presents an active mock officer session by default and does not feature a logged-out toggle or locked-pill state.
