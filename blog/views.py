"""
Blog application views module.

This module contains all the view classes and functions for the blog application,
including CRUD operations for blog posts, image management, and admin dashboard
functionality.

Classes:
    BlogPostListView: Displays a paginated list of published blog posts
    BlogPostDetailView: Shows individual blog post details
    BlogPostCreateView: Handles blog post creation with image upload
    BlogPostUpdateView: Manages blog post editing
    BlogPostDeleteView: Handles blog post deletion

Functions:
    create_blog_post: Manual blog post creation view
    edit_blog_post: Blog post editing view
    manage_blog_images: Image management for blog posts
    upload_images: Bulk image upload for blog posts
    blog_admin_dashboard: Admin dashboard for blog management
"""

import os
import json
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.contrib import messages
from django.utils import timezone
from django.utils.translation import gettext as _
from django.http import Http404
from django.db.models import Q
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from .models import BlogPost, BlogImage
from .forms import BlogPostForm, BlogImageForm, BlogImageFormSet, BlogPostFilterForm
from Karkahan.models import Factory
from django.urls import reverse
from .utils import (
    handle_multiple_images, get_location_cascading_data, 
    set_featured_image, delete_blog_image, get_blog_statistics
)
from .mixins import (
    LocationCascadingMixin, UserFormMixin, BlogAuthorRequiredMixin, 
    BlogAdminRequiredMixin, ActivityLoggingMixin, ImageHandlingMixin
)
from category.models import Category, SubCategory
from location.models import Country, State, City, District, Region
from Karkahan.views import process_hierarchical_fields
from Accounts.decorators import email_verified_required


