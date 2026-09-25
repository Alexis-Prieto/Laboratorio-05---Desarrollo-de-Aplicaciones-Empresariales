"""Public views for the movies application."""

from django.db.models import Avg
from django.shortcuts import get_object_or_404, render

from .models import Genre, Movie


def recommendations(request, genre_id):
    """List the best rated movies that belong to the requested genre.

    The movies are annotated with their average score so that the database
    performs the aggregation, and they are ordered from the highest score.
    """
    genre = get_object_or_404(Genre, pk=genre_id)
    movies = (
        Movie.objects.filter(genres=genre)
        .annotate(average_score=Avg('ratings__score'))
        .order_by('-average_score', 'title')
    )
    context = {
        'genre': genre,
        'movies': movies,
    }
    return render(request, 'movies/recommendations.html', context)
