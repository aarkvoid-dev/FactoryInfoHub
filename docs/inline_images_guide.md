# Inline Images in Blog Posts - User Guide

This guide explains how to add images between article content in your blog posts using the new inline image feature.

## Overview

The inline image feature allows you to place images directly within your blog content, creating a more engaging and visually appealing reading experience. Instead of having images only at the top or bottom of your post, you can now intersperse them throughout your content.

## How It Works

The system uses special placeholders in your blog content that get automatically replaced with actual images when the post is displayed. These placeholders follow a simple pattern:

- `[image:0]` - Shows the image with order 0 (first uploaded image)
- `[image:1]` - Shows the image with order 1 (second uploaded image)
- `[image:2]` - Shows the image with order 2 (third uploaded image)
- `[image:featured]` - Shows the featured image

## Step-by-Step Guide

### Step 1: Upload Images to Your Blog Post

1. **Create or edit your blog post** through the admin interface or your blog management page
2. **Upload images** using the "Manage Images" feature
3. **Set image properties**:
   - **Order**: Determines which placeholder (`[image:0]`, `[image:1]`, etc.) will display this image
   - **Caption**: Optional text that appears below the image
   - **Featured**: Mark one image as featured to use with `[image:featured]` placeholder

### Step 2: Write Your Blog Content

When writing your blog content, include image placeholders where you want images to appear:

```markdown
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
```

### Step 3: Preview and Publish

1. **Preview your post** to see how images appear in context
2. **Adjust image order** if needed by editing image properties
3. **Publish your post** when satisfied with the layout

## Image Features

### Automatic Styling
- Images are automatically styled with responsive design
- Images are centered and have rounded corners
- Images scale properly on different screen sizes
- Captions are displayed below each image

### Image Management
- **Order field**: Controls which placeholder displays each image
- **Caption field**: Adds descriptive text below images
- **Featured option**: Designates a main image for hero sections
- **Automatic optimization**: Images are optimized for web display

## Best Practices

### Planning Your Content
1. **Upload all images first** before writing content
2. **Plan image placement** to break up long text sections
3. **Use descriptive captions** for better accessibility
4. **Consider image order** carefully to match your content flow

### Content Structure
- Use images to illustrate key points in your content
- Place images strategically to maintain reader engagement
- Use `[image:featured]` for your main hero or cover image
- Don't overcrowd content with too many images

### Image Quality
- Use high-quality images (minimum 800x600 pixels)
- Ensure images are relevant to your content
- Use appropriate file formats (JPG for photos, PNG for graphics)
- Keep file sizes reasonable for fast loading

## Examples

### Example 1: Factory Tour
```markdown
# Factory Tour: ABC Textiles

Welcome to our factory tour! We'll be exploring the ABC Textiles manufacturing facility.

[image:0]

The image above shows our main production floor. As you can see, we have state-of-the-art equipment.

Our production process involves several key stages:

[image:1]

This image demonstrates our weaving process, which is one of the most critical steps in textile manufacturing.

Quality control is paramount in our operations:

[image:featured]

Our quality control team ensures every product meets our high standards.

Thank you for joining our tour!
```

### Example 2: Product Review
```markdown
# Review: XYZ Industrial Machine

Today I'm reviewing the XYZ Industrial Machine, a popular choice in manufacturing circles.

[image:0]

The machine's design is both functional and aesthetically pleasing. The build quality is excellent.

Key features include:

- Advanced automation capabilities
- Energy-efficient operation
- Easy maintenance access

[image:1]

This image shows the control panel, which is intuitive and user-friendly.

Performance testing revealed impressive results:

[image:2]

The machine operates smoothly and efficiently under various conditions.

Overall, I highly recommend the XYZ Industrial Machine for manufacturing applications.
```

## Troubleshooting

### Common Issues

**Q: My image placeholder isn't showing up**
A: Check that:
- The image exists and is uploaded
- The order number matches your placeholder
- The image is not marked as deleted

**Q: Images aren't displaying in the right order**
A: Verify the order field in your image settings matches your placeholders

**Q: Featured image isn't showing**
A: Make sure one image is marked as "featured" in your image settings

**Q: Images are too large or small**
A: The system automatically optimizes images, but you can adjust CSS if needed

### Getting Help

If you encounter issues with inline images:

1. Check that images are properly uploaded and have correct order numbers
2. Verify image placeholders match your image order
3. Ensure the blog post is published and not in draft mode
4. Contact support if issues persist

## Advanced Usage

### Custom Styling

You can customize the appearance of inline images by adding CSS to your blog template:

```css
.blog-image-wrapper {
    margin: 2rem 0;
    border-radius: 8px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

.blog-image-wrapper img {
    max-width: 100%;
    height: auto;
    border-radius: 8px;
}
```

### Multiple Image Galleries

You can create multiple image galleries within a single post by using different image placeholders:

```markdown
# Comprehensive Factory Overview

## Production Area

[image:0]
[image:1]

## Quality Control

[image:2]
[image:featured]

## Packaging

[image:3]
```

## Conclusion

The inline image feature provides a powerful way to enhance your blog content with visual elements. By following this guide, you can create engaging, well-illustrated blog posts that captivate your readers and effectively communicate your message.

Remember to plan your image placement carefully, use descriptive captions, and maintain a good balance between text and visual content for the best reader experience.