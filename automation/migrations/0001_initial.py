from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name='TestResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True)),
                ('test_case', models.CharField(max_length=255)),
                ('url', models.URLField(max_length=2048)),
                ('passed', models.BooleanField(default=False)),
                ('comment', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'db_table': 'testing'},
        ),
        migrations.CreateModel(
            name='ListingData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=512)),
                ('price', models.CharField(blank=True, max_length=100)),
                ('image_url', models.URLField(blank=True, max_length=2048)),
                ('listing_url', models.URLField(blank=True, max_length=2048)),
                ('scraped_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'db_table': 'listing_data'},
        ),
        migrations.CreateModel(
            name='SuggestionData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True)),
                ('text', models.CharField(max_length=512)),
                ('search_query', models.CharField(max_length=255)),
                ('captured_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'db_table': 'suggestion_data'},
        ),
        migrations.CreateModel(
            name='NetworkLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True)),
                ('url', models.URLField(max_length=2048)),
                ('method', models.CharField(default='GET', max_length=10)),
                ('status_code', models.IntegerField(blank=True, null=True)),
                ('resource_type', models.CharField(blank=True, max_length=50)),
                ('captured_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'db_table': 'network_logs'},
        ),
        migrations.CreateModel(
            name='ConsoleLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True)),
                ('level', models.CharField(default='INFO', max_length=20)),
                ('message', models.TextField()),
                ('source', models.CharField(blank=True, max_length=512)),
                ('captured_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'db_table': 'console_logs'},
        ),
    ]
