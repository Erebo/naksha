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
