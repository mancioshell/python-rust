#![recursion_limit = "1024"]

mod repositories;
mod models;

use std::sync::Arc;
use pyo3::prelude::*;

use repositories::report_repository::ReportRepository;
use repositories::report_repository::DatabaseClient;
use models::secret::Secret;
use futures::stream::FuturesUnordered;
use futures::StreamExt;

#[pyfunction]
fn get_client(
    py: Python,
    secret: Secret,
) -> PyResult<Bound<PyAny>> {
    pyo3_asyncio_0_21::tokio::future_into_py(py, async move {
        let client: DatabaseClient = DatabaseClient::init(&secret).await;

        Ok(Python::with_gil(|py| client.into_py(py)))
    })
}

#[pyfunction]
fn get_namespaces_by_account(
    py: Python,
    client: DatabaseClient,
    account: String,
) -> PyResult<Bound<PyAny>> {
    pyo3_asyncio_0_21::tokio::future_into_py(py, async move {
        let report_repository: ReportRepository = ReportRepository::init(client);
        let namespaces: Vec<String> = report_repository.get_namespaces(&account).await.unwrap();

        Ok(Python::with_gil(|py| namespaces.into_py(py)))
    })
}

#[pyfunction]
fn update_report_view(
    py: Python,
    client: DatabaseClient,
    account: String,
    namespaces: Vec<String>,
    aggregation_window: String,
) -> PyResult<Bound<PyAny>> {
    let namespaces = Arc::new(namespaces);

    let report_repository: ReportRepository = ReportRepository::init(client);

    pyo3_asyncio_0_21::tokio::future_into_py(py, async move {

        let mut futures = FuturesUnordered::new();

        for namespace in namespaces.iter() {
            let task = report_repository.update_report(
                &account,
                namespace.as_str(),
                &aggregation_window
            );
            futures.push(Box::pin(task));
        }

        while let Some(_result) = futures.next().await {}

        Ok(())
    })
}

/// A Python module implemented in Rust.
#[pymodule]
fn metrics_aggregator(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<Secret>()?;
    m.add_function(wrap_pyfunction!(get_client, m)?)?;
    m.add_function(wrap_pyfunction!(update_report_view, m)?)?;
    m.add_function(wrap_pyfunction!(get_namespaces_by_account, m)?)?;
    Ok(())
}
