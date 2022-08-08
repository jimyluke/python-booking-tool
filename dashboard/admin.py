from django.contrib import admin
from .models import History

class HistoryAdmin(admin.ModelAdmin):
    model = History
    list_display = ['username', 'password',  'auth_token', 'login_state','configuration','result','reservation','user','created_at','updated_at',]
    list_filter = ['user']
admin.site.register(History, HistoryAdmin)