class BlogPostListView(ListView):
    model = BlogPost
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        # If user is not logged in, only show published, non-deleted blogs
        if not self.request.user.is_authenticated:
            queryset = BlogPost.objects.filter(
                is_published=True,
                is_deleted=False
            ).select_related('author', 'subcategory', 'region')
        else:
            # If user is logged in, show:
            # 1. All published, non-deleted blogs (for public viewing)
            # 2. User's own blogs regardless of published status (but exclude deleted)
            user_published = BlogPost.objects.filter(
                is_published=True,
                is_deleted=False
            ).select_related('author', 'subcategory', 'region')
            
            user_owned = BlogPost.objects.filter(
                author=self.request.user,
                is_deleted=False
            ).select_related('author', 'subcategory', 'region')
            
            # Combine the querysets and remove duplicates
            queryset = (user_published | user_owned).distinct()
        
        # Prepare initial data for form based on GET parameters
        initial_data = {}
        if 'category' in self.request.GET:
            try:
                category_id = int(self.request.GET.get('category'))
                initial_data['category'] = category_id
            except (ValueError, TypeError):
                pass
        
        if 'subcategory' in self.request.GET:
            try:
                subcategory_id = int(self.request.GET.get('subcategory'))
                initial_data['subcategory'] = subcategory_id
            except (ValueError, TypeError):
                pass
        
        if 'country' in self.request.GET:
            try:
                country_id = int(self.request.GET.get('country'))
                initial_data['country'] = country_id
            except (ValueError, TypeError):
                pass
        
        if 'state' in self.request.GET:
            try:
                state_id = int(self.request.GET.get('state'))
                initial_data['state'] = state_id
            except (ValueError, TypeError):
                pass
        
        if 'city' in self.request.GET:
            try:
                city_id = int(self.request.GET.get('city'))
                initial_data['city'] = city_id
            except (ValueError, TypeError):
                pass
        
        if 'district' in self.request.GET:
            try:
                district_id = int(self.request.GET.get('district'))
                initial_data['district'] = district_id
            except (ValueError, TypeError):
                pass
        
        if 'region' in self.request.GET:
            try:
                region_id = int(self.request.GET.get('region'))
                initial_data['region'] = region_id
            except (ValueError, TypeError):
                pass

        # Apply filters using the filter form
        self.filter_form = BlogPostFilterForm(self.request.GET, initial=initial_data)
        if self.filter_form.is_valid():
            category = self.filter_form.cleaned_data.get('category')
            subcategory = self.filter_form.cleaned_data.get('subcategory')
            country = self.filter_form.cleaned_data.get('country')
            state = self.filter_form.cleaned_data.get('state')
            city = self.filter_form.cleaned_data.get('city')
            district = self.filter_form.cleaned_data.get('district')
            region = self.filter_form.cleaned_data.get('region')

            if category:
                queryset = queryset.filter(category=category)
            if subcategory:
                queryset = queryset.filter(subcategory=subcategory)
            if country:
                queryset = queryset.filter(country=country)
            if state:
                queryset = queryset.filter(state=state)
            if city:
                queryset = queryset.filter(city=city)
            if district:
                queryset = queryset.filter(district=district)
            if region:
                queryset = queryset.filter(region=region)

        # Apply search with AND for multi-word queries
        search_query = self.request.GET.get('search', '')
        if search_query:
            terms = search_query.split()
            q_objects = Q()
            for term in terms:
                term_q = Q(title__icontains=term) | Q(content__icontains=term) | Q(excerpt__icontains=term)
                q_objects &= term_q
            queryset = queryset.filter(q_objects)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = self.filter_form
        context['search_query'] = self.request.GET.get('search', '')
        context['categories'] = Category.objects.all()
        context['countries'] = Country.objects.all()

        # --- Filter Logic for Related Factories ---
        req = self.request.GET
        factory_filters = {}
        
        # 1. Location Mapping
        loc_mapping = {
            'country': 'country_id',
            'state': 'state_id',
            'city': 'city_id',
            'district': 'district_id',
            'region': 'region_id',
        }

        for url_key, model_field in loc_mapping.items():
            val = req.get(url_key)
            if val:
                factory_filters[model_field] = val

        # 2. Category Mapping
        # Filters factories based on the blog category selected
        category_val = req.get('category')
        if category_val:
            factory_filters['category_id'] = category_val

        # 3. Execute Query
        # We use .distinct() in case of complex joins, and limit to 8
        factories = Factory.objects.filter(**factory_filters).filter(is_active=True, is_verified=True).select_related('city', 'country', 'category')
        
        if not factory_filters:
            # If no filters, show featured/latest
            context['related_factories'] = factories.order_by('-created_at')[:4]
        else:
            context['related_factories'] = factories[:8]
        
        return context


class BlogPostDetailView(DetailView):
    model = BlogPost
    template_name = 'blog/post_detail.html'
    context_object_name = 'post'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return BlogPost.objects.filter(Q(is_published=True,is_deleted=False) | Q(author=self.request.user) ).select_related('author', 'subcategory', 'region') if self.request.user.is_authenticated else BlogPost.objects.filter(is_published=True,is_deleted=False).select_related('author', 'subcategory', 'region')


# class BlogPostCreateView(LoginRequiredMixin, CreateView):
#     model = BlogPost
#     form_class = BlogPostForm
#     template_name = 'blog/post_form.html'
#     success_url = reverse_lazy('blog:post_list')

#     def form_valid(self, form):
#         form.instance.author = self.request.user
#         if form.instance.is_published:
#             form.instance.published_at = timezone.now()
#         return super().form_valid(form)

