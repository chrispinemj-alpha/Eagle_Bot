from eagle_bot.app import create_app


def test_health_endpoint():
    client = create_app().test_client()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_coworkers_endpoint():
    client = create_app().test_client()
    response = client.get("/api/coworkers")
    assert response.status_code == 200
    assert len(response.get_json()) == 6


def test_prepare_endpoint():
    client = create_app().test_client()
    response = client.post("/api/orders/prepare", json={"owner_id": "u1", "objective": "Research a topic"})
    assert response.status_code == 200
    assert response.get_json()["status"] == "prepared"
