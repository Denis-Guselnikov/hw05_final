from django import forms
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from .models import Follow, Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {'text': 'Введите текст', 'group': 'Выберите группу'}

    def clean_slug(self):
        """Обрабатывает случай, если slug не уникален."""
        cleaned_data = super().clean()
        slug = cleaned_data.get('slug')
        if not slug:
            title = cleaned_data.get('title')
            slug = slugify(title)[:10]
        if Post.objects.filter(slug=slug).exists():
            raise ValidationError(
                f'Адрес "{slug}" уже существует, '
                'придумайте уникальное значение'
            )
        return slug


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)


class FollowForm(forms.ModelForm):
    class Meta:
        model = Follow
        fields = ('user',)
