def test_register_login_and_current_user(client):
    register_response = client.post(
        "/auth/register",
        json={
            "email": "newlearner@example.com",
            "full_name": "New Learner",
            "password": "secret123",
        },
    )

    assert register_response.status_code == 201
    token = register_response.json()["access_token"]

    me_response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "newlearner@example.com"
    assert me_response.json()["role"] == "learner"

    login_response = client.post(
        "/auth/login",
        json={"email": "newlearner@example.com", "password": "secret123"},
    )
    assert login_response.status_code == 200
    assert login_response.json()["token_type"] == "bearer"
