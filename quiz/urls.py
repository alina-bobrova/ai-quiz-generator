from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('quiz/<int:quiz_id>/', views.quiz_detail, name='quiz_detail'),
    path('quiz/<int:quiz_id>/results/', views.quiz_results, name='quiz_results'),
    path('quiz/shared/<str:share_code>/', views.shared_quiz, name='shared_quiz'),
    path('my-quizzes/', views.my_quizzes, name='my_quizzes'),
    path('api/generate_quiz/', views.generate_quiz, name='generate_quiz'),
    path('api/generate_quiz_from_file/', views.generate_quiz_from_file, name='generate_quiz_from_file'),
    path('api/quiz/<int:quiz_id>/toggle-public/', views.toggle_quiz_public, name='toggle_quiz_public'),
    path('api/quiz/<int:quiz_id>/delete/', views.delete_quiz, name='delete_quiz'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/change-password/', views.change_password_view, name='change_password'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]
