def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_openapi_lists_all_endpoints(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert {path: set(methods) for path, methods in paths.items()} == {
        "/api/health": {"get"},
        "/api/photos": {"post"},
        "/api/photos/{photo_id}": {"get"},
        "/api/photos/{photo_id}/preview": {"post"},
        "/api/photos/{photo_id}/render": {"post"},
        "/api/photos/{photo_id}/estimate": {"post"},
        "/api/jobs/{job_id}": {"get"},
        "/api/gallery": {"get", "post"},
        "/api/gallery/{item_id}": {"delete"},
    }


def test_every_endpoint_has_a_summary(client):
    paths = client.get("/openapi.json").json()["paths"]
    missing = [
        f"{method.upper()} {path}"
        for path, operations in paths.items()
        for method, operation in operations.items()
        if not operation.get("summary")
    ]
    assert missing == []
