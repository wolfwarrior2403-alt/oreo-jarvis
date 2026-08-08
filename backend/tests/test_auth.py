import os


def test_pair_with_valid_code_returns_tokens(client):
    resp = client.post(
        "/auth/pair",
        json={
            "pairing_code": os.environ["DEVICE_PAIRING_CODE"],
            "device_name": "phone-1",
            "user_display_name": "Alice",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["user_id"]
    assert body["device_id"]


def test_pair_with_invalid_code_rejected(client):
    resp = client.post(
        "/auth/pair",
        json={"pairing_code": "wrong-code", "device_name": "phone-1"},
    )
    assert resp.status_code == 401


def test_protected_endpoint_requires_token(client):
    resp = client.get("/actions/pending")
    assert resp.status_code in (401, 403)


def test_protected_endpoint_rejects_garbage_token(client):
    resp = client.get("/actions/pending", headers={"Authorization": "Bearer not-a-real-token"})
    assert resp.status_code == 401


def test_refresh_token_rotates_and_old_one_is_rejected(client, paired_device):
    resp = client.post("/auth/refresh", json={"refresh_token": paired_device["refresh_token"]})
    assert resp.status_code == 200
    new_tokens = resp.json()
    assert new_tokens["access_token"] != paired_device["access_token"]
    assert new_tokens["refresh_token"] != paired_device["refresh_token"]

    # Reusing the old (now-rotated-away) refresh token must fail.
    resp = client.post("/auth/refresh", json={"refresh_token": paired_device["refresh_token"]})
    assert resp.status_code == 401
