def test_dashboard_overview(
    client,
    auth_headers,
):
    response = client.get(
        "/api/v1/dashboard/overview",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert isinstance(response.json(), dict)


def test_dashboard_recent(
    client,
    auth_headers,
):
    response = client.get(
        "/api/v1/dashboard/recent",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_dashboard_timeline(
    client,
    auth_headers,
):
    response = client.get(
        "/api/v1/dashboard/timeline",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_dashboard_severity(
    client,
    auth_headers,
):
    response = client.get(
        "/api/v1/dashboard/severity",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_dashboard_root_causes(
    client,
    auth_headers,
):
    response = client.get(
        "/api/v1/dashboard/root-causes",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_dashboard_failed_components(
    client,
    auth_headers,
):
    response = client.get(
        "/api/v1/dashboard/failed-components",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_dashboard_confidence(
    client,
    auth_headers,
):
    response = client.get(
        "/api/v1/dashboard/confidence",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert isinstance(response.json(), dict)