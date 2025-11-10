"""API routers exposed by the MISIX backend."""

from .auth import router as auth_router  # noqa: F401
from .notes import router as notes_router  # noqa: F401
from .tasks import router as tasks_router  # noqa: F401
from .assistant import router as assistant_router  # noqa: F401
from .finances import router as finances_router  # noqa: F401
from .personal import router as personal_router  # noqa: F401
from .health import router as health_router  # noqa: F401
from .dashboard import router as dashboard_router  # noqa: F401
