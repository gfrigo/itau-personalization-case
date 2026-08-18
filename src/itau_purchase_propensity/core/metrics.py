import time
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

REQUEST_COUNT = Counter(
    "http_requests_total", "Total de requisicoes HTTP", ["path", "status_code"]
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds", "Latencia das requisicoes HTTP", ["path"]
)
RECOMMENDATIONS_TOTAL = Counter(
    "recommendations_total", "Total de recomendacoes servidas"
)
RECOMMENDATIONS_COLD_START_TOTAL = Counter(
    "recommendations_cold_start_total", "Recomendacoes servidas via fallback de cold start"
)
MODEL_SCORE = Histogram(
    "model_score",
    "Distribuicao do score do modelo de propensao (usuarios com historico)",
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
)


async def track_request_metrics(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start

    route = request.scope.get("route")
    path = route.path if route else request.url.path

    REQUEST_COUNT.labels(path, response.status_code).inc()
    REQUEST_LATENCY.labels(path).observe(duration)

    return response


def render_metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
