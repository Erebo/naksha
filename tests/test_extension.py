"""Tests for Chrome Extension Manifest V3 configuration, files, and contracts."""
import json
from pathlib import Path

EXTENSION_DIR = Path(__file__).resolve().parent.parent / "extension"


def test_manifest_v3_validity():
    """Verify manifest.json conforms to Manifest V3 requirements."""
    manifest_file = EXTENSION_DIR / "manifest.json"
    assert manifest_file.exists(), "manifest.json must exist in extension directory"

    with open(manifest_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data.get("manifest_version") == 3
    assert data.get("name")
    assert data.get("version") == "1.0.0"

    # Verify side panel configuration
    assert "side_panel" in data
    assert data["side_panel"].get("default_path") == "sidepanel.html"

    # Verify background service worker
    assert "background" in data
    assert data["background"].get("service_worker") == "background.js"

    # Verify permissions
    assert "sidePanel" in data.get("permissions", [])
    assert "storage" in data.get("permissions", [])

    # Verify content script targets mock portals only
    content_scripts = data.get("content_scripts", [])
    assert len(content_scripts) >= 1
    matches = content_scripts[0].get("matches", [])
    assert any("portals" in m for m in matches)
    # Ensure live gov sites are NOT targeted
    assert not any("gov.bd" in m for m in matches)


def test_extension_required_files_exist():
    """Verify all referenced files in manifest actually exist on disk."""
    required_files = [
        "manifest.json",
        "background.js",
        "content.js",
        "content.css",
        "sidepanel.html",
        "sidepanel.css",
        "sidepanel.js",
        "icons/icon16.png",
        "icons/icon48.png",
        "icons/icon128.png",
        "vendor/leaflet/leaflet.js",
        "vendor/leaflet/leaflet.css",
    ]

    for rel_path in required_files:
        target = EXTENSION_DIR / rel_path
        assert target.exists(), f"Required extension file {rel_path} does not exist"
        assert target.stat().st_size > 0, f"File {rel_path} must not be empty"


def test_sidepanel_html_contract():
    """Verify sidepanel.html contains required Bangla Leaflet GIS structures."""
    sidepanel_file = EXTENSION_DIR / "sidepanel.html"
    html = sidepanel_file.read_text(encoding="utf-8")

    # GIS Map element
    assert 'id="sp-map"' in html
    # Bengali headers and typography
    assert "নকশা" in html
    assert "ক্যাডাস্ট্রাল জিআইএস" in html
    # Context bar for detected identifiers
    assert 'id="sp-detected-dag"' in html
    assert 'id="sp-detected-khatian"' in html
    assert 'id="sp-detected-mouza"' in html
    # Trust Ledger Tab
    assert 'id="tab-ledger"' in html
    assert "Ed25519" in html
    # Synthetic notice
    assert "কৃত্রিম ডেমো ডেটা" in html


def test_sidepanel_mv3_csp_compliance():
    """Verify sidepanel.html complies with Chrome MV3 CSP by executing no remote scripts."""
    sidepanel_file = EXTENSION_DIR / "sidepanel.html"
    html = sidepanel_file.read_text(encoding="utf-8")

    # All script src must be local relative paths, no remote CDNs
    import re
    script_srcs = re.findall(r'<script\s+[^>]*src=["\']([^"\']+)["\']', html)
    for src in script_srcs:
        assert not src.startswith("http://") and not src.startswith("https://"), (
            f"Remote script src '{src}' violates Chrome Extension Manifest V3 CSP"
        )
    assert any("vendor/leaflet/leaflet.js" in s for s in script_srcs)


def test_extension_uses_clean_osm_tilelayer_without_carto_watermark():
    """Verify sidepanel.js uses OpenStreetMap and has no API-key-required CartoDB watermark."""
    sidepanel_js = (EXTENSION_DIR / "sidepanel.js").read_text(encoding="utf-8")
    assert "tile.openstreetmap.org" in sidepanel_js
    assert "cartocdn.com" not in sidepanel_js


def test_extension_resilience_and_timeout_protection():
    """Verify sidepanel.js has AbortController timeout and Leaflet existence guards."""
    sidepanel_js = (EXTENSION_DIR / "sidepanel.js").read_text(encoding="utf-8")
    assert "AbortController" in sidepanel_js
    assert "typeof L === 'undefined'" in sidepanel_js
    assert "sp-tile-warning" in sidepanel_js
    assert "resolveParcelId" in sidepanel_js


def test_extension_content_script_sidepanel_guidance():
    """Verify content.js contains Bangla guidance toast if programmatic sidepanel is restricted."""
    content_js = (EXTENSION_DIR / "content.js").read_text(encoding="utf-8")
    assert "showPanelGuideToast" in content_js
    assert "নকশা (NAKSHA) সাইড প্যানেল নির্দেশিকা" in content_js
    assert "NAKSHA_OPEN_SIDEPANEL" in content_js


def test_rule_grid_renders_backend_rules_without_hardcoded_numbers():
    """Verify RuleGrid.js dynamically renders data.rules and has no hardcoded values or statutes."""
    rule_grid_js = (EXTENSION_DIR / "components" / "RuleGrid.js").read_text(encoding="utf-8")

    # 1. No hardcoded metric numbers or static values
    assert "0.90" not in rule_grid_js
    assert "০.৯০" not in rule_grid_js
    assert "124" not in rule_grid_js
    assert "১২৪" not in rule_grid_js
    assert "64%" not in rule_grid_js
    assert "৬৪%" not in rule_grid_js
    assert "5.10" not in rule_grid_js
    assert "6.00" not in rule_grid_js

    # 2. No hardcoded Act citations
    assert "State Acquisition Act" not in rule_grid_js
    assert "রাষ্ট্রীয় অধিগ্রহণ আইন" not in rule_grid_js
    assert "§86" not in rule_grid_js
    assert "ধারা ৮৬" not in rule_grid_js

    # 3. Dynamic rules rendering & UNKNOWN state handling
    assert "data.rules" in rule_grid_js
    assert "UNKNOWN" in rule_grid_js
    assert "Insufficient data" in rule_grid_js
    assert "অপর্যাপ্ত তথ্য" in rule_grid_js
    assert "legal_ref" in rule_grid_js
    assert "cited_record_ids" in rule_grid_js
