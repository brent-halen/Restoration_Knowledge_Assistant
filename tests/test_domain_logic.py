from src.knowledge_base import infer_damage_type
from src.tools import _load_technicians, _normalize_damage_type


def test_infer_damage_type_from_filename():
    assert infer_damage_type("water_damage_playbook.md") == "water_damage"
    assert infer_damage_type("mold_remediation_notes.md") == "mold"
    assert infer_damage_type("fire_smoke_cleanup.md") == "fire_damage"
    assert infer_damage_type("insurance_documentation_checklist.md") == "general"


def test_normalize_damage_type_aliases():
    assert _normalize_damage_type("water") == "water_damage"
    assert _normalize_damage_type("water damage") == "water_damage"
    assert _normalize_damage_type("fire") == "fire_damage"
    assert _normalize_damage_type("smoke") == "fire_damage"
    assert _normalize_damage_type("something unexpected") == "general"


def test_mock_technicians_load():
    technicians = _load_technicians()
    assert technicians
    assert any(record.on_call for record in technicians)
    assert all(record.name for record in technicians)
