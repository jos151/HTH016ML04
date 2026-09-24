"""
Test suite validating the integrity, structure, and pipeline execution of all test fixtures.
"""

from pathlib import Path
import pytest
from scripts.generate_test_fixtures import validate_fixtures


def test_all_fixtures_integrity():
    """Runs automated validation across all 12 generated test fixtures."""
    fixtures_dir = Path(__file__).resolve().parent.parent / "data" / "test_fixtures"
    assert fixtures_dir.exists(), "Fixtures directory does not exist"

    manifest_file = fixtures_dir / "README.md"
    assert manifest_file.exists(), "Manifest README.md missing"

    meta_file = fixtures_dir / "fixtures_metadata.json"
    assert meta_file.exists(), "Companion metadata JSON missing"

    results = validate_fixtures(fixtures_dir)
    assert len(results) == 12, f"Expected 12 validated fixtures, got {len(results)}"

    for fixture_name, res in results.items():
        assert res["status"] == "VALIDATED", f"Fixture {fixture_name} failed validation"
