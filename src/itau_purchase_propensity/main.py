from contextlib import asynccontextmanager

from fastapi import FastAPI

from itau_purchase_propensity.api.routes.health import router as health_router
from itau_purchase_propensity.api.routes.recommendations import router as recommendations_router
from itau_purchase_propensity.core.config import config
from itau_purchase_propensity.core.logging import configure_logging
from itau_purchase_propensity.data.repository import DataRepository
from itau_purchase_propensity.ml.model import PropensityModel


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(config.log_level)
    app.state.repository = DataRepository(
        config.events_path, config.products_path, config.cold_start_window_days
    )
    app.state.model = PropensityModel(config.model_path)
    yield


app = FastAPI(title="Personalization Service", lifespan=lifespan)

app.include_router(health_router)
app.include_router(recommendations_router)
