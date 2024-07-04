from pymongo import MongoClient
from dotenv import dotenv_values
from string import Template

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
    client = MongoClient(DATABASE_URL)
    return client


def insert_documents():

    config = dotenv_values(".env")
    hostname = config.get("HOSTNAME")
    username = config.get("USERNAME")
    password = config.get("PASSWORD")
    dbname = config.get("DBNAME")

    client = get_client(hostname, username, password, dbname)

    db = client.get_default_database()
    collection = db["namespaces"]

    namespaces = [
        {"account": "account1", "namespaces": ["namespace1", "namespace2"]},
        {"account": "account2", "namespaces": ["namespace3", "namespace4"]},
    ]

    collection.insert_many(namespaces)

    collection = db[f"account1_metrics"]

    documents = [
        {
            "info": {
                "account": "account1",
                "namespace": "namespace1",
                "container_name": "container1",
                "timestamp": "2021-01-01T00:00:00Z",
            },
            "metrics": {
                "cpu_usage": 0.1,
                "memory_usage": 0.2,
            },
        },
        {
            "info": {
                "account": "account1",
                "namespace": "namespace1",
                "container_name": "container2",
                "timestamp": "2021-01-01T00:00:00Z",
            },
            "metrics": {
                "cpu_usage": 0.3,
                "memory_usage": 0.4,
            },
        },
        {
            "info": {
                "account": "account1",
                "namespace": "namespace2",
                "container_name": "container3",
                "timestamp": "2021-01-01T00:00:00Z",
            },
            "metrics": {
                "cpu_usage": 0.5,
                "memory_usage": 0.6,
            },
        },
    ]

    collection.insert_many(documents)
    collection = db[f"account2_metrics"]

    documents = [
        {
            "info": {
                "account": "account2",
                "namespace": "namespace3",
                "container_name": "container4",
                "timestamp": "2021-01-01T00:00:00Z",
            },
            "metrics": {
                "cpu_usage": 0.7,
                "memory_usage": 0.8,
            },
        },
        {
            "info": {
                "account": "account2",
                "namespace": "namespace4",
                "container_name": "container5",
                "timestamp": "2021-01-01T00:00:00Z",
            },
            "metrics": {
                "cpu_usage": 0.9,
                "memory_usage": 1.0,
            },
        },
    ]

    collection.insert_many(documents)
    client.close()

insert_documents()