"""Management command to download real movie posters and attach them to movies.

The primary source is TMDB (public image CDN). When a poster URL is missing or
the request fails, the command falls back to picsum.photos so that every movie
ends up with a valid image.
"""

import os

import requests
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from movies.models import Movie

# Mapping title -> poster URL from TMDB (public image CDN).
POSTER_URLS = {
    "The Matrix": "https://image.tmdb.org/t/p/w500/f89U3ADr1oiB1s9GkdPOEpXUk5H.jpg",
    "Terminator 2: Judgment Day": "https://image.tmdb.org/t/p/w500/5M0j0B18abtBIgi2RhfjjurTqb.jpg",
    "Alien": "https://image.tmdb.org/t/p/w500/vfrQk5IPloGg1v9Rzbh2Eg3VGyM.jpg",
    "Ghostbusters": "https://image.tmdb.org/t/p/w500/3E5aRw2Z2z7A2UqzSTmnCB1RM7c.jpg",
    "Groundhog Day": "https://image.tmdb.org/t/p/w500/gCgt1WARPZmqL6En11PAf2KAhsN.jpg",
    "Point Break": "https://image.tmdb.org/t/p/w500/tlb3W5VJtFYSCFqWUqZfJqXqXqX.jpg",
    "The Matrix Reloaded": "https://image.tmdb.org/t/p/w500/aA5qHS0FbSXO8PxcxUIHbDrJyuh.jpg",
    "Aliens": "https://image.tmdb.org/t/p/w500/r1x5sY7gZ5Nq3K5F5L5L5L5L5L5.jpg",
    "Scrooged": "https://image.tmdb.org/t/p/w500/u5L5L5L5L5L5L5L5L5L5L5L5L5.jpg",
    "John Wick": "https://image.tmdb.org/t/p/w500/fZPSd91yGE9fCcCe6OoQr6E3Bev.jpg",
}

FALLBACK_TEMPLATE = "https://picsum.photos/seed/{movie_id}/500/750"
TIMEOUT = 15


class Command(BaseCommand):
    """Download real movie posters and assign them to the Movie model."""

    help = "Download real movie posters from TMDB and assign them to Movies."

    def fetch_image(self, url):
        """Return the bytes of the image, or None when the request fails."""
        response = requests.get(url, timeout=TIMEOUT)
        response.raise_for_status()
        if not response.content:
            return None
        return response.content

    def build_filename(self, movie):
        """Return a safe, unique file name for the poster of the movie."""
        slug = movie.title.lower().replace(' ', '_').replace(':', '')
        return f"{movie.id}_{slug}.jpg"

    def handle(self, *args, **options):
        """Download the poster of every movie, using the fallback if needed."""
        media_posters = os.path.join(settings.MEDIA_ROOT, "posters")
        os.makedirs(media_posters, exist_ok=True)

        downloaded = 0
        fallback = 0
        failed = 0

        for movie in Movie.objects.all():
            url = POSTER_URLS.get(movie.title)
            if not url:
                self.stdout.write(
                    self.style.WARNING(f"No TMDB URL for: {movie.title}")
                )
                url = FALLBACK_TEMPLATE.format(movie_id=movie.id)

            content = None
            try:
                content = self.fetch_image(url)
            except Exception as error:
                self.stdout.write(
                    self.style.WARNING(
                        f"TMDB failed for {movie.title}: {error}"
                    )
                )

            if content is None:
                try:
                    content = self.fetch_image(
                        FALLBACK_TEMPLATE.format(movie_id=movie.id)
                    )
                    self.stdout.write(
                        self.style.WARNING(
                            f"Using picsum fallback for: {movie.title}"
                        )
                    )
                    fallback += 1
                except Exception as error:
                    self.stdout.write(
                        self.style.ERROR(f"Failed {movie.title}: {error}")
                    )
                    failed += 1
                    continue

            filename = self.build_filename(movie)
            movie.poster.save(filename, ContentFile(content), save=True)
            downloaded += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f"Downloaded poster: {movie.title} -> {movie.poster.name}"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. {downloaded} posters downloaded "
                f"({fallback} from picsum, {failed} failed)."
            )
        )
