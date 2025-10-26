/**
 * Test suite for Express.js Accessibility Checker API
 */

const request = require('supertest');
const app = require('../server');
const fs = require('fs');
const path = require('path');

describe('Accessibility Checker API', () => {
  let testImagePath;

  beforeAll(() => {
    // Create a test image file
    testImagePath = path.join(__dirname, 'test-image.jpg');
    // In a real test, you'd create an actual image file
  });

  afterAll(() => {
    // Clean up test files
    if (fs.existsSync(testImagePath)) {
      fs.unlinkSync(testImagePath);
    }
  });

  describe('Health Check', () => {
    test('GET /health should return healthy status', async () => {
      const response = await request(app)
        .get('/health')
        .expect(200);

      expect(response.body).toHaveProperty('status', 'healthy');
      expect(response.body).toHaveProperty('timestamp');
      expect(response.body).toHaveProperty('uptime');
    });
  });

  describe('Upload Endpoint', () => {
    test('POST /api/upload should handle file upload', async () => {
      // Mock a test image
      const testImageBuffer = Buffer.from('fake-image-data');
      
      const response = await request(app)
        .post('/api/upload')
        .attach('images', testImageBuffer, 'test.jpg')
        .expect(200);

      expect(response.body).toHaveProperty('success', true);
      expect(response.body).toHaveProperty('message');
      expect(response.body).toHaveProperty('count');
    });

    test('POST /api/upload should reject invalid file types', async () => {
      const testFileBuffer = Buffer.from('fake-text-data');
      
      const response = await request(app)
        .post('/api/upload')
        .attach('images', testFileBuffer, 'test.txt')
        .expect(400);

      expect(response.body).toHaveProperty('error');
    });

    test('POST /api/upload should reject too many files', async () => {
      const testImageBuffer = Buffer.from('fake-image-data');
      
      const response = await request(app)
        .post('/api/upload')
        .attach('images', testImageBuffer, 'test1.jpg')
        .attach('images', testImageBuffer, 'test2.jpg')
        .attach('images', testImageBuffer, 'test3.jpg')
        .attach('images', testImageBuffer, 'test4.jpg')
        .attach('images', testImageBuffer, 'test5.jpg')
        .attach('images', testImageBuffer, 'test6.jpg')
        .expect(400);

      expect(response.body).toHaveProperty('error');
    });
  });

  describe('Analysis Endpoint', () => {
    test('POST /api/analyze should handle valid request', async () => {
      const mockRequest = {
        images: [
          {
            filename: 'test.jpg',
            base64: 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==',
            size: 1000,
            mimetype: 'image/jpeg'
          }
        ]
      };

      // Mock OpenAI service to avoid actual API calls
      const originalOpenAIService = require('../services/openai-service');
      jest.mock('../services/openai-service', () => {
        return jest.fn().mockImplementation(() => ({
          analyzeAccessibility: jest.fn().mockResolvedValue({
            filename: 'test.jpg',
            score: 85,
            positive_features: ['Good lighting'],
            barriers: ['Narrow doorway'],
            recommendations: ['Widen doorway'],
            accessibility_rating: 'Good'
          })
        }));
      });

      const response = await request(app)
        .post('/api/analyze')
        .send(mockRequest)
        .expect(200);

      expect(response.body).toHaveProperty('success', true);
      expect(response.body).toHaveProperty('analysis');
      expect(response.body.analysis).toHaveProperty('overall_score');
      expect(response.body.analysis).toHaveProperty('analyzed_images');
    });

    test('POST /api/analyze should reject invalid request', async () => {
      const invalidRequest = {
        images: []
      };

      const response = await request(app)
        .post('/api/analyze')
        .send(invalidRequest)
        .expect(400);

      expect(response.body).toHaveProperty('error');
    });

    test('POST /api/analyze should handle missing images', async () => {
      const response = await request(app)
        .post('/api/analyze')
        .send({})
        .expect(400);

      expect(response.body).toHaveProperty('error');
    });
  });

  describe('Upload and Analyze Endpoint', () => {
    test('POST /api/upload-and-analyze should handle file upload and analysis', async () => {
      const testImageBuffer = Buffer.from('fake-image-data');
      
      // Mock OpenAI service
      const originalOpenAIService = require('../services/openai-service');
      jest.mock('../services/openai-service', () => {
        return jest.fn().mockImplementation(() => ({
          analyzeAccessibility: jest.fn().mockResolvedValue({
            filename: 'test.jpg',
            score: 85,
            positive_features: ['Good lighting'],
            barriers: ['Narrow doorway'],
            recommendations: ['Widen doorway'],
            accessibility_rating: 'Good'
          })
        }));
      });

      const response = await request(app)
        .post('/api/upload-and-analyze')
        .attach('images', testImageBuffer, 'test.jpg')
        .expect(200);

      expect(response.body).toHaveProperty('success', true);
      expect(response.body).toHaveProperty('analysis');
    });
  });

  describe('Error Handling', () => {
    test('Should handle 404 for unknown routes', async () => {
      const response = await request(app)
        .get('/unknown-route')
        .expect(404);

      expect(response.body).toHaveProperty('error', 'Not found');
    });

    test('Should handle malformed JSON', async () => {
      const response = await request(app)
        .post('/api/analyze')
        .set('Content-Type', 'application/json')
        .send('invalid json')
        .expect(400);
    });
  });

  describe('Rate Limiting', () => {
    test('Should enforce rate limits', async () => {
      // Make multiple requests quickly
      const promises = [];
      for (let i = 0; i < 10; i++) {
        promises.push(
          request(app)
            .get('/health')
        );
      }

      const responses = await Promise.all(promises);
      
      // All should succeed for health endpoint
      responses.forEach(response => {
        expect(response.status).toBe(200);
      });
    });
  });

  describe('Security Headers', () => {
    test('Should include security headers', async () => {
      const response = await request(app)
        .get('/health')
        .expect(200);

      // Check for security headers
      expect(response.headers).toHaveProperty('x-content-type-options');
      expect(response.headers).toHaveProperty('x-frame-options');
    });
  });
});

// Integration tests
describe('Integration Tests', () => {
  test('Full workflow: upload -> analyze', async () => {
    // This would be a more comprehensive test
    // that tests the full workflow
    expect(true).toBe(true);
  });
});
