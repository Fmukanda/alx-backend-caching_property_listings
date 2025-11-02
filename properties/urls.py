from django.urls import path
from . import views

app_name = 'properties'

urlpatterns = [
    path('', views.property_list, name='property_list'),
    path('uncached/', views.property_list_uncached, name='property_list_uncached'),
    path('create-sample/', views.create_sample_property, name='create_sample_property'),
    path('cache-metrics/', views.cache_metrics, name='cache_metrics'),
    path('api/cache-metrics/', views.cache_metrics_api, name='cache_metrics_api'),
]