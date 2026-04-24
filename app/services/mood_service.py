class MoodService:
    """Mock mood detector for iteration 1."""

    def detect_mood(self, text: str) -> tuple[str, float]:
        lowered = text.lower()
        if any(word in lowered for word in ["fericit", "bucurie", "great", "happy"]):
            return "Calm", 0.82
        if any(word in lowered for word in ["stres", "anxiet", "obosit", "trist"]):
            return "Anxious", 0.76
        return "Neutral", 0.65


class KeywordMoodDetector(MoodService):
    """Alias class used where dependency injection expects a detector implementation."""

