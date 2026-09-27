from app.services.rag_service import rag_service
from app.services.llm_service import llm_service


def test_rag_search_good_samaritan():
    res = rag_service.search_knowledge("Are donors protected from liability under the Good Samaritan Act?")
    assert "Bill Emerson Good Samaritan" in res["answer"]
    assert len(res["sources"]) >= 1
    assert res["confidence_score"] > 0.6


def test_rag_search_temperature_danger_zone():
    res = rag_service.search_knowledge("What is the temperature danger zone for cooked food?")
    assert "4" in res["answer"] or "60" in res["answer"]
    assert len(res["sources"]) >= 1


def test_llm_recipe_generation():
    recipe = llm_service.generate_rescue_recipe(
        ingredients=["Ripe Tomatoes", "Sourdough Bread", "Chickpeas"],
        dietary_preference="vegan",
        servings=40
    )
    assert "recipe_title" in recipe
    assert "instructions" in recipe
    assert len(recipe["instructions"]) >= 2
    assert "safety_tips" in recipe
