from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from .models import Answer, AnswerLike, Profile, Question, QuestionLike, Tag


class ProfileInline(admin.StackedInline):
    model = Profile
    fk_name = 'user'
    extra = 0
    max_num = 1
    can_delete = False
    readonly_fields = ('created_at',)


class UserWithProfileAdmin(UserAdmin):
    inlines = (ProfileInline,)

    def get_inline_instances(self, request, obj=None):
        return super().get_inline_instances(request, obj) if obj else []


User = get_user_model()
admin.site.unregister(User)
admin.site.register(User, UserWithProfileAdmin)


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    readonly_fields = ('author', 'is_correct')

    def has_add_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('author')


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'score', 'created_at')
    search_fields = ('title', 'text', 'author__username', 'tags__name')
    list_filter = ('created_at',)
    list_select_related = ('author',)
    raw_id_fields = ('author',)
    autocomplete_fields = ('tags',)
    inlines = (AnswerInline,)

    def get_queryset(self, request):
        return super().get_queryset(request).with_rating()

    @admin.display(description='Рейтинг', ordering='rating')
    def score(self, obj):
        return obj.rating


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('id', 'question', 'author', 'is_correct', 'created_at')
    search_fields = ('text', 'question__title', 'author__username')
    list_filter = ('is_correct', 'created_at')
    list_select_related = ('question', 'author')
    raw_id_fields = ('question', 'author')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)
    list_filter = ('created_at',)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'avatar', 'created_at')
    search_fields = ('user__username', 'user__email')
    list_filter = ('created_at',)
    list_select_related = ('user',)
    raw_id_fields = ('user',)


@admin.register(QuestionLike)
class QuestionLikeAdmin(admin.ModelAdmin):
    list_display = ('question', 'user', 'value', 'created_at')
    search_fields = ('question__title', 'user__username')
    list_filter = ('value', 'created_at')
    list_select_related = ('question', 'user')
    raw_id_fields = ('question', 'user')


@admin.register(AnswerLike)
class AnswerLikeAdmin(admin.ModelAdmin):
    list_display = ('answer', 'user', 'value', 'created_at')
    search_fields = ('answer__text', 'user__username')
    list_filter = ('value', 'created_at')
    list_select_related = ('answer', 'user')
    raw_id_fields = ('answer', 'user')
