# Rogra — Платформа для обсуждений

**Rogra** — это веб-платформа для создания и обсуждения постов, написанная на Django.

## 📋 Содержание

- [Возможности](#возможности)
- [Технологии](#технологии)
- [Установка](#установка)
- [Запуск](#запуск)
- [Структура проекта](#структура-проекта)
- [Модели данных](#модели-данных)
- [API Endpoints](#api-endpoints)
- [Админ-панель](#админ-панель)

---

## 🚀 Возможности

- **Регистрация и аутентификация** пользователей
- **Создание постов** трёх типов:
  - Текстовые посты
  - Посты с изображениями
  - Опросы (polls)
- **Система голосования** за посты (лайки/дизлайки)
- **Комментарии** к постам с возможностью редактирования (в течение 1 часа)
- **Теги** для категоризации контента
- **Профиль пользователя** с аватаром и аудио
- **Голосование в опросах** с отображением результатов в реальном времени
- **Сортировка постов**: новые, популярные, обсуждаемые

---

## 🛠 Технологии

| Технология | Версия | Описание |
|------------|--------|----------|
| Python | 3.14+ | Язык программирования |
| Django | 6.0+ | Веб-фреймворк |
| Bootstrap | 5.3+ | CSS-фреймворк |
| Bootstrap Icons | 1.10+ | Иконки |
| SQLite | — | База данных (dev) |
| Pillow | — | Работа с изображениями |

---

## 📦 Установка

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd rogra
```

### 2. Создание виртуального окружения

```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Применение миграций

```bash
python manage.py migrate
```

### 5. Создание суперпользователя (опционально)

```bash
python manage.py createsuperuser
```

---

## ▶️ Запуск

### Режим разработки

```bash
python manage.py runserver
```

После запуска откройте в браузере: `http://127.0.0.1:8000/`

### Продакшн (с gunicorn)

```bash
gunicorn projectigrok.wsgi:application
```

---

## 📁 Структура проекта

```
rogra/
├── manage.py              # Скрипт управления Django
├── db.sqlite3             # База данных SQLite
├── requirements.txt       # Зависимости проекта
├── README.md              # Документация
├── core/                  # Основное приложение
│   ├── models.py          # Модели данных
│   ├── views.py           # Представления (контроллеры)
│   ├── forms.py           # Формы
│   ├── urls.py            # Маршрутизация
│   ├── admin.py           # Настройки админ-панели
│   ├── signals.py         # Сигналы Django
│   ├── tests.py           # Тесты
│   ├── templates/core/    # HTML-шаблоны
│   ├── migrations/        # Миграции БД
│   └── managment/commands/ # Пользовательские команды
├── projectigrok/          # Конфигурация проекта
│   ├── settings.py        # Настройки Django
│   ├── urls.py            # Корневые URL
│   ├── wsgi.py            # WSGI-конфигурация
│   └── asgi.py            # ASGI-конфигурация
└── media/                 # Загружаемые файлы
    ├── avatars/           # Аватары пользователей
    ├── posts/             # Изображения постов
    └── profile_audio/     # Аудиофайлы профилей
```

---

## 🗃 Модели данных

### User (встроенная Django)
Стандартная модель пользователя Django.

### Profile
| Поле | Тип | Описание |
|------|-----|----------|
| user | OneToOne | Связь с User |
| bio | TextField | Информация о себе |
| avatar | ImageField | Аватарка |
| profile_audio | FileField | Аудиофайл |
| created_at | DateTime | Дата создания |

### Tag
| Поле | Тип | Описание |
|------|-----|----------|
| name | CharField | Название тега |
| slug | SlugField | URL-идентификатор |
| description | TextField | Описание |
| color | CharField | Цвет (blue, green, orange, purple, red) |

### Post
| Поле | Тип | Описание |
|------|-----|----------|
| author | ForeignKey | Автор поста |
| title | CharField | Заголовок |
| content | TextField | Содержание |
| post_type | CharField | Тип (text, image, poll) |
| image | ImageField | Изображение |
| upvotes | IntegerField | Количество лайков |
| downvotes | IntegerField | Количество дизлайков |
| tags | ManyToMany | Теги |
| created_at | DateTime | Дата создания |

### Comment
| Поле | Тип | Описание |
|------|-----|----------|
| post | ForeignKey | Связь с постом |
| author | ForeignKey | Автор комментария |
| text | TextField | Текст комментария |
| created_at | DateTime | Дата создания |

### PostVote
| Поле | Тип | Описание |
|------|-----|----------|
| user | ForeignKey | Пользователь |
| post | ForeignKey | Пост |
| vote_type | CharField | Тип (up/down) |
| created_at | DateTime | Дата голосования |

### PollOption
| Поле | Тип | Описание |
|------|-----|----------|
| post | ForeignKey | Связь с опросом |
| text | CharField | Текст варианта ответа |

### PollVote
| Поле | Тип | Описание |
|------|-----|----------|
| user | ForeignKey | Пользователь |
| post | ForeignKey | Опрос |
| option | ForeignKey | Выбранный вариант |

---

## 🌐 API Endpoints

### Аутентификация
| Метод | URL | Описание |
|-------|-----|----------|
| GET/POST | `/register/` | Регистрация |
| GET/POST | `/login/` | Вход |
| GET | `/logout/` | Выход |

### Посты
| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/` | Главная страница (список постов) |
| GET/POST | `/create-post/` | Создание поста |
| GET | `/post/<id>/` | Детальная страница поста |
| POST | `/post/<id>/vote/` | Голосование за пост |
| POST | `/post/<id>/poll-vote/` | Голосование в опросе |

### Профиль
| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/profile/<username>/` | Страница профиля |
| GET/POST | `/edit-profile/` | Редактирование профиля |

### Комментарии
| Метод | URL | Описание |
|-------|-----|----------|
| GET/POST | `/comment/<id>/edit/` | Редактирование комментария |
| GET | `/comment/<id>/delete/` | Удаление комментария |

---

## ⚙️ Админ-панель

Доступна по адресу: `/admin/`

### Зарегистрированные модели:
- **Profile** — профили пользователей
- **Post** — все посты
- **Comment** — комментарии
- **Tag** — теги
- **PostVote** — голоса за посты (с фильтрацией и поиском)

Для доступа используйте учётные данные суперпользователя, созданного через `createsuperuser`.

---

## 📝 Управление тегами

Теги можно добавить через админ-панель или программно:

```python
from core.models import Tag

Tag.objects.create(
    name='Новости',
    slug='news',
    description='Новости и объявления',
    color='blue'
)
```

Доступные цвета: `blue`, `green`, `orange`, `purple`, `red`

---

## 🔧 Настройки

Основные настройки находятся в `projectigrok/settings.py`:

- `DEBUG` — режим отладки
- `DATABASES` — конфигурация БД
- `MEDIA_URL` / `MEDIA_ROOT` — настройки медиафайлов
- `STATIC_URL` — настройки статики

---

## 📄 Лицензия

MIT
