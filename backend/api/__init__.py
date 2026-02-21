from .submit import router as submit_router
from .stats import router as stats_router
from .benchmark import router as benchmark_router
from .statistics import router as statistics_router
from .components import router as components_router
from .trends import router as trends_router

__all__ = ["submit_router", "stats_router", "benchmark_router", "statistics_router", "components_router", "trends_router"]
