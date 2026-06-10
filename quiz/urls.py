from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = "quiz"

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="quiz:login"), name="logout"),

    path("", views.dashboard_view, name="dashboard"),
    path("setup/", views.mcq_quiz_config_view, name="quiz_config"),
    path("api/filters/", views.api_filter_options, name="api_filters"),  # <-- Added filter route
    path("api/engine/", views.start_exam_engine_api, name="exam_engine_api"),
    path("api/save-note/", views.save_question_note_api, name="save_note_api"),
    path("simulator/", views.diagnosis_simulator_view, name="diagnosis_simulator"),
    path("api/diagnosis/fetch/", views.get_random_diagnosis_case_api, name="fetch_diagnosis_case"),
    path("api/diagnosis/terms/", views.get_medical_terms_autocomplete_api, name="medical_terms_api"),
    path('api/save-answer/', views.save_user_answer_api, name='save_user_answer'),
    path('api/save-diagnosis-progress/', views.save_diagnosis_progress_api, name='save_diagnosis_progress'),
    path("api/save-answer/", views.save_user_answer_api, name="save_user_answer"),
]