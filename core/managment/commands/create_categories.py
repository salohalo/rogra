from django.core.management.base import BaseCommand
from core.models import Category


class Command(BaseCommand):
    help = 'Создает начальные категории для постов'

    def handle(self, *args, **options):
        categories = [
            ('Обсуждение', 'discussion', 'Общие обсуждения'),
            ('Вопрос', 'question', 'Вопросы к сообществу'),
            ('Новости', 'news', 'Новости и события'),
            ('Идеи', 'ideas', 'Идеи и предложения'),
            ('Юмор', 'humor', 'Смешные посты и мемы'),
            ('Технологии', 'tech', 'Технологии и IT'),
            ('Игры', 'games', 'Видеоигры и настолки'),
            ('Кино', 'movies', 'Фильмы и сериалы'),
            ('Музыка', 'music', 'Музыка и исполнители'),
            ('Книги', 'books', 'Книги и литература'),
            ('Спорт', 'sports', 'Спортивные события'),
            ('Образование', 'education', 'Учеба и образование'),
            ('Искусство', 'art', 'Искусство и творчество'),
            ('Наука', 'science', 'Научные открытия'),
            ('Политика', 'politics', 'Политические обсуждения'),
        ]

        created_count = 0
        for name, slug, description in categories:
            obj, created = Category.objects.get_or_create(
                name=name,
                slug=slug,
                defaults={'description': description}
            )
            if created:
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(f'Успешно создано {created_count} категорий из {len(categories)}')
        )