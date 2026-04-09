from app.schemas.search import ParsedFilters
from app.services.ai_search_service import AISearchService


def test_infers_green_space_sort_for_park_proximity():
    filters = ParsedFilters(proximity_to="park")

    updated = AISearchService.infer_comfort_sort_from_proximity(filters)

    assert updated.sort_by_comfort == "green_space"


def test_infers_education_sort_for_school_proximity():
    filters = ParsedFilters(proximity_to="school")

    updated = AISearchService.infer_comfort_sort_from_proximity(filters)

    assert updated.sort_by_comfort == "education"


def test_keeps_explicit_sort_when_present():
    filters = ParsedFilters(proximity_to="school", sort_by_comfort="safety")

    updated = AISearchService.infer_comfort_sort_from_proximity(filters)

    assert updated.sort_by_comfort == "safety"


def test_keeps_sort_none_for_unknown_proximity():
    filters = ParsedFilters(proximity_to="unknown_category")

    updated = AISearchService.infer_comfort_sort_from_proximity(filters)

    assert updated.sort_by_comfort is None


def test_infers_education_sort_from_russian_school_keyword():
    filters = ParsedFilters()

    updated = AISearchService.infer_comfort_sort_from_query_text(
        "квартира рядом со школой",
        filters,
    )

    assert updated.sort_by_comfort == "education"


def test_infers_green_space_sort_from_uzbek_park_keyword():
    filters = ParsedFilters()

    updated = AISearchService.infer_comfort_sort_from_query_text(
        "kvartira park yaqinida",
        filters,
    )

    assert updated.sort_by_comfort == "green_space"


def test_keeps_explicit_sort_for_query_text_inference():
    filters = ParsedFilters(sort_by_comfort="safety")

    updated = AISearchService.infer_comfort_sort_from_query_text(
        "apartment near school",
        filters,
    )

    assert updated.sort_by_comfort == "safety"
