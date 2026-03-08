async def test_get_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_get_ready_when_otel_disabled(client):
    """When OTEL_SDK_DISABLED=true (test default), /ready should return ready."""
    response = await client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
