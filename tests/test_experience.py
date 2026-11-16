from conftest import asset, login, notice, post


def test_search_respects_notice_audience_and_asset_ownership(client):
    login(client)
    notice(client, title="Private Test record", departments="1", roles="employee")
    notice(client, title="Future Test record", starts_at="2099-01-01T00:00")
    asset(client, tag="TEST-LAPTOP")
    post(client, "/assetpass/assets/1/assign", user_id="4", condition="Good")
    login(client, "bob")
    result = client.get("/api/experience/search?q=test").json["results"]
    assert result == []
    login(client, "alice")
    result = client.get("/api/experience/search?q=test").json["results"]
    assert {r["title"] for r in result} == {"Private Test record", "TEST-LAPTOP"}
    assert all("purchase_cost" not in r and "password" not in r for r in result)
    login(client, "deptmgr")
    assert any(
        r["title"] == "TEST-LAPTOP"
        for r in client.get("/api/experience/search?q=test").json["results"]
    )


def test_notification_drawer_is_scoped_and_read_requires_csrf(client):
    login(client)
    notice(client, title="IT only drawer", departments="1")
    login(client, "alice")
    result = client.get("/api/experience/notifications").json
    assert result["unread"] == 1 and result["items"][0]["message"] == "IT only drawer"
    assert client.post("/api/experience/notifications/read").status_code == 400
    assert post(client, "/api/experience/notifications/read").json == {"ok": True}
    assert client.get("/api/experience/notifications").json["unread"] == 0
    login(client, "bob")
    assert client.get("/api/experience/notifications").json["items"] == []


def test_batch_print_labels_requires_management_and_limits_selection(client):
    login(client)
    asset(client)
    result = client.get("/assetpass/labels?ids=1")
    assert result.status_code == 200 and b"CIR-001" in result.data
    assert client.get("/assetpass/labels?ids=").status_code == 400
    assert client.get("/assetpass/labels?ids=not-an-id").status_code == 400
    assert (
        client.get("/assetpass/labels?ids=" + ",".join(str(i) for i in range(1, 52))).status_code
        == 400
    )
    login(client, "alice")
    assert client.get("/assetpass/labels?ids=1").status_code == 403


def test_compiled_interface_is_shipped_without_node_runtime(client):
    page = client.get("/login")
    assert b"experience/experience.js" in page.data
    assert b"experience/experience.css" in page.data
    assert client.get("/static/experience/experience.js").status_code == 200
    assert client.get("/static/experience/experience.css").status_code == 200
