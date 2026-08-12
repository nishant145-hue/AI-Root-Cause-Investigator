from app.main import app


print("\n=== APPLICATION ROUTES ===\n")

for route in app.routes:
    print(
        type(route).__name__,
        getattr(route, "path", None),
        getattr(route, "methods", None),
    )

print("\n=== API ROUTER ROUTES ===\n")

from app.api.v1.api import api_router

for route in api_router.routes:
    print(
        type(route).__name__,
        getattr(route, "path", None),
        getattr(route, "methods", None),
    )

print("\n=== INVESTIGATION ROUTER ROUTES ===\n")

from app.api.v1.investigation import router as investigation_router

for route in investigation_router.routes:
    print(
        type(route).__name__,
        getattr(route, "path", None),
        getattr(route, "methods", None),
    )