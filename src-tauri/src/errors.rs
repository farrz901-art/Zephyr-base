use std::error::Error;
use std::fmt;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum BridgeErrorKind {
    Input,
    Dependency,
    Processing,
    Lineage,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BridgeError {
    kind: BridgeErrorKind,
    detail: String,
}

impl BridgeError {
    pub fn new(kind: BridgeErrorKind, detail: impl Into<String>) -> Self {
        Self {
            kind,
            detail: detail.into(),
        }
    }

    pub fn input(detail: impl Into<String>) -> Self {
        Self::new(BridgeErrorKind::Input, detail)
    }

    pub fn dependency(detail: impl Into<String>) -> Self {
        Self::new(BridgeErrorKind::Dependency, detail)
    }

    pub fn processing(detail: impl Into<String>) -> Self {
        Self::new(BridgeErrorKind::Processing, detail)
    }

    pub fn lineage(detail: impl Into<String>) -> Self {
        Self::new(BridgeErrorKind::Lineage, detail)
    }

    pub fn user_safe_message(&self) -> &'static str {
        match self.kind {
            BridgeErrorKind::Input => "Base command bridge rejected the input.",
            BridgeErrorKind::Dependency => "Local runtime could not be prepared.",
            BridgeErrorKind::Processing => {
                "Base command bridge could not complete the bundled public-core run."
            }
            BridgeErrorKind::Lineage => {
                "Base command bridge could not read local lineage metadata."
            }
        }
    }

    pub fn detail(&self) -> &str {
        &self.detail
    }
}

impl fmt::Display for BridgeError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{} :: {}", self.user_safe_message(), self.detail())
    }
}

impl Error for BridgeError {}

pub fn to_user_safe_string(error: BridgeError) -> String {
    error.to_string()
}
