/**
 * OpenRouter Vision Service for Accessibility Analysis
 * Uses OpenRouter API with GPT-4o vision for computer vision analysis
 */

const OpenAI = require('openai');
const winston = require('winston');

class OpenRouterVisionService {
    constructor() {
        this.openaiClient = new OpenAI({
            apiKey: process.env.OPENROUTER_API_KEY || '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',
            baseURL: 'https://openrouter.ai/api/v1',
            defaultHeaders: {
                'HTTP-Referer': 'http://localhost:3000',
                'X-Title': 'Accessibility Checker'
            }
        });
        
        this.logger = winston.createLogger({
            level: 'info',
            format: winston.format.combine(
                winston.format.timestamp(),
                winston.format.json()
            ),
            transports: [
                new winston.transports.Console()
            ]
        });
    }

    async analyzeAccessibility(base64Image, filename) {
        try {
            this.logger.info('Starting OpenRouter vision analysis', { filename });

            const prompt = `Analyze this image for accessibility features and barriers. Look for:

ACCESSIBILITY FEATURES:
- Wide doorways (32+ inches)
- Ramps and accessible entrances
- Grab bars in bathrooms
- Accessible parking spaces
- Elevators or ground floor access
- Good lighting
- Clear pathways (36+ inches wide)
- Accessible counter heights
- Non-slip surfaces
- Emergency accessibility features

BARRIERS:
- Narrow doorways (<32 inches)
- Steps without ramps
- High thresholds
- Narrow hallways
- Poor lighting
- Slippery surfaces
- Inaccessible bathrooms
- High counter heights
- Cluttered pathways

Please provide:
1. A list of detected accessibility features
2. A list of detected barriers
3. An overall accessibility score (0-100)
4. Specific recommendations for improvement

Format your response as JSON with this structure:
{
  "accessibility_features": ["feature1", "feature2"],
  "barriers": ["barrier1", "barrier2"],
  "score": 75,
  "recommendations": ["recommendation1", "recommendation2"]
}`;

            const response = await this.openaiClient.chat.completions.create({
                model: "openai/gpt-4o",
                messages: [
                    {
                        role: "user",
                        content: [
                            {
                                type: "text",
                                text: prompt
                            },
                            {
                                type: "image_url",
                                image_url: {
                                    url: `data:image/jpeg;base64,${base64Image}`
                                }
                            }
                        ]
                    }
                ],
                max_tokens: 2000,
                temperature: 0.3
            });
            
            const analysisText = response.choices[0].message.content;
            
            // Try to parse JSON response
            let analysis;
            try {
                analysis = JSON.parse(analysisText);
            } catch (parseError) {
                // If JSON parsing fails, extract information from text
                analysis = this.parseTextResponse(analysisText);
            }

            const result = {
                score: analysis.score || 50,
                analysis: {
                    overall_score: analysis.score || 50,
                    accessibility_features: analysis.accessibility_features || [],
                    barriers: analysis.barriers || [],
                    recommendations: analysis.recommendations || [],
                    confidence: 0.9,
                    analysis_method: 'openrouter_vision'
                },
                metadata: {
                    filename: filename,
                    timestamp: new Date().toISOString(),
                    model_used: 'gpt-4o-vision',
                    processing_time_ms: 2000
                }
            };

            this.logger.info('OpenRouter vision analysis completed', { 
                filename, 
                score: result.score 
            });

            return result;

        } catch (error) {
            this.logger.error('OpenRouter vision analysis failed', { 
                filename, 
                error: error.message 
            });
            throw new Error(`OpenRouter vision analysis failed: ${error.message}`);
        }
    }

    parseTextResponse(text) {
        // Extract information from text response when JSON parsing fails
        const features = [];
        const barriers = [];
        const recommendations = [];
        let score = 50;

        // Look for score patterns
        const scoreMatch = text.match(/score[:\s]*(\d+)/i);
        if (scoreMatch) {
            score = parseInt(scoreMatch[1]);
        }

        // Look for features
        const featureMatches = text.match(/features?[:\s]*([^\n]+)/gi);
        if (featureMatches) {
            featureMatches.forEach(match => {
                const items = match.split(/[,\n]/).map(item => item.trim()).filter(item => item);
                features.push(...items);
            });
        }

        // Look for barriers
        const barrierMatches = text.match(/barriers?[:\s]*([^\n]+)/gi);
        if (barrierMatches) {
            barrierMatches.forEach(match => {
                const items = match.split(/[,\n]/).map(item => item.trim()).filter(item => item);
                barriers.push(...items);
            });
        }

        // Look for recommendations
        const recMatches = text.match(/recommendations?[:\s]*([^\n]+)/gi);
        if (recMatches) {
            recMatches.forEach(match => {
                const items = match.split(/[,\n]/).map(item => item.trim()).filter(item => item);
                recommendations.push(...items);
            });
        }

        return {
            score: Math.max(0, Math.min(100, score)),
            accessibility_features: features.slice(0, 10), // Limit to 10 features
            barriers: barriers.slice(0, 10), // Limit to 10 barriers
            recommendations: recommendations.slice(0, 10) // Limit to 10 recommendations
        };
    }
}

module.exports = OpenRouterVisionService;