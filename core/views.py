from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegisterForm, ProfileUpdateForm, PostForm
from .models import Post, Profile, User, Comment
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import PostVote, Tag, PollOption, PollVote
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
    sort_by = request.GET.get('sort', 'new')
    posts = Post.objects.all()

    if sort_by == 'popular':
        posts = posts.annotate(
            vote_difference=models.F('upvotes') - models.F('downvotes')
        ).order_by('-vote_difference', '-created_at')
    elif sort_by == 'discussed':
        posts = posts.annotate(
            comment_count=models.Count('comments')
        ).order_by('-comment_count', '-created_at')
    else:
        posts = posts.order_by('-created_at')

    # Собираем все голоса пользователя в опросах (список ID выбранных вариантов)
    user_poll_votes = []
    if request.user.is_authenticated:
        user_poll_votes = list(PollVote.objects.filter(user=request.user).values_list('option_id', flat=True))

    for post in posts:
        if request.user.is_authenticated:
            post.user_vote = post.user_vote(request.user)
        else:
            post.user_vote = None

        post.get_upvotes_count = post.get_upvotes_count()
        post.get_downvotes_count = post.get_downvotes_count()

    popular_tags = Tag.objects.annotate(post_count=models.Count('posts')).order_by('-post_count')[:10]

    context = {
        'posts': posts,
        'current_sort': sort_by,
        'popular_tags': popular_tags,
        'user_poll_votes': user_poll_votes,  # <--- Передаем в контекст
    }

    return render(request, 'core/home.html', context)


def post_detail_view(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.all().order_by('created_at')

    # Собираем голос пользователя для конкретного опроса
    user_poll_votes = []
    if request.user.is_authenticated:
        post.user_vote = post.user_vote(request.user)
        user_poll_votes = list(
            PollVote.objects.filter(user=request.user, post=post).values_list('option_id', flat=True))
    else:
        post.user_vote = None

    post.get_upvotes_count = post.get_upvotes_count()
    post.get_downvotes_count = post.get_downvotes_count()

    for comment in comments:
        comment.can_edit = comment.can_edit(request.user) if request.user.is_authenticated else False

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
        'user_poll_votes': user_poll_votes,  # <--- Передаем в контекст
    }

    return render(request, 'core/post_detail.html', context)


@login_required
def create_post_view(request):
    all_tags = Tag.objects.all()

    if request.method == 'POST':
        # Передаем обычный request.POST, форма сама поймет, что пришел список чекбоксов
        form = PostForm(request.POST, request.FILES)

        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            form.save_m2m()  # Сохраняем связи ManyToMany (теги)

            if post.post_type == 'poll':
                options = request.POST.getlist('poll_options')
                for opt_text in options:
                    if opt_text.strip():
                        PollOption.objects.create(post=post, text=opt_text.strip())

            messages.success(request, 'Пост успешно создан!')
            return redirect('post_detail', post_id=post.id)
    else:
        form = PostForm()

    return render(request, 'core/create_post.html', {
        'form': form,
        'all_tags': all_tags,
    })


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


@login_required
@require_POST
def vote_poll_view(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    option_id = request.POST.get('option_id')
    option = get_object_or_404(PollOption, id=option_id, post=post)

    # Создаем или обновляем голос
    vote, created = PollVote.objects.get_or_create(
        user=request.user,
        post=post,
        defaults={'option': option}
    )

    if not created:
        vote.option = option
        vote.save()

    # Собираем данные для фронтенда (ВАЖНО для JS)
    options_data = [
        {
            'id': opt.id,
            'percentage': opt.get_percentage()
        } for opt in post.poll_options.all()
    ]

    # Возвращаем SUCCESS: TRUE
    return JsonResponse({
        'success': True,  # Этот ключ уберет ошибку в браузере
        'total_votes': post.poll_votes.count(),
        'options': options_data
    })