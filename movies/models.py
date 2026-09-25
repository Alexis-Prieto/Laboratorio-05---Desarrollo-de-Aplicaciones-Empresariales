"""Database models for the movies application."""

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Genre(models.Model):
    """A movie genre such as Action, Drama or Science Fiction."""

    name = models.CharField(max_length=80, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Genre'
        verbose_name_plural = 'Genres'

    def __str__(self):
        return self.name


class Person(models.Model):
    """A person involved in movies, typically as an actor or director."""

    first_name = models.CharField(max_length=60)
    last_name = models.CharField(max_length=60)
    birth_date = models.DateField(null=True, blank=True)
    photo = models.ImageField(upload_to='persons/', null=True, blank=True)

    class Meta:
        ordering = ['last_name', 'first_name']
        verbose_name = 'Person'
        verbose_name_plural = 'People'

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        """Return the person name as a single readable string."""
        return f'{self.first_name} {self.last_name}'.strip()


class Movie(models.Model):
    """A movie, linked to genres and cast through many-to-many relations."""

    title = models.CharField(max_length=200)
    synopsis = models.TextField(blank=True)
    release_date = models.DateField()
    poster = models.ImageField(upload_to='posters/', null=True, blank=True)
    genres = models.ManyToManyField(
        Genre,
        related_name='movies',
        blank=True,
    )
    cast = models.ManyToManyField(
        Person,
        related_name='movies',
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title']
        verbose_name = 'Movie'
        verbose_name_plural = 'Movies'

    def __str__(self):
        return self.title

    @property
    def average_rating(self):
        """Return the average score of the ratings, or None if there are none."""
        ratings = list(self.ratings.all())
        if not ratings:
            return None
        total = sum(rating.score for rating in ratings)
        return round(total / len(ratings), 2)


class Rating(models.Model):
    """A score given by a viewer to a movie, from 1 to 5 stars."""

    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name='ratings',
    )
    score = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Rating'
        verbose_name_plural = 'Ratings'

    def __str__(self):
        return f'{self.movie.title}: {self.score}/5'

