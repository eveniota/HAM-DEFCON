import secrets
import string
import httpx
from enochecker3 import (
    ChainDB,
    Enochecker,
    GetflagCheckerTaskMessage,
    HavocCheckerTaskMessage,
    MumbleException,
    PutflagCheckerTaskMessage,
)

from enochecker3.utils import assert_equals, assert_in

SERVICE_NAME = "docuvault"
SERVICE_PORT = 8000
checker = Enochecker(SERVICE_NAME, SERVICE_PORT)
app = lambda: checker.app

def random_string(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


@checker.putflag(0)
async def putflag_workspace_memo(
    task: PutflagCheckerTaskMessage,
    client: httpx.AsyncClient,
    db: ChainDB,
) -> str:
    username = f"exec_{random_string(8)}"
    password = random_string(16)
    handle = f"team_{random_string(8)}"
    title = f"Confidential Memo {random_string(4)}"

    reg_resp = await client.post(
        "/api/register",
        data={"username": username, "password": password, "bio": "Security Officer"},
    )

    if reg_resp.status_code != 200:
        raise MumbleException(f"Register failed during putflag(0): {reg_resp.text}")

    ws_resp = await client.post(
        "/api/workspaces",
        data={"handle": handle, "name": f"Workspace {handle}", "is_private": "true"},
    )
    if ws_resp.status_code != 200:
        raise MumbleException(f"Workspace creation failed: {ws_resp.text}")

    ws_data = ws_resp.json()
    ws_id = ws_data.get("id")

    doc_resp = await client.post(
        f"/api/workspaces/{ws_id}/documents",
        data={"title": title, "content": task.flag, "is_confidential": "true"},
    )
    if doc_resp.status_code != 200:
        raise MumbleException(f"Document creation failed: {doc_resp.text}")

    await db.set("username", username)
    await db.set("password", password)
    await db.set("handle", handle)
    return handle

@checker.getflag(0)
async def getflag_workspace_memo(
    task: GetflagCheckerTaskMessage,
    client: httpx.AsyncClient,
    db: ChainDB,
) -> None:
    try:
        username = await db.get("username")
        password = await db.get("password")
        handle = await db.get("handle")
    except KeyError as e:
        raise MumbleException(f"Missing data in DB: {e}")

    login_resp = await client.post(
        "/api/login",
        data={"username": username, "password": password},
    )
    if login_resp.status_code != 200:
        raise MumbleException("Login failed during getflag(0)")

    ws_resp = await client.get(f"/api/workspaces/{handle}")
    if ws_resp.status_code != 200:
        raise MumbleException("Could not retrieve workspace during getflag(0)")

    data = ws_resp.json()
    docs = data.get("documents", [])
    all_contents = " ".join([d.get("content", "") for d in docs])
    assert_in(task.flag, all_contents, "Flag not found in workspace documents")

@checker.putflag(1)
async def putflag_document_export(
    task: PutflagCheckerTaskMessage,
    client: httpx.AsyncClient,
    db: ChainDB,
) -> str:
    username = f"proj_{random_string(8)}"
    password = random_string(16)
    handle = f"ws_{random_string(8)}"
    title = f"Project Spec {random_string(4)}"

    reg_resp = await client.post(
        "/api/register",
        data={"username": username, "password": password, "bio": "Project Manager"},
    )

    if reg_resp.status_code != 200:
        raise MumbleException("Register failed during putflag(1)")

    ws_resp = await client.post(
                "/api/workspaces",
                data={"handle": handle, "name": f"Project {handle}", "is_private": "true"},
    )
    if ws_resp.status_code != 200:
        raise MumbleException("Workspace creation failed during putflag(1)")
    ws_id = ws_resp.json().get("id")

    # 3. Create Document with Flag
    doc_resp = await client.post(
        f"/api/workspaces/{ws_id}/documents",
        data={"title": title, "content": task.flag, "is_confidential": "true"},
    )
    if doc_resp.status_code != 200:
        raise MumbleException("Document creation failed during putflag(1)")
    doc_id = doc_resp.json().get("document_id")

    # 4. Save state
    await db.set("username", username)
    await db.set("password", password)
    await db.set("ws_id", str(ws_id))
    await db.set("doc_id", str(doc_id))

    return str(doc_id)

@checker.getflag(1)
async def getflag_document_export(
    task: GetflagCheckerTaskMessage,
    client: httpx.AsyncClient,
    db: ChainDB,
) -> None:
    try:
        username = await db.get("username")
        password = await db.get("password")
        ws_id = await db.get("ws_id")
        doc_id = await db.get("doc_id")
    except KeyError as e:
        raise MumbleException("Missing putflag(1) state in DB") from e

    login_resp = await client.post(
        "/api/login",
        data={"username": username, "password": password},
    )
    if login_resp.status_code != 200:
        raise MumbleException("Login failed during getflag(1)")

    # Test the export endpoint
    export_resp = await client.get(
        f"/api/workspaces/{ws_id}/documents/{doc_id}/export"
    )
    if export_resp.status_code != 200:
        raise MumbleException("Export endpoint failed during getflag(1)")

    doc_data = export_resp.json().get("document", {})
    content = doc_data.get("content", "")

    assert_in(task.flag, content, "Flag not found in exported document")

@checker.putflag(2)
async def putflag_executive_bio(
    task: PutflagCheckerTaskMessage,
    client: httpx.AsyncClient,
    db: ChainDB,
) -> str:
    username = f"vip_{random_string(8)}"
    password = random_string(16)

    reg_resp = await client.post(
        "/api/register",
        data={"username": username, "password": password, "bio": task.flag},
    )
    if reg_resp.status_code != 200:
        raise MumbleException("Register failed during putflag(2)")

    user_id = reg_resp.json().get("user_id")

    await db.set("username", username)
    await db.set("password", password)
    await db.set("user_id", str(user_id))

    return str(user_id)


@checker.getflag(2)
async def getflag_executive_bio(
    task: GetflagCheckerTaskMessage,
    client: httpx.AsyncClient,
    db: ChainDB,
) -> None:
    try:
        username = await db.get("username")
        password = await db.get("password")
    except KeyError as e:
        raise MumbleException("Missing putflag(2) state in DB") from e

    login_resp = await client.post(
        "/api/login",
        data={"username": username, "password": password},
    )
    if login_resp.status_code != 200:
        raise MumbleException("Login failed during getflag(2)")

    me_resp = await client.get("/api/me")
    if me_resp.status_code != 200:
        raise MumbleException("Failed to access /api/me during getflag(2)")

    bio = me_resp.json().get("bio", "")
    assert_in(task.flag, bio, "Flag not found in user bio")


@checker.havoc(0)
async def havoc_workflow(
    task: HavocCheckerTaskMessage,
    client: httpx.AsyncClient,
) -> None:
    # 1. Check index page
    index_resp = await client.get("/")
    assert_equals(index_resp.status_code, 200, "Index page unreachable")

    # 2. User registration and logout workflow
    username = f"tester_{random_string(6)}"
    password = random_string(14)
    reg_resp = await client.post(
        "/api/register",
        data={"username": username, "password": password, "bio": "Regular Tester"},
    )
    assert_equals(reg_resp.status_code, 200, "Havoc register failed")

    # 3. Create a public workspace & public document
    handle = f"public_{random_string(6)}"
    ws_resp = await client.post(
        "/api/workspaces",
        data={"handle": handle, "name": "Public Space", "is_private": "false"},
    )
    assert_equals(ws_resp.status_code, 200, "Havoc workspace creation failed")
    ws_id = ws_resp.json().get("id")

    doc_resp = await client.post(
        f"/api/workspaces/{ws_id}/documents",
        data={"title": "Public Note", "content": "Welcome everyone!", "is_confidential":"false"},
    )
    assert_equals(doc_resp.status_code, 200, "Havoc document creation failed")
    doc_id = doc_resp.json().get("document_id")

    # 4. Generate share link and test public /share endpoint
    share_resp = await client.get(f"/api/documents/{doc_id}/share-link")
    assert_equals(share_resp.status_code, 200, "Share link creation failed")
    share_url = share_resp.json().get("share_url")

    # View shared document anonymously (clear cookies)
    client.cookies.clear()
    view_resp = await client.get(share_url)
    assert_equals(view_resp.status_code, 200, "Public share viewing failed")
