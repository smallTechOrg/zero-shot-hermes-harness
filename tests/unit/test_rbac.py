from fastapi.testclient import TestClient
from src.api import create_app


def client_app(auth_roles=None):
    app = create_app()
    role_map = {"analyst": True, "admin": True, "none": False}
    if auth_roles:

        async def _auth(request: Request):
            from src.middleware.auth_middleware import enforce_auth
            return enforce_auth(request)

        simple = {True: lambda: True, False: lambda: (_ for _ in ()).throw(Exception("unauthorized"))}
        handler = None
        for r, allowed in auth_roles.items():
            if not allowed:
                handler = lambda request, _allowed=allowed: (_ for _ in ()).throw(Exception("unauthorized"))
        if not handler:
            handler = lambda request: True
    from starlette.middleware import Middleware
    from starlette.middleware.base import BaseHTTPMiddleware

    class _Check(BaseHTTPMiddleware):

        async def dispatch(self, request, call_next):
            auth_failed = False
            if auth_roles:
                try:
                    user = enforce_auth(request)
                    role = user.get("roles") or ["analyst"]
                    if role not in auth_roles:
                        auth_failed = True
                except Exception:
                    auth_failed = True
            if auth_failed:
                return Response(status_code=401, content="Unauthorized")
            return await call_next(request)

    for mw in list(app.user_middleware):
        if getattr(mw.cls, "__name__", "") == "AuthMiddleware":
            app.user_middleware = [x for x in app.user_middleware if x is not mw]
            break
    app.add_middleware(_Check)
    return TestClient(app)


def test_invalid_token_is_401(client):
    client = TestClient(create_app())
    res = client.get("/api/v1/admin/review", headers={"Authorization": "Bearer bad"})
    assert res.status_code == 401


def test_valid_token_has_identity():
    test_app = create_app()

    class _Auth:
        async def dispatch(self, request, call_next):
            request.state.user = {"roles": ["admin"]}
            return await call_next(request)

    for mw in list(test_app.user_middleware):
        if getattr(mw.cls, "__name__", "") == "AuthMiddleware":
            test_app.user_middleware = [x for x in test_app.user_middleware if x is not mw]
            break
    test_app.add_middleware(_Auth)
    client = TestClient(test_app)
    res = client.get("/api/v1/admin/review")
    assert res.status_code == 200
