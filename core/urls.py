from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/<str:username>/', views.profile_view, name='profile'),
    path('edit-profile/', views.edit_profile_view, name='edit_profile'),
    path('post/<int:post_id>/', views.post_detail_view, name='post_detail'),
    path('create-post/', views.create_post_view, name='create_post'),
    path('post/<int:post_id>/vote/', views.vote_post_view, name='vote_post'),
    path('comment/<int:comment_id>/delete/', views.delete_comment_view, name='delete_comment'),
    path('comment/<int:comment_id>/edit/', views.edit_comment_view, name='edit_comment'),
]