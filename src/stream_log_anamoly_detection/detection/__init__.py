"""Detection stage: flags anomalous security events with a pre-trained model."""

from .message_detector import AnomalyDetector

__all__ = ["AnomalyDetector"]
