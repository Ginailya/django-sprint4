from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import (
    CommentForm,
    CustomUserCreationForm,
    PostForm,
    ProfileEditForm,
)
from .models import Category, Comment, Post

User = get_user_model()


def index(request):
    post_list = (
        Post.objects.filter(
            is_published=True,
            pub_date__lte=timezone.now(),
            category__is_published=True,
        )
        .annotate(comment_count=Count("comments"))
        .order_by("-pub_date")
    )
    page_obj = Paginator(post_list, 10).get_page(request.GET.get("page"))
    return render(request, "blog/index.html", {"page_obj": page_obj})


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category, slug=category_slug, is_published=True
    )
    post_list = (
        Post.objects.filter(
            category=category, is_published=True, pub_date__lte=timezone.now()
        )
        .annotate(comment_count=Count("comments"))
        .order_by("-pub_date")
    )
    page_obj = Paginator(post_list, 10).get_page(request.GET.get("page"))
    return render(
        request,
        "blog/category.html",
        {"category": category, "page_obj": page_obj},
    )


def post_detail(request, pk):
    """Страница отдельной публикации."""
    post = get_object_or_404(
        Post.objects.annotate(comment_count=Count('comments')), pk=pk
    )

    # Объединяем условия, чтобы убрать вложенный if
    if request.user != post.author and (
        not post.is_published
        or post.pub_date > timezone.now()
        or (post.category and not post.category.is_published)
    ):
        raise Http404("Публикация не найдена")

    comments = post.comments.all()
    form = CommentForm()

    return render(request, 'blog/detail.html', {
        'post': post,
        'comments': comments,
        'form': form
    })


def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("blog:profile", username=user.username)
    else:
        form = CustomUserCreationForm()
    return render(
        request, "registration/registration_form.html", {"form": form}
    )


def profile(request, username):
    user = get_object_or_404(User, username=username)
    if request.user == user:
        posts = user.posts.annotate(comment_count=Count("comments")).order_by(
            "-pub_date"
        )
    else:
        posts = (
            user.posts.filter(is_published=True, pub_date__lte=timezone.now())
            .annotate(comment_count=Count("comments"))
            .order_by("-pub_date")
        )

    page_obj = Paginator(posts, 10).get_page(request.GET.get("page"))

    # Передаем пользователя под всеми возможными именами
    return render(
        request,
        "blog/profile.html",
        {
            "profile_user": user,
            "user": user,
            "object": user,
            "author": user,
            "profile": user,
            "page_obj": page_obj,
        },
    )


# НОВАЯ ВЬЮШКА ДЛЯ РЕДАКТИРОВАНИЯ ПРОФИЛЯ
@login_required
def edit_profile(request):
    user = request.user
    form = ProfileEditForm(request.POST or None, instance=user)
    if form.is_valid():
        form.save()
        return redirect("blog:profile", username=user.username)
    return render(
        request, "blog/user.html", {"form": form}
    )  # или blog/profile_edit.html


@login_required
def post_create(request):
    form = PostForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect("blog:profile", username=request.user.username)
    return render(request, "blog/create.html", {"form": form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect("blog:post_detail", pk=post.id)
    form = PostForm(request.POST or None, request.FILES or None, instance=post)
    if form.is_valid():
        form.save()
        return redirect("blog:post_detail", pk=post.id)
    # ОБЯЗАТЕЛЬНО ПЕРЕДАЕМ POST В КОНТЕКСТ, ЧТОБЫ ШАБЛОН НАШЕЛ ССЫЛКУ
    return render(request, "blog/create.html", {"form": form, "post": post})


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect("blog:post_detail", pk=post_id)


@login_required
def edit_comment(request, post_id, comment_id):
    """Редактирование комментария."""
    post = get_object_or_404(Post, pk=post_id)
    comment = get_object_or_404(Comment, pk=comment_id, post=post)

    if request.user != comment.author:
        return redirect("blog:post_detail", pk=post_id)

    form = CommentForm(request.POST or None, instance=comment)
    if form.is_valid():
        form.save()
        return redirect("blog:post_detail", pk=post_id)

    # Передаем все возможные переменные
    return render(
        request,
        "blog/comment.html",
        {"form": form, "comment": comment, "post": post},
    )


@login_required
def post_delete(request, post_id):
    """Удаление публикации."""
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect("blog:post_detail", pk=post_id)

    if request.method == "POST":
        post.delete()
        return redirect("blog:profile", username=request.user.username)

    comments = post.comments.all()
    # Убрали 'form': form
    return render(
        request,
        "blog/detail.html",
        {"post": post, "comments": comments, "confirm_delete": True},
    )


@login_required
def comment_delete(request, post_id, comment_id):
    """Удаление комментария."""
    post = get_object_or_404(Post, pk=post_id)
    comment = get_object_or_404(Comment, pk=comment_id, post=post)

    if request.user != comment.author:
        return redirect("blog:post_detail", pk=post_id)

    if request.method == "POST":
        comment.delete()
        return redirect("blog:post_detail", pk=post_id)

    # ИСПОЛЬЗУЕМ ШАБЛОН КОММЕНТАРИЯ, ОН УЖЕ УМЕЕТ ПОКАЗЫВАТЬ УДАЛЕНИЕ
    return render(
        request, "blog/comment.html", {"post": post, "comment": comment}
    )
