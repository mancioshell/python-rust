from typing import List
from pymongo import MongoClient
from model import AggregationWindow


class AggregationRepository:

    def __init__(self) -> None:
        pass

    def _sort_by_timestamp(self):
        return {"$sort": {"timestamp": 1}}

    def _group_metric_by_time_window(self, aggregation_type: AggregationWindow):
    
        _id = {
            "account": "$info.account",
            "namespace": "$info.namespace",
            "container_name": "$info.container_name",
            "timestamp": {
                "$dateTrunc": {"date": "$timestamp", "unit": aggregation_type.value, "binSize": 1}
            },
        }

        cpu_usage_value = "$metrics.cpu_usage"
        memory_usage_value = "$metrics.memory_usage"

        return {
            "$group": {
                "_id": {**_id},
                "avg_cpu_usage": {"$avg": cpu_usage_value},
                "min_cpu_usage": {"$min": cpu_usage_value},
                "max_cpu_usage": {"$max": cpu_usage_value},
                "percentile_cpu_usage": {
                    "$percentile": {
                        "input": cpu_usage_value,
                        "p": [0.9, 0.95, 0.99],
                        "method": "approximate",
                    }
                },
                "avg_memory_usage": {"$avg": memory_usage_value},
                "min_memory_usage": {"$min": memory_usage_value},
                "max_memory_usage": {"$max": memory_usage_value},
                "percentile_memory_usage": {
                    "$percentile": {
                        "input": memory_usage_value,
                        "p": [0.9, 0.95, 0.99],
                        "method": "approximate",
                    }
                },
                "timestamp": {"$first": "$timestamp"},
            }
        }

    def _project_report_item(self, aggregation_type: AggregationWindow):
        return {
            "$project": {
                "account": "$_id.account",
                "namespace": "$_id.namespace",
                "container_name": "$_id.container_name",
                "cpu": {
                    "usage": "$avg_cpu_usage",
                    "min": "$min_cpu_usage",
                    "max": "$max_cpu_usage",
                    "percentile": {
                        "p90": {"$arrayElemAt": ["$percentile_cpu_usage", 0]},
                        "p95": {"$arrayElemAt": ["$percentile_cpu_usage", 1]},
                        "p99": {"$arrayElemAt": ["$percentile_cpu_usage", 2]},
                    }
                },
                "memory": {
                    "usage": "$avg_memory_usage",
                    "min": "$min_memory_usage",
                    "max": "$max_memory_usage",
                    "percentile": {
                        "p90": {"$arrayElemAt": ["$percentile_memory_usage", 0]},
                        "p95": {"$arrayElemAt": ["$percentile_memory_usage", 1]},
                        "p99": {"$arrayElemAt": ["$percentile_memory_usage", 2]},
                    },
                },
                "timestamp": {
                    "$dateTrunc": {
                        "date": "$timestamp",
                        "unit": aggregation_type.value,
                    }
                },
                "aggregation_type": aggregation_type.value,
            }
        }

    def _group_by_aggregation_time_window(self):
        return {
            "$group": {
                "_id": {
                    "account": "$account",
                    "namespace": "$namespace",
                    "aggregation_type": "$aggregation_type",
                },
                "data": {
                    "$push": {
                        "account": "$account",
                        "namespace": "$namespace",
                        "container_name": "$container_name",
                        "cpu": "$cpu",
                        "memory": "$memory",
                        "timestamp": "$timestamp",
                    },
                },
            },
        }

    async def get_namespaces_by_account(
        self, client: MongoClient, account: str
    ) -> List[str]:

        try:
            collection_name = f"namespaces"
            collection = client.get_default_database()[collection_name]

            result = await collection.find_one({"account": account})
            if result is None:
                return []
            namespaces = result["namespaces"]
            return namespaces

        except Exception as error:
            raise error

    async def update_report_view(
        self,
        client: MongoClient,
        account: str,
        namespace: str,
        aggregation_window: AggregationWindow,
    ) -> None:

        try:

            collection_name = f"{account}_metrics"
            collection = client.get_default_database()[collection_name]

            query = {
                "info.account": account,
                "info.namespace": namespace,
            }

            sort_by_timestamp = self._sort_by_timestamp()
            group_by_pipeline = self._group_metric_by_time_window(aggregation_window)
            project_report_by_pipeline = self._project_report_item(aggregation_window)
            group_by_aggregation_time_window = self._group_by_aggregation_time_window()

            pipeline = [
                {"$match": {**query}},
                sort_by_timestamp,
                group_by_pipeline,
                project_report_by_pipeline,
                group_by_aggregation_time_window,
                {
                    "$project": {
                        "_id": 0,
                    }
                },
            ]

            result = collection.aggregate(pipeline, allowDiskUse=True)
            docs = await result.to_list(None)
            print(docs)

            return None

        except Exception as error:
            self.logger.error(error)  # type: ignore
            raise error
