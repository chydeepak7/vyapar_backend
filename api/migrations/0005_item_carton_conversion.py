from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """
    Replaces the old rigid carton fields with a flexible ItemUnitConversion table.
    Also adds conversion_factor to TransactionLine so stock can be correctly tracked
    when selling in alternate units.
    """

    dependencies = [
        ('api', '0004_decimal_places_10'),
    ]

    operations = [
        # --- ItemUnitConversion table ---
        migrations.CreateModel(
            name='ItemUnitConversion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('unit_name', models.CharField(max_length=50, help_text='e.g. Carton, Box, Dozen, Bag')),
                ('conversion_factor', models.DecimalField(
                    max_digits=15, decimal_places=4, default=1,
                    help_text='1 of this unit = how many base units (e.g. 1 Carton = 12 pcs → factor=12)',
                )),
                ('purchase_price', models.DecimalField(max_digits=24, decimal_places=10, default=0,
                    help_text='Purchase price in this unit')),
                ('sale_price', models.DecimalField(max_digits=24, decimal_places=10, default=0,
                    help_text='Sale price in this unit')),
                ('item', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='unit_conversions',
                    to='api.item',
                )),
                ('user', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    to='auth.user',
                )),
            ],
            options={'ordering': ['unit_name']},
        ),

        # --- Add conversion_factor to TransactionLine ---
        migrations.AddField(
            model_name='transactionline',
            name='conversion_factor',
            field=models.DecimalField(
                max_digits=15, decimal_places=4, default=1,
                help_text='Factor to convert line qty to base stock units (1 = no conversion)',
            ),
        ),
    ]
