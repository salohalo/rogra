from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegisterForm, ProfileUpdateForm, PostForm
from .models import Post, Profile, User, Comment
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import PostVote, Tag
from django.db import models
from .forms import RegisterForm, ProfileUpdateForm, PostForm, CommentForm

@login_required
@require_POST
def vote_post_view(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    vote_type = request.POST.get('vote_type')

    if vote_type not in ['up', 'down']:
        return JsonResponse({'error': 'Неверный тип голоса'}, status=400)

    # Проверяем, есть ли уже такой голос от пользователя
    existing_vote = PostVote.objects.filter(user=request.user, post=post).first()

    if existing_vote:
        # Если пользователь нажимает на уже выбранный голос - удаляем его
        if existing_vote.vote_type == vote_type:
            existing_vote.delete()
            user_vote = None
        else:
            # Если нажимает на противоположный - меняем голос
            existing_vote.vote_type = vote_type
            existing_vote.save()
            user_vote = vote_type
    else:
        # Если голоса нет - создаем новый
        PostVote.objects.create(
            user=request.user,
            post=post,
            vote_type=vote_type
        )
        user_vote = vote_type

    # Обновляем счетчики в модели Post
    post.upvotes = post.get_upvotes_count()
    post.downvotes = post.get_downvotes_count()
    post.save()

    return JsonResponse({
        'success': True,
        'upvotes': post.get_upvotes_count(),
        'downvotes': post.get_downvotes_count(),
        'total_votes': post.total_votes(),
        'user_vote': user_vote  # Может быть 'up', 'down' или None
    })


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('home')
    else:
        form = RegisterForm()
    return render(request, 'core/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Неверный логин или пароль')
    return render(request, 'core/login.html')


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


def home_view(request):
    # Получаем тип сортировки из GET параметра
    sort_by = request.GET.get('sort', 'new')

    # Базовый QuerySet
    posts = Post.objects.all()

    # Применяем сортировку в зависимости от выбора
    if sort_by == 'popular':
        # Сначала самые популярные (по разнице лайков-дизлайков)
        posts = posts.annotate(
            vote_difference=models.F('upvotes') - models.F('downvotes')
        ).order_by('-vote_difference', '-created_at')
    elif sort_by == 'discussed':
        # Сначала самые обсуждаемые (по количеству комментариев)
        posts = posts.annotate(
            comment_count=models.Count('comments')
        ).order_by('-comment_count', '-created_at')
    else:  # 'new' по умолчанию
        posts = posts.order_by('-created_at')

    # Добавляем информацию о голосах пользователя для каждого поста
    for post in posts:
        if request.user.is_authenticated:
            post.user_vote = post.user_vote(request.user)
        else:
            post.user_vote = None

        # Используем методы для подсчета голосов
        post.get_upvotes_count = post.get_upvotes_count()
        post.get_downvotes_count = post.get_downvotes_count()

    popular_tags = Tag.objects.annotate(post_count=models.Count('posts')).order_by('-post_count')[:10]
    # Передаем текущий тип сортировки в шаблон
    context = {
        'posts': posts,
        'current_sort': sort_by,
        'popular_tags': popular_tags,  # Добавляем теги
    }

    return render(request, 'core/home.html', context)


def profile_view(request, username):
    user = get_object_or_404(User, username=username)
    profile = get_object_or_404(Profile, user=user)
    user_posts = Post.objects.filter(author=user).order_by('-created_at')

    return render(request, 'core/profile.html', {
        'profile_user': user,
        'profile': profile,
        'posts': user_posts
    })


@login_required
def edit_profile_view(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль успешно обновлен!')
            return redirect('profile', username=request.user.username)
    else:
        form = ProfileUpdateForm(instance=request.user.profile)

    return render(request, 'core/edit_profile.html', {'form': form})


def post_detail_view(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.all().order_by('created_at')

    # Добавляем информацию о голосах для поста
    if request.user.is_authenticated:
        post.user_vote = post.user_vote(request.user)
    else:
        post.user_vote = None

    post.get_upvotes_count = post.get_upvotes_count()
    post.get_downvotes_count = post.get_downvotes_count()

    for comment in comments:
        comment.can_edit = comment.can_edit(request.user) if request.user.is_authenticated else False

    # Обработка добавления комментария
    if request.method == 'POST' and request.user.is_authenticated:
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            messages.success(request, 'Комментарий добавлен!')
            return redirect('post_detail', post_id=post.id)
    else:
        form = CommentForm()

    context = {
        'post': post,
        'comments': comments,
        'form': form,
    }

    return render(request, 'core/post_detail.html', context)


@login_required
def create_post_view(request):
    all_tags = Tag.objects.all()

    if request.method == 'POST':
        # Преобразуем строку с ID тегов в список
        if 'tags' in request.POST and request.POST['tags']:
            tag_ids = request.POST['tags'].split(',')
            # Создаем копию POST данных с правильным форматом
            post_data = request.POST.copy()
            post_data.setlist('tags', tag_ids)
            form = PostForm(post_data, request.FILES)
        else:
            form = PostForm(request.POST, request.FILES)

        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            form.save_m2m()
            messages.success(request, 'Пост успешно создан!')
            return redirect('post_detail', post_id=post.id)
    else:
        form = PostForm()

    return render(request, 'core/create_post.html', {
        'form': form,
        'all_tags': all_tags,
    })


@login_required
def delete_comment_view(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    post_id = comment.post.id

    # Проверяем права: автор комментария или staff
    if request.user == comment.author or request.user.is_staff:
        comment.delete()
        messages.success(request, 'Комментарий удален')

    return redirect('post_detail', post_id=post_id)


@login_required
def edit_comment_view(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    # Проверяем права на редактирование
    if not comment.can_edit(request.user):
        messages.error(request, 'Вы не можете редактировать этот комментарий')
        return redirect('post_detail', post_id=comment.post.id)

    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Комментарий обновлен')
            return redirect('post_detail', post_id=comment.post.id)
    else:
        form = CommentForm(instance=comment)

    return render(request, 'core/edit_comment.html', {
        'form': form,
        'comment': comment,
        'post': comment.post
    })