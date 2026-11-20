import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        # --- Category ---
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['name'], 'verbose_name_plural': 'Categories'},
        ),
        # --- Unit ---
        migrations.CreateModel(
            name='Unit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
                ('short_name', models.CharField(max_length=20, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['name']},
        ),
        # --- Warehouse ---
        migrations.CreateModel(
            name='Warehouse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('address', models.TextField(blank=True)),
                ('contact_person', models.CharField(blank=True, max_length=100)),
                ('phone', models.CharField(blank=True, max_length=30)),
                ('is_default', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['name']},
        ),
        # --- Party: add credit_limit + payment_terms ---
        migrations.AddField(
            model_name='party',
            name='credit_limit',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=14),
        ),
        migrations.AddField(
            model_name='party',
            name='payment_terms',
            field=models.CharField(blank=True, max_length=100),
        ),
        # --- Item: replace CharField category/unit with FKs + keep denorm fields ---
        migrations.RemoveField(model_name='item', name='category'),
        migrations.RemoveField(model_name='item', name='unit'),
        migrations.AddField(
            model_name='item',
            name='category',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='items', to='api.category',
            ),
        ),
        migrations.AddField(
            model_name='item',
            name='category_name',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='item',
            name='unit',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='items', to='api.unit',
            ),
        ),
        migrations.AddField(
            model_name='item',
            name='unit_name',
            field=models.CharField(blank=True, max_length=20),
        ),
        # --- OpeningStock ---
        migrations.CreateModel(
            name='OpeningStock',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('rate', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('date', models.DateField()),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('item', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='opening_stocks', to='api.item',
                )),
                ('warehouse', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='opening_stocks', to='api.warehouse',
                )),
            ],
            options={'ordering': ['-date']},
        ),
    ]
