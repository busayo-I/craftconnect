from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import JobPosting
from .serializers import JobPostingSerializer



# CREATE JOB (Client)
@swagger_auto_schema(
    method="post",
    operation_summary="Create a Job Posting",
    operation_description="Allows a client to create a new job posting.",
    tags=["Job Posting"],
    request_body=JobPostingSerializer,
    responses={
        200: openapi.Response("Job created successfully", JobPostingSerializer),
        400: "Validation error"
    }
)
@api_view(["POST"])
#@permission_classes([IsAuthenticated])
def create_job(request):
    data = request.data.copy()
    data["client"] = request.user.id

    serializer = JobPostingSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response({
            "message": "Job created successfully",
            "job": serializer.data
        })
    return Response(serializer.errors, status=400)



# LIST ALL OPEN JOBS
@swagger_auto_schema(
    method="get",
    operation_summary="List all open job postings",
    operation_description="Retrieve all job postings with status 'open'.",
    tags=["Job Posting"],
    responses={200: JobPostingSerializer(many=True)}
)
@api_view(["GET"])
def list_jobs(request):
    jobs = JobPosting.objects.filter(status="open").order_by("-created_at")
    serializer = JobPostingSerializer(jobs, many=True)
    return Response(serializer.data)



# ASSIGN JOB TO ARTISAN
@swagger_auto_schema(
    method="post",
    operation_summary="Assign job to an artisan",
    operation_description="Artisan accepts a job. Changes status from 'open' to 'assigned'.",
    tags=["Job Posting"],
    responses={
        200: "Job assigned successfully",
        404: "Job not found",
        400: "Invalid job state"
    }
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def assign_job(request, job_id):
    try:
        job = JobPosting.objects.get(id=job_id)
    except JobPosting.DoesNotExist:
        return Response({"error": "Job not found"}, status=404)

    if job.status != "open":
        return Response({"error": "Job is not open for assignment"}, status=400)

    job.assigned_artisan = request.user
    job.status = "assigned"
    job.save()

    return Response({
        "message": "Job assigned to artisan",
        "job": JobPostingSerializer(job).data
    })



# CLIENT COMPLETES JOB
@swagger_auto_schema(
    method="post",
    operation_summary="Mark a job as completed",
    operation_description="Only the client who created the job can mark it as completed.",
    tags=["Job Posting"],
    responses={
        200: "Job completed",
        403: "Unauthorized",
        404: "Job not found"
    }
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def complete_job(request, job_id):
    try:
        job = JobPosting.objects.get(id=job_id)
    except JobPosting.DoesNotExist:
        return Response({"error": "Job not found"}, status=404)

    if job.client != request.user:
        return Response({"error": "Only the client can complete the job"}, status=403)

    job.status = "completed"
    job.save()

    return Response({
        "message": "Job marked as completed",
        "job": JobPostingSerializer(job).data
    })

