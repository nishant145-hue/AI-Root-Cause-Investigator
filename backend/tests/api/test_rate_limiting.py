from uuid import uuid4

from app.core.rate_limit import limiter


def test_login_rate_limit_returns_429(client, monkeypatch):
    """
    Verify that the login endpoint returns HTTP 429
    after exceeding its configured rate limit.
    """

    # Enable the limiter only for this test.
    # monkeypatch automatically restores the original value
    # after the test completes.
    monkeypatch.setattr(limiter, "enabled", True)

    # Use a unique IP so this test starts with a clean bucket.
    client_ip = f"10.0.{uuid4().int % 250}.{uuid4().int % 250}"

    headers = {
        "X-Forwarded-For": client_ip,
    }

    responses = []

    for _ in range(6):
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "nonexistent@example.com",
                "password": "WrongPassword123!",
            },
            headers=headers,
        )

        responses.append(response)

    # At least one request must be rate limited.
    assert any(
        response.status_code == 429
        for response in responses
    )

    # The rate-limit response must not expose internals.
    rate_limited = next(
        response
        for response in responses
        if response.status_code == 429
    )

    detail = rate_limited.text.lower()

    assert "traceback" not in detail
    assert "exception" not in detail
    assert "secret_key" not in detail
    assert "database" not in detail