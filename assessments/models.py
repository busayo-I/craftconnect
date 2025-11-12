from django.db import models
from users.models import Artisan

class Assessment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    artisan = models.ForeignKey(
        Artisan,
        on_delete=models.CASCADE,
        related_name='assessments'
    )
    trade_category = models.CharField(max_length=100)
    questions = models.JSONField()  # AI-generated questions (list)
    answers = models.JSONField(null=True, blank=True)  # Artisan answers (dict)
    ai_feedback = models.TextField(null=True, blank=True)  # Optional AI comments
    score = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.artisan.first_name} - {self.trade_category} ({self.status})"