@email_verified_required
@login_required
def create_blog_post(request):
    if request.method == "POST":
        # 1. Get Basic Info
        title = request.POST.get('title')
        content = request.POST.get('content')
        excerpt = request.POST.get('excerpt')
        is_published = request.POST.get('is_published') == 'on'

        # 2. Hierarchy Helper Function
        def get_or_create_item(model, val, parent_field=None, parent_obj=None):
            if not val: return None
            if val.isdigit():
                return model.objects.get(id=val)
            # Create new if it's text
            params = {'name': val}
            if parent_field and parent_obj:
                params[parent_field] = parent_obj
            obj, _ = model.objects.get_or_create(**params)
            return obj

        # 3. Process Categories
        cat_val = request.POST.get('category')
        category = get_or_create_item(Category, cat_val)
        
        sub_val = request.POST.get('subcategory')
        subcategory = get_or_create_item(SubCategory, sub_val, 'category', category)

        # 4. Process Locations
        country = get_or_create_item(Country, request.POST.get('country'))
        state = get_or_create_item(State, request.POST.get('state'), 'country', country)
        city = get_or_create_item(City, request.POST.get('city'), 'state', state)
        district = get_or_create_item(District, request.POST.get('district'), 'city', city)
        region = get_or_create_item(Region, request.POST.get('region'), 'district', district)

        # 5. Save Blog
        blog = BlogPost.objects.create(
            title=title,
            content=content,
            excerpt=excerpt,
            author=request.user,
            category=category,
            subcategory=subcategory,
            country=country,
            state=state,
            city=city,
            district=district,
            region=region,
            is_published=is_published,
            published_at=timezone.now() if is_published else None
        )
        
        # 6. Handle Multiple Images
        images = request.FILES.getlist('images')
        for i, image in enumerate(images):
            BlogImage.objects.create(
                blog_post=blog,
                image=image,
                order=i,
                is_featured=(i == 0)  # First image is featured by default
            )
        
        return redirect('blog:post_list')

    # GET request: provide top-level data
    context = {
        'categories': Category.objects.all(),
        'countries': Country.objects.all(),
    }
    return render(request, 'blog/create_blog_manual.html', context)


@email_verified_required
@login_required
def create_blog_post_form(request):
    if request.method == 'POST':
        data = request.POST.copy()                 # make mutable copy
        process_hierarchical_fields(data)           # convert new names to IDs
        form = BlogPostForm(data, request.FILES)    # use the modified data
        if form.is_valid():
            try:
                # The form's save method now handles images automatically
                blog = form.save(commit=True, author=request.user)
                
                messages.success(request, _('Blog post created successfully!'))
                return redirect('blog:post_list')
            except Exception as e:
                form.add_error(None, _('An error occurred while saving the blog post. Please try again.'))
                print(f"Error saving blog post: {e}")
        else:
            print(f"Form errors: {form.errors}")
    else:
        form = BlogPostForm()

    context = {
        'form': form,
        'categories': Category.objects.all(),
        'countries': Country.objects.all(),
        'factories': Factory.objects.filter(is_active=True),
    }
    return render(request, 'blog/post_form.html', context)


def blog_author_or_admin_required(view_func):
    """Decorator to check if user is admin or blog author"""
    def _wrapped_view(request, slug, *args, **kwargs):
        blog = get_object_or_404(BlogPost, slug=slug)
        
        # Check if user is admin or the author of the blog
        if not (request.user.is_staff or request.user == blog.author):
            messages.error(request, "You don't have permission to edit this blog post.")
            return redirect('blog:post_detail', slug=slug)
        
        return view_func(request, slug, *args, **kwargs)
    return _wrapped_view


@login_required
@blog_author_or_admin_required
def edit_blog_post(request, slug):
    blog = get_object_or_404(BlogPost, slug=slug)

    if request.method == 'POST':
        data = request.POST.copy()
        process_hierarchical_fields(data)
        form = BlogPostForm(data, request.FILES, instance=blog)
        if form.is_valid():
            # The form's save method now handles images automatically
            blog = form.save(commit=True, author=request.user)
            return redirect('blog:post_detail', slug=blog.slug)
    else:
        form = BlogPostForm(instance=blog)

    context = {
        'form': form,
        'blog': blog,
        'categories': Category.objects.all(),
        'countries': Country.objects.all(),
        'factories': Factory.objects.filter(is_active=True),
    }
    return render(request, 'blog/post_form.html', context)


