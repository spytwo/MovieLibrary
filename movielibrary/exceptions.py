from urllib.parse import quote

from fastapi import FastAPI, Request, status
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse, RedirectResponse


async def http_exception_handler(request: Request, exc: HTTPException):
    if request.method == "POST" and not request.url.path.startswith("/api"):
        referer = request.headers.get("referer", "/")

        error_msg = (
            exc.detail if isinstance(exc.detail, str) else "Ошибка валидации данных"
        )

        base_referer = referer.split("?")[0]
        encoded_error = quote(error_msg)
        redirect_url = f"{base_referer}?error={encoded_error}"

        return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)

    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


def setup_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(HTTPException, http_exception_handler)
