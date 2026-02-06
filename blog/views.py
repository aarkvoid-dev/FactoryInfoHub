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

from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.contrib import messages
from django.utils import timezone
from django.utils.translation import gettext as _
from django.http import Http404
from .models import BlogPost, BlogImage
from .forms import BlogPostForm, BlogImageForm, BlogImageFormSet
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


class BlogPostListView(ListView):
    model = BlogPost
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        queryset = BlogPost.objects.filter(is_published=True)\
            .select_related('author', 'subcategory', 'region')

        request = self.request

        # Search
        q = request.GET.get('q')
        if q:
            queryset = queryset.filter(title__icontains=q)

        # Category
        category = request.GET.get('category')
        if category:
            queryset = queryset.filter(category_id=category)

        # Location Filters
        country = request.GET.get('country')
        state = request.GET.get('state')
        city = request.GET.get('city')
        district = request.GET.get('district')
        region = request.GET.get('region')

        if country:
            queryset = queryset.filter(country_id=country)

        if state:
            queryset = queryset.filter(state_id=state)

        if city:
            queryset = queryset.filter(city_id=city)

        if district:
            queryset = queryset.filter(district_id=district)

        if region:
            queryset = queryset.filter(region_id=region)

        return queryset
    


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['countries'] = Country.objects.all()
        return context


class BlogPostDetailView(DetailView):
    model = BlogPost
    template_name = 'blog/post_detail.html'
    context_object_name = 'post'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return BlogPost.objects.filter(is_published=True).select_related('author', 'subcategory', 'region')


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


@login_required
def create_blog_post_form(request):
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                blog = form.save(commit=False, author=request.user)
                blog.save()
                
                # Handle multiple images - check for multiple files with same name
                images = request.FILES.getlist('images')
                if images and any(images):  # Only process if images exist
                    for i, image in enumerate(images):
                        BlogImage.objects.create(
                            blog_post=blog,
                            image=image,
                            order=i,
                            is_featured=(i == 0)  # First image is featured by default
                        )
                
                messages.success(request, _('Blog post created successfully!'))
                return redirect('blog:post_list')
            except Exception as e:
                form.add_error(None, _('An error occurred while saving the blog post. Please try again.'))
                print(f"Error saving blog post: {e}")  # For debugging
        else:
            # Form validation errors
            print(f"Form errors: {form.errors}")  # For debugging
    else:
        form = BlogPostForm()
    
    context = {
        'form': form,
        'categories': Category.objects.all(),
        'countries': Country.objects.all(),
    }
    return render(request, 'blog/post_form.html', context)


@login_required
def edit_blog_post(request, slug):
    blog = get_object_or_404(BlogPost, slug=slug, author=request.user)
    
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES, instance=blog)
        if form.is_valid():
            blog = form.save()
            
            # Handle multiple images - check for multiple files with same name
            images = request.FILES.getlist('images')
            if images and any(images):  # Only process if images exist
                for i, image in enumerate(images):
                    BlogImage.objects.create(
                        blog_post=blog,
                        image=image,
                        order=i,
                        is_featured=(i == 0)  # First image is featured by default
                    )
            
            return redirect('blog:post_detail', slug=blog.slug)
    else:
        form = BlogPostForm(instance=blog)
    
    context = {
        'form': form,
        'blog': blog,
        'categories': Category.objects.all(),
        'countries': Country.objects.all(),
    }
    return render(request, 'blog/edit_blog.html', context)


@login_required
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
    blog = get_object_or_404(BlogPost, slug=slug, author=request.user)
    
    if request.method == 'POST':
        # Handle image deletion
        if 'delete_image' in request.POST:
            image_id = request.POST.get('delete_image')
            image = get_object_or_404(BlogImage, id=image_id, blog_post=blog)
            image.delete()
            messages.success(request, _('Image deleted successfully!'))
            return redirect('blog:manage_images', slug=blog.slug)
        
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
            return redirect('blog:manage_images', slug=blog.slug)
        
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
            return redirect('blog:manage_images', slug=blog.slug)
        
        # Handle image caption update
        if 'update_caption' in request.POST:
            image_id = request.POST.get('image_id')
            caption = request.POST.get('caption', '')
            image = get_object_or_404(BlogImage, id=image_id, blog_post=blog)
            image.caption = caption
            image.save()
            messages.success(request, _('Image caption updated successfully!'))
            return redirect('blog:manage_images', slug=blog.slug)
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
            return redirect('blog:manage_images',slug=blog.slug)
    
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
def upload_images(request, slug):
    blog = get_object_or_404(BlogPost, slug=slug, author=request.user)
    
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
    template_name = 'blog/edit_blog.html'
    context_object_name = 'post'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    success_url = reverse_lazy('blog:post_list')

    def get_queryset(self):
        return BlogPost.objects.filter(author=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['countries'] = Country.objects.all()
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
