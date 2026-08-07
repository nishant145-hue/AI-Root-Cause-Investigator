def test_export_csv(client):
    response = client.get("/api/v1/reports/csv")

    assert response.status_code == 200

    assert response.headers["content-type"].startswith(
        "text/csv"
    )
    
def test_export_excel(client):
    response = client.get("/api/v1/reports/excel")

    assert response.status_code == 200

    assert response.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument"
    )
    
def test_export_pdf(client):
    response = client.get("/api/v1/reports/pdf")

    assert response.status_code == 200

    assert response.headers["content-type"].startswith(
        "application/pdf"
    )