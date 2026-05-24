from collections import Counter
from datetime import date, timedelta

from app.core.contracts import EntryRepositoryProtocol, MoodDetectorProtocol
from app.core.exceptions import NotFoundError, ValidationError
from app.models.entry import Entry


class EntryService:
    def __init__(self, entry_repository: EntryRepositoryProtocol, mood_service: MoodDetectorProtocol) -> None:
        self.entry_repository = entry_repository
        self.mood_service = mood_service

    def list_entries(
        self,
        user_id: int,
        search: str | None = None,
        mood: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[Entry]:
        if date_from and date_to and date_from > date_to:
            raise ValidationError("Intervalul de date este invalid.")
        return self.entry_repository.list_by_user(user_id, search, mood, date_from, date_to)

    def create_entry(self, user_id: int, title: str, content: str, entry_date: date) -> Entry:
        self._validate(title, content)
        mood_label, mood_confidence = self.mood_service.detect_mood(content)
        entry = Entry(
            user_id=user_id,
            title=title.strip(),
            content=content.strip(),
            entry_date=entry_date,
            mood_label=mood_label,
            mood_confidence=mood_confidence,
        )
        return self.entry_repository.add(entry)

    def update_entry(self, entry_id: int, user_id: int, title: str, content: str, entry_date: date) -> Entry:
        self._validate(title, content)
        entry = self.entry_repository.get_by_id_for_user(entry_id, user_id)
        if not entry:
            raise NotFoundError("Intrarea nu a fost gasita.")

        entry.title = title.strip()
        entry.content = content.strip()
        entry.entry_date = entry_date
        entry.mood_label, entry.mood_confidence = self.mood_service.detect_mood(content)
        self.entry_repository.commit()
        return entry

    def delete_entry(self, entry_id: int, user_id: int) -> None:
        entry = self.entry_repository.get_by_id_for_user(entry_id, user_id)
        if not entry:
            raise NotFoundError("Intrarea nu a fost gasita.")
        self.entry_repository.delete(entry)

    def get_dashboard_stats(self, user_id: int, today: date | None = None) -> dict[str, object]:
        entries = self.entry_repository.list_by_user(user_id)
        current_day = today or date.today()
        current_month_entries = [
            entry
            for entry in entries
            if entry.entry_date.year == current_day.year and entry.entry_date.month == current_day.month
        ]
        confidence_values = [
            entry.mood_confidence
            for entry in entries
            if entry.mood_confidence is not None
        ]
        mood_counts = Counter(entry.mood_label or "Necunoscut" for entry in entries)
        weekday_counts = Counter(entry.entry_date.weekday() for entry in entries)
        writing_days = {entry.entry_date for entry in entries}
        total_entries = len(entries)
        # Calculate streaks based on unique writing dates (dates <= today)
        unique_dates = sorted({d for d in writing_days if d <= current_day})

        if not unique_dates:
            current_streak = 0
            longest_streak = 0
        else:
            # current streak: count consecutive days ending at the most recent entry date <= today
            last_date = unique_dates[-1]
            streak = 0
            check_date = last_date
            while check_date in writing_days:
                streak += 1
                check_date = check_date - timedelta(days=1)
            current_streak = streak

            # longest streak: scan sorted dates for the longest consecutive run
            longest = 1
            run = 1
            for prev, curr in zip(unique_dates, unique_dates[1:]):
                if curr == prev + timedelta(days=1):
                    run += 1
                    if run > longest:
                        longest = run
                else:
                    run = 1
            longest_streak = longest

        return {
            "total_entries": total_entries,
            "current_month_entries": len(current_month_entries),
            "writing_days": len(writing_days),
            "average_mood_confidence": round(sum(confidence_values) / len(confidence_values), 2)
            if confidence_values
            else 0,
            "top_mood": mood_counts.most_common(1)[0][0] if mood_counts else "N/A",
            "mood_distribution": [
                {
                    "mood": mood,
                    "count": count,
                    "percent": round((count / total_entries) * 100) if total_entries else 0,
                }
                for mood, count in mood_counts.most_common()
            ],
            "weekday_frequency": [
                {"day": label, "count": weekday_counts[index]}
                for index, label in enumerate(["Lun", "Mar", "Mie", "Joi", "Vin", "Sam", "Dum"])
            ],
            "current_streak": current_streak,
            "longest_streak": longest_streak,
        }

    def get_entry(self, entry_id: int, user_id: int) -> Entry:
        entry = self.entry_repository.get_by_id_for_user(entry_id, user_id)
        if not entry:
            raise NotFoundError("Intrarea nu a fost gasita.")
        return entry

    @staticmethod
    def _validate(title: str, content: str) -> None:
        if not title.strip() or not content.strip():
            raise ValidationError("Titlul si continutul sunt obligatorii.")
