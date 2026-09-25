"""URL patterns for the movies application."""

from django.urls import path

from . import views

app_name = 'movies'

urlpatterns = [
    path(
        'recommendations/<int:genre_id>/',
        views.recommendations,
        name='recommendations',
    ),
]