@login_required
@blog_author_or_admin_required
def manage_images(request, slug):
    """
    Manage images for a specific blog post.
    
    This view allows users to upload, delete, and manage images for their blog posts.
    Users can set featured images, reorder images, and delete unwanted images.
    
    Args:
        request (HttpRequest): HTTP request object
        slug (str): Blog post slug
    
    Returns:
        HttpResponse: Rendered manage images template or redirect
    """
    blog = get_object_or_404(BlogPost, slug=slug)
    
    if request.method == 'POST':
        # Handle image deletion
        if 'delete_image' in request.POST:
            image_id = request.POST.get('delete_image')
            image = get_object_or_404(BlogImage, id=image_id, blog_post=blog)
            image.delete()
            messages.success(request, _('Image deleted successfully!'))
            return redirect('blog:post_detail', slug=blog.slug)
        
        # Handle featured image selection
        if 'set_featured' in request.POST:
            image_id = request.POST.get('set_featured')
            image = get_object_or_404(BlogImage, id=image_id, blog_post=blog)
            # Unset all featured images
            BlogImage.objects.filter(blog_post=blog).update(is_featured=False)
            # Set new featured image
            image.is_featured = True
            image.save()
            messages.success(request, _('Featured image updated successfully!'))
            return redirect('blog:post_detail', slug=blog.slug)
        
        # Handle image order update
        if 'update_order' in request.POST:
            order_data = request.POST.getlist('image_order')
            for order, image_id in enumerate(order_data):
                try:
                    image = BlogImage.objects.get(id=image_id, blog_post=blog)
                    image.order = order
                    image.save()
                except BlogImage.DoesNotExist:
                    continue
            messages.success(request, _('Image order updated successfully!'))
            return redirect('blog:post_detail', slug=blog.slug)
        
        # Handle image caption update
        if 'update_caption' in request.POST:
            image_id = request.POST.get('image_id')
            caption = request.POST.get('caption', '')
            image = get_object_or_404(BlogImage, id=image_id, blog_post=blog)
            image.caption = caption
            image.save()
            messages.success(request, _('Image caption updated successfully!'))
            return redirect('blog:post_detail', slug=blog.slug)
        if request.FILES.getlist('images'):
            files = request.FILES.getlist('images')

            last_order = blog.images.count()

            for i,file in enumerate(files):
                BlogImage.objects.create(
                    blog_post=blog,
                    image=file,
                    order=last_order+i,
                    is_featured=(last_order==0 and i==0)
                )

            messages.success(request,'Images uploaded!')
            return redirect('blog:post_detail',slug=blog.slug)
    
    context = {
        'blog': blog,
        'images': blog.images.all().order_by('order'),
        'title': _('Manage Images for') + f' {blog.title}'
    }
    return render(request, 'blog/manage_images.html', context)


@login_required
def manage_blog_images(request, slug):
    """
    Legacy function - redirects to the new manage_images function.
    
    This maintains backward compatibility while the new function is used.
    """
    return manage_images(request, slug)


@login_required
@blog_author_or_admin_required
def upload_images(request, slug):
    blog = get_object_or_404(BlogPost, slug=slug)
    
    if request.method == 'POST':
        images = request.FILES.getlist('images')
        for i, image in enumerate(images):
            BlogImage.objects.create(
                blog_post=blog,
                image=image,
                order=blog.images.count() + i,
                is_featured=False
            )
        return redirect('blog:manage_images', slug=blog.slug)
    
    context = {
        'blog': blog,
    }
    return render(request, 'blog/upload_images.html', context)


class BlogPostUpdateView(LoginRequiredMixin, UpdateView):
    model = BlogPost
    form_class = BlogPostForm
    template_name = 'blog/post_form.html'
    context_object_name = 'post'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    # success_url = reverse_lazy('blog:post_detail')

    def get_queryset(self):
        return BlogPost.objects.filter(Q(author=self.request.user)) if not self.request.user.is_staff else BlogPost.objects.all()

    def form_valid(self, form):
        # Use the form's save method which handles images automatically
        blog = form.save(commit=True, author=self.request.user)
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'slug': self.object.slug})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['featured_image'] = self.object.get_featured_image()
        context['gallery_images'] = self.object.get_gallery_images()
        context['related_factories'] = self.object.related_factories.filter(is_active=True)
        context['factories'] = Factory.objects.filter(is_active=True)
        return context


# Blog Admin Dashboard
@login_required
def blog_admin_dashboard(request):
    """Blog admin dashboard for content management"""
    if not request.user.is_staff:
        from django.http import Http404
        raise Http404("Access denied")

    # Statistics
    total_posts = BlogPost.objects.all_with_deleted().count()
    published_posts = BlogPost.objects.filter(is_published=True).count()
    draft_posts = BlogPost.objects.filter(is_published=False, is_deleted=False).count()
    deleted_posts = BlogPost.objects.deleted_only().count()

    # Recent posts
    recent_posts = BlogPost.objects.all_with_deleted()[:10]

    # Category distribution
    from django.db.models import Count
    category_stats = BlogPost.objects.values('subcategory__name').annotate(
        count=Count('id')
    ).order_by('-count')[:5]

    context = {
        'total_posts': total_posts,
        'published_posts': published_posts,
        'draft_posts': draft_posts,
        'deleted_posts': deleted_posts,
        'recent_posts': recent_posts,
        'category_stats': category_stats,
    }
    return render(request, 'blog/admin_dashboard.html', context)


class BlogPostDeleteView(LoginRequiredMixin, DeleteView):
    model = BlogPost
    template_name = 'blog/post_confirm_delete.html'
    context_object_name = 'post'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    success_url = reverse_lazy('blog:post_list')

    def get_queryset(self):
        return BlogPost.objects.filter(author=self.request.user)


# New Blog Delete Functions
@login_required
@blog_author_or_admin_required
def blog_soft_delete(request, slug):
    """Soft delete a blog post"""
    blog = get_object_or_404(BlogPost, slug=slug)
    
    if request.method == 'POST':
        blog.soft_delete()
        messages.success(request, f'Blog post "{blog.title}" has been moved to trash.')
        return redirect('blog:post_list')
    
    context = {
        'blog': blog,
        'action': 'soft_delete'
    }
    return render(request, 'blog/confirm_soft_delete.html', context)


@login_required
@blog_author_or_admin_required  
def blog_hard_delete(request, slug):
    """Hard delete a blog post (permanent deletion)"""
    blog = get_object_or_404(BlogPost, slug=slug)
    
    # Only allow hard delete for soft-deleted blogs or superusers
    if not blog.is_deleted and not request.user.is_superuser:
        messages.error(request, "You can only hard delete blogs that are in the trash.")
        return redirect('blog:post_detail', slug=blog.slug)
    
    if request.method == 'POST':
        blog_name = blog.title
        blog.hard_delete()
        messages.success(request, f'Blog post "{blog_name}" has been permanently deleted.')
        return redirect('blog:post_list')
    
    context = {
        'blog': blog,
        'action': 'hard_delete'
    }
    return render(request, 'blog/confirm_hard_delete.html', context)


@login_required
@blog_author_or_admin_required
def blog_restore(request, slug):
    """Restore a soft-deleted blog post"""
    blog = get_object_or_404(BlogPost, slug=slug, is_deleted=True)
    
    if request.method == 'POST':
        blog.restore()
        messages.success(request, f'Blog post "{blog.title}" has been restored.')
        return redirect('blog:post_detail', slug=blog.slug)
    
    context = {
        'blog': blog,
        'action': 'restore'
    }
    return render(request, 'blog/confirm_restore.html', context)


