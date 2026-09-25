"""Tests for the movies application."""

from datetime import date

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Genre, Movie, Person, Rating


class ModelTests(TestCase):
    """Verify the models, their relations and the computed properties."""

    def setUp(self):
        self.action = Genre.objects.create(name='Action')
        self.drama = Genre.objects.create(name='Drama')
        self.person = Person.objects.create(
            first_name='Ana',
            last_name='Torres',
            birth_date=date(1990, 5, 4),
        )
        self.movie = Movie.objects.create(
            title='Sample Movie',
            synopsis='A movie used in the tests.',
            release_date=date(2020, 1, 1),
        )
        self.movie.genres.set([self.action, self.drama])
        self.movie.cast.set([self.person])

    def test_str_methods(self):
        self.assertEqual(str(self.action), 'Action')
        self.assertEqual(str(self.person), 'Ana Torres')
        self.assertEqual(str(self.movie), 'Sample Movie')
        self.assertEqual(str(Rating(movie=self.movie, score=4)), 'Sample Movie: 4/5')

    def test_person_full_name_property(self):
        self.assertEqual(self.person.full_name, 'Ana Torres')

    def test_average_rating_is_none_without_ratings(self):
        self.assertIsNone(self.movie.average_rating)

    def test_average_rating_calculates_the_mean(self):
        Rating.objects.create(movie=self.movie, score=5)
        Rating.objects.create(movie=self.movie, score=4)
        self.assertEqual(self.movie.average_rating, 4.5)

    def test_movie_str_methods_and_relations(self):
        self.assertEqual(self.movie.genres.count(), 2)
        self.assertEqual(self.person.movies.count(), 1)

    def test_deleting_a_movie_deletes_its_ratings(self):
        Rating.objects.create(movie=self.movie, score=3)
        self.assertEqual(Rating.objects.count(), 1)
        self.movie.delete()
        self.assertEqual(Rating.objects.count(), 0)


class AdminConfigTests(TestCase):
    """Verify the ModelAdmin options of the movies application."""

    def test_movie_admin_options(self):
        movie_admin = admin.site._registry[Movie]
        self.assertEqual(movie_admin.list_per_page, 20)
        self.assertEqual(movie_admin.date_hierarchy, 'release_date')
        self.assertEqual(set(movie_admin.search_fields), {'title', 'synopsis'})
        self.assertEqual(set(movie_admin.filter_horizontal), {'genres', 'cast'})
        self.assertIn('created_at', movie_admin.readonly_fields)
        self.assertIn('updated_at', movie_admin.readonly_fields)
        self.assertEqual(len(movie_admin.inlines), 1)

    def test_all_models_are_registered(self):
        registered = {
            model.__name__
            for model in admin.site._registry
            if model._meta.app_label == 'movies'
        }
        self.assertEqual(registered, {'Movie', 'Genre', 'Person', 'Rating'})

    def test_rating_inline_is_tabular_with_one_extra(self):
        rating_inline = admin.site._registry[Movie].inlines[0]
        self.assertEqual(rating_inline.model, Rating)
        self.assertEqual(rating_inline.extra, 1)


class PermissionTests(TestCase):
    """Verify the group based access control of the admin."""

    def setUp(self):
        from django.contrib.auth.models import Group, Permission

        user_model = get_user_model()
        self.editor = user_model.objects.create_user(
            username='editor_test',
            password='Test12345!',
            is_staff=True,
        )
        group = Group.objects.create(name='editores')
        for codename in ('add_movie', 'change_movie'):
            group.permissions.add(
                Permission.objects.get(
                    content_type__app_label='movies',
                    codename=codename,
                )
            )
        self.editor.groups.add(group)

    def test_editor_can_add_and_change_but_not_delete(self):
        self.assertTrue(self.editor.has_perm('movies.add_movie'))
        self.assertTrue(self.editor.has_perm('movies.change_movie'))
        self.assertFalse(self.editor.has_perm('movies.delete_movie'))

    def test_editor_cannot_reach_the_delete_view(self):
        self.client.force_login(self.editor)
        movie = Movie.objects.create(title='Protected', release_date=date(2021, 1, 1))
        response = self.client.get(
            reverse('admin:movies_movie_delete', args=[movie.pk])
        )
        self.assertEqual(response.status_code, 403)

    def test_editor_can_open_the_movie_changelist(self):
        self.client.force_login(self.editor)
        response = self.client.get(reverse('admin:movies_movie_changelist'))
        self.assertEqual(response.status_code, 200)


class RecommendationsViewTests(TestCase):
    """Verify the public recommendations view."""

    def setUp(self):
        self.genre = Genre.objects.create(name='Action')
        self.other = Genre.objects.create(name='Drama')
        self.best = Movie.objects.create(title='Best', release_date=date(2020, 1, 1))
        self.worst = Movie.objects.create(title='Worst', release_date=date(2019, 1, 1))
        self.best.genres.add(self.genre)
        self.worst.genres.add(self.genre)
        Rating.objects.create(movie=self.best, score=5)
        Rating.objects.create(movie=self.worst, score=2)

    def test_view_returns_200_and_lists_movies_by_score(self):
        response = self.client.get(
            reverse('movies:recommendations', args=[self.genre.pk])
        )
        self.assertEqual(response.status_code, 200)
        titles = [movie.title for movie in response.context['movies']]
        self.assertEqual(titles, ['Best', 'Worst'])

    def test_view_returns_404_for_unknown_genre(self):
        response = self.client.get(reverse('movies:recommendations', args=[99999]))
        self.assertEqual(response.status_code, 404)

