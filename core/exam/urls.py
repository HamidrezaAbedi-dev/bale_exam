from django.urls import path

from . import views

urlpatterns = [

    path("register/", views.register_user),

    path("user/<str:user>/", views.get_user),

    path("user/update/<str:user>/", views.update_user),

    path("exam/result/", views.save_exam_result),

]




