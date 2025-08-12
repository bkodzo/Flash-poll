from django.urls import path
from . import views


urlpatterns = [
    path("api/polls/", views.create_poll, name="create_poll"),
    path("p/<slug:slug>/", views.poll_page,name="poll_page"),
    path("api/vote/", views.cast_vote,name="cast_vote"),

]