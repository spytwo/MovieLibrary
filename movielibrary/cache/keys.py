from fastapi import Request


def key_builder(
    func,
    namespace="",
    request: Request = None,
    response=None,
    args=None,
    kwargs=None,
):
    return f"fastapi-cache:{request.method}:{request.url.path}?{request.url.query}"
