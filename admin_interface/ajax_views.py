"""
AJAX views for factory image management
"""
import os
import uuid
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import json

from Karkahan.models import Factory, FactoryImage


@login_required
@require_POST
def upload_factory_image(request):
    """Handle factory image upload via AJAX"""
    if request.method == 'POST':
        factory_id = request.POST.get('factory_id')
        factory = get_object_or_404(Factory, id=factory_id)
        
        if 'image' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'No image provided'})
        
        image_file = request.FILES['image']
        
        # Validate file type
        valid_types = ['image/jpeg', 'image/png', 'image/webp']
        if image_file.content_type not in valid_types:
            return JsonResponse({'success': False, 'error': 'Invalid file type. Only JPG, PNG, and WebP are allowed.'})
        
        # Generate unique filename
        ext = os.path.splitext(image_file.name)[1]
        filename = f"factory_{factory_id}_{uuid.uuid4().hex}{ext}"
        path = os.path.join('factories/', filename)
        
        # Save the file
        saved_path = default_storage.save(path, ContentFile(image_file.read()))
        
        # Create FactoryImage instance
        # Check if this is the first image - if so, make it primary
        is_first_image = not FactoryImage.objects.filter(factory=factory).exists()
        
        factory_image = FactoryImage.objects.create(
            factory=factory,
            image=path,
            is_primary=is_first_image
        )
        
        return JsonResponse({
            'success': True,
            'image_id': factory_image.id,
            'image_url': factory_image.image.url,
            'is_primary': factory_image.is_primary
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
@require_POST
def update_image_caption(request):
    """Update image caption/alt_text via AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            image_id = data.get('image_id')
            caption = data.get('caption', '')
            
            image = get_object_or_404(FactoryImage, id=image_id)
            image.alt_text = caption
            image.save()
            
            return JsonResponse({'success': True})
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
@require_POST
def set_primary_image(request):
    """Set a factory image as primary via AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            image_id = data.get('image_id')
            
            image = get_object_or_404(FactoryImage, id=image_id)
            factory = image.factory
            
            # Unset all primary images for this factory
            FactoryImage.objects.filter(factory=factory, is_primary=True).update(is_primary=False)
            
            # Set the new primary image
            image.is_primary = True
            image.save()
            
            return JsonResponse({'success': True, 'image_id': image.id})
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
@require_POST
def delete_image(request):
    """Delete a factory image via AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            image_id = data.get('image_id')
            
            image = get_object_or_404(FactoryImage, id=image_id)
            
            # Delete the file from storage
            if image.image:
                if default_storage.exists(image.image.name):
                    default_storage.delete(image.image.name)
            
            # Delete the database record
            image.delete()
            
            return JsonResponse({'success': True})
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
@require_POST
def reorder_images(request):
    """Reorder factory images via AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            order = data.get('order', [])
            
            # Update the order of images
            for index, image_id in enumerate(order):
                try:
                    image = FactoryImage.objects.get(id=image_id)
                    image.order = index
                    image.save()
                except FactoryImage.DoesNotExist:
                    continue
            
            return JsonResponse({'success': True})
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})