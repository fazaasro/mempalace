"""Tests for mempalace.onboarding."""

import os

from mempalace.onboarding import (
    DEFAULT_WINGS,
    _generate_aaak_bootstrap,
    _warn_ambiguous,
    quick_setup,
)

# Force UTF-8 for Windows (source file contains Unicode symbols like hearts/stars)
os.environ["PYTHONUTF8"] = "1"


# ── DEFAULT_WINGS ───────────────────────────────────────────────────────


def test_default_wings_has_expected_keys():
    assert "work" in DEFAULT_WINGS
    assert "personal" in DEFAULT_WINGS
    assert "combo" in DEFAULT_WINGS


def test_default_wings_work_has_projects():
    assert "projects" in DEFAULT_WINGS["work"]


def test_default_wings_personal_has_family():
    assert "family" in DEFAULT_WINGS["personal"]


def test_default_wings_combo_has_both():
    wings = DEFAULT_WINGS["combo"]
    assert "family" in wings
    assert "work" in wings


def test_default_wings_values_are_lists():
    for mode, wings in DEFAULT_WINGS.items():
        assert isinstance(wings, list), f"{mode} wings should be a list"
        assert len(wings) >= 3, f"{mode} should have at least 3 wings"


# ── _warn_ambiguous ─────────────────────────────────────────────────────


def test_warn_ambiguous_flags_common_words():
    people = [
        {"name": "Grace", "relationship": "friend"},
        {"name": "Riley", "relationship": "daughter"},
    ]
    result = _warn_ambiguous(people)
    assert "Grace" in result
    # Riley is not a common English word
    assert "Riley" not in result


def test_warn_ambiguous_empty_list():
    result = _warn_ambiguous([])
    assert result == []


def test_warn_ambiguous_no_ambiguous_names():
    people = [
        {"name": "Riley", "relationship": "daughter"},
        {"name": "Devon", "relationship": "friend"},
    ]
    result = _warn_ambiguous(people)
    assert result == []


def test_warn_ambiguous_multiple_hits():
    people = [
        {"name": "Grace", "relationship": "friend"},
        {"name": "May", "relationship": "aunt"},
        {"name": "Joy", "relationship": "sister"},
    ]
    result = _warn_ambiguous(people)
    assert "Grace" in result
    assert "May" in result
    assert "Joy" in result


# ── quick_setup ─────────────────────────────────────────────────────────


def test_quick_setup_creates_registry(tmp_path):
    registry = quick_setup(
        mode="personal",
        people=[{"name": "Riley", "relationship": "daughter", "context": "personal"}],
        projects=["MemPalace"],
        config_dir=tmp_path,
    )
    assert "Riley" in registry.people
    assert "MemPalace" in registry.projects
    assert registry.mode == "personal"


def test_quick_setup_work_mode(tmp_path):
    registry = quick_setup(
        mode="work",
        people=[{"name": "Alice", "relationship": "colleague", "context": "work"}],
        projects=["Acme"],
        config_dir=tmp_path,
    )
    assert registry.mode == "work"
    assert "Alice" in registry.people
    assert "Acme" in registry.projects


def test_quick_setup_empty(tmp_path):
    registry = quick_setup(mode="personal", people=[], config_dir=tmp_path)
    assert len(registry.people) == 0
    assert len(registry.projects) == 0


def test_quick_setup_saves_to_disk(tmp_path):
    quick_setup(
        mode="personal",
        people=[{"name": "Riley", "relationship": "daughter", "context": "personal"}],
        config_dir=tmp_path,
    )
    assert (tmp_path / "entity_registry.json").exists()


# ── _generate_aaak_bootstrap ───────────────────────────────────────────


def test_generate_aaak_bootstrap_creates_files(tmp_path):
    people = [
        {"name": "Riley", "relationship": "daughter", "context": "personal"},
        {"name": "Devon", "relationship": "friend", "context": "personal"},
    ]
    projects = ["MemPalace"]
    wings = ["family", "creative"]
    _generate_aaak_bootstrap(people, projects, wings, "personal", config_dir=tmp_path)

    assert (tmp_path / "aaak_entities.md").exists()
    assert (tmp_path / "critical_facts.md").exists()


def test_generate_aaak_bootstrap_entities_content(tmp_path):
    people = [{"name": "Riley", "relationship": "daughter", "context": "personal"}]
    projects = ["MemPalace"]
    wings = ["family"]
    _generate_aaak_bootstrap(people, projects, wings, "personal", config_dir=tmp_path)

    content = (tmp_path / "aaak_entities.md").read_text()
    assert "Riley" in content
    assert "RIL" in content  # entity code
    assert "MemPalace" in content


def test_generate_aaak_bootstrap_facts_content(tmp_path):
    people = [
        {"name": "Alice", "relationship": "colleague", "context": "work"},
    ]
    projects = ["Acme"]
    wings = ["projects"]
    _generate_aaak_bootstrap(people, projects, wings, "work", config_dir=tmp_path)

    content = (tmp_path / "critical_facts.md").read_text()
    assert "Alice" in content
    assert "Acme" in content
    assert "work" in content.lower()


def test_generate_aaak_bootstrap_empty_people(tmp_path):
    _generate_aaak_bootstrap([], [], ["general"], "personal", config_dir=tmp_path)
    assert (tmp_path / "aaak_entities.md").exists()
    assert (tmp_path / "critical_facts.md").exists()
