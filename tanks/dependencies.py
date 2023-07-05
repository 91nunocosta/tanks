from functools import cache
from typing import Annotated

import sqlmodel
from fastapi import Depends

import tanks.hooks.sales_monitor
from tanks.hooks.avgsales_updater import AvgSalesUpdater

from .config import Settings


@cache
def get_settings() -> Settings:
    return Settings()  # type: ignore


@cache
def get_session() -> sqlmodel.Session:
    engine = sqlmodel.create_engine(url=get_settings().database_url)
    return Session(engine)


Session = Annotated[sqlmodel.Session, Depends(get_session)]


@cache
def get_sales_monitor(session: Session):
    return tanks.hooks.sales_monitor.SalesMonitor(
        session=session, avgsales_updater=AvgSalesUpdater(session)
    )


SalesMonitor = Annotated[
    tanks.hooks.sales_monitor.SalesMonitor,
    Depends(get_sales_monitor),
]
