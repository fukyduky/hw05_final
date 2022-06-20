from django.forms import ModelForm

from .models import Post, Comment


class PostForm(ModelForm):
    class Meta:
        model = Post
        labels = {'text': 'Сообщение', 'group': 'Группа'}
        help_texts = {'text': 'Введите ссообщение', 'group': 'Выберите группу'}
        fields = ['text', 'group', 'image']


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        labels = {'text': 'Добавить комментарий'}
        help_texts = {'text': 'Ведите комментарий'}
