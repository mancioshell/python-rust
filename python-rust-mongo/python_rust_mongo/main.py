from fastapi import Request, Depends, FastAPI
from typing import Any
from motor.motor_asyncio import AsyncIOMotorClient
from string import Template
from functools import partial
from dotenv import dotenv_values
import anyio

from model import AggregationWindow
from metrics_aggregator import get_client, Secret, get_namespaces_by_account, update_report_view

app = FastAPI()


async def get_client_from_rust(hostname: str, username: str, password: str, dbname: str):

    secret = Secret(hostname, username, password, dbname)

    client = await get_client(secret)
    return client


async def on_startup(app: FastAPI) -> None:

    config = dotenv_values(".env")
    hostname = config.get("HOSTNAME")
    username = config.get("USERNAME")
    password = config.get("PASSWORD")
    dbname = config.get("DBNAME")

    client = await get_client_from_rust(hostname, username, password, dbname)
    app.state.client = client


app.add_event_handler(
    event_type="startup",
    func=partial(on_startup, app=app),
)


def inject_client(request: Request) -> Any:
    return request.app.state.client


@app.get("/aggregations", tags=["aggregations"])
async def aggregate(
    account: str,
    aggregation_window: AggregationWindow,
    client: Any = Depends(inject_client),
) -> None:

    namespaces = await get_namespaces_by_account(client, account)

    async def update(client, account, namespaces, aggregation_window):
        await update_report_view(client, account, namespaces, aggregation_window)

    async with anyio.create_task_group() as tg:
       tg.start_soon(
            update,
            client,
            account,
            namespaces,
            aggregation_window.value,
        )
            

    return None
