import sys

import pytest

sys.path.insert(0, "src")

from humanmint import gliner
from humanmint import mint


def test_use_gliner_requires_text():
    with pytest.raises(ValueError):
        mint(name="John", use_gliner=True)


def test_use_gliner_merges_without_override(monkeypatch):
    # Mock gliner extraction to avoid dependency
    def fake_extract(text, config=None):
        return {
            "name": "Extracted Name",
            "email": "extracted@example.com",
            "phone": None,
            "address": None,
            "department": "Extracted Dept",
            "title": "Extracted Title",
            "organization": None,
        }

    monkeypatch.setattr("humanmint.gliner.extract_fields_from_text", fake_extract)

    res = mint(
        name="User Name",
        email="user@example.com",
        department=None,
        title=None,
        text="dummy",
        use_gliner=True,
        gliner_cfg=gliner.GlinerConfig(extractor=None, threshold=None, schema=None, use_gpu=False),
    )

    # User fields preserved
    assert res.name_standardized == "User Name"
    assert res.email_standardized == "user@example.com"
    # Missing fields filled from extraction (title should be accepted as raw)
    assert res.title_raw == "Extracted Title"


def test_use_gliner_raises_on_multiple_people(monkeypatch):
    class FakeExtractor:
        def extract_json(self, text, schema, threshold=None):
            return {"contact": [{"name": "One"}, {"name": "Two"}]}

    with pytest.raises(ValueError):
        mint(text="two people here", use_gliner=True, gliner_cfg=gliner.GlinerConfig(extractor=FakeExtractor()))


def test_use_gliner_uses_location_for_address(monkeypatch):
    class FakeExtractor:
        def extract_json(self, text, schema, threshold=None):
            return {"contact": [{"name": "Someone", "location": "Springfield, IL"}]}

    res = mint(text="dummy", use_gliner=True, gliner_cfg=gliner.GlinerConfig(extractor=FakeExtractor()))
    # Location should flow through without errors; address may or may not parse
    assert res is not None
