from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from postcard_frontend.core.config import get_settings
from postcard_frontend.services.backend_api import BackendApiClient, BackendUnavailableError

settings = get_settings()
app = FastAPI(title=settings.app_name)
app.add_middleware(SessionMiddleware, secret_key=settings.frontend_secret_key)

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parents[2] / "templates"))
client = BackendApiClient(settings)


def is_authenticated(request: Request) -> bool:
    return bool(request.session.get("authenticated"))


def require_auth(request: Request) -> RedirectResponse | None:
    if is_authenticated(request):
        return None
    return RedirectResponse(url="/login", status_code=302)


def fetch_with_fallback(path: str, *, default: dict, params: dict | None = None) -> tuple[dict, str | None]:
    try:
        return client.fetch(path, params=params), None
    except BackendUnavailableError:
        return default, "Backend is temporarily unavailable."


def template_response(request: Request, template_name: str, context: dict, *, status_code: int = 200) -> HTMLResponse:
    payload = {"request": request, **context}
    return templates.TemplateResponse(template_name, payload, status_code=status_code)


@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    if not is_authenticated(request):
        return RedirectResponse(url="/login", status_code=302)
    return RedirectResponse(url="/dashboard", status_code=302)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if is_authenticated(request):
        return RedirectResponse(url="/dashboard", status_code=302)
    return template_response(request, "login.html", {"title": "Вход"})


