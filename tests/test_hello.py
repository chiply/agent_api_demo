async def test_get_hello(client):
    response = await client.get("/hello")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, world!"}
