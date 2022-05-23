from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('group', 'text', 'image')
        labels = {
            "group": "Группа",
            "text": "Текст",
            'image': 'Картинка',
        }
        help_texts = {
            'text': 'Напишите текст поста',
            'group': 'Группа поста',
            'image': 'Вставьте картинку'
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {
            'text': 'Текст',
        }
        help_texts = {
            'text': 'Текст нового комментария',
        }
