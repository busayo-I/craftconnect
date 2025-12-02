from rest_framework import serializers
from .models import JobPosting

class JobPostingSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobPosting
        fields = "__all__"
        read_only_fields = ["id", "client", "status", "assigned_artisan", "created_at"]
