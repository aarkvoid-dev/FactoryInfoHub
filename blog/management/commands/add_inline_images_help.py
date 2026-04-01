"""
Management command to display help information about inline image placement in blog posts.

This command provides documentation and examples for using the new inline image
feature in blog content.
"""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Display help information about inline image placement in blog posts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--examples',
            action='store_true',
            help='Show examples of inline image usage',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Inline Image Placement Help ===\n'))
        
        self.stdout.write(self.style.WARNING('How to Add Images Between Article Content:\n'))
        
        self.stdout.write(self.style.SUCCESS('1. Upload Images to Your Blog Post'))
        self.stdout.write('   - Go to your blog post edit page')
        self.stdout.write('   - Use the "Manage Images" feature to upload images')
        self.stdout.write('   - Set image order and captions as needed\n')
        
        self.stdout.write(self.style.SUCCESS('2. Use Image Placeholders in Content'))
        self.stdout.write('   - In your blog content, use these placeholders:')
        self.stdout.write('   - [image:0] - Shows image with order 0 (first image)')
        self.stdout.write('   - [image:1] - Shows image with order 1 (second image)')
        self.stdout.write('   - [image:2] - Shows image with order 2 (third image)')
        self.stdout.write('   - [image:featured] - Shows the featured image\n')
        
        self.stdout.write(self.style.SUCCESS('3. Example Blog Content:\n'))
        
        example_content = """
        # My Factory Tour Blog Post

        Welcome to our factory tour! Today we're visiting the ABC Textiles factory.

        [image:0]

        As you can see in the image above, the factory has modern machinery and equipment.

        The production process starts with raw materials and goes through several stages:

        1. Material preparation
        2. Weaving process
        3. Quality inspection
        4. Packaging

        [image:1]

        This image shows the weaving process in action.

        After production, all items go through a strict quality control process:

        [image:featured]

        The featured image shows our quality control team at work.

        Thank you for joining our factory tour!
        """
        
        self.stdout.write(self.style.SUCCESS('Example Blog Content:'))
        self.stdout.write(example_content)
        
        self.stdout.write(self.style.SUCCESS('4. Image Features:'))
        self.stdout.write('   - Images are automatically styled with responsive design')
        self.stdout.write('   - Captions are displayed below each image')
        self.stdout.write('   - Images are centered and have rounded corners')
        self.stdout.write('   - Images scale properly on different screen sizes\n')
        
        self.stdout.write(self.style.SUCCESS('5. Tips:'))
        self.stdout.write('   - Upload all images before writing your content')
        self.stdout.write('   - Use descriptive captions for better accessibility')
        self.stdout.write('   - Plan your image placement to break up long text sections')
        self.stdout.write('   - Use [image:featured] for your main hero image\n')
        
        self.stdout.write(self.style.SUCCESS('6. Image Management:'))
        self.stdout.write('   - Set one image as "featured" for the hero section')
        self.stdout.write('   - Use the order field to control image sequence')
        self.stdout.write('   - Add captions to provide context for each image')
        self.stdout.write('   - Images are automatically optimized for web display\n')
        
        self.stdout.write(self.style.SUCCESS('=== End of Help ==='))