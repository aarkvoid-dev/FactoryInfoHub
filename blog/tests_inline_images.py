"""
Test module for inline image functionality in blog posts.

This module contains tests to verify that the inline image feature
works correctly in blog content rendering.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from blog.models import BlogPost, BlogImage
from blog.templatetags.blog_extras import render_blog_content
from category.models import Category, SubCategory
from location.models import Country, State, City, District, Region


class InlineImageTests(TestCase):
    """Test cases for inline image functionality in blog posts."""
    
    def setUp(self):
        """Set up test data."""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create category and subcategory
        self.category = Category.objects.create(name='Textiles')
        self.subcategory = SubCategory.objects.create(
            name='Cotton Manufacturing',
            category=self.category
        )
        
        # Create location
        self.country = Country.objects.create(name='India')
        self.state = State.objects.create(name='Gujarat', country=self.country)
        self.city = City.objects.create(name='Ahmedabad', state=self.state)
        self.district = District.objects.create(name='Ahmedabad', city=self.city)
        self.region = Region.objects.create(
            name='Maninagar',
            district=self.district
        )
        
        # Create test blog post
        self.blog_post = BlogPost.objects.create(
            title='Test Blog Post with Images',
            content='This is a test blog post with [image:0] inline images and [image:1] more content.',
            excerpt='Test excerpt',
            author=self.user,
            category=self.category,
            subcategory=self.subcategory,
            country=self.country,
            state=self.state,
            city=self.city,
            district=self.district,
            region=self.region,
            is_published=True,
            published_at=timezone.now()
        )
        
        # Create test images
        self.image1 = BlogImage.objects.create(
            blog_post=self.blog_post,
            order=0,
            caption='First image caption',
            is_featured=False
        )
        # Note: We can't actually upload files in tests without proper file handling,
        # but we can test the logic
        
    def test_render_blog_content_with_image_placeholders(self):
        """Test that image placeholders are correctly replaced with HTML."""
        content = 'This is content with [image:0] an inline image.'
        images = self.blog_post.images.all()
        
        result = render_blog_content(content, images)
        
        # Check that the placeholder was replaced
        self.assertNotIn('[image:0]', result)
        self.assertIn('blog-image-wrapper', result)
        
    def test_render_blog_content_with_featured_image(self):
        """Test that featured image placeholder works correctly."""
        content = 'This content has [image:featured] the featured image.'
        images = self.blog_post.images.all()
        
        # Set first image as featured
        self.image1.is_featured = True
        self.image1.save()
        
        result = render_blog_content(content, images)
        
        # Check that the placeholder was replaced
        self.assertNotIn('[image:featured]', result)
        self.assertIn('blog-image-wrapper', result)
        
    def test_render_blog_content_with_multiple_images(self):
        """Test rendering content with multiple image placeholders."""
        # Create second image
        image2 = BlogImage.objects.create(
            blog_post=self.blog_post,
            order=1,
            caption='Second image caption',
            is_featured=False
        )
        
        content = 'Content with [image:0] first image and [image:1] second image.'
        images = self.blog_post.images.all()
        
        result = render_blog_content(content, images)
        
        # Check that both placeholders were replaced
        self.assertNotIn('[image:0]', result)
        self.assertNotIn('[image:1]', result)
        self.assertIn('blog-image-wrapper', result)
        
    def test_render_blog_content_with_invalid_image_reference(self):
        """Test handling of invalid image references."""
        content = 'Content with [image:999] invalid image reference.'
        images = self.blog_post.images.all()
        
        result = render_blog_content(content, images)
        
        # Invalid reference should remain as placeholder
        self.assertIn('[image:999]', result)
        
    def test_render_blog_content_with_mixed_content(self):
        """Test rendering content with mixed text and images."""
        # Create second image
        image2 = BlogImage.objects.create(
            blog_post=self.blog_post,
            order=1,
            caption='Second image caption',
            is_featured=False
        )
        
        content = '''This is a blog post about factory tours.

[image:0]

The factory has modern equipment and machinery.

[image:1]

Quality control is very important in manufacturing.

[image:featured]

Thank you for reading!'''
        
        images = self.blog_post.images.all()
        
        result = render_blog_content(content, images)
        
        # Check that valid placeholders were replaced
        self.assertNotIn('[image:0]', result)
        self.assertNotIn('[image:1]', result)
        self.assertIn('[image:featured]', result)  # Featured image doesn't exist
        
        # Check that HTML structure is correct
        self.assertIn('blog-image-wrapper', result)
        self.assertIn('This is a blog post about factory tours.', result)
        self.assertIn('Quality control is very important', result)
        
    def test_render_blog_content_empty_content(self):
        """Test handling of empty content."""
        content = ''
        images = self.blog_post.images.all()
        
        result = render_blog_content(content, images)
        
        self.assertEqual(result, '')
        
    def test_render_blog_content_no_images(self):
        """Test handling when no images are available."""
        content = 'Content with [image:0] but no images.'
        images = BlogImage.objects.none()
        
        result = render_blog_content(content, images)
        
        # Placeholder should remain since no images exist
        self.assertIn('[image:0]', result)


if __name__ == '__main__':
    import unittest
    unittest.main()