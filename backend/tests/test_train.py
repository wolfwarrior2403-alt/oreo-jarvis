import io


def test_upload_text_file_is_chunked_and_indexed(client, auth_headers, stub_heavy_dependencies):
    content = ("Oreo is a personal AI assistant. " * 50).encode("utf-8")
    resp = client.post(
        "/train/upload",
        headers=auth_headers,
        files={"files": ("notes.txt", io.BytesIO(content), "text/plain")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["indexed"] is True
    assert body[0]["chunk_count"] > 0
    assert len(stub_heavy_dependencies.items) == body[0]["chunk_count"]


def test_upload_unsupported_type_is_stored_but_not_indexed(client, auth_headers):
    resp = client.post(
        "/train/upload",
        headers=auth_headers,
        files={"files": ("audio.bin", io.BytesIO(b"\x00\x01\x02"), "application/octet-stream")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body[0]["indexed"] is False
    assert body[0]["chunk_count"] == 0


def test_upload_requires_auth(client):
    resp = client.post("/train/upload", files={"files": ("notes.txt", io.BytesIO(b"hi"), "text/plain")})
    assert resp.status_code in (401, 403)
