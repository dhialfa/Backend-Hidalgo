# accounts/migrations/0002_rename_usuario_to_user.py
from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),  # tu última previa
    ]

    operations = [
        migrations.RenameModel(old_name="Usuario", new_name="User"),
        migrations.RenameField(model_name="user", old_name="rol", new_name="role"),
        migrations.RenameField(model_name="user", old_name="telefono", new_name="phone"),
    ]
