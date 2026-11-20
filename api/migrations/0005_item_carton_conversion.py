from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_decimal_places_10'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='pieces_per_carton',
            field=models.PositiveIntegerField(
                default=1,
                help_text='How many pieces/items are in one carton',
            ),
        ),
        migrations.AddField(
            model_name='item',
            name='carton_purchase_price',
            field=models.DecimalField(
                max_digits=24,
                decimal_places=10,
                default=0,
                help_text='Purchase price per carton',
            ),
        ),
        migrations.AddField(
            model_name='item',
            name='carton_sale_price',
            field=models.DecimalField(
                max_digits=24,
                decimal_places=10,
                default=0,
                help_text='Sale price per carton',
            ),
        ),
    ]
