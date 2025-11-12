from django.urls import path
from .views import start_assessment, submit_assessment

urlpatterns = [
    path('start/', start_assessment, name='start_assessment'),
    path('submit/', submit_assessment, name='submit_assessment'),
]