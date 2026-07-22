from sqlalchemy import func, select

from src.models import Alert


async def test_file_crud_and_download(api_client) -> None:
    client, _session_maker, dispatched = api_client

    response = await client.post(
        "/files",
        data={"title": "  Contract  "},
        files={"file": ("contract.txt", b"first line\nsecond line", "text/plain")},
    )
    assert response.status_code == 201
    created = response.json()
    file_id = created["id"]
    assert created["title"] == "Contract"
    assert created["size"] == 22
    assert dispatched == [file_id]

    response = await client.get("/files")
    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [file_id]

    response = await client.patch(f"/files/{file_id}", json={"title": "Updated"})
    assert response.status_code == 200
    assert response.json()["title"] == "Updated"

    response = await client.get(f"/files/{file_id}/download")
    assert response.status_code == 200
    assert response.content == b"first line\nsecond line"

    response = await client.delete(f"/files/{file_id}")
    assert response.status_code == 204
    assert (await client.get(f"/files/{file_id}")).status_code == 404


async def test_delete_file_cascades_alerts(api_client) -> None:
    client, session_maker, _dispatched = api_client
    response = await client.post(
        "/files",
        data={"title": "Report"},
        files={"file": ("report.pdf", b"pdf", "application/pdf")},
    )
    file_id = response.json()["id"]

    async with session_maker() as session:
        session.add(Alert(file_id=file_id, level="info", message="Processed"))
        await session.commit()

    assert (await client.delete(f"/files/{file_id}")).status_code == 204
    async with session_maker() as session:
        count = await session.scalar(select(func.count(Alert.id)))
    assert count == 0


async def test_empty_upload_is_rejected(api_client) -> None:
    client, _session_maker, dispatched = api_client
    response = await client.post(
        "/files",
        data={"title": "Empty"},
        files={"file": ("empty.txt", b"", "text/plain")},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "File is empty"}
    assert dispatched == []


async def test_blank_title_is_rejected(api_client) -> None:
    client, _session_maker, dispatched = api_client
    response = await client.post(
        "/files",
        data={"title": "   "},
        files={"file": ("data.txt", b"data", "text/plain")},
    )
    assert response.status_code == 400
    assert dispatched == []
