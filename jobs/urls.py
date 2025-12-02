from django.urls import path
from .views import (
    create_job, 
    list_jobs, 
    assign_job, 
    complete_job
)

urlpatterns = [
    path("create/", create_job, name="create-job"),
    path("all/", list_jobs, name="list-jobs"),
    path("<int:job_id>/assign/", assign_job, name="assign-job"),
    path("<int:job_id>/complete/", complete_job, name="complete-job"),
]