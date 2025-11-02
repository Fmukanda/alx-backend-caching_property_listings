from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.core.cache import cache
from .models import Property
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Property)
def invalidate_cache_on_save(sender, instance, **kwargs):
    """
    Invalidate the all_properties cache when a Property is created or updated
    """
    cache_key = 'all_properties'
    
    try:
        # Check if cache key exists before deleting
        if cache.has_key(cache_key):
            cache.delete(cache_key)
            logger.info(f"✅ Cache invalidated due to {instance} being {'created' if kwargs.get('created') else 'updated'}")
        else:
            logger.info(f"ℹ️  Cache key '{cache_key}' not found during {instance} save")
            
    except Exception as e:
        logger.error(f"❌ Error invalidating cache on save: {e}")

@receiver(post_delete, sender=Property)
def invalidate_cache_on_delete(sender, instance, **kwargs):
    """
    Invalidate the all_properties cache when a Property is deleted
    """
    cache_key = 'all_properties'
    
    try:
        # Check if cache key exists before deleting
        if cache.has_key(cache_key):
            cache.delete(cache_key)
            logger.info(f"✅ Cache invalidated due to {instance} being deleted")
        else:
            logger.info(f"ℹ️  Cache key '{cache_key}' not found during {instance} deletion")
            
    except Exception as e:
        logger.error(f"❌ Error invalidating cache on delete: {e}")

@receiver(pre_save, sender=Property)
def log_property_changes(sender, instance, **kwargs):
    """
    Log changes when a Property is updated (optional, for debugging)
    """
    if instance.pk:  # Only for updates, not creations
        try:
            old_instance = Property.objects.get(pk=instance.pk)
            if old_instance.title != instance.title:
                logger.info(f"Property title changed from '{old_instance.title}' to '{instance.title}'")
            if old_instance.price != instance.price:
                logger.info(f"Property price changed from {old_instance.price} to {instance.price}")
        except Property.DoesNotExist:
            pass