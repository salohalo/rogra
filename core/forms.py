from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile, Post, Comment, Tag  # Добавьте Tag


class TagCheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    template_name = 'core/widgets/tag_checkbox_select.html'

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)

        # Добавляем цвет тега в опцию
        if value:
            try:
                tag = Tag.objects.get(id=value)
                option['attrs']['data-color'] = tag.color
                option['attrs']['data-name'] = tag.name
            except Tag.DoesNotExist:
                pass
        return option


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'avatar', 'profile_audio']
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Расскажите о себе...'
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'profile_audio': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'audio/*'
            })
        }


class PostForm(forms.ModelForm):
    # Убираем кастомные виджеты - будем делать все в шаблоне
    class Meta:
        model = Post
        fields = ['title', 'content', 'post_type', 'image', 'tags']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Заголовок поста'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Напишите что-нибудь...'
            }),
            'post_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            # Для тегов не указываем виджет - сделаем кастомный в шаблоне
            'tags': forms.SelectMultiple(attrs={'class': 'd-none'}),  # Скрываем стандартный
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Напишите комментарий...'
            })
        }