from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        help_texts = {
            'text': _('Tекст нового поста'),
            'group': _('Группа, к которой будет относиться пост')
        }

        def clean_text(self):
            data = self.cleaned.data['text']
            if not data:
                raise forms.ValidationError('Поле не может быть пустым.')
            return data


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        help_texts = {
            'text': _('Tекст комментария')
        }

        def clean_text(self):
            data = self.cleaned.data['text']
            if not data:
                raise forms.ValidationError('Поле не может быть пустым.')
            return data
