use pyo3::prelude::*;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
#[pyclass]
pub struct Secret {
    pub hostname: String,
    pub username: String,
    pub password: String,
    pub db_name: String,
}

#[pymethods]
impl Secret {
    #[new]
    fn new(
        hostname: String,
        username: String,
        password: String,
        db_name: String,
    ) -> Self {
        Secret {
            hostname,
            username,
            password,
            db_name,
        }
    }
}
