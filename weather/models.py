from django.db import models
from django.contrib.auth.models import User


class SearchHistory(models.Model):
    SEARCH_TYPE_CHOICES = [
        ("current", "Current Weather"),
        ("forecast", "5-Day Forecast"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="searches")
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=10, blank=True)
    search_type = models.CharField(max_length=10, choices=SEARCH_TYPE_CHOICES)
    temperature = models.FloatField(null=True, blank=True)
    description = models.CharField(max_length=200, blank=True)
    searched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-searched_at"]

    def __str__(self):
        return f"{self.user.username} — {self.city} ({self.search_type})"


class FavoriteCity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorites")
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=10, blank=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["city"]
        unique_together = ("user", "city")   # no duplicates per user

    def __str__(self):
        return f"{self.user.username} ♥ {self.city}"
