"""Synchronous handlers wrapped by ``AdmittedWorkerRoute`` resolve their
parameter and return types the way the declared FastAPI floor (0.115) does:
``inspect.signature(call)`` with string annotations evaluated in
``call.__globals__`` -- the wrapper's module, not the handler's (fastapi
0.115.0 ``dependencies/utils.py`` get_typed_signature /
get_typed_return_annotation). PR #207 review: route signature compatibility.
"""

from __future__ import annotations

import inspect
from typing import Any

from fastapi.routing import APIRoute

from tests.api._remote import RemoteHarness


def _resolve_like_0115(call: Any) -> tuple[list[tuple[str, Any]], Any]:
    signature = inspect.signature(call)
    globalns = getattr(call, "__globals__", {})

    def typed(annotation: Any) -> Any:
        if isinstance(annotation, str):  # 0.115 evaluates it in call's globals
            return eval(annotation, globalns, globalns)  # noqa: S307
        return annotation

    params = [(p.name, typed(p.annotation)) for p in signature.parameters.values()]
    return params, typed(signature.return_annotation)


def test_wrapped_routes_resolve_under_the_declared_fastapi_floor(
    remote: RemoteHarness,
) -> None:
    def api_routes(routes: Any) -> Any:
        for route in routes:
            if hasattr(route, "original_router"):  # FastAPI's nested include
                yield from api_routes(route.original_router.routes)
            elif isinstance(route, APIRoute):
                yield route

    wrapped = [
        route
        for route in api_routes(remote.app.routes)
        if hasattr(route.endpoint, "__wrapped__")
    ]
    assert len(wrapped) > 10  # every synchronous handler is wrapped
    for route in wrapped:
        original = inspect.signature(route.endpoint.__wrapped__, eval_str=True)
        params, returned = _resolve_like_0115(route.endpoint)
        assert params == [
            (p.name, p.annotation) for p in original.parameters.values()
        ], route.path
        assert returned == original.return_annotation, route.path
        assert inspect.iscoroutinefunction(route.endpoint)
