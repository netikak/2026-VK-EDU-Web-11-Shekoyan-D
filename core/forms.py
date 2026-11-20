from pathlib import Path

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import transaction

from questions.models import Profile


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['class'] = 'form-control field'
        self.fields['password'].widget.attrs['class'] = 'form-control field'


class SignupForm(UserCreationForm):
    email = forms.EmailField(label='Email', max_length=254)
    first_name = forms.CharField(label='Имя', max_length=30)

    class Meta(UserCreationForm.Meta):
        fields = ('username', 'email', 'first_name')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control field'

    @transaction.atomic
    def save(self, commit=True):
        return super().save(commit=commit)


class AvatarField(forms.ImageField):
    def to_python(self, data):
        if data and data.size > 2 * 1024 * 1024:
            raise ValidationError('Файл должен быть не больше 2 МБ.', code='file_too_large')
        image = super().to_python(data)
        if image is None:
            return None
        formats = {'.png': 'PNG', '.jpg': 'JPEG', '.jpeg': 'JPEG'}
        extension = Path(image.name).suffix.lower()
        if extension in formats and image.image.format != formats[extension]:
            raise ValidationError('Формат изображения не соответствует расширению файла.')
        if max(image.image.size) > 4096:
            raise ValidationError('Ширина и высота изображения должны быть не больше 4096 пикселей.')
        return image


class ProfileForm(forms.Form):
    email = forms.EmailField(label='Email', max_length=254, widget=forms.EmailInput(
        attrs={'class': 'form-control field', 'autocomplete': 'email'},
    ))
    nick = forms.CharField(label='Ник', max_length=30, widget=forms.TextInput(
        attrs={'class': 'form-control field', 'autocomplete': 'nickname'},
    ))
    avatar = AvatarField(
        label='Аватар', required=False,
        validators=[FileExtensionValidator(['png', 'jpg', 'jpeg'])],
        help_text='JPG или PNG, не больше 2 МБ и 4096 × 4096 пикселей.',
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control field', 'accept': 'image/png,image/jpeg',
        }),
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        profile = getattr(user, 'profile', None)
        super().__init__(*args, initial={
            'email': user.email,
            'nick': user.first_name or user.username[:30],
            'avatar': profile.avatar if profile else None,
        }, **kwargs)

    @transaction.atomic
    def save(self):
        self.user.email = self.cleaned_data['email']
        self.user.first_name = self.cleaned_data['nick']
        self.user.save(update_fields=['email', 'first_name'])

        profile, _ = Profile.objects.get_or_create(user=self.user)
        if 'avatar' in self.changed_data:
            profile.avatar = self.cleaned_data['avatar'] or ''
            profile.save(update_fields=['avatar'])
        return profile
