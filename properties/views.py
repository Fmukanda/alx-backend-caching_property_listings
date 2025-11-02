from django.shortcuts import render, redirect
from django.views.decorators.cache import never_cache
from django.http import JsonResponse
from .utils import (
    get_all_properties, 
    get_cached_properties_count, 
    clear_properties_cache, 
    is_properties_cached,
    get_redis_cache_metrics,
    get_cache_performance_analysis
)
from django.core.cache import cache
from .models import Property

def property_list(request):
    """
    View to display all properties using low-level cache API
    """
    # Get properties from cache or database
    properties = get_all_properties()
    
    # Get cache info for template
    cache_key = 'all_properties'
    is_cached = is_properties_cached()
    cached_count = get_cached_properties_count()
    
    context = {
        'properties': properties,
        'total_properties': properties.count(),
        'is_cached': is_cached,
        'cache_key': cache_key,
        'cached_count': cached_count,
    }
    
    # Handle cache clearing via query parameter (for testing)
    if request.GET.get('clear_cache') == 'true':
        clear_properties_cache()
        context['cache_cleared'] = True
        return redirect('properties:property_list')
    
    return render(request, 'properties/property_list.html', context)

@never_cache
def property_list_uncached(request):
    """
    Alternative view that never uses cache (for testing)
    """
    properties = Property.objects.all().order_by('-created_at')
    
    context = {
        'properties': properties,
        'total_properties': properties.count(),
        'is_cached': False,
        'cache_key': 'none',
    }
    
    return render(request, 'properties/property_list.html', context)

def create_sample_property(request):
    """
    View to create a sample property for testing signals (for development only)
    """
    if request.method == 'POST':
        title = request.POST.get('title', 'Sample Property')
        description = request.POST.get('description', 'This is a sample property description')
        price = request.POST.get('price', 250000.00)
        location = request.POST.get('location', 'Sample Location')
        
        property = Property.objects.create(
            title=title,
            description=description,
            price=price,
            location=location
        )
        
        return redirect('properties:property_list')
    
    return render(request, 'properties/create_sample.html')

@never_cache
def property_list_uncached(request):
    """
    Alternative view that never uses cache (for testing)
    """
    properties = Property.objects.all().order_by('-created_at')
    
    context = {
        'properties': properties,
        'total_properties': properties.count(),
        'is_cached': False,
        'cache_key': 'none',
    }
    
    return render(request, 'properties/property_list.html', context)

def property_detail(request, property_id):
    cache_key = f'property_{property_id}'
    property_obj = cache.get(cache_key)
    
    if not property_obj:
        try:
            property_obj = Property.objects.get(id=property_id)
            cache.set(cache_key, property_obj, 60 * 60)  # Cache for 1 hour
        except Property.DoesNotExist:
            property_obj = None
    
    return render(request, 'properties/detail.html', {'property': property_obj})


@cache_page(60 * 15)  # Cache for 15 minutes (900 seconds)
def property_list(request):
    """
    View to display all properties with response cached for 15 minutes
    """
    properties = Property.objects.all().order_by('-created_at')
    
    # Check if response is served from cache
    cache_key = f"property_list_page_{request.get_full_path()}"
    is_cached = cache.has_key(cache_key)
    
    context = {
        'properties': properties,
        'total_properties': properties.count(),
        'is_cached': is_cached,
        'cache_key': cache_key,
    }
    
    return render(request, 'properties/property_list.html', context)


def cache_metrics(request):
    """
    View to display Redis cache metrics and performance analysis
    """
    metrics = get_redis_cache_metrics()
    analysis = get_cache_performance_analysis(metrics)
    
    context = {
        'metrics': metrics,
        'analysis': analysis,
        'properties_cached': is_properties_cached(),
        'cached_properties_count': get_cached_properties_count(),
    }
    
    # Handle cache clearing
    if request.GET.get('clear_cache') == 'true':
        clear_properties_cache()
        context['cache_cleared'] = True
        return redirect('properties:cache_metrics')
    
    # Handle cache refresh
    if request.GET.get('refresh_cache') == 'true':
        get_all_properties()  # This will refresh the cache
        context['cache_refreshed'] = True
        return redirect('properties:cache_metrics')
    
    return render(request, 'properties/cache_metrics.html', context)

def cache_metrics_api(request):
    """
    API endpoint to get cache metrics in JSON format
    """
    metrics = get_redis_cache_metrics()
    analysis = get_cache_performance_analysis(metrics)
    
    return JsonResponse({
        'metrics': metrics,
        'analysis': analysis,
        'properties_cached': is_properties_cached(),
        'cached_properties_count': get_cached_properties_count(),
        'timestamp': timezone.now().isoformat(),
    })