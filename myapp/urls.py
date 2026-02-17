from django.contrib import admin
from django.urls import path
from myapp import views

urlpatterns = [
    # path('admin/', admin.site.urls),
    path("", views.user_login, name = 'user_login'),
    path("auth/google/login/", views.google_login_start, name="google_login_start"),
    path("auth/google/callback/", views.google_login_callback, name="google_login_callback"),
    path("home/", views.home, name = 'home'),
    path("upload_files/", views.upload_files, name = 'upload_files'),
    path("register_user/", views.register_user, name = 'register_user'),
    path("dashboard/", views.dashboard, name = 'dashboard'),
    path("dashboard/documents/", views.dashboard_documents, name = 'dashboard_documents'),
    path("analyse_kpi/", views.analyse_kpi, name = 'analyse_kpi'),
    path("log_out/", views.log_out, name = 'log_out'),
    path("showcase_report/", views.showcase_report, name = 'showcase_report')
]