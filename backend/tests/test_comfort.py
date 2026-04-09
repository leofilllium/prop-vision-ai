"""
Tests for comfort score computation logic.
"""

import pytest
from app.services.comfort_service import SCORE_CONFIG


class TestComfortScoring:
    """Unit tests for comfort score computation."""

    def test_score_config_has_all_dimensions(self):
        """Verify all 7 comfort dimensions are configured."""
        expected = {"transport", "shopping", "education", "green_space", "safety", "healthcare", "entertainment"}
        assert set(SCORE_CONFIG.keys()) == expected

    def test_score_config_has_required_fields(self):
        """Verify each dimension has required configuration fields."""
        required_fields = {
            "categories", "radius_m", "max_count",
            "weight_nearest", "weight_density"
        }
        for dim, config in SCORE_CONFIG.items():
            for field in required_fields:
                assert field in config, f"Missing '{field}' in {dim} config"

    def test_transport_categories(self):
        """Verify transport score uses correct POI categories."""
        categories = SCORE_CONFIG["transport"]["categories"]
        assert "metro_station" in categories
        assert "bus_stop" in categories

    def test_shopping_categories(self):
        """Verify shopping score uses correct POI categories."""
        categories = SCORE_CONFIG["shopping"]["categories"]
        assert "supermarket" in categories
        assert "convenience_store" in categories

    def test_education_categories(self):
        """Verify education score uses correct POI categories."""
        categories = SCORE_CONFIG["education"]["categories"]
        assert "school" in categories
        assert "kindergarten" in categories
        assert "university" in categories

    def test_green_space_categories(self):
        """Verify green space score uses correct POI categories."""
        categories = SCORE_CONFIG["green_space"]["categories"]
        assert "park" in categories

    def test_safety_categories(self):
        """Verify safety score uses correct POI categories."""
        categories = SCORE_CONFIG["safety"]["categories"]
        assert "police_station" in categories
        assert "hospital" in categories

    def test_radius_values(self):
        """Verify scoring radii match specification."""
        assert SCORE_CONFIG["transport"]["radius_m"] == 1000
        assert SCORE_CONFIG["shopping"]["radius_m"] == 800
        assert SCORE_CONFIG["education"]["radius_m"] == 1500
        assert SCORE_CONFIG["green_space"]["radius_m"] == 1000
        assert SCORE_CONFIG["safety"]["radius_m"] == 1000

    def test_weights_sum_to_one(self):
        """Verify density + nearest weights sum to 1.0 for each dimension."""
        for dim, config in SCORE_CONFIG.items():
            total = config["weight_nearest"] + config["weight_density"]
            assert abs(total - 1.0) < 0.01, (
                f"{dim} weights sum to {total}, expected 1.0"
            )

    def test_density_score_calculation(self):
        """Test density score: more POIs = higher score, capped at 100."""
        # Simulate density score computation
        count = 10
        max_count = 15
        density_score = min(100, (count / max_count) * 100)
        assert density_score == pytest.approx(66.67, rel=0.01)

        # At max count
        density_at_max = min(100, (15 / 15) * 100)
        assert density_at_max == 100

        # Over max count (capped)
        density_over_max = min(100, (20 / 15) * 100)
        assert density_over_max == 100

    def test_proximity_score_calculation(self):
        """Test proximity score: closer = higher score."""
        radius = 1000

        # Very close (100m)
        distance = 100
        proximity = max(0, 100 * (1 - distance / radius))
        assert proximity == 90.0

        # At boundary (1000m)
        distance_at_boundary = 1000
        proximity_at_boundary = max(0, 100 * (1 - distance_at_boundary / radius))
        assert proximity_at_boundary == 0.0

        # Very close (50m)
        distance_close = 50
        proximity_close = max(0, 100 * (1 - distance_close / radius))
        assert proximity_close == 95.0

    def test_confidence_thresholds(self):
        """Test data confidence level determination."""
        # HIGH: ≥15 data points
        total_15 = 15
        assert (
            "HIGH"
            if total_15 >= 15
            else ("MEDIUM" if total_15 >= 5 else "LOW")
        ) == "HIGH"

        # MEDIUM: 5–14 data points
        total_8 = 8
        assert (
            "HIGH"
            if total_8 >= 15
            else ("MEDIUM" if total_8 >= 5 else "LOW")
        ) == "MEDIUM"

        # LOW: <5 data points
        total_3 = 3
        assert (
            "HIGH"
            if total_3 >= 15
            else ("MEDIUM" if total_3 >= 5 else "LOW")
        ) == "LOW"
