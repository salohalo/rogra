from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    profile_audio = models.FileField(upload_to='profile_audio/', null=True, blank=True)

    def __str__(self):
        return f'Профиль {self.user.username}'


# В models.py добавьте после класса PostVote:

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=20, default='primary')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class Post(models.Model):
    POST_TYPES = [
        ('text', 'Текст'),
        ('image', 'Изображение'),
        ('poll','Опрос'),
    ]

    author = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)
    post_type = models.CharField(max_length=10, choices=POST_TYPES, default='text')
    image = models.ImageField(upload_to='posts/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    upvotes = models.IntegerField(default=0)
    downvotes = models.IntegerField(default=0)
    tags = models.ManyToManyField(Tag, blank=True, related_name='posts')

    def __str__(self):
        return self.title

    def total_votes(self):
        return self.upvotes - self.downvotes

    def get_upvotes_count(self):
        return self.votes.filter(vote_type='up').count()

    def get_downvotes_count(self):
        return self.votes.filter(vote_type='down').count()

    def user_vote(self, user):
        """Получить голос пользователя для этого поста"""
        if user.is_authenticated:
            vote = self.votes.filter(user=user).first()
            return vote.vote_type if vote else None
        return None

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Комментарий от {self.author} к {self.post.title}'

    def can_edit(self, user):
        """Проверяет, может ли пользователь редактировать комментарий"""
        if user != self.author:
            return False

        # Можно редактировать только в течение 1 часа после создания
        from django.utils import timezone
        from datetime import timedelta

        time_limit = self.created_at + timedelta(hours=1)
        return timezone.now() <= time_limit


class PostVote(models.Model):
    VOTE_TYPES = [
        ('up', 'Лайк'),
        ('down', 'Дизлайк'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='votes')
    vote_type = models.CharField(max_length=4, choices=VOTE_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'post']  # один пользователь - один голос на пост

    def __str__(self):
        return f'{self.user.username} - {self.vote_type} - {self.post.title}'

class PollOption(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='poll_options')
    text = models.CharField(max_length=200)

    def __str__(self):
        return self.text

    @property
    def total_votes(self):
        return self.votes.count()

    def get_percentage(self):
        all_votes = self.post.poll_votes.count()
        if all_votes == 0:
            return 0
        return int((self.total_votes / all_votes) * 100)

    def user_voted(self, user):
        if user.is_authenticated:
            # Проверяем наличие записи в PollVote для этого юзера и этой опции
            return self.votes.filter(user=user).exists()
        return False

class PollVote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='poll_votes')
    option = models.ForeignKey(PollOption, on_delete=models.CASCADE, related_name='votes')

    class Meta:
        unique_together = ['user', 'post'] # Один юзер — один голос