from django.db import migrations, models


def initialize_display_order(apps, schema_editor):
    ArticleImage = apps.get_model('store', 'ArticleImage')
    for article_id in ArticleImage.objects.values_list('article_id', flat=True).distinct():
        images = ArticleImage.objects.filter(article_id=article_id).order_by('-is_primary', 'created_at', 'id')
        for order, image in enumerate(images):
            image.display_order = order
            image.save(update_fields=['display_order'])


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0003_alter_articlesize_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='articleimage',
            name='display_order',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.RunPython(initialize_display_order, migrations.RunPython.noop),
    ]
