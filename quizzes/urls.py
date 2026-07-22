from django.urls import path
from . import views

app_name = 'quizzes'

urlpatterns = [
    path('module/<int:module_id>/', views.quiz_detail_view, name='quiz_detail'),
    path('module/<int:module_id>/submit/', views.submit_quiz_view, name='submit_quiz'),
    path('attempt/<int:attempt_id>/result/', views.quiz_result_view, name='quiz_result'),
]

