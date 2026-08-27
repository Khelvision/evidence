"""The site's release index is generated, so the page cannot claim something the registries do not.

The prose on the page is authored. Everything between the generated markers is a deterministic
allowlisted projection of `registry/*.json`, and these tests fail if the checked-in page drifts from
that projection or if the renderer would publish something it should refuse.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "site" / "index.html"


@pytest.fixture(scope="module")
def renderer() -> Any:
    spec = importlib.util.spec_from_file_location("render_site", ROOT / "tools" / "render_site.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _release(**overrides: Any) -> dict[str, Any]:
    release = {
        "artifact_id": "release-synthetic-v0-1",
        "digest": {"algorithm": "sha256", "value": "a" * 64},
        "media_type": "application/gzip",
    }
    release.update(overrides)
    return release


def test_checked_in_page_matches_the_renderer(renderer: Any) -> None:
    assert PAGE.read_text(encoding="utf-8") == renderer.render_page()


def test_generated_block_is_the_only_generated_region(renderer: Any) -> None:
    page = PAGE.read_text(encoding="utf-8")
    assert page.count(renderer.BEGIN) == 1
    assert page.count(renderer.END) == 1
    assert page.index(renderer.BEGIN) < page.index(renderer.END)


def test_empty_registries_say_so_from_the_data(renderer: Any) -> None:
    block = renderer.render_block({"official": [], "community": []})

    assert "Both registries are empty" in block
    assert "No official releases." in block
    assert "No community releases." in block
    assert "<table>" not in block


def test_official_and_community_stay_visibly_separate(renderer: Any) -> None:
    block = renderer.render_block({"official": [_release()], "community": [_release()]})

    assert 'data-registry="official"' in block
    assert 'data-registry="community"' in block
    assert block.index('data-registry="official"') < block.index('data-registry="community"')
    assert "endorsement, licence clearance, or a quality award" in block
    assert "Both registries are empty" not in block


def test_release_rows_render_their_content_address(renderer: Any) -> None:
    block = renderer.render_block({"official": [_release()], "community": []})

    assert "release-synthetic-v0-1" in block
    assert "a" * 64 in block
    assert "application/gzip" in block


def test_releases_are_ordered_by_artifact_id(renderer: Any, tmp_path: Path, monkeypatch) -> None:
    _write_registries(
        renderer,
        tmp_path,
        monkeypatch,
        official=[_release(artifact_id="release-b"), _release(artifact_id="release-a")],
    )
    projected = renderer.project_registries()

    assert [entry["artifact_id"] for entry in projected["official"]] == ["release-a", "release-b"]


def test_unallowlisted_field_is_refused(renderer: Any) -> None:
    with pytest.raises(renderer.SiteRefused, match="unpublishable field"):
        renderer.project_release(_release(internal_owner="asha"), "registry.official.releases[0]")


def test_unallowlisted_digest_field_is_refused(renderer: Any) -> None:
    release = _release(digest={"algorithm": "sha256", "value": "a" * 64, "salt": "private"})

    with pytest.raises(renderer.SiteRefused, match="digest carries unpublishable field"):
        renderer.project_release(release, "registry.official.releases[0]")


def test_unsafe_value_is_refused(renderer: Any) -> None:
    with pytest.raises(renderer.SiteRefused, match="not publishable"):
        renderer.project_release(
            _release(media_type="video/mp4; src=http://192.168.1.2/master"),
            "registry.official.releases[0]",
        )


def test_markup_in_registry_data_cannot_become_markup(renderer: Any) -> None:
    block = renderer.render_block(
        {"official": [_release(media_type="<script>alert(1)</script>")], "community": []}
    )

    assert "<script>" not in block
    assert "&lt;script&gt;" in block


def test_invalid_registry_is_refused(renderer: Any, tmp_path: Path, monkeypatch) -> None:
    _write_registries(renderer, tmp_path, monkeypatch, official_overrides={"registry": "community"})

    with pytest.raises(renderer.SiteRefused, match="declares registry"):
        renderer.project_registries()


def test_registry_failing_its_contract_is_refused(
    renderer: Any, tmp_path: Path, monkeypatch
) -> None:
    _write_registries(renderer, tmp_path, monkeypatch, official_overrides={"schema_version": "9"})

    with pytest.raises(renderer.SiteRefused, match="not a valid registry"):
        renderer.project_registries()


def test_release_data_digest_binds_the_projection(renderer: Any) -> None:
    empty = renderer.release_data_digest({"official": [], "community": []})
    filled = renderer.release_data_digest({"official": [_release()], "community": []})

    assert empty != filled
    assert empty == renderer.release_data_digest({"official": [], "community": []})
    assert empty in PAGE.read_text(encoding="utf-8")


def _write_registries(
    renderer: Any,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    official: list[dict[str, Any]] | None = None,
    official_overrides: dict[str, Any] | None = None,
) -> None:
    registry = tmp_path / "registry"
    registry.mkdir()
    for name in ("official", "community"):
        document: dict[str, Any] = {
            "schema_name": "EvidenceRegistryV1",
            "schema_version": "1.0.0",
            "record_id": f"registry-{name}-v1",
            "registry": name,
            "releases": official if name == "official" and official else [],
        }
        if name == "official" and official_overrides:
            document.update(official_overrides)
        (registry / f"{name}.json").write_text(json.dumps(document), encoding="utf-8")
    monkeypatch.setattr(renderer, "REGISTRY", registry)
