use serde::{Serialize, Deserialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct Namespace {
    pub account: String,
    pub namespaces: Vec<String>,
}