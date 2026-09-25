"""Admin customisation for the movies application.

The admin classes below are registered instead of the plain
``admin.site.register(Model)`` shortcut, which allows defining the columns,
filters, search fields and inlines used in the Django administration panel.
"""

from django.contrib import admin

from .models import Genre, Movie, Person, Rating


class RatingInline(admin.TabularInline):
    """Edit the ratings of a movie directly from the movie form."""

    model = Rating
    extra = 1
    fields = ('score', 'comment', 'created_at')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    """Administration options for the Movie model."""

    list_display = ('title', 'release_date', 'average_rating_display', 'genres_count')
    list_filter = ('genres', 'release_date', 'created_at')
    search_fields = ('title', 'synopsis')
    date_hierarchy = 'release_date'
    list_per_page = 20
    list_select_related = True
    filter_horizontal = ('genres', 'cast')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('title',)
    inlines = (RatingInline,)
    fieldsets = (
        ('Main information', {
            'fields': ('title', 'synopsis', 'release_date', 'poster'),
        }),
        ('Classification and cast', {
            'fields': ('genres', 'cast'),
        }),
        ('Audit', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at'),
        }),
    )

    @admin.display(description='Average rating', ordering='title')
    def average_rating_display(self, obj):
        """Return the average score of the movie, or a dash if it has no ratings."""
        average = obj.average_rating
        return f'{average:.2f} / 5' if average is not None else '-'

    @admin.display(description='Genres', ordering='title')
    def genres_count(self, obj):
        """Return the number of genres linked to the movie."""
        return obj.genres.count()


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    """Administration options for the Genre model."""

    list_display = ('name', 'movies_count', 'description')
    search_fields = ('name', 'description')
    list_per_page = 20
    ordering = ('name',)

    @admin.display(description='Number of movies')
    def movies_count(self, obj):
        """Return the number of movies that belong to the genre."""
        return obj.movies.count()


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    """Administration options for the Person model."""

    list_display = ('first_name', 'last_name', 'birth_date', 'movies_count')
    search_fields = ('first_name', 'last_name')
    list_per_page = 20
    ordering = ('last_name', 'first_name')
    fields = ('first_name', 'last_name', 'birth_date', 'photo')

    @admin.display(description='Number of movies')
    def movies_count(self, obj):
        """Return the number of movies in which the person appears."""
        return obj.movies.count()


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    """Administration options for the Rating model."""

    list_display = ('movie', 'score', 'created_at', 'comment_preview')
    list_filter = ('score', 'created_at')
    search_fields = ('movie__title', 'comment')
    list_per_page = 20
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)

    @admin.display(description='Comment preview')
    def comment_preview(self, obj):
        """Return a shortened version of the comment for the change list."""
        if not obj.comment:
            return '-'
        text = obj.comment
        return text[:50] + '...' if len(text) > 50 else text
