"""Management command to load sample data for the movies application."""

from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from movies.models import Genre, Movie, Person, Rating

GENRES = [
    ('Action', 'Films focused on fast pacing, physical action and conflict.'),
    ('Drama', 'Stories centred on characters, conflict and emotion.'),
    ('Comedy', 'Humorous stories intended to make the audience laugh.'),
    ('Science Fiction', 'Speculative stories based on science and technology.'),
]

PEOPLE = [
    ('Keanu', 'Reeves', date(1964, 9, 2)),
    ('Laurence', 'Fishburne', date(1961, 7, 30)),
    ('Carrie-Anne', 'Moss', date(1967, 12, 27)),
    ('Sigourney', 'Weaver', date(1949, 10, 8)),
    ('Bill', 'Murray', date(1950, 9, 21)),
    ('Hugo', 'Weaver', date(1960, 12, 18)),
]

MOVIES = [
    {
        'title': 'The Matrix',
        'release_date': date(1999, 3, 30),
        'synopsis': (
            'A hacker discovers that reality is a simulation built to control '
            'humanity, and joins a rebellion against the machines.'
        ),
        'genres': ['Science Fiction', 'Action'],
        'cast': ['Keanu Reeves', 'Laurence Fishburne', 'Carrie-Anne Moss'],
        'ratings': [
            (5, 'A defining science fiction classic.'),
            (5, 'Excellent world building.'),
        ],
    },
    {
        'title': 'Terminator 2: Judgment Day',
        'release_date': date(1991, 7, 3),
        'synopsis': (
            'A reprogrammed terminator is sent back in time to protect a boy '
            'and prevent the creation of Skynet.'
        ),
        'genres': ['Action', 'Science Fiction'],
        'cast': ['Sigourney Weaver', 'Hugo Weaver'],
        'ratings': [(4, 'Great action sequences.')],
    },
    {
        'title': 'Alien',
        'release_date': date(1979, 5, 25),
        'synopsis': (
            'The crew of a commercial spacecraft encounters a deadly alien '
            'organism aboard their ship.'
        ),
        'genres': ['Science Fiction', 'Drama'],
        'cast': ['Sigourney Weaver'],
        'ratings': [
            (5, 'Tension from the first minute.'),
            (4, 'A masterpiece of horror.'),
        ],
    },
    {
        'title': 'Ghostbusters',
        'release_date': date(1984, 6, 8),
        'synopsis': (
            'A team of scientists starts a ghost busting business in New York '
            'City and investigates a haunted hotel.'
        ),
        'genres': ['Comedy', 'Science Fiction'],
        'cast': ['Bill Murray', 'Sigourney Weaver'],
        'ratings': [(4, 'Funny and full of character.')],
    },
    {
        'title': 'Groundhog Day',
        'release_date': date(1993, 2, 12),
        'synopsis': (
            'A cynical television reporter keeps living the same day over and '
            'over until he changes himself.'
        ),
        'genres': ['Comedy', 'Drama'],
        'cast': ['Bill Murray'],
        'ratings': [
            (5, 'A perfect comedy with depth.'),
            (5, 'Loved it.'),
            (4, 'Very funny.'),
        ],
    },
    {
        'title': 'Point Break',
        'release_date': date(1991, 5, 12),
        'synopsis': (
            'A young FBI agent infiltrates the world of surfers and bank '
            'robbers in California.'
        ),
        'genres': ['Action', 'Drama'],
        'cast': ['Keanu Reeves'],
        'ratings': [(4, 'Great soundtrack.')],
    },
    {
        'title': 'The Matrix Reloaded',
        'release_date': date(2003, 5, 15),
        'synopsis': (
            'Neo and the rebel leaders continue the fight against the machines '
            'while the Oracle reveals more about the real world.'
        ),
        'genres': ['Science Fiction', 'Action'],
        'cast': ['Keanu Reeves', 'Laurence Fishburne', 'Carrie-Anne Moss'],
        'ratings': [(3, 'Impressive but long.')],
    },

    {
        'title': 'Aliens',
        'release_date': date(1986, 7, 18),
        'synopsis': (
            'Ellen Ripley returns to the planet with a squad of marines to '
            'find out why the colony has stopped answering calls.'
        ),
        'genres': ['Science Fiction', 'Action'],
        'cast': ['Sigourney Weaver'],
        'ratings': [(5, 'The best sequel of its era.'), (4, 'Intense.')],
    },
    {
        'title': 'Scrooged',
        'release_date': date(1988, 11, 23),
        'synopsis': (
            'A cynical television executive is visited by three ghosts on '
            'Christmas Eve to show him the value of his life.'
        ),
        'genres': ['Comedy', 'Drama'],
        'cast': ['Bill Murray'],
        'ratings': [],
    },
    {
        'title': 'John Wick',
        'release_date': date(2014, 10, 24),
        'synopsis': (
            'A retired hitman takes revenge on the criminals who killed his '
            'dog and stole his car.'
        ),
        'genres': ['Action', 'Drama'],
        'cast': ['Keanu Reeves'],
        'ratings': [(4, 'Excellent action.')],
    },
]


class Command(BaseCommand):
    """Create genres, people, movies and ratings used as sample data."""

    help = 'Load sample genres, people, movies and ratings into the database.'

    @transaction.atomic
    def handle(self, *args, **options):
        """Create the sample data, reusing the records that already exist."""
        genres = {}
        for name, description in GENRES:
            genre, created = Genre.objects.get_or_create(
                name=name,
                defaults={'description': description},
            )
            genres[name] = genre
            verb = 'Created' if created else 'Found'
            self.stdout.write(f'{verb} genre: {genre.name}')

        people = {}
        for first_name, last_name, birth_date in PEOPLE:
            person, created = Person.objects.get_or_create(
                first_name=first_name,
                last_name=last_name,
                defaults={'birth_date': birth_date},
            )
            people[person.full_name] = person
            verb = 'Created' if created else 'Found'
            self.stdout.write(f'{verb} person: {person.full_name}')

        for movie_data in MOVIES:
            movie, created = Movie.objects.get_or_create(
                title=movie_data['title'],
                defaults={
                    'synopsis': movie_data['synopsis'],
                    'release_date': movie_data['release_date'],
                },
            )
            movie.genres.set(genres[name] for name in movie_data['genres'])
            movie.cast.set(people[full_name] for full_name in movie_data['cast'])
            for score, comment in movie_data['ratings']:
                Rating.objects.get_or_create(
                    movie=movie,
                    score=score,
                    comment=comment,
                )
            verb = 'Created' if created else 'Updated'
            self.stdout.write(f'{verb} movie: {movie.title}')

        self.stdout.write(
            self.style.SUCCESS(
                f'Seed finished: {Genre.objects.count()} genres, '
                f'{Person.objects.count()} people, {Movie.objects.count()} movies, '
                f'{Rating.objects.count()} ratings.'
            )
        )

