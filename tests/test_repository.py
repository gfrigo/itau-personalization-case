def test_is_known_user(repo):
    assert repo.is_known_user("u1") is True
    assert repo.is_known_user("ghost") is False


def test_get_interaction_count_sums_all_event_types(repo):
    assert repo.get_interaction_count("u1", "p_a1") == 2
    assert repo.get_interaction_count("u1", "p_b2") == 0


def test_get_affinity_category_picks_most_frequent_category(repo):
    assert repo.get_affinity_category("u1") == "eletronicos"
    assert repo.get_affinity_category("u2") == "livros"
    assert repo.get_affinity_category("ghost") is None


def test_get_trending_score_defaults_to_zero_without_recent_events(repo):
    assert repo.get_trending_score("p_a2") == 0.0


def test_get_trending_score_weights_purchase_above_view(repo):
    assert repo.get_trending_score("p_a1") > repo.get_trending_score("p_b2")
