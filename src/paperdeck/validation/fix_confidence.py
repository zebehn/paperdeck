"""Confidence levels for automatic fixes."""

from enum import Enum


class FixConfidence(Enum):
    """Confidence levels for automatic fixes.

    Used to determine whether a fix should be applied automatically
    based on confidence threshold configuration.
    """

    VERY_HIGH = 0.95  # Almost certain fix is correct
    HIGH = 0.85       # High confidence, low risk
    MEDIUM = 0.70     # Moderate confidence, some risk
    LOW = 0.50        # Low confidence, report only
    NONE = 0.0        # Cannot auto-fix

    def should_auto_fix(self, threshold: float = 0.80) -> bool:
        """Check if confidence exceeds threshold for auto-fixing.

        Args:
            threshold: Minimum confidence required (0.0-1.0)

        Returns:
            True if this confidence level exceeds the threshold
        """
        return self.value >= threshold

    def to_display(self) -> str:
        """Human-readable confidence level.

        Returns:
            String representation of confidence level
        """
        if self.value >= 0.90:
            return "very high"
        elif self.value >= 0.80:
            return "high"
        elif self.value >= 0.70:
            return "medium"
        elif self.value >= 0.50:
            return "low"
        else:
            return "none"
