from django.conf import settings
from django.db import models

class LibraryEntry(models.Model):
    STATUS_WISHLIST = "wishlist"
    STATUS_PLAYING = "playing"
    STATUS_COMPLETED = "completed"
    STATUS_DROPPED = "dropped"

    ALLOWED_STATUSES = (
        STATUS_WISHLIST,
        STATUS_PLAYING,
        STATUS_COMPLETED,
        STATUS_DROPPED,
    )

    external_game_id = models.CharField(max_length=100)
    status = models.CharField(max_length=20)
    hours_played = models.IntegerField(default=0)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, # Importante
        on_delete=models.CASCADE,
        null=True,        # para no romper datos existentes
        blank=True,
        related_name="library_entries",
    )

    # --- Simple methods for easy unit tests (not used by the exercises) ---

    def external_id_length(self) -> int:
        return len(self.external_game_id or "")

    def external_id_upper(self) -> str:
        return (self.external_game_id or "").upper()

    def hours_played_label(self) -> str:
        if self.hours_played == 0:
            return "none"
        elif self.hours_played < 10:
            return "low"
        else:
            return "high"

    def status_value(self) -> int:
        if self.status == self.STATUS_WISHLIST:
            return 0
        elif self.status == self.STATUS_PLAYING:
            return 1
        elif self.status == self.STATUS_COMPLETED:
            return 2
        elif self.status == self.STATUS_DROPPED:
            return 3
        else:
            return -1

class GameEntry(models.Model):
    external_game_id = models.CharField(max_length=255)
    status = models.CharField(max_length=255)
    hours_played = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.external_game_id} - {self.status}"
    
