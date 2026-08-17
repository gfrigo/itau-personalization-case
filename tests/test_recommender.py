from itau_purchase_propensity.domain.recommender import cold_start_ranking, recommend


def test_recommend_known_user_ranks_by_model_score(repo, fake_model):
    result = recommend("u1", repo, fake_model, top_n=2)

    assert result.cold_start is False
    assert [item.product_id for item in result.items] == ["p_a1", "p_b1"]
    assert result.items[0].score > result.items[1].score


def test_recommend_unknown_user_triggers_cold_start(repo, fake_model):
    result = recommend("ghost", repo, fake_model, top_n=2)

    assert result.cold_start is True
    assert [item.product_id for item in result.items] == ["p_a1", "p_b1"]


def test_cold_start_ranking_guarantees_category_coverage(repo):
    # Trending puro colocaria p_a3 (eletronicos, 5.0) a frente de p_b1 (livros, 3.0),
    # deixando "livros" de fora do top 2. A cota por categoria evita isso.
    ranking = cold_start_ranking(repo, top_n=2)

    assert ranking == ["p_a1", "p_b1"]
    categories = {repo.products[pid]["category"] for pid in ranking}
    assert categories == {"eletronicos", "livros"}


def test_cold_start_ranking_orders_by_trending_when_all_fit(repo):
    ranking = cold_start_ranking(repo, top_n=5)

    assert ranking == ["p_a1", "p_a3", "p_b1", "p_b2", "p_a2"]
