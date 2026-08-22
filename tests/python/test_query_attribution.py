from narhnsw.query_attribution import _orientation_flags


def test_orientation_requires_unvisited_target_and_hnsw_queue_eligibility():
    assert _orientation_flags(
        expansion_event=10,
        target_visit_event=12,
        target_distance=2.0,
        source_distance=3.0,
        lower_bound=2.5,
        result_size=10,
        search_ef=10,
    ) == (True, True, True)
    assert _orientation_flags(
        expansion_event=10,
        target_visit_event=9,
        target_distance=1.0,
        source_distance=3.0,
        lower_bound=2.5,
        result_size=10,
        search_ef=10,
    ) == (False, False, False)
    assert _orientation_flags(
        expansion_event=10,
        target_visit_event=None,
        target_distance=4.0,
        source_distance=3.0,
        lower_bound=2.5,
        result_size=10,
        search_ef=10,
    ) == (True, False, False)


def test_orientation_uses_free_result_capacity_before_distance_bound():
    assert _orientation_flags(
        expansion_event=10,
        target_visit_event=None,
        target_distance=4.0,
        source_distance=3.0,
        lower_bound=2.5,
        result_size=4,
        search_ef=10,
    ) == (True, True, False)
