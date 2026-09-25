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
        """Return the Permission objects matching the given (app, model, codename)."""
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
            self.stdout.write(
                self.style.WARNING(
                    f'User "{EDITOR_USERNAME}" created with the initial password. '
                    'Change it before any real deployment.'
                )
            )
        else:
            self.stdout.write(f'User "{EDITOR_USERNAME}" already existed.')

        editor.groups.set([editors])

        self.stdout.write(
            self.style.SUCCESS(
                f'Groups ready: "{editors.name}" ({editors.permissions.count()} '
                f'permissions), "{readers.name}" ({readers.permissions.count()} '
                f'permissions). User "{editor.username}" belongs to "{editors.name}".'
            )
        )
