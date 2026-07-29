from fastapi import Request


def key_builder(
    func,
    namespace="",
    request: Request = None,
    response=None,
    args=None,
    kwargs=None,
):
    if request is not None:
        return f"fastapi-cache:{request.method}:{request.url.path}?{request.url.query}"

    clean_args = args[1:] if args and hasattr(args[0], "__class__") else args

    return f"fastapi-cache:{func.__module__}:{func.__name__}:{clean_args}:{kwargs}"
