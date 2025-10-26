# 🏠 Accessibility Checker Frontend

A modern, responsive web frontend for analyzing home accessibility features and barriers.

## ✨ Features

- **📸 Image Upload**: Drag & drop or click to upload images
- **🌐 Web Scraping**: Enter URLs to automatically scrape and analyze images
- **🔍 AI Analysis**: Uses AWS Bedrock/Claude for intelligent accessibility analysis
- **📊 Visual Results**: Beautiful score display and detailed recommendations
- **📱 Responsive Design**: Works on desktop, tablet, and mobile

## 🚀 Quick Start

### 1. Start the Backend
Make sure your Express.js backend is running:
```bash
cd ../express-backend
node server.js
```

### 2. Start the Frontend
```bash
cd frontend
node server.js
```

### 3. Open in Browser
Go to: http://localhost:8080

## 🎯 How to Use

### Method 1: Upload Images
1. Click "Choose Images" or drag & drop files
2. Select one or more images
3. Click "Analyze Accessibility"

### Method 2: Web Scraping
1. Enter a URL (e.g., property listing, real estate site)
2. Click "Scrape Images"
3. The system will automatically find and load images
4. Click "Analyze Accessibility"

## 🔧 Technical Details

### Architecture
- **Frontend**: Pure HTML/CSS/JavaScript (no frameworks)
- **Backend**: Express.js with AWS Bedrock
- **Image Processing**: Client-side base64 conversion
- **Web Scraping**: CORS proxy for cross-origin requests

### API Endpoints
- `GET /health` - Health check
- `POST /api/analyze` - Analyze base64 images
- `POST /api/upload` - Upload image files
- `POST /api/upload-and-analyze` - Upload and analyze in one step

### Supported Image Formats
- JPEG (.jpg, .jpeg)
- PNG (.png)
- WebP (.webp)
- GIF (.gif)

## 🌐 Web Scraping Integration

The frontend can automatically scrape images from:
- Real estate listings
- Property websites
- Home improvement sites
- Any website with images

### Example URLs to Try
- Zillow property listings
- Realtor.com listings
- Home improvement blogs
- Architecture websites

## 📱 Mobile Support

The frontend is fully responsive and works on:
- Desktop computers
- Tablets
- Mobile phones
- Touch devices

## 🔒 Security Features

- CORS protection
- File type validation
- Size limits (10MB per image)
- Input sanitization

## 🎨 Customization

### Styling
Edit `index.html` to customize:
- Colors and themes
- Layout and spacing
- Typography
- Animations

### Functionality
Modify the JavaScript to:
- Add new image sources
- Change analysis parameters
- Customize result display
- Add new features

## 🐛 Troubleshooting

### Common Issues

1. **"Server is not running" error**
   - Make sure Express.js backend is running on port 3000
   - Check console for backend errors

2. **Images not loading**
   - Check CORS settings
   - Verify image URLs are accessible
   - Try different image formats

3. **Analysis fails**
   - Check AWS Bedrock credentials
   - Verify backend logs
   - Ensure images are valid

### Debug Mode
Open browser developer tools to see:
- Network requests
- Console errors
- API responses

## 📈 Performance Tips

- Limit images to 5 per analysis
- Use compressed images when possible
- Close unused browser tabs
- Ensure stable internet connection

## 🔄 Updates

To update the frontend:
1. Stop the server (Ctrl+C)
2. Replace files with new versions
3. Restart the server
4. Refresh browser

## 📞 Support

For issues or questions:
1. Check the console for errors
2. Verify backend is running
3. Test with different images
4. Check network connectivity

## 🎉 Success!

Your accessibility checker is now ready to help analyze homes for accessibility features and barriers!
