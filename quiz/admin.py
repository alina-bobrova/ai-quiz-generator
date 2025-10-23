from django.contrib import admin
from .models import Quiz, Question, Answer, UserAnswer, Achievement, UserAchievement, UserStats


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'created_at', 'score', 'is_public']
    list_filter = ['created_at', 'is_public', 'user']
    search_fields = ['title', 'user__username']
    readonly_fields = ['created_at']


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['text', 'quiz', 'get_answer_count']
    list_filter = ['quiz']
    search_fields = ['text', 'quiz__title']
    
    def get_answer_count(self, obj):
        return obj.answers.count()
    get_answer_count.short_description = 'Количество ответов'


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ['text', 'question', 'is_correct']
    list_filter = ['is_correct', 'question__quiz']
    search_fields = ['text', 'question__text']


@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ['user', 'question', 'answer', 'is_correct']
    list_filter = ['is_correct', 'user']
    search_fields = ['user__username', 'question__text', 'answer__text']


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'points', 'condition']
    list_filter = ['points']
    search_fields = ['name', 'description']


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ['user', 'achievement', 'unlocked_at']
    list_filter = ['unlocked_at', 'achievement']
    search_fields = ['user__username', 'achievement__name']


@admin.register(UserStats)
class UserStatsAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_quizzes_created', 'total_quizzes_completed', 'total_points', 'average_score']
    list_filter = ['last_activity']
    search_fields = ['user__username']
    readonly_fields = ['last_activity']