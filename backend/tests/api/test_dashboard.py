def test_dashboard_overview(client):
    response = client.get("/api/v1/dashboard/overview")

    assert response.status_code == 200

    data = response.json()

    assert "total_investigations" in data
    assert "average_confidence" in data


def test_dashboard_recent(client):
    response = client.get("/api/v1/dashboard/recent")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_dashboard_timeline(client):
    response = client.get("/api/v1/dashboard/timeline")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_dashboard_severity(client):
    response = client.get("/api/v1/dashboard/severity")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_dashboard_root_causes(client):
    response = client.get("/api/v1/dashboard/root-causes")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_dashboard_failed_components(client):
    response = client.get("/api/v1/dashboard/failed-components")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_dashboard_confidence(client):
    response = client.get("/api/v1/dashboard/confidence")

    assert response.status_code == 200

    data = response.json()

    assert "average_confidence" in data
    assert "minimum_confidence" in data
    assert "maximum_confidence" in data