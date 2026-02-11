from django.contrib import admin
from .models import Profile, Post, Comment, PostVote, Tag

admin.site.register(Profile)
admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(Tag)
@admin.register(PostVote)
class PostVoteAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'vote_type', 'created_at']
    list_filter = ['vote_type', 'created_at']
    search_fields = ['user__username', 'post__title']