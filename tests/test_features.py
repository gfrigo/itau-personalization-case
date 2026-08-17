from itau_purchase_propensity.domain.features import compute_features, to_feature_row


def test_compute_features_known_user_matching_category(repo):
    features = compute_features(repo, "u1", "p_a1")

    assert features == {
        "interactions": 2,  # view + purchase
        "price": 100.0,
        "avg_rating": 4.5,
        "popularity_score": 0.8,
        "user_affinity_match": 1,  # afinidade de u1 e eletronicos, igual a categoria de p_a1
    }


def test_compute_features_known_user_different_category(repo):
    features = compute_features(repo, "u2", "p_a1")

    assert features["interactions"] == 0
    assert features["user_affinity_match"] == 0  # afinidade de u2 e livros, produto e eletronicos


def test_compute_features_unknown_user_has_no_interactions_or_affinity(repo):
    features = compute_features(repo, "ghost", "p_a1")

    assert features["interactions"] == 0
    assert features["user_affinity_match"] == 0


def test_to_feature_row_respects_feature_cols_order(repo):
    features = compute_features(repo, "u1", "p_a1")

    row = to_feature_row(features, ["price", "user_affinity_match", "interactions"])

    assert row == [100.0, 1, 2]
