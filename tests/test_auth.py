def test_demo_login_and_auth_profile(client):
    # Test demo login for donor
    res = client.post("/api/v1/auth/demo-login?role=donor")
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["profile"]["role"] == "donor"

    token = data["access_token"]
    # Get profile with bearer token
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["role"] == "donor"
