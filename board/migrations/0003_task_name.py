# Generated by Django 4.2.9 on 2024-02-26 06:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('board', '0002_remove_task_developer'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='name',
            field=models.CharField(default=False, max_length=255),
        ),
    ]
