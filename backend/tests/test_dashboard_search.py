from tests.helpers import first_track


def test_dashboard_recommends_next_lesson(client, learner_headers):
    response = client.get("/dashboard", headers=learner_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["active_track"] == "Python Backend Junior Path"
    assert body["recommended_next_lesson"]["title"] == "Why return is better than print for backend logic"
    assert body["current_level"] == "Programming Foundation"


def test_track_taxonomy_contains_clean_nested_learning_structure(client, learner_headers):
    track = first_track(client, learner_headers)
    response = client.get(f"/tracks/{track['id']}", headers=learner_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["language"]["slug"] == "python"
    assert body["levels"]
    assert body["levels"][0]["modules"]
    assert body["levels"][0]["modules"][0]["lessons"]


def test_search_returns_content_and_practice_surfaces(client, learner_headers):
    response = client.get("/search?q=return", headers=learner_headers)

    assert response.status_code == 200
    body = response.json()
    assert any(item["type"] == "concept_tag" for item in body["concept_tags"])
    assert any("return" in item["title"].lower() for item in body["lessons"])
    assert body["questions"]
    assert body["debug_tasks"]
    assert body["mini_tasks"]
