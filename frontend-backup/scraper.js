/**
 * Web Scraping Integration for Accessibility Checker
 * Fetches images from URLs and prepares them for analysis
 */

class ImageScraper {
    constructor() {
        this.corsProxy = 'https://api.allorigins.win/raw?url=';
    }

    /**
     * Fetch images from a URL (for web scraping integration)
     * @param {string} url - The URL to scrape images from
     * @returns {Promise<Array>} Array of image objects
     */
    async fetchImagesFromUrl(url) {
        try {
            console.log('🔍 Fetching images from:', url);
            
            // Try multiple approaches for different sites
            let images = [];
            
            // Approach 1: Direct fetch with CORS proxy
            try {
                const proxyUrl = this.corsProxy + encodeURIComponent(url);
                const response = await fetch(proxyUrl);
                
                if (response.ok) {
                    const html = await response.text();
                    images = this.extractImagesFromHTML(html, url);
                    console.log(`✅ Found ${images.length} images via CORS proxy`);
                }
            } catch (error) {
                console.warn('⚠️ CORS proxy failed:', error.message);
            }
            
            // Approach 2: Try direct fetch (for same-origin or CORS-enabled sites)
            if (images.length === 0) {
                try {
                    const response = await fetch(url, {
                        mode: 'cors',
                        headers: {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                        }
                    });
                    
                    if (response.ok) {
                        const html = await response.text();
                        images = this.extractImagesFromHTML(html, url);
                        console.log(`✅ Found ${images.length} images via direct fetch`);
                    }
                } catch (error) {
                    console.warn('⚠️ Direct fetch failed:', error.message);
                }
            }
            
            // Approach 3: For Zillow specifically, try to extract from JSON data
            if (images.length === 0 && url.includes('zillow.com')) {
                images = await this.extractZillowImages(url);
                console.log(`✅ Found ${images.length} images from Zillow JSON`);
            }
            
            // Approach 3.5: Try to find images with different size parameters
            if (images.length === 0) {
                try {
                    const proxyUrl = this.corsProxy + encodeURIComponent(url);
                    const response = await fetch(proxyUrl);
                    
                    if (response.ok) {
                        const html = await response.text();
                        
                        // Look for images with different size parameters
                        const sizePatterns = [
                            /https:\/\/[^"'\s]*\.(jpg|jpeg|png|gif|webp)[^"'\s]*/gi,
                            /"url":"([^"]*\.(jpg|jpeg|png|gif|webp)[^"]*)"/gi,
                            /"src":"([^"]*\.(jpg|jpeg|png|gif|webp)[^"]*)"/gi,
                            /"image":"([^"]*\.(jpg|jpeg|png|gif|webp)[^"]*)"/gi
                        ];
                        
                        const allMatches = [];
                        sizePatterns.forEach(pattern => {
                            const matches = html.match(pattern);
                            if (matches) {
                                allMatches.push(...matches);
                            }
                        });
                        
                        if (allMatches.length > 0) {
                            const seenUrls = new Set();
                            const newImages = [];
                            
                            allMatches.forEach(match => {
                                let url = match.replace(/^"|"$/g, '');
                                if (url.startsWith('//')) {
                                    url = 'https:' + url;
                                } else if (url.startsWith('/')) {
                                    const base = new URL(url);
                                    url = base.origin + url;
                                }
                                
                                if (this.isImageUrl(url)) {
                                    const normalizedUrl = this.normalizeImageUrl(url);
                                    if (!seenUrls.has(normalizedUrl)) {
                                        seenUrls.add(normalizedUrl);
                                        newImages.push({
                                            url: url,
                                            alt: `Property Image ${newImages.length + 1}`,
                                            filename: this.getFilenameFromUrl(url),
                                            index: newImages.length
                                        });
                                    }
                                }
                            });
                            
                            if (newImages.length > 0) {
                                images = newImages;
                                console.log(`✅ Found ${images.length} images via size pattern matching`);
                            }
                        }
                    }
                } catch (error) {
                    console.warn('⚠️ Size pattern matching failed:', error.message);
                }
            }
            
            // Approach 4: Try alternative CORS proxies
            if (images.length === 0) {
                const alternativeProxies = [
                    'https://cors-anywhere.herokuapp.com/',
                    'https://api.codetabs.com/v1/proxy?quest=',
                    'https://thingproxy.freeboard.io/fetch/'
                ];
                
                for (const proxy of alternativeProxies) {
                    try {
                        const proxyUrl = proxy + encodeURIComponent(url);
                        const response = await fetch(proxyUrl);
                        
                        if (response.ok) {
                            const html = await response.text();
                            images = this.extractImagesFromHTML(html, url);
                            if (images.length > 0) {
                                console.log(`✅ Found ${images.length} images via alternative proxy`);
                                break;
                            }
                        }
                    } catch (error) {
                        console.warn(`⚠️ Alternative proxy failed:`, error.message);
                    }
                }
            }
            
            if (images.length === 0) {
                throw new Error('No images found. The site may use JavaScript rendering or have anti-scraping measures.');
            }
            
            return images;
            
        } catch (error) {
            console.error('❌ Error fetching images:', error);
            throw new Error(`Failed to fetch images from ${url}: ${error.message}`);
        }
    }

    /**
     * Extract image URLs from HTML content
     * @param {string} html - HTML content
     * @param {string} baseUrl - Base URL for relative links
     * @returns {Array} Array of image objects
     */
    extractImagesFromHTML(html, baseUrl) {
        const images = [];
        const seenUrls = new Set(); // Track seen URLs to avoid duplicates
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        
        // Find all img tags with various attributes
        const imgTags = doc.querySelectorAll('img');
        
        imgTags.forEach((img, index) => {
            // Try multiple possible image source attributes
            const possibleSrcs = [
                img.src,
                img.getAttribute('data-src'),
                img.getAttribute('data-lazy'),
                img.getAttribute('data-original'),
                img.getAttribute('data-srcset'),
                img.getAttribute('data-lazy-src'),
                img.getAttribute('data-defer-src'),
                img.getAttribute('data-img-src')
            ];
            
            for (const src of possibleSrcs) {
                if (src && src.trim()) {
                    let processedSrc = src.trim();
                    
                    // Handle srcset (take the first URL)
                    if (processedSrc.includes(',')) {
                        processedSrc = processedSrc.split(',')[0].trim();
                    }
                    
                    // Convert relative URLs to absolute
                    if (processedSrc.startsWith('//')) {
                        processedSrc = 'https:' + processedSrc;
                    } else if (processedSrc.startsWith('/')) {
                        const base = new URL(baseUrl);
                        processedSrc = base.origin + processedSrc;
                    } else if (!processedSrc.startsWith('http')) {
                        const base = new URL(baseUrl);
                        processedSrc = base.origin + '/' + processedSrc;
                    }
                    
                    // Normalize URL to avoid duplicates with different parameters
                    const normalizedUrl = this.normalizeImageUrl(processedSrc);
                    
                    // Filter for common image formats and avoid duplicates
                    if (this.isImageUrl(processedSrc) && !seenUrls.has(normalizedUrl)) {
                        seenUrls.add(normalizedUrl);
                        images.push({
                            url: processedSrc,
                            alt: img.alt || `Image ${index + 1}`,
                            filename: this.getFilenameFromUrl(processedSrc),
                            index: index
                        });
                        break; // Only add one image per img tag
                    }
                }
            }
        });
        
        // Also look for background images in CSS
        const elementsWithBg = doc.querySelectorAll('[style*="background-image"]');
        elementsWithBg.forEach((element, index) => {
            const style = element.getAttribute('style');
            const bgMatch = style.match(/background-image:\s*url\(['"]?([^'")]+)['"]?\)/i);
            if (bgMatch) {
                let bgSrc = bgMatch[1];
                if (bgSrc.startsWith('//')) {
                    bgSrc = 'https:' + bgSrc;
                } else if (bgSrc.startsWith('/')) {
                    const base = new URL(baseUrl);
                    bgSrc = base.origin + bgSrc;
                } else if (!bgSrc.startsWith('http')) {
                    const base = new URL(baseUrl);
                    bgSrc = base.origin + '/' + bgSrc;
                }
                
                const normalizedUrl = this.normalizeImageUrl(bgSrc);
                if (this.isImageUrl(bgSrc) && !seenUrls.has(normalizedUrl)) {
                    seenUrls.add(normalizedUrl);
                    images.push({
                        url: bgSrc,
                        alt: `Background Image ${index + 1}`,
                        filename: this.getFilenameFromUrl(bgSrc),
                        index: images.length + index
                    });
                }
            }
        });
        
        // Also look for images in JSON data or script tags
        const scriptTags = doc.querySelectorAll('script');
        scriptTags.forEach((script, index) => {
            const content = script.textContent || script.innerHTML;
            if (content) {
                // Look for image URLs in JSON data
                const imageUrlPatterns = [
                    /https:\/\/[^"'\s]*\.(jpg|jpeg|png|gif|webp|bmp)/gi,
                    /"url":\s*"([^"]*\.(jpg|jpeg|png|gif|webp|bmp)[^"]*)"/gi,
                    /"imageUrl":\s*"([^"]+)"/gi,
                    /"photoUrl":\s*"([^"]+)"/gi
                ];
                
                for (const pattern of imageUrlPatterns) {
                    const matches = content.match(pattern);
                    if (matches) {
                        matches.forEach(match => {
                            let url = match.replace(/^"|"$/g, ''); // Remove quotes
                            if (url.startsWith('//')) {
                                url = 'https:' + url;
                            } else if (url.startsWith('/')) {
                                const base = new URL(baseUrl);
                                url = base.origin + url;
                            }
                            
                            const normalizedUrl = this.normalizeImageUrl(url);
                            if (this.isImageUrl(url) && !seenUrls.has(normalizedUrl)) {
                                seenUrls.add(normalizedUrl);
                                images.push({
                                    url: url,
                                    alt: `JSON Image ${images.length + 1}`,
                                    filename: this.getFilenameFromUrl(url),
                                    index: images.length
                                });
                            }
                        });
                    }
                }
            }
        });
        
        console.log(`🔍 Found ${images.length} unique images (filtered duplicates)`);
        
        // Debug: Log first few URLs to see what we're getting
        if (images.length > 0) {
            console.log('📸 First few image URLs:');
            images.slice(0, 5).forEach((img, index) => {
                console.log(`  ${index + 1}. ${img.url}`);
            });
        }
        
        return images;
    }

    /**
     * Check if URL is an image
     * @param {string} url - URL to check
     * @returns {boolean} True if URL appears to be an image
     */
    isImageUrl(url) {
        const imageExtensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg', '.tiff', '.ico'];
        const lowerUrl = url.toLowerCase();
        
        // Check for image extensions
        const hasImageExt = imageExtensions.some(ext => lowerUrl.includes(ext));
        
        // Check for common image-related keywords
        const hasImageKeyword = lowerUrl.includes('image') ||
                               lowerUrl.includes('photo') ||
                               lowerUrl.includes('picture') ||
                               lowerUrl.includes('img') ||
                               lowerUrl.includes('gallery') ||
                               lowerUrl.includes('media');
        
        // Check for common image hosting patterns
        const hasImageHosting = lowerUrl.includes('cloudinary') ||
                               lowerUrl.includes('imgur') ||
                               lowerUrl.includes('flickr') ||
                               lowerUrl.includes('unsplash') ||
                               lowerUrl.includes('pexels');
        
        // Exclude common non-image URLs and generic images
        const isNotImage = lowerUrl.includes('logo') ||
                          lowerUrl.includes('icon') ||
                          lowerUrl.includes('avatar') ||
                          lowerUrl.includes('thumbnail') ||
                          lowerUrl.includes('placeholder') ||
                          lowerUrl.includes('spacer') ||
                          lowerUrl.includes('pixel') ||
                          lowerUrl.includes('transparent') ||
                          lowerUrl.includes('blank') ||
                          lowerUrl.includes('default') ||
                          lowerUrl.includes('loading') ||
                          lowerUrl.includes('spinner') ||
                          lowerUrl.includes('arrow') ||
                          lowerUrl.includes('button') ||
                          lowerUrl.includes('badge') ||
                          lowerUrl.includes('banner') ||
                          lowerUrl.includes('header') ||
                          lowerUrl.includes('footer');
        
        // For Zillow specifically, look for property photo patterns
        const isZillowPropertyPhoto = lowerUrl.includes('photos.zillowstatic.com') ||
                                    lowerUrl.includes('images.zillowstatic.com') ||
                                    (lowerUrl.includes('zillow') && (hasImageExt || hasImageKeyword));
        
        // Must be a valid image and not a generic/UI element
        const isValidImage = (hasImageExt || hasImageKeyword || hasImageHosting || isZillowPropertyPhoto) && !isNotImage;
        
        // Additional filtering for size - avoid very small images (likely icons)
        const hasSizeParams = lowerUrl.includes('w=') || lowerUrl.includes('h=') || lowerUrl.includes('size=');
        const isLikelyIcon = hasSizeParams && (lowerUrl.includes('w=16') || lowerUrl.includes('w=24') || lowerUrl.includes('w=32') || lowerUrl.includes('h=16') || lowerUrl.includes('h=24') || lowerUrl.includes('h=32'));
        
        return isValidImage && !isLikelyIcon;
    }

    /**
     * Extract images specifically from Zillow listings
     * @param {string} url - Zillow URL
     * @returns {Promise<Array>} Array of image objects
     */
    async extractZillowImages(url) {
        try {
            console.log('🏠 Attempting Zillow-specific extraction...');
            
            // Try to extract ZPID from URL
            const zpidMatch = url.match(/\/(\d+)_zpid/);
            if (!zpidMatch) {
                throw new Error('Could not extract ZPID from Zillow URL');
            }
            
            const zpid = zpidMatch[1];
            console.log('🔍 Found ZPID:', zpid);
            
            // Try to fetch from Zillow's API endpoints
            const apiEndpoints = [
                `https://www.zillow.com/homedetails/${zpid}_zpid/`,
                `https://www.zillow.com/graphql`,
                `https://www.zillow.com/api/v1/property/${zpid}`
            ];
            
            for (const endpoint of apiEndpoints) {
                try {
                    const proxyUrl = this.corsProxy + encodeURIComponent(endpoint);
                    const response = await fetch(proxyUrl);
                    
                    if (response.ok) {
                        const content = await response.text();
                        
                        // Look for image URLs in the content with better patterns
                        const imagePatterns = [
                            /https:\/\/photos\.zillowstatic\.com\/[^"'\s]+/g,
                            /https:\/\/images\.zillowstatic\.com\/[^"'\s]+/g,
                            /"photoUrl":"([^"]+)"/g,
                            /"imageUrl":"([^"]+)"/g,
                            /"url":"([^"]*\.(jpg|jpeg|png|webp)[^"]*)"/g
                        ];
                        
                        const allMatches = [];
                        imagePatterns.forEach(pattern => {
                            const matches = content.match(pattern);
                            if (matches) {
                                allMatches.push(...matches);
                            }
                        });
                        
                        if (allMatches.length > 0) {
                            const seenUrls = new Set();
                            const images = [];
                            
                            allMatches.forEach(match => {
                                let url = match.replace(/^"|"$/g, ''); // Remove quotes
                                if (url.startsWith('//')) {
                                    url = 'https:' + url;
                                }
                                
                                // Only include property photos, not UI elements
                                if (this.isImageUrl(url) && !url.includes('icon') && !url.includes('logo') && !url.includes('avatar')) {
                                    const normalizedUrl = this.normalizeImageUrl(url);
                                    if (!seenUrls.has(normalizedUrl)) {
                                        seenUrls.add(normalizedUrl);
                                        images.push({
                                            url: url,
                                            alt: `Zillow Property Image ${images.length + 1}`,
                                            filename: this.getFilenameFromUrl(url),
                                            index: images.length
                                        });
                                    }
                                }
                            });
                            
                            console.log(`✅ Found ${images.length} unique Zillow property images`);
                            return images;
                        }
                    }
                } catch (error) {
                    console.warn(`⚠️ Zillow endpoint failed:`, error.message);
                }
            }
            
            // Fallback: Try to extract from page content using regex patterns
            try {
                const proxyUrl = this.corsProxy + encodeURIComponent(url);
                const response = await fetch(proxyUrl);
                
                if (response.ok) {
                    const html = await response.text();
                    
                    // Look for Zillow-specific image patterns
                    const zillowImagePatterns = [
                        /https:\/\/photos\.zillowstatic\.com\/[^"'\s]+/g,
                        /https:\/\/images\.zillowstatic\.com\/[^"'\s]+/g,
                        /"photoUrl":"([^"]+)"/g,
                        /"imageUrl":"([^"]+)"/g,
                        /"url":"([^"]*\.(jpg|jpeg|png|webp)[^"]*)"/g
                    ];
                    
                    const allImages = [];
                    for (const pattern of zillowImagePatterns) {
                        const matches = html.match(pattern);
                        if (matches) {
                            allImages.push(...matches);
                        }
                    }
                    
                    if (allImages.length > 0) {
                        const seenUrls = new Set();
                        const uniqueImages = [];
                        
                        allImages.forEach(url => {
                            const cleanUrl = url.replace(/^"|"$/g, ''); // Remove quotes
                            const normalizedUrl = this.normalizeImageUrl(cleanUrl);
                            
                            if (!seenUrls.has(normalizedUrl)) {
                                seenUrls.add(normalizedUrl);
                                uniqueImages.push({
                                    url: cleanUrl,
                                    alt: `Zillow Property Image ${uniqueImages.length + 1}`,
                                    filename: this.getFilenameFromUrl(cleanUrl),
                                    index: uniqueImages.length
                                });
                            }
                        });
                        
                        console.log(`✅ Found ${uniqueImages.length} unique Zillow images via pattern matching`);
                        return uniqueImages;
                    }
                }
            } catch (error) {
                console.warn(`⚠️ Zillow pattern matching failed:`, error.message);
            }
            
            return [];
            
        } catch (error) {
            console.error('❌ Zillow extraction failed:', error);
            return [];
        }
    }

    /**
     * Normalize image URL to avoid duplicates with different parameters
     * @param {string} url - URL to normalize
     * @returns {string} Normalized URL
     */
    normalizeImageUrl(url) {
        try {
            const urlObj = new URL(url);
            // Remove common query parameters that don't affect the image
            const paramsToRemove = ['w', 'h', 'width', 'height', 'size', 'quality', 'format', 'fit', 'crop'];
            paramsToRemove.forEach(param => urlObj.searchParams.delete(param));
            
            // Remove trailing slashes and normalize
            let normalized = urlObj.toString();
            if (normalized.endsWith('/')) {
                normalized = normalized.slice(0, -1);
            }
            
            return normalized;
        } catch {
            return url;
        }
    }

    /**
     * Extract filename from URL
     * @param {string} url - URL to extract filename from
     * @returns {string} Filename
     */
    getFilenameFromUrl(url) {
        try {
            const urlObj = new URL(url);
            const pathname = urlObj.pathname;
            const filename = pathname.split('/').pop();
            return filename || 'image.jpg';
        } catch {
            return 'image.jpg';
        }
    }

    /**
     * Convert image URL to base64
     * @param {string} imageUrl - Image URL
     * @returns {Promise<string>} Base64 encoded image
     */
    async imageUrlToBase64(imageUrl) {
        try {
            const response = await fetch(imageUrl);
            if (!response.ok) {
                throw new Error(`Failed to fetch image: ${response.status}`);
            }
            
            const blob = await response.blob();
            return new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onload = () => resolve(reader.result.split(',')[1]);
                reader.onerror = reject;
                reader.readAsDataURL(blob);
            });
        } catch (error) {
            console.error('❌ Error converting image to base64:', error);
            throw error;
        }
    }

    /**
     * Scrape and prepare images for analysis
     * @param {string} url - URL to scrape
     * @param {number} maxImages - Maximum number of images to process
     * @returns {Promise<Array>} Array of prepared images
     */
    async scrapeAndPrepareImages(url, maxImages = 20) {
        try {
            const images = await this.fetchImagesFromUrl(url);
            const limitedImages = images.slice(0, maxImages);
            
            const preparedImages = [];
            
            for (const img of limitedImages) {
                try {
                    console.log(`🔄 Processing image: ${img.filename}`);
                    const base64 = await this.imageUrlToBase64(img.url);
                    
                    preparedImages.push({
                        filename: img.filename,
                        base64: base64,
                        url: img.url,
                        alt: img.alt
                    });
                } catch (error) {
                    console.warn(`⚠️ Failed to process image ${img.filename}:`, error);
                }
            }
            
            console.log(`✅ Successfully prepared ${preparedImages.length} images`);
            return preparedImages;
            
        } catch (error) {
            console.error('❌ Error in scrapeAndPrepareImages:', error);
            throw error;
        }
    }
}

// Export for use in the main application
window.ImageScraper = ImageScraper;
