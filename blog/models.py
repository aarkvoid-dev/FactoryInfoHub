from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.contrib.auth.models import User
from category.models import SubCategory, Category
from location.models import Region, District, City, State, Country
from Home.models import SoftDeleteModel
from Karkahan.models import Factory


class BlogPost(SoftDeleteModel):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    content = models.TextField()
    excerpt = models.TextField(blank=True, help_text="Brief summary of the post")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_posts',blank=True, null=True)
    
    # --- Category Hierarchy ---
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='blogs', blank=True, null=True)
    subcategory = models.ForeignKey(SubCategory, on_delete=models.CASCADE, related_name='blog_posts', blank=True, null=True)
    
    # --- Location Hierarchy ---
    country = models.ForeignKey(Country, on_delete=models.PROTECT, related_name='blogs', blank=True, null=True)
    state = models.ForeignKey(State, on_delete=models.PROTECT, related_name='blogs', blank=True, null=True)
    city = models.ForeignKey(City, on_delete=models.PROTECT, related_name='blogs', blank=True, null=True)
    district = models.ForeignKey(District, on_delete=models.PROTECT, related_name='blogs', blank=True, null=True)
    region = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True, blank=True, related_name='blog_posts')
    
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Related factories
    related_factories = models.ManyToManyField(Factory, blank=True, related_name='blog_posts', 
                                              help_text="Factories related to this blog post")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Blog Post"
        verbose_name_plural = "Blog Posts"
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_published']),
            models.Index(fields=['is_deleted']),
            models.Index(fields=['author']),
            models.Index(fields=['category']),
            models.Index(fields=['subcategory']),
            models.Index(fields=['country']),
            models.Index(fields=['state']),
            models.Index(fields=['city']),
            models.Index(fields=['created_at']),
            models.Index(fields=['published_at']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            self.slug = base_slug
            counter = 1
            while BlogPost.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{base_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('blog:post_detail', kwargs={'slug': self.slug})

    def get_featured_image(self):
        """Get the featured image for this blog post"""
        return self.images.filter(is_featured=True).first()

    def get_gallery_images(self):
        """Get all images except the featured one for gallery display"""
        return self.images.exclude(is_featured=True).order_by('order')


import os
from django.utils.deconstruct import deconstructible

@deconstructible
class BlogImageUploadPath:
    def __init__(self, sub_path=""):
        self.sub_path = sub_path

    def __call__(self, instance, filename):
        # Get the blog post title and slug for better organization
        blog_title = instance.blog_post.slug if instance.blog_post.slug else "blog"
        # Generate a unique filename
        import uuid
        ext = filename.split('.')[-1]
        filename = f"{uuid.uuid4().hex}.{ext}"
        return os.path.join('blog_images', blog_title, filename)

class BlogImage(models.Model):
    blog_post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=BlogImageUploadPath(), max_length=500)
    caption = models.CharField(max_length=200, blank=True)
    is_featured = models.BooleanField(default=False, help_text="Set as the main image for this blog post")
    order = models.PositiveIntegerField(default=0, help_text="Order of the image in the gallery")
    
    class Meta:
        ordering = ['order']
        verbose_name = "Blog Image"
        verbose_name_plural = "Blog Images"
    
    def __str__(self):
        return f"{self.blog_post.title} - Image {self.order}"
    
    def save(self, *args, **kwargs):
        # Ensure featured image logic
        if self.is_featured:
            # Unset featured status for other images of the same blog post
            BlogImage.objects.filter(blog_post=self.blog_post, is_featured=True).update(is_featured=False)
        super().save(*args, **kwargs)
