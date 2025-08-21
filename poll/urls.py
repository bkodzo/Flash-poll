from django.urls import path
from . import views


urlpatterns = [
    path("api/polls/", views.create_poll, name="create_poll"),
    path("p/<slug:slug>/", views.poll_page,name="poll_page"),
    path("api/vote/", views.cast_vote,name="cast_vote"),

    #admin urls
    path('manage/<slug:slug>/', views.admin_poll_view, name='admin_poll'),
    path('manage/<slug:slug>/delete/', views.admin_poll_delete, name='admin_delete'),
    path('manage/<slug:slug>/extend/', views.admin_poll_extend, name='admin_extend'),


]