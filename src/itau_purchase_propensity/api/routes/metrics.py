from fastapi import APIRouter, Response

from itau_purchase_propensity.core.metrics import render_metrics

router = APIRouter()


@router.get("/metrics")
def metrics() -> Response:
    return render_metrics()