# Admin Blog Management Functions
@login_required
def admin_blog_soft_delete(request, blog_id):
    """Admin soft delete a blog post"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to perform this action.")
        return redirect('admin_interface:admin_blogs')
    
    blog = get_object_or_404(BlogPost, id=blog_id)
    
    if request.method == 'POST':
        blog.soft_delete()
        messages.success(request, f'Blog post "{blog.title}" has been moved to trash.')
        return redirect('admin_interface:admin_blogs')
    
    context = {
        'blog': blog,
        'action': 'soft_delete'
    }
    return render(request, 'admin_interface/blogs/blog_soft_delete.html', context)


@login_required
def admin_blog_hard_delete(request, blog_id):
    """Admin hard delete a blog post (permanent deletion)"""
    if not request.user.is_superuser:
        messages.error(request, "You don't have permission to perform this action.")
        return redirect('admin_interface:admin_blogs')
    
    blog = get_object_or_404(BlogPost, id=blog_id)
    
    if request.method == 'POST':
        blog_name = blog.title
        blog.hard_delete()
        messages.success(request, f'Blog post "{blog_name}" has been permanently deleted.')
        return redirect('admin_interface:admin_blogs')
    
    context = {
        'blog': blog,
        'action': 'hard_delete'
    }
    return render(request, 'admin_interface/blogs/blog_hard_delete.html', context)


@login_required
def admin_blog_restore(request, blog_id):
    """Admin restore a soft-deleted blog post"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to perform this action.")
        return redirect('admin_interface:admin_blogs')
    
    blog = get_object_or_404(BlogPost, id=blog_id, is_deleted=True)
    
    if request.method == 'POST':
        blog.restore()
        messages.success(request, f'Blog post "{blog.title}" has been restored.')
        return redirect('admin_interface:admin_blogs')
    
    context = {
        'blog': blog,
        'action': 'restore'
    }
    return render(request, 'admin_interface/blogs/blog_restore.html', context)


@login_required
def admin_blog_permanent_delete(request, blog_id):
    """Admin permanent delete a blog post (bypassing soft delete)"""
    if not request.user.is_superuser:
        messages.error(request, "You don't have permission to perform this action.")
        return redirect('admin_interface:admin_blogs')
    
    blog = get_object_or_404(BlogPost, id=blog_id)
    
    if request.method == 'POST':
        blog_name = blog.title
        blog.delete()  # This is the actual Django delete, not soft delete
        messages.success(request, f'Blog post "{blog_name}" has been permanently deleted.')
        return redirect('admin_interface:admin_blogs')
    
    context = {
        'blog': blog,
        'action': 'permanent_delete'
    }
    return render(request, 'admin_interface/blogs/blog_permanent_delete.html', context)


@login_required
def tinymce_image_upload(request):
    """
    Handle image uploads from TinyMCE editor.
    
    This view processes image uploads from the TinyMCE editor and returns
    the URL of the uploaded image so it can be inserted into the content.
    
    Returns:
        JsonResponse: JSON response with location of uploaded file or error
    """
    if request.method == 'POST' and request.FILES.get('file'):
        try:
            image_file = request.FILES['file']
            
            # Validate file type
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']
            file_extension = os.path.splitext(image_file.name)[1].lower()
            
            if file_extension not in allowed_extensions:
                return JsonResponse({
                    'error': f'Invalid file type. Allowed: {", ".join(allowed_extensions)}'
                }, status=400)
            
            # Validate file size (max 10MB)
            max_size = 10 * 1024 * 1024  # 10MB
            if image_file.size > max_size:
                return JsonResponse({
                    'error': 'File too large. Maximum size is 10MB.'
                }, status=400)
            
            # Generate unique filename
            import uuid
            unique_filename = f"blog_images/{uuid.uuid4().hex}_{image_file.name}"
            
            # Save the file
            file_path = default_storage.save(unique_filename, ContentFile(image_file.read()))
            file_url = settings.MEDIA_URL + file_path
            
            return JsonResponse({'location': file_url})
            
        except Exception as e:
            return JsonResponse({
                'error': f'Upload failed: {str(e)}'
            }, status=500)
    
    return JsonResponse({'error': 'No file provided'}, status=400)