@app.post("/login", response_class=HTMLResponse)
def login_submit(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == settings.admin_username and password == settings.admin_password:
        request.session["authenticated"] = True
        return RedirectResponse(url="/dashboard", status_code=302)

    return template_response(
        request,
        "login.html",
        {"title": "Вход", "error": "Неверный логин или пароль."},
        status_code=401,
    )


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    redirect = require_auth(request)
    if redirect:
        return redirect
    summary, backend_error = fetch_with_fallback(
        "/internal/summary",
        default={
            "totals": {
                "users": 0,
                "prompts": 0,
                "blocked_prompts": 0,
                "generations": 0,
                "failed_generations": 0,
                "active_generations": 0,
            },
            "recent_generations": [],
        },
    )
    return template_response(request, "dashboard.html", {"title": "Дашборд", "summary": summary, "backend_error": backend_error})


@app.get("/users", response_class=HTMLResponse)
def users(request: Request, search: str | None = None):
    redirect = require_auth(request)
    if redirect:
        return redirect
    data, backend_error = fetch_with_fallback(
        "/internal/users",
        default={"items": []},
        params={"search": search} if search else None,
    )
    return template_response(
        request,
        "users.html",
        {
            "title": "Пользователи",
            "items": data["items"],
            "search": search or "",
            "backend_error": backend_error,
        },
    )


@app.get("/users/{user_id}", response_class=HTMLResponse)
def user_detail(request: Request, user_id: int):
    redirect = require_auth(request)
    if redirect:
        return redirect
    data, backend_error = fetch_with_fallback(
        f"/internal/users/{user_id}",
        default={"user": None, "recent_prompts": [], "recent_generations": []},
    )
    if backend_error:
        return template_response(
            request,
            "user_detail.html",
            {"title": "Пользователь", "backend_error": backend_error, "unavailable": True},
            status_code=503,
        )
    if not data["user"]:
        return template_response(
            request,
            "user_detail.html",
            {"title": "Пользователь", "backend_error": backend_error, "not_found": True},
            status_code=404,
        )
    return template_response(
        request,
        "user_detail.html",
        {
            "title": "Пользователь",
            "backend_error": backend_error,
            "user": data["user"],
            "recent_prompts": data["recent_prompts"],
            "recent_generations": data["recent_generations"],
        },
    )


@app.get("/prompts", response_class=HTMLResponse)
def prompts(request: Request, status: str | None = None):
    redirect = require_auth(request)
    if redirect:
        return redirect
    params = {"status": status} if status else None
    data, backend_error = fetch_with_fallback("/internal/prompts", default={"items": []}, params=params)
    return template_response(
        request,
        "prompts.html",
        {
            "title": "Промпты",
            "items": data["items"],
            "status": status or "",
            "backend_error": backend_error,
        },
    )


@app.get("/prompts/{prompt_id}", response_class=HTMLResponse)
def prompt_detail(request: Request, prompt_id: int):
    redirect = require_auth(request)
    if redirect:
        return redirect
    data, backend_error = fetch_with_fallback(
        f"/internal/prompts/{prompt_id}",
        default={"prompt": None, "user": None, "generations": []},
    )
    if backend_error:
        return template_response(
            request,
            "prompt_detail.html",
            {"title": "Промпт", "backend_error": backend_error, "unavailable": True},
            status_code=503,
        )
    if not data["prompt"]:
        return template_response(
            request,
            "prompt_detail.html",
            {"title": "Промпт", "backend_error": backend_error, "not_found": True},
            status_code=404,
        )
    return template_response(
        request,
        "prompt_detail.html",
        {
            "title": "Промпт",
            "backend_error": backend_error,
            "prompt": data["prompt"],
            "user": data["user"],
            "generations": data["generations"],
        },
    )


@app.get("/generations", response_class=HTMLResponse)
def generations(request: Request, status: str | None = None):
    redirect = require_auth(request)
    if redirect:
        return redirect
    params = {"status": status} if status else None
    data, backend_error = fetch_with_fallback("/internal/generations", default={"items": []}, params=params)
    return template_response(
        request,
        "generations.html",
        {
            "title": "Генерации",
            "items": data["items"],
            "status": status or "",
            "backend_error": backend_error,
        },
    )


@app.get("/generations/{generation_id}", response_class=HTMLResponse)
def generation_detail(request: Request, generation_id: int):
    redirect = require_auth(request)
    if redirect:
        return redirect
    data, backend_error = fetch_with_fallback(
        f"/internal/generations/{generation_id}",
        default={"generation": None, "prompt": None, "user": None},
    )
    if backend_error:
        return template_response(
            request,
            "generation_detail.html",
            {"title": "Генерация", "backend_error": backend_error, "unavailable": True},
            status_code=503,
        )
    if not data["generation"]:
        return template_response(
            request,
            "generation_detail.html",
            {"title": "Генерация", "backend_error": backend_error, "not_found": True},
            status_code=404,
        )
    return template_response(
        request,
        "generation_detail.html",
        {
            "title": "Генерация",
            "backend_error": backend_error,
            "generation": data["generation"],
            "prompt": data["prompt"],
            "user": data["user"],
        },
    )


@app.get("/errors", response_class=HTMLResponse)
def errors(request: Request):
    redirect = require_auth(request)
    if redirect:
        return redirect
    data, backend_error = fetch_with_fallback("/internal/errors", default={"items": []})
    return template_response(
        request,
        "errors.html",
        {"title": "Ошибки", "items": data["items"], "backend_error": backend_error},
    )


@app.get("/exports/{export_name}")
def export_proxy(request: Request, export_name: str):
    redirect = require_auth(request)
    if redirect:
        return redirect

    allowed = {
        "users.csv": "/internal/exports/users.csv",
        "prompts.csv": "/internal/exports/prompts.csv",
        "generations.csv": "/internal/exports/generations.csv",
    }
    backend_path = allowed.get(export_name)
    if not backend_path:
        return Response(status_code=404)

    try:
        content, content_type = client.fetch_bytes(backend_path)
        return Response(
            content=content,
            media_type=content_type,
            headers={"Content-Disposition": f'attachment; filename="{export_name}"'},
        )
    except BackendUnavailableError:
        return Response(content="Backend is temporarily unavailable.", status_code=503, media_type="text/plain")


@app.get("/images/generations/{generation_id}")
def generation_image_proxy(request: Request, generation_id: int):
    redirect = require_auth(request)
    if redirect:
        return redirect

    try:
        content, content_type = client.fetch_bytes(f"/internal/generations/{generation_id}/image")
        return Response(content=content, media_type=content_type)
    except BackendUnavailableError:
        return Response(content="Backend is temporarily unavailable.", status_code=503, media_type="text/plain")
