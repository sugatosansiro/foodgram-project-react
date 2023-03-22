import csv

from django.core.management import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        with open(
            '../data/ingredients.csv',
            'r',
            encoding='utf-8',
            newline=''
        ) as csvfile:
            reader = csv.DictReader(csvfile, delimiter=',')
            # for row in reader:
            #     print(', '.join(row))
            Ingredient.objects.bulk_create(
                Ingredient(**data) for data in reader)
        self.stdout.write(self.style.SUCCESS('Данные успешно загружены'))
