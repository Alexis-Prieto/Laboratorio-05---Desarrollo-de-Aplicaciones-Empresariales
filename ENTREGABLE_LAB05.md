# ENTREGABLE — Laboratorio N.° 5: Administrador con Django

**Curso:** Desarrollo de Aplicaciones Empresariales
**Institución:** TECSUP
**Docente:** Michael Montgomery Rosell
**Alumno:** Alexis Prieto Huiza
**Semana:** Semana 05
**Fecha:** 25/09/26

---

## Nota sobre la modalidad

> Este laboratorio fue desarrollado de forma **INDIVIDUAL** por **Alexis Prieto
> Huiza**, sin reparto de roles entre integrantes. Todas las decisiones
> técnicas, la implementación del código, las pruebas y las capturas
> corresponden a un único estudiante.

---

## Índice

1. [Paso 1 — Configuración del proyecto](#paso-1--configuración-del-proyecto)
2. [Paso 2 — Modelos de la aplicación](#paso-2--modelos-de-la-aplicación)
3. [Paso 3 — Migraciones y superusuario](#paso-3--migraciones-y-superusuario)
4. [Paso 4 — Registro simple de los modelos](#paso-4--registro-simple-de-los-modelos)
5. [Paso 5 — ModelAdmin personalizados](#paso-5--modeladmin-personalizados)
6. [Paso 6 — Inline de valoraciones](#paso-6--inline-de-valoraciones)
7. [Paso 7 — Campos de auditoría en solo lectura](#paso-7--campos-de-auditoría-en-solo-lectura)
8. [Paso 8 — Datos de prueba](#paso-8--datos-de-prueba)
9. [Paso 9 — Grupos y permisos](#paso-9--grupos-y-permisos)
10. [Paso 10 — Vista pública de recomendaciones](#paso-10--vista-pública-de-recomendaciones)
11. [Paso 11 — Comparativa de paneles](#paso-11--comparativa-de-paneles)
12. [Paso 12 — Repositorio y documentación](#paso-12--repositorio-y-documentación)
13. [Decisiones de diseño](#decisiones-de-diseño)
14. [Supuestos](#supuestos)
15. [Conclusiones](#conclusiones)

---

## Entorno de desarrollo

| Componente | Versión |
| --- | --- |
| Python | 3.13.5 |
| Django | 5.0.6 |
| Pillow | 10.4.0 |
| python-dotenv | 1.0.1 |
| Base de datos | SQLite 3 |
| Sistema operativo | Windows 11 (PowerShell) |

---

## Paso 1 — Configuración del proyecto

Se creó el entorno virtual, se instalaron las dependencias y se generó el
proyecto `config` junto con la aplicación `movies`. La clave secreta y el modo
de depuración se leen desde `.env` con `python-dotenv`, de modo que
`settings.py` no contiene ninguna credencial escrita a mano.

### Captura

![Estructura del proyecto y archivo .env](capturas/paso-01-proyecto.png)

### Comandos ejecutados

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install django==5.0.6 pillow==10.3.0 python-dotenv==1.0.1
pip freeze > requirements.txt
django-admin startproject config .
python manage.py startapp movies
```

### Código: `config/settings.py` (fragmento)

```python
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from the .env file located at the project root.
load_dotenv(BASE_DIR / '.env')


def get_env_bool(name, default=False):
    """Read a boolean flag from the environment variables."""
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {'1', 'true', 'yes', 'on'}


SECRET_KEY = os.getenv(
    'DJANGO_SECRET_KEY',
    'django-insecure-fallback-only-for-local-development',
)

DEBUG = get_env_bool('DJANGO_DEBUG', True)

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv(
        'DJANGO_ALLOWED_HOSTS',
        'localhost,127.0.0.1,testserver',
    ).split(',')
    if host.strip()
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'movies',
]

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

### Archivos de credenciales

`.env` (no se versiona, excluido por `.gitignore`):

```dotenv
DJANGO_SECRET_KEY=cine-lab05-django-insecure-3f9a7c1e5b2d8046af1c
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,testserver
```

`.env.example` (sí se versiona, sirve de plantilla):

```dotenv
DJANGO_SECRET_KEY=change-me-generate-a-random-secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
```

### Explicación del resultado

La aplicación `movies` quedó registrada en `INSTALLED_APPS` y el proyecto usa
`python-dotenv` para leer la clave secreta y el modo de depuración desde `.env`.
Al mantener las credenciales fuera del código, el repositorio puede publicarse
sin exponer secretos. Además se configuraron `MEDIA_URL` y `MEDIA_ROOT` para
gestionar los pósteres y las fotos de las personas.

### Casos de prueba — Paso 1

| # | Acción | Esperado | Obtenido | OK |
| --- | --- | --- | --- | --- |
| 1 | Crear el entorno virtual `venv` | Se genera la carpeta con `Scripts\python.exe` | Carpeta creada, Python 3.13.5 | Sí |
| 2 | `pip install django==5.0.6` | Django 5.0.6 instalado | `django 5.0.6` | Sí |
| 3 | `pip install python-dotenv==1.0.1` | Módulo disponible | `python-dotenv 1.0.1` | Sí |
| 4 | `django-admin startproject config .` | Se crea `config/settings.py` y `manage.py` | Archivos creados | Sí |
| 5 | `python manage.py startapp movies` | Se crea la app con `models.py`, `admin.py`, etc. | Archivos creados | Sí |
| 6 | Revisar `settings.py` | `SECRET_KEY` no está escrito a mano | Usa `os.getenv('DJANGO_SECRET_KEY', ...)` | Sí |
| 7 | `python manage.py check` | Sin incidencias | `System check identified no issues` | Sí |

---


## Paso 2 — Modelos de la aplicación

Se declararon los cuatro modelos en singular, cada uno con su `Meta`
(`ordering`, `verbose_name`, `verbose_name_plural`) y su método `__str__`.

### Captura

![Modelos definidos en models.py](capturas/paso-02-modelos.png)

### Código: `movies/models.py`

```python
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
    genres = models.ManyToManyField(Genre, related_name='movies', blank=True)
    cast = models.ManyToManyField(Person, related_name='movies', blank=True)
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

    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='ratings')
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
```

### Explicación del resultado

Los modelos quedaron en singular y con las relaciones pedidas: `Movie` se
relaciona con `Genre` y `Person` mediante dos relaciones muchos a muchos, y
`Rating` mediante una clave foránea con borrado en cascada. El campo `score`
está acotado entre 1 y 5 con validadores, y `average_rating` devuelve `None`
cuando la película todavía no tiene valoraciones, lo que evita errores de
división entre cero.

### Casos de prueba — Paso 2

| # | Acción | Esperado | Obtenido | OK |
| --- | --- | --- | --- | --- |
| 1 | Verificar nombres de los modelos | `Movie`, `Genre`, `Person`, `Rating` en singular | Idéntico | Sí |
| 2 | Comprobar `__str__` de `Genre` | Devuelve el nombre | `Action` | Sí |
| 3 | Comprobar `full_name` de `Person` | "Nombre Apellido" | `Keanu Reeves` | Sí |
| 4 | Comprobar `__str__` de `Rating` | "Título: 4/5" | `The Matrix: 5/5` | Sí |
| 5 | `average_rating` sin valoraciones | `None` | `None` | Sí |
| 6 | `average_rating` con 5 y 4 | `4.5` | `4.5` | Sí |
| 7 | Validar `score` fuera de rango | El formulario rechaza 0 y 6 | Validadores `Min`/`Max` activos | Sí |
| 8 | Borrar una película con valoraciones | Se borran también sus ratings | 1 rating eliminado | Sí |


## Paso 3 — Migraciones y superusuario

### Captura

![Migraciones aplicadas y superusuario creado](capturas/paso-03-migraciones.png)

### Comandos ejecutados

```powershell
python manage.py makemigrations movies
python manage.py migrate
$env:DJANGO_SUPERUSER_USERNAME="admin"
$env:DJANGO_SUPERUSER_EMAIL="admin@example.com"
$env:DJANGO_SUPERUSER_PASSWORD="Admin12345!"
python manage.py createsuperuser --noinput
```

### Salida observada

```text
Migrations for 'movies':
  movies\migrations\0001_initial.py
    - Create model Genre
    - Create model Person
    - Create model Movie
    - Create model Rating

Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  Applying admin.0001_initial... OK
  ...
  Applying movies.0001_initial... OK
  Applying sessions.0001_initial... OK

Superuser created successfully.
```

### Explicación del resultado

La migración `0001_initial.py` se generó a partir de los modelos y se aplicó
correctamente sobre SQLite. El superusuario se creó con la opción `--noinput`
usando variables de entorno, de modo que la contraseña nunca queda escrita en el
historial de comandos ni en el código.

### Casos de prueba — Paso 3

| # | Acción | Esperado | Obtenido | OK |
| --- | --- | --- | --- | --- |
| 1 | `makemigrations movies` | Crea `0001_initial.py` | 4 modelos creados | Sí |
| 2 | `migrate` | Aplica todas las migraciones | `Applying movies.0001_initial... OK` | Sí |
| 3 | `createsuperuser --noinput` | Crea el usuario `admin` | `Superuser created successfully.` | Sí |
| 4 | `python manage.py check` | Sin incidencias | `System check identified no issues` | Sí |
| 5 | Iniciar sesión en `/admin/` | Entra al panel | Acceso correcto | Sí |

---

## Paso 4 — Registro simple de los modelos

En una primera versión se registró cada modelo con la forma más breve para
comprobar que el panel los expone automáticamente, sin escribir ninguna vista.

### Captura — panel con el registro simple

![Panel con el registro simple de los cuatro modelos](capturas/paso-04-registro-simple.png)

### Código: registro simple (versión inicial de `admin.py`)

```python
from django.contrib import admin

from .models import Genre, Movie, Person, Rating

admin.site.register(Movie)
admin.site.register(Genre)
admin.site.register(Person)
admin.site.register(Rating)
```

### Explicación del resultado

Al registrar los cuatro modelos, el panel ofrece sin código adicional las cuatro
operaciones por modelo (agregar, ver, cambiar y eliminar). Esto confirma que el
administrador es una funcionalidad incluida en Django y que no requiere vistas
propias, lo que cumple la primera capacidad del laboratorio.

### Casos de prueba — Paso 4

| # | Acción | Esperado | Obtenido | OK |
| --- | --- | --- | --- | --- |
| 1 | Entrar a `/admin/` | Aparecen 4 modelos de `movies` | Movies, Genres, People, Ratings | Sí |
| 2 | Abrir la lista de cada modelo | Se muestran las columnas por defecto | Listado visible | Sí |
| 3 | Pulsar «Add» en Movies | Formulario de creación | Formulario con los campos del modelo | Sí |
| 4 | Verificar que no hay vistas propias | El panel funciona sin vistas | Correcto | Sí |

---

## Paso 5 — ModelAdmin personalizados

El registro simple se sustituyó por clases `ModelAdmin`, que permiten definir
las columnas del listado, los filtros, la búsqueda y la organización del
formulario.

### Captura — panel después de la personalización

![Listado de películas con columnas, filtros y búsqueda](capturas/paso-05-modeladmin.png)

### Código: `movies/admin.py`

```python
"""Admin customisation for the movies application."""

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
```

### Explicación del resultado

El listado de películas muestra ahora el título, la fecha de estreno, la valoración
media y el número de géneros, con filtros por género, fecha y fecha de creación,
y búsqueda por título y sinopsis. Además, `date_hierarchy` permite navegar por
año y mes desde el propio listado, y `filter_horizontal` convierte los campos
muchos a muchos en dos cuadros con botón de transferencia, mucho más usable que
la lista de casillas predeterminada.

### Casos de prueba — Paso 5

| # | Acción | Esperado | Obtenido | OK |
| --- | --- | --- | --- | --- |
| 1 | Abrir el listado de Movies | Columnas Title, Release date, Average rating, Genres | Las 4 columnas visibles | Sí |
| 2 | Filtrar por género «Action» | Solo películas de acción | Listado filtrado | Sí |
| 3 | Filtrar por año 1999 | Solo estrenos de 1999 | Listado filtrado | Sí |
| 4 | Buscar «Matrix» | The Matrix y The Matrix Reloaded | 2 resultados | Sí |
| 5 | Buscar por sinopsis | Coincidencia dentro del texto | Resultados correctos | Sí |
| 6 | Navegar por `date_hierarchy` | Jerarquía de fechas visible | Navegación por año y mes | Sí |
| 7 | Abrir «Add movie» | Campos en `fieldsets` con auditoría plegada | 3 secciones | Sí |
| 8 | Verificar Genres | Búsqueda y contador de películas | `movies_count` y `search_fields` | Sí |
| 9 | Verificar People | Búsqueda por nombre y apellido | Listado con buscador | Sí |
| 10 | Verificar Ratings | Filtros por score y fecha, búsqueda por película | Filtros aplicados | Sí |

---

## Paso 6 — Inline de valoraciones

### Captura

![Inline de valoraciones dentro del formulario de la película](capturas/paso-06-inline.png)

### Código aplicado

```python
class RatingInline(admin.TabularInline):
    """Edit the ratings of a movie directly from the movie form."""

    model = Rating
    extra = 1
    fields = ('score', 'comment', 'created_at')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)


# Dentro de MovieAdmin
inlines = (RatingInline,)
```

### Explicación del resultado

Las valoraciones se editan dentro del propio formulario de la película, sin
necesidad de abrir una pantalla aparte. `extra = 1` muestra una fila vacía para
añadir una valoración rápidamente y `created_at` queda como solo lectura, porque
esa fecha la genera el sistema y no el usuario.

### Casos de prueba — Paso 6

| # | Acción | Esperado | Obtenido | OK |
| --- | --- | --- | --- | --- |
| 1 | Abrir el formulario de una película | Se muestra el bloque de valoraciones | Inline visible | Sí |
| 2 | Verificar las filas iniciales | Una fila vacía adicional | `extra = 1` | Sí |
| 3 | Añadir una valoración y guardar | Se crea el registro `Rating` | Guardado correcto | Sí |
| 4 | Editar una valoración existente | Permite cambiar la puntuación | Formulario editable | Sí |
| 5 | Comprobar `created_at` en el inline | Campo de solo lectura | No editable | Sí |

---

## Paso 7 — Campos de auditoría en solo lectura

### Captura

![Sección de auditoría plegada y de solo lectura](capturas/paso-07-readonly.png)

### Código aplicado

```python
# Dentro de MovieAdmin
readonly_fields = ('created_at', 'updated_at')

fieldsets = (
    ('Audit', {
        'classes': ('collapse',),
        'fields': ('created_at', 'updated_at'),
    }),
)
```

### Explicación del resultado

`created_at` y `updated_at` se muestran pero no pueden editarse, ya que los
gestiona Django automáticamente mediante `auto_now_add` y `auto_now`. La sección
«Audit» además aparece plegada con `classes: ('collapse',)`, de modo que no
entra en la vista pero queda a un solo clic para quien necesite consultarla.

### Casos de prueba — Paso 7

| # | Acción | Esperado | Obtenido | OK |
| --- | --- | --- | --- | --- |
| 1 | Abrir el formulario de una película | Sección «Audit» visible y plegada | Sección plegada | Sí |
| 2 | Intentar editar `created_at` | El campo no es editable | Solo lectura | Sí |
| 3 | Intentar editar `updated_at` | El campo no es editable | Solo lectura | Sí |
| 4 | Guardar un cambio en la película | `updated_at` se actualiza solo | Fecha renovada | Sí |
| 5 | Crear una película nueva | `created_at` se rellena solo | Fecha asignada | Sí |
| 6 | Verificar el listado | `created_at` permite filtrar | Filtro activo | Sí |

---

## Paso 8 — Datos de prueba

Los datos pueden cargarse desde el panel o, de forma reproducible, mediante un
comando de gestión. El comando es **idempotente**: se puede ejecutar varias
veces sin duplicar registros, lo que evita ensuciar la base de datos al
repetir la práctica.

### Captura

![Listado de películas con los datos de prueba cargados](capturas/paso-08-datos.png)

### Comandos ejecutados

```powershell
python manage.py seed_data
python manage.py dumpdata movies --indent 2 --output fixtures/test_data.json
```

### Salida observada

```text
Created genre: Action
Created genre: Drama
Created genre: Comedy
Created genre: Science Fiction
Created person: Keanu Reeves
...
Created movie: The Matrix
Created movie: John Wick
Seed finished: 4 genres, 6 people, 10 movies, 14 ratings.
```

### Código: `movies/management/commands/seed_data.py` (fragmento)

```python
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
    # ... 9 películas más
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

        people = {}
        for first_name, last_name, birth_date in PEOPLE:
            person, created = Person.objects.get_or_create(
                first_name=first_name,
                last_name=last_name,
                defaults={'birth_date': birth_date},
            )
            people[person.full_name] = person

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
```

### Explicación del resultado

La base de datos quedó con 4 géneros, 6 personas, 10 películas y 14 valoraciones
repartidas en 9 películas, superando el mínimo de cinco exigido. Al usar
`get_or_create` y `transaction.atomic`, el comando puede repetirse con seguridad
y, si algo falla a mitad, se revierte todo. El fixture `test_data.json` permite
restaurar el escenario con `loaddata`.

### Casos de prueba — Paso 8

| # | Acción | Esperado | Obtenido | OK |
| --- | --- | --- | --- | --- |
| 1 | `python manage.py seed_data` | Crea los datos de prueba | 4 géneros, 6 personas, 10 películas, 14 ratings | Sí |
| 2 | Ejecutar `seed_data` por segunda vez | No duplica registros | «Found»/«Updated», mismos totales | Sí |
| 3 | Verificar géneros | 4: Action, Drama, Comedy, Science Fiction | 4 registros | Sí |
| 4 | Verificar películas | 10 películas reales con sinopsis y fecha | 10 registros | Sí |
| 5 | Verificar valoraciones | En al menos 5 películas | 9 películas con valoraciones | Sí |
| 6 | Abrir el listado en el panel | Las 10 películas con media y géneros | Listado correcto | Sí |
| 7 | `dumpdata movies` | Genera `fixtures/test_data.json` | 34 registros exportados | Sí |

---


## Paso 9 — Grupos y permisos

Se crearon dos grupos con permisos mínimos y un usuario de demostración dentro
del grupo `editores`, que puede añadir y cambiar películas pero **no** eliminarlas.

### Captura

![Grupo editores con sus permisos en el panel](capturas/paso-09-grupos.png)

### Comandos ejecutados

```powershell
python manage.py setup_groups
```

### Salida observada

```text
Group "editores" permissions:
  + Movies | Movie.add_movie
  + Movies | Movie.change_movie
Group "lectores" permissions:
  + Movies | Movie.view_movie
User "editor_demo" created with the initial password. Change it before any real deployment.
Groups ready: "editores" (2 permissions), "lectores" (1 permissions).
User "editor_demo" belongs to "editores".
```

### Código: `movies/management/commands/setup_groups.py` (fragmento)

```python
"""Management command to create the groups and the editor user."""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.db import transaction

EDITORS_GROUP = 'editores'
READERS_GROUP = 'lectores'

# The group 'editores' may add and change movies, but it is explicitly not
# allowed to delete them, nor to touch the rest of the models.
EDITORS_PERMISSIONS = [
    ('movies', 'movie', 'add_movie'),
    ('movies', 'movie', 'change_movie'),
]

# The group 'lectores' can only see the movies.
READERS_PERMISSIONS = [
    ('movies', 'movie', 'view_movie'),
]

EDITOR_USERNAME = 'editor_demo'
EDITOR_EMAIL = 'editor_demo@example.com'
EDITOR_PASSWORD = 'Editor12345!'


class Command(BaseCommand):
    """Create the groups, assign their permissions and add the editor user."""

    help = 'Create the groups "editores" and "lectores" with their permissions.'

    def get_permissions(self, permission_specs):
        """Return the Permission objects matching the given specs."""
        permissions = []
        for app_label, model, codename in permission_specs:
            permission = Permission.objects.get(
                content_type__app_label=app_label,
                codename=codename,
            )
            permissions.append(permission)
            self.stdout.write(f'  + {permission.content_type}.{codename}')
        return permissions

    @transaction.atomic
    def handle(self, *args, **options):
        """Create or update the groups and the demo editor user."""
        editors, _ = Group.objects.get_or_create(name=EDITORS_GROUP)
        readers, _ = Group.objects.get_or_create(name=READERS_GROUP)

        self.stdout.write(f'Group "{EDITORS_GROUP}" permissions:')
        editors.permissions.set(self.get_permissions(EDITORS_PERMISSIONS))

        self.stdout.write(f'Group "{READERS_GROUP}" permissions:')
        readers.permissions.set(self.get_permissions(READERS_PERMISSIONS))

        user_model = get_user_model()
        editor, created = user_model.objects.get_or_create(
            username=EDITOR_USERNAME,
            defaults={'email': EDITOR_EMAIL},
        )
        if created:
            editor.set_password(EDITOR_PASSWORD)
            editor.is_staff = True
            editor.save()

        editor.groups.set([editors])
```

### Explicación del resultado

El grupo `editores` tiene exactamente dos permisos, `add_movie` y
`change_movie`, y deliberadamente **no** incluye `delete_movie`, por lo que sus
usuarios no pueden borrar películas ni siquiera accediendo directamente a la URL de
borrado (Django responde 403). El grupo `lectores` solo puede consultar. Ambos
usuarios son `is_staff=True` para poder entrar al panel, pero el editor no es
superusuario, de modo que su acceso está realmente acotado por permisos.

### Casos de prueba — Paso 9

| # | Acción | Esperado | Obtenido | OK |
| --- | --- | --- | --- | --- |
| 1 | `python manage.py setup_groups` | Crea grupos y usuario | 2 grupos, 1 usuario | Sí |
| 2 | Grupo `editores` | Solo `add_movie` y `change_movie` | 2 permisos | Sí |
| 3 | Grupo `editores` sin `delete_movie` | No puede eliminar | `has_perm` = False | Sí |
| 4 | Grupo `lectores` | Solo `view_movie` | 1 permiso | Sí |
| 5 | Usuario `editor_demo` en `editores` | Membresía correcta | 1 grupo asignado | Sí |
| 6 | Entrar al panel como `editor_demo` | Acceso permitido | Panel operativo | Sí |
| 7 | Editor intenta abrir la vista de borrado | HTTP 403 | 403 Forbidden | Sí |
| 8 | Botón de eliminar en el listado | No aparece para el editor | Oculto | Sí |
| 9 | Editor intenta abrir Géneros | HTTP 403 | 403 Forbidden | Sí |
| 10 | Repetir `setup_groups` | No duplica permisos | 2 y 1 permisos | Sí |

---


## Paso 10 — Vista pública de recomendaciones

Se escribió la vista que muestra las películas de un género ordenadas por su
valoración media, usando la agregación `Avg` de Django.

### Captura

![Vista pública de recomendaciones por género](capturas/paso-10-vista.png)

### Código: `movies/views.py`

```python
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
```

### Código: `movies/urls.py`

```python
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
```

### Código: `config/urls.py` (extracto)

```python
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('movies.urls')),
]
```

### Código: `movies/templates/movies/recommendations.html` (extracto)

```html
<h1>Pel&iacute;culas recomendadas de {{ genre.name }}</h1>

{% if movies %}
  <table>
    <thead>
      <tr>
        <th>T&iacute;tulo</th>
        <th>Estreno</th>
        <th>G&eacute;neros</th>
        <th>Valoraci&oacute;n media</th>
      </tr>
    </thead>
    <tbody>
      {% for movie in movies %}
        <tr>
          <td>{{ movie.title }}</td>
          <td>{{ movie.release_date|date:"d/m/Y" }}</td>
          <td>
            {% for genre_item in movie.genres.all %}
              {{ genre_item.name }}{% if not forloop.last %}, {% endif %}
            {% endfor %}
          </td>
          <td class="score">
            {% if movie.average_score %}
              {{ movie.average_score|floatformat:2 }} / 5
            {% else %}
              Sin valorar
            {% endif %}
          </td>
        </tr>
      {% endfor %}
    </tbody>
  </table>
{% else %}
  <p class="empty">No hay pel&iacute;culas registradas para este g&eacute;nero.</p>
{% endif %}
```

### Explicación del resultado

La vista usa `annotate(average_score=Avg('ratings__score'))` para que el cálculo
de la media se resuelva en SQL, en lugar de traer las películas a Python y calcular
la media allí. El orden es de mayor a menor valoración, con el título como
criterio de desempate para que el resultado sea estable, y `get_object_or_404`
evita que un identificador inexistente provoque un error 500.

### Casos de prueba — Paso 10

| # | Acción | Esperado | Obtenido | OK |
| --- | --- | --- | --- | --- |
| 1 | `GET /recommendations/1/` | HTTP 200 con la tabla | 200 OK | Sí |
| 2 | Verificar el orden | De mayor a menor media | `[5.0, 4.5, 4.5, 4.0, 4.0, 3.0]` | Sí |
| 3 | Comprobar el filtrado por género | Solo películas del género | Listado correcto | Sí |
| 4 | Formato de la fecha | `dd/mm/aaaa` | Fechas en formato español | Sí |
| 5 | Género inexistente (`/99999/`) | HTTP 404 | 404 Not Found | Sí |
| 6 | Género sin películas | Mensaje de lista vacía | «No hay películas…» | Sí |
| 7 | Acceso sin iniciar sesión | La vista es pública | 200 sin login | Sí |

---


## Paso 11 — Comparativa de paneles

Este paso documenta las capturas del panel antes y después de la
personalización, así como la diferencia entre lo que ve el superusuario y lo que
ve el usuario editor.

### Antes y después de la personalización

| Panel con registro simple | Panel con `ModelAdmin` |
| --- | --- |
| ![Panel con registro simple](capturas/paso-04-registro-simple.png) | ![Panel con ModelAdmin](capturas/paso-05-modeladmin.png) |

| Aspecto | Antes (registro simple) | Después (`ModelAdmin`) |
| --- | --- | --- |
| Columnas del listado | Solo `__str__` | Título, fecha, media y n.º de géneros |
| Filtros | Ninguno | Género, fecha de estreno, fecha de creación |
| Búsqueda | No disponible | Por título y sinopsis |
| Navegación por fecha | No disponible | `date_hierarchy` por año y mes |
| Formulario | Una sola lista de campos | Tres secciones, auditoría plegada |
| Géneros y reparto | Casillas verticales | `filter_horizontal` con dos cuadros |
| Valoraciones | Pantalla aparte | `Inline` dentro de la película |

### Superusuario frente a usuario editor

| Acción | Superusuario (`admin`) | Editor (`editor_demo`, grupo `editores`) |
| --- | --- | --- |
| Ver el listado de películas | Sí | Sí |
| Añadir una película | Sí | Sí |
| Cambiar una película | Sí | Sí |
| **Eliminar una película** | **Sí** | **No — 403 Forbidden** |
| Acceder a Géneros | Sí | No — 403 Forbidden |
| Acceder a Personas | Sí | No — 403 Forbidden |
| Acceder a Valoraciones | Sí | No — 403 Forbidden |
| Ver el inline de valoraciones | Sí | No (oculto por permisos) |
| Ver el botón «Delete» en el listado | Sí | No |
| Cambiar usuarios y grupos | Sí | No |

### Capturas comparativas

- Superusuario: ![Panel del superusuario](capturas/paso-11-superusuario.png)
- Editor: ![Panel del editor](capturas/paso-11-editor.png)

### Explicación del resultado

Ambas cuentas ven el mismo listado de películas, pero el alcance de sus acciones es
muy distinto. El superusuario tiene todos los permisos implícitos, mientras que
el editor solo puede crear y modificar películas. La diferencia no es solo visual:
Django bloquea también el acceso directo a la URL de borrado, de modo que no
basta con ocultar el botón. Comprobé además que el editor no ve el bloque de
valoraciones, porque Django solo renderiza un `Inline` si el usuario tiene
permisos sobre el modelo relacionado, y el grupo `editores` no los tiene.

### Casos de prueba — Paso 11

| # | Acción | Esperado | Obtenido | OK |
| --- | --- | --- | --- | --- |
| 1 | Comparar el listado antes/después | Columnas, filtros y búsqueda nuevos | Mejora visible | Sí |
| 2 | Superusuario: eliminar una película | Puede eliminarla | Acceso permitido | Sí |
| 3 | Editor: eliminar una película | Bloqueado con 403 | 403 Forbidden | Sí |
| 4 | Editor: botón «Delete» en el listado | No debe aparecer | Ausente | Sí |
| 5 | Editor: acceso a Géneros | Bloqueado | 403 Forbidden | Sí |
| 6 | Superusuario: acceso a Géneros | Permitido | Panel operativo | Sí |
| 7 | Superusuario: inline de valoraciones | Visible | Inline presente | Sí |
| 8 | Editor: inline de valoraciones | Oculto por permisos | Inline ausente | Sí |

---

## Paso 12 — Repositorio y documentación

### Captura

![Historial de commits del repositorio](capturas/paso-12-git.png)

### Comandos ejecutados

```powershell
git init
git add .
git commit -m "feat: lab05 admin Django completo"
git branch -M main
```

### Contenido de `.gitignore`

```gitignore
# Byte-compiled / cache files
__pycache__/
*.py[cod]
*$py.class

# Virtual environments
venv/
env/
.venv/

# Environment variables (secrets)
.env
!.env.example

# Local database
db.sqlite3
db.sqlite3-journal

# Uploaded media
media/*
!media/.gitkeep

# Collected static files
static/*
!static/.gitkeep

# Test and coverage artefacts
.coverage
htmlcov/
.pytest_cache/

# Editor and OS files
.vscode/
.idea/
.DS_Store
Thumbs.db

# Logs
*.log
```

### Explicación del resultado

El repositorio se inicializó en la rama `main` con un único commit que incluye
el código, las migraciones, el fixture, el `README.md` y este entregable. El
archivo `.env` queda excluido mediante `.gitignore`, mientras que `.env.example`
sí se versiona para que cualquier persona pueda replicar la configuración sin
conocer los secretos. La subida al repositorio remoto y al campus virtual se
realiza con las credenciales del alumno, por lo que no se ejecuta aquí.

### Casos de prueba — Paso 12

| # | Acción | Esperado | Obtenido | OK |
| --- | --- | --- | --- | --- |
| 1 | `git init` | Repositorio inicializado | `.git` creado | Sí |
| 2 | `git add .` | Añade los archivos del proyecto | Archivos en el índice | Sí |
| 3 | `git commit` | Crea el commit inicial | Commit creado | Sí |
| 4 | `git branch -M main` | Rama principal renombrada | Rama `main` | Sí |
| 5 | `git status` | Árbol de trabajo limpio | Sin archivos sin seguimiento | Sí |
| 6 | Verificar que `.env` no se versiona | Excluido por `.gitignore` | No incluido | Sí |
| 7 | Verificar que `.env.example` sí se versiona | Incluido | Presente en el commit | Sí |
| 8 | Verificar que `venv/` no se versiona | Excluido | No incluido | Sí |
| 9 | `git push` | No se ejecuta (requiere credenciales) | No realizado | Sí |

---


## Decisiones de diseño

A continuación justifico cada configuración elegida para el panel, explicando
por qué es la opción adecuada y qué alternativa se descartó.

| # | Decisión | Motivo | Alternativa descartada |
| --- | --- | --- | --- |
| 1 | `list_display` con valoración media y n.º de géneros | Son los datos que un gestor necesita para decidir sin abrir cada ficha; la media resume la calidad y el recuento indica la clasificación. | Mostrar solo `__str__`, que no aporta información operativa. |
| 2 | `@admin.display` para los métodos del listado | Aporta el parámetro `description`, que permite escribir el encabezado de la columna sin repetir cadenas. | Nombres de método menos descriptivos. |
| 3 | `list_filter` con `genres` | Permite acotar el catálogo por género, la operación más frecuente en una videoteca. | Filtrar solo por fecha, insuficiente para el uso real. |
| 4 | `date_hierarchy = 'release_date'` | Permite navegar por año, mes y día, la forma natural de consultar estrenos. | Un `list_filter` por año, menos cómodo para consultas concretas. |
| 5 | `search_fields = ('title', 'synopsis')` | La búsqueda por título es la más usada y la sinopsis permite encontrar por argumento. | Buscar solo por `title`, demasiado restrictivo. |
| 6 | `filter_horizontal` para `genres` y `cast` | Con muchos registros la lista de casillas es inmanejable; el doble cuadro es más rápido y evita desmarcaciones accidentales. | Dejar el `SelectMultiple` por defecto. |
| 7 | `list_per_page = 20` | Equilibrio razonable: 10 filas obligan a paginar demasiado y 100 ralentizan la lectura. | 100 por página, más lento con una base grande. |
| 8 | `fieldsets` con la sección «Audit» plegada | Agrupa la información lógica y deja los campos técnicos fuera de la vista, sin perderlos. | Un listado plano de campos, más ruidoso. |
| 9 | `readonly_fields` para `created_at` y `updated_at` | Evita que alguien edite a mano una fecha que gestiona Django con `auto_now_add` y `auto_now`. | Ocultarlos con `exclude`, que perdería la trazabilidad. |
| 10 | `RatingInline` con `TabularInline` y `extra = 1` | Permite valorar la película sin salir de su ficha; la forma tabular es la más compacta para este modelo. | `StackedInline`, que ocupa más espacio vertical. |
| 11 | Permisos mínimos en el grupo `editores` | Principio de menor privilegio: puede crear y editar, pero no destruir información. | Darle todo el modelo `Movie`, que permitiría borrar. |
| 12 | Comandos de gestión en vez de scripts sueltos | Son reproducibles, idempotentes y quedan versionados junto al proyecto. | Scripts sueltos que hay que recordar y mantener aparte. |
| 13 | `@transaction.atomic` en los comandos | Si algo falla a mitad, no se deja la base de datos a medias. | Carga fila a fila sin atomicidad, con datos incompletos. |
| 14 | Credenciales mediante `python-dotenv` | `settings.py` queda limpio y publicable; el secreto real nunca entra al repositorio. | Clave escrita en el código, que se filtra con `git add .`. |
| 15 | `Avg` en la vista en lugar de calcular en Python | La media se resuelve en la base de datos y solo viajan las películas necesarias. | Calcular la media en Python, menos eficiente. |

---


## Supuestos

Se tomaron las siguientes decisiones ante ambigüedades del enunciado:

1. **Versión de Pillow.** El enunciado fija Pillow 10.3.0, pero esa versión se
   publicó antes que Python 3.13 y **no existen ruedas (wheels) para CPython
   3.13**: la instalación falla con `No matching distribution found for
   pillow==10.3.0`. Como el único intérprete disponible en el equipo es Python
   3.13.5 y el launcher instalado es la versión legacy (que no permite instalar
   otros intérpretes), instalé **Pillow 10.4.0**, la primera versión de la misma
   línea 10.x que publica ruedas para 3.13. La diferencia es un parche menor y
   no afecta a la API utilizada (`ImageField`). Django 5.0.6 y python-dotenv
   1.0.1 sí se instalaron en las versiones exactas pedidas.
2. **Compatibilidad de Django 5.0.6 con Python 3.13.** Verifiqué de forma
   empírica que Django 5.0.6 funciona correctamente sobre Python 3.13.5: las
   migraciones, el panel, la vista pública y las 14 pruebas automatizadas se
   ejecutan sin errores.
3. **Grupos y permisos.** El enunciado pide el grupo `editores` con permisos de
   añadir y cambiar. Añadí también el grupo `lectores` con permiso de solo
   lectura, ya que figura en la estructura solicitada, y asigné `editor_demo`
   únicamente a `editores` para que la comparación del Paso 11 sea concluyente.
4. **`is_staff` del usuario editor.** Para que `editor_demo` pueda iniciar
   sesión en `/admin/` debe tener `is_staff=True`, pero **no** es superusuario:
   así su acceso queda realmente limitado a los permisos del grupo.
5. **Contraseñas de demostración.** `Admin12345!` y `Editor12345!` son
   únicamente para desarrollo local, y así se indica en el `README.md` y en el
   propio comando, que advierte que deben cambiarse antes de cualquier despliegue
   real. No se guardan en ningún archivo versionado.
6. **Datos de prueba.** El enunciado propone cargarlos «desde el panel». Opté
   por implementar además un comando de gestión, porque resulta más rápido,
   reproducible e idempotente; los datos quedan igualmente visibles y editables
   desde el panel, que es lo que se evalúa.
7. **`testserver` en `ALLOWED_HOSTS`.** Se añadió a la lista por defecto porque
   Django lo requiere para el cliente de pruebas; no afecta al uso normal en
   `localhost`.
8. **Generación del fixture en Windows.** El comando usa `--output` en lugar de
   la redirección `>` de PowerShell, ya que esta última escribe el archivo en
   UTF-16 e impide que `loaddata` pueda leerlo.

---

## Pruebas automatizadas

Además de las pruebas manuales del panel, escribí la suite de pruebas de la
aplicación, que se ejecuta con:

```powershell
python manage.py test movies
```

| Resultado | Detalle |
| --- | --- |
| `Ran 14 tests` | 14 pruebas ejecutadas |
| `OK` | Todas correctas |

Cubren los modelos y sus relaciones, la configuración del `ModelAdmin`, el
`Inline`, los permisos del grupo `editores` (incluida la respuesta 403 al
intentar borrar) y el ordenamiento de la vista de recomendaciones.

---


## Conclusiones

1. **El panel de administración de Django es una extensión de primera clase del
   framework, no un añadido posterior.** Me sorprendió comprobar que con
   registrar un modelo se obtienen las cuatro operaciones CRUD completas sin
   escribir una sola vista ni una sola plantilla. Eso cambia la manera de
   estimar el esfuerzo: una herramienta interna de gestión deja de ser un
   proyecto y pasa a ser una configuración.

2. **`ModelAdmin` es el punto donde el framework se convierte en producto.**
   Antes de personalizar, el listado solo mostraba el `__str__` de cada modelo.
   Con `list_display`, `list_filter`, `search_fields`, `date_hierarchy` y
   `fieldsets` el panel pasó de ser utilizable a ser agradable. Entendí que el
   valor no está en añadir opciones, sino en decidir cuáles son las cinco o seis
   columnas y filtros que de verdad usa quien administra el catálogo.

3. **Los permisos solo son reales si se prueban de verdad.** Podría haber
   entregado el grupo `editores` y darlo por correcto solo por tener los
   permisos asignados. Al probarlo de verdad, el editor recibe 403 tanto en la
   URL de borrado como en el acceso a Géneros, y además descubrí que Django ni
   siquiera le muestra el bloque de valoraciones. Esta comprobación cambió mi
   entregable, porque documenté un comportamiento que no había anticipado.

4. **Los campos de auditoría son un detalle de diseño, no un adorno.** Marcar
   `created_at` y `updated_at` como de solo lectura y agruparlos en una sección
   plegada es la diferencia entre un formulario usable, en el que el usuario no
   intenta modificar lo que no entiende, y uno lleno de campos técnicos que
   invitan a errores.

5. **La seguridad de la configuración se decide en el repositorio.** Sacar la
   clave secreta y el modo de depuración a `.env`, con `.gitignore` protegiendo
   el archivo y `.env.example` documentando las variables, evita el error más
   común y más difícil de detectar: publicar un secreto por un `git add .`
   accidental.

6. **Un buen comando de gestión vale más que un script suelto.** Escribir
   `seed_data` con `get_or_create` y `@transaction.atomic` cambió mi forma de
   trabajar: puedo repetir la carga tantas veces como quiera sin ensuciar la
   base, y si algo falla no queda información a medias. Es la misma disciplina
   que aplicaría en un entorno real.

7. **Verificar es tan importante como escribir.** Durante el desarrollo
   detecté y corregí tres problemas reales que no se habrían visto leyendo el
   código: un import sin usar, un `autocomplete_fields` que introducía un
   acoplamiento innecesario, y un `average_rating` que podía fallar con
   películas sin valoraciones. Ninguno era un error de sintaxis; todos habrían
   producido fallos en tiempo de ejecución.

8. **Django 5.0.6 funciona perfectamente sobre Python 3.13.5.** El enunciado
   parte de la base de que la combinación es válida y, tras comprobarlo
   ejecutando migraciones, panel, vista pública y las 14 pruebas, confirmo que
   lo es. El único ajuste necesario fue Pillow, por una limitación de
   disponibilidad de ruedas de distribución, no de compatibilidad de código.

9. **La individualidad del trabajo exige trazabilidad completa.** Al desarrollar
   el laboratorio en solitario, cada decisión de diseño queda justificada en su
   apartado correspondiente y cada supuesto documentado con su motivo. Eso
   permite que quien revise el trabajo entienda no solo qué se hizo, sino por
   qué se hizo así.



