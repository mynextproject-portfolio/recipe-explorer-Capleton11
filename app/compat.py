"""Compatibility hacks loaded at app startup.

This module provides a safe replacement for
`prometheus_fastapi_instrumentator.routing.get_route_name` which handles
route objects that don't expose a `path` attribute (e.g. internal
`_IncludedRouter` instances). Importing this module monkeypatches the
instrumentator at runtime without editing site-packages.
"""
from typing import List, Optional

from starlette.routing import Match, Mount, Route
from starlette.types import Scope
from starlette.requests import HTTPConnection


def _get_route_name(scope: Scope, routes: List[Route], route_name: Optional[str] = None) -> Optional[str]:
    for route in routes:
        match, child_scope = route.matches(scope)
        if match == Match.FULL:
            route_path = getattr(route, "path", None)
            name = route_path if isinstance(route_path, str) else getattr(route, "name", None)
            child_scope = {**scope, **child_scope}
            if isinstance(route, Mount) and getattr(route, "routes", None):
                child_route_name = _get_route_name(child_scope, route.routes, name)
                if child_route_name is None:
                    name = None
                else:
                    if isinstance(name, str) and isinstance(child_route_name, str):
                        name += child_route_name
                    else:
                        name = None
            return name
        elif match == Match.PARTIAL and route_name is None:
            route_path = getattr(route, "path", None)
            route_name = route_path if isinstance(route_path, str) else getattr(route, "name", None)
    return None


def safe_get_route_name(request: HTTPConnection) -> Optional[str]:
    app = request.app
    scope = request.scope
    routes = app.routes
    route_name = _get_route_name(scope, routes)

    if not route_name and getattr(app.router, "redirect_slashes", False) and scope["path"] != "/":
        redirect_scope = dict(scope)
        if scope["path"].endswith("/"):
            redirect_scope["path"] = scope["path"][0:-1]
            trim = True
        else:
            redirect_scope["path"] = scope["path"] + "/"
            trim = False

        route_name = _get_route_name(redirect_scope, routes)
        if route_name is not None:
            route_name = route_name + "/" if trim else route_name[:-1]
    return route_name


def apply_patches() -> None:
    try:
        import prometheus_fastapi_instrumentator.routing as pfr

        pfr.get_route_name = safe_get_route_name
    except Exception:
        # Do not crash the application if the instrumentator is not installed
        # or the import shape changes; this is a non-critical compatibility
        # helper.
        pass


apply_patches()
