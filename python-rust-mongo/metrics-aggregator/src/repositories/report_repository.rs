
use std::io::ErrorKind;
use futures::StreamExt;
use pyo3::prelude::*;

use mongodb::{bson::doc, error::Result, Client, Collection, Database};
use mongodb::options::AggregateOptions;
use crate::models::namespace_model::Namespace;
use crate::models::secret::Secret;

#[derive(Clone, Debug)]
#[pyclass]
pub struct DatabaseClient {
    db: Database
}

impl DatabaseClient {
    pub async fn init(
        secret: &Secret
    ) -> Self {

        let hostname = secret.to_owned().hostname;
        let username = secret.to_owned().username;
        let password = secret.to_owned().password;

        let db_name = secret.to_owned().db_name;

        let uri = format!("mongodb://{}:{}@{}", username, password, hostname);

        let client = Client::with_uri_str(uri)
            .await
            .expect("error connecting to database");

        let db = client.database(&db_name);

        DatabaseClient {
            db
        }
    }
}

pub struct ReportRepository {
    client: DatabaseClient
}

impl ReportRepository {

    pub fn init(
        client: DatabaseClient
    ) -> Self {
        ReportRepository {
            client
        }
    }

    pub async fn get_namespaces(&self, account: &str) -> Result<Vec<String>> {
        let filter = doc! {"account": account};

        let collection: Collection<Namespace> = self.client.db.collection("namespaces");

        match collection.find_one(filter, None).await {
            Ok(option) => match option {
                Some(namespace) => {
                    Ok(namespace.namespaces)
                },
                None => {
                    println!("Nessun namespace trovato per l'account: {}", account);
                    Err(mongodb::error::Error::from(ErrorKind::NotFound))
                },
            },
            Err(e) => {
                println!("Errore durante la ricerca del namespace: {:?}", e);
                Err(e)
            },
        }
    }
    
    pub async fn update_report(
        &self,
        account: &str,
        namespace: &str,
        aggregation_window: &str,
    ) -> Result<()> {
        let collection_name = format!("{}_metrics", account);

        let collection: Collection<()> = self.client.db
            .collection(collection_name.as_str());

        let group = doc! {

            "$group": {
                "_id": {
                    "account": "$info.account",
                    "namespace": "$info.namespace",
                    "container_name": "$info.container_name",
                    "timestamp": {
                        "$dateTrunc": {
                            "date": "$timestamp",
                            "unit": aggregation_window,
                            "binSize": 1
                        }
                    }
                },
                "avg_memory_usage": {
                    "$avg": "$metrics.memory_usage"
                },
                "min_memory_usage": {
                    "$min": "$metrics.memory_usage"
                },
                "max_memory_usage": {
                    "$max": "$metrics.memory_usage"
                },
                "percentile_memory_usage": {
                    "$percentile": {
                        "input": "$metrics.memory_usage",
                        "p": [
                            0.9,
                            0.95,
                            0.99
                        ],
                        "method": "approximate"
                    }
                },
                "avg_cpu_usage": {
                    "$avg": "$metrics.cpu_usage"
                },
                "min_cpu_usage": {
                    "$min": "$metrics.cpu_usage"
                },
                "max_cpu_usage": {
                    "$max": "$metrics.cpu_usage"
                },
                "percentile_cpu_usage": {
                    "$percentile": {
                        "input": "$metrics.cpu_usage",
                        "p": [
                            0.9,
                            0.95,
                            0.99
                        ],
                        "method": "approximate"
                    }
                },
                "timestamp": {
                    "$first": "$timestamp"
                }
            }

        };

        let project = doc! {
            "$project": {
                "account": "$_id.account",
                "namespace": "$_id.namespace",
                "container_name": "$_id.container_name",
                "cpu": {
                    "usage": "$avg_cpu_usage",
                    "min": "$min_cpu_usage",
                    "max": "$max_cpu_usage",
                    "percentile": {
                        "p90": {
                            "$arrayElemAt": [
                                "$percentile_cpu_usage",
                                0
                            ]
                        },
                        "p95": {
                            "$arrayElemAt": [
                                "$percentile_cpu_usage",
                                1
                            ]
                        },
                        "p99": {
                            "$arrayElemAt": [
                                "$percentile_cpu_usage",
                                2
                            ]
                        }
                    }                    
                },
                "memory": {
                    "usage": "$avg_memory_usage",
                    "min": "$min_memory_usage",
                    "max": "$max_memory_usage",
                    "percentile": {
                        "p90": {
                            "$arrayElemAt": [
                                "$percentile_memory_usage",
                                0
                            ]
                        },
                        "p95": {
                            "$arrayElemAt": [
                                "$percentile_memory_usage",
                                1
                            ]
                        },
                        "p99": {
                            "$arrayElemAt": [
                                "$percentile_memory_usage",
                                2
                            ]
                        }
                    }                    
                },               
                "timestamp": {
                    "$dateTrunc": {
                        "date": "$timestamp",
                        "unit": "day"
                    }
                },
                "aggregation_type":  &aggregation_window.to_string()
            }
        };

        let group_data = doc! {
            "$group": {
                "_id": {
                    "account": "$account",
                    "namespace": "$namespace",
                    "aggregation_type": "$aggregation_type"
                },
                "data": {
                    "$push": {
                        "account": "$account",
                        "namespace": "$namespace",
                        "container_name": "$container_name",
                        "cpu": "$cpu",
                        "memory": "$memory",
                        "timestamp": "$timestamp",
                    }
                }
            }
        };

        let id_project = doc! {
            "$project": {
                "_id": 0
            }
        };

        let mut pipeline = vec![
            doc! {
                "$match" : {
                    "info.account": account,
                    "info.namespace": namespace
                },
            },
            doc! {
                    "$sort": {
                    "timestamp": 1
                }
            },
        ];

        pipeline.push(group);
        pipeline.push(project);
        pipeline.push(group_data);
        pipeline.push(id_project);
        
        let mut options = AggregateOptions::default();
        options.allow_disk_use = Some(true);

        let results = collection
            .aggregate(pipeline, Some(options))
            .await
            .expect("Error on aggregate");

        print!("{:?}", results.collect::<Vec<_>>().await);

        Ok(())
    }
}
