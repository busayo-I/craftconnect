from django.db import models
from django.conf import settings

class JobPosting(models.Model):
    STATUS_CHOICES = [
        ("open", "Open"),
        ("assigned", "Assigned"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    trade_category = models.ForeignKey("users.TradeCategory", on_delete=models.CASCADE)

    title = models.CharField(max_length=255)
    description = models.TextField()
    budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    location = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")

    assigned_artisan = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_jobs"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
