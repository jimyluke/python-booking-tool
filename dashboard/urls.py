from django.urls import path
from . import views

from django.contrib import admin
admin.site.site_header  =  "Resy BOT"  
admin.site.site_title  =  "Resy BOT"
admin.site.index_title  =  "Resy BOT"

urlpatterns = [
    path('index/', views.index, name='dashboard-index'),
    path('dashboard-optim-vs', views.optimvs, name='dashboard-optim-vs'),
    path('dashboard-optim-test', views.optimtest, name='dashboard-optim-test'),
    path('dashboard-optim-testlogin', views.optimtestlogin, name='dashboard-optim-testlogin'),
    path('dashboard-optim-reservations', views.optimreservations, name='dashboard-optim-reservations'),
    path('dashboard-optim-db', views.optimdb, name='dashboard-optim-db'),
    path('dashboard-sample1/', views.sample1, name='dashboard-sample1'),
    path('dashboard-simulation/', views.simulation, name='dashboard-simulation'),
]
