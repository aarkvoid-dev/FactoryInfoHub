# File Upload Size Limit Solution

## Problem
Users were getting a 413 "Request Entity Too Large" error when uploading images to the blog or factory forms.

## Solution Implemented

### 1. Client-Side Validation (JavaScript)
Added automatic file size validation in `templates/base.html` that:
- Checks all file inputs on the page
- Validates total file size before upload
- Shows user-friendly error message below the file input
- Clears the file selection if size exceeds limit
- Default limit: 5MB (can be overridden with `data-max-size` attribute)

**Features:**
- Real-time validation on file selection
- Shows exact file size and limit in MB
- Warning icon (⚠️) for better visibility
- Works for all file upload fields across the site

### 2. Server-Side Configuration

#### Nginx Configuration (`deployment/nginx.conf`)
Added `client_max_body_size 100M;` to allow uploads up to 100MB.

#### Django Settings (`FactoryInfoHub/settings.py`)
Added three key settings:
```python
DATA_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024  # 100 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024  # 100 MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000
```

## Configuration Details

### Client-Side Limit
- **Default**: 5MB per file input
- **Override**: Add `data-max-size="10485760"` (10MB in bytes) to any file input
- **Example**: `<input type="file" name="images" data-max-size="10485760">`

### Server-Side Limit
- **Nginx**: 100MB
- **Django**: 100MB
- **Maximum fields**: 1000 per request

## How It Works

1. **User selects files** → JavaScript immediately checks total size
2. **If size > limit** → Shows error message and clears selection
3. **If size ≤ limit** → Allows upload to proceed
4. **Server receives request** → Nginx and Django validate again
5. **If still too large** → Returns 413 error (shouldn't happen with client validation)

## Benefits

1. **Better UX**: Users get immediate feedback before upload starts
2. **Saves bandwidth**: Prevents uploading files that will be rejected
3. **Clear messaging**: Shows exact size and limit
4. **Consistent**: Works across all upload forms
5. **Configurable**: Easy to adjust limits per form or globally

## Usage

### For Developers
To use a different limit for a specific file input:
```html
<input type="file" name="large_files" data-max-size="52428800"> <!-- 50MB -->
```

### For Users
- If you see an error: "Total file size (X MB) exceeds the limit of Y MB"
- Solution: Upload smaller files or split into multiple uploads
- Contact support if you need higher limits

## Testing

To test the implementation:
1. Try uploading a file larger than 5MB
2. Should see error message appear immediately
3. File selection should be cleared
4. Upload button should remain disabled

## Future Improvements

- Add image compression before upload
- Show progress bar during upload
- Allow multiple smaller uploads instead of one large
- Add server-side image resizing
- Implement chunked uploads for very large files

## Files Modified

1. `templates/base.html` - Added JavaScript validation
2. `deployment/nginx.conf` - Added client_max_body_size
3. `FactoryInfoHub/settings.py` - Added upload limits

## Support

If users continue to experience upload issues:
1. Check browser console for JavaScript errors
2. Verify file size is under limit
3. Check server logs for 413 errors
4. Ensure Nginx was reloaded after config change
5. Verify Django settings are loaded (restart server if needed)