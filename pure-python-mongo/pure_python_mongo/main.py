from fastapi import Request, Depends, FastAPI
from typing import Any
from motor.motor_asyncio import AsyncIOMotorClient
from string import Template
from functools import partial
from dotenv import dotenv_values
import anyio

from model import AggregationWindow
from repository import AggregationRepository

app = FastAPI()


def get_client(hostname: str, username: str, password: str, dbname: str):

    prefix = "mongodb"

    DATABASE_URL = Template(
        "${prefix}://${username}:${password}@${host}/${dbname}?authSource=admin"
    ).substitute(
        prefix=prefix,
        username=username,
        password=password,
        host=hostname,
        dbname=dbname,
    )
    client = AsyncIOMotorClient(DATABASE_URL)
    return client


async def on_startup(app: FastAPI) -> None:

    config = dotenv_values(".env")
    hostname = config.get("HOSTNAME")
    username = config.get("USERNAME")
    password = config.get("PASSWORD")
    dbname = config.get("DBNAME")

    client = get_client(hostname, username, password, dbname)
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

    repository = AggregationRepository()
    namespaces = await repository.get_namespaces_by_account(client, account)

    async with anyio.create_task_group() as tg:
        for namespace in namespaces:
            tg.start_soon(
                repository.update_report_view,
                client,
                account,
                namespace,
                aggregation_window,
            )

    return None
