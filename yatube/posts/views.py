from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User
from .utils import page


def index(request):
    post_list = Post.objects.select_related('author', 'group')
    page_obj = page(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    """Возращает 10 постов указанной темы."""
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('author')
    page_obj = page(request, posts)
    context = {
        'group': group,
        'posts': posts,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    page_obj = page(request, post_list)
    number_of_posts = post_list.count()
    context = {
        'page_obj': page_obj,
        'author': author,
        'post_list': post_list,
        'number_of_posts': number_of_posts
    }
    if request.user.is_authenticated:
        following = author.following.filter(user=request.user)
        context['following'] = following
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """Показывает пост."""
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    comments = post.comments.all()

    posts_count = post.author.posts.count()
    context = {
        'post': post,
        'form': form,
        'comments': comments,
        'posts_count': posts_count,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    """Создаёт новый пост."""
    form = PostForm(
        request.POST or None
    )
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {'form': form})

    temp_form = form.save(commit=False)
    temp_form.author = request.user
    temp_form.save()
    return redirect(
        'posts:profile', temp_form.author
    )


@login_required
def post_edit(request, post_id):
    """Редактирует пост."""
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'post': post,
        'form': form,
        'is_edit': True,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    # Создаю функцию для обработки отправленного комментария
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    page_obj = page(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(
            user=request.user,
            author=author
        )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follow = Follow.objects.filter(
        user=request.user,
        author=author
    ).exists()

    if not follow and author != request.user:

        Follow.objects.create(
            user=request.user,
            author=author
        )
