/**
 * AWS Rekognition Service for Object Detection
 * Detects accessibility-related objects in property images
 */

const { RekognitionClient, DetectLabelsCommand } = require('@aws-sdk/client-rekognition');
const { fromEnv } = require('@aws-sdk/credential-providers');
const winston = require('winston');

class RekognitionService {
    constructor() {
        this.rekognitionClient = new RekognitionClient({
            region: process.env.AWS_DEFAULT_REGION || 'us-east-1',
            credentials: {
                accessKeyId: process.env.REKOGNITION_ACCESS_KEY_ID || 'AKIAZCFIPEU2AFQVL4OF',
                secretAccessKey: process.env.REKOGNITION_SECRET_ACCESS_KEY || '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'
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

        // Define specific accessibility features to detect
        this.accessibilityObjects = {
            // Positive accessibility features
            positive: [
                'Ramp', 'Handrail', 'Grab Bar', 'Wheelchair Accessible', 'Wide Doorway',
                'Elevator', 'Lift', 'Accessible Bathroom', 'Accessible Kitchen',
                'Good Lighting', 'Clear Pathway', 'Wide Hallway', 'Accessible Entrance',
                'Non-slip Surface', 'Safety Rail', 'Emergency Exit', 'Fire Extinguisher',
                'Smoke Detector', 'Accessible Counter', 'Wide Corridor', 'Level Surface'
            ],
            // Barriers and obstacles
            negative: [
                'Step', 'Stair', 'Narrow Doorway', 'Threshold', 'Barrier', 'Obstacle',
                'Cluttered', 'Poor Lighting', 'Narrow Hallway', 'Inaccessible',
                'High Counter', 'Narrow Path', 'Trip Hazard', 'Slippery Surface',
                'Steep Stair', 'Narrow Stair', 'High Step', 'Uneven Surface',
                'Cluttered Hallway', 'Narrow Corridor', 'High Threshold'
            ],
            // Safety features
            safety: [
                'Fire Extinguisher', 'Smoke Detector', 'Emergency Exit', 'Safety Rail',
                'Non-slip Surface', 'Good Lighting', 'Clear Exit', 'Emergency Equipment',
                'Exit Sign', 'Emergency Lighting', 'Safety Equipment'
            ],
            // Specific measurements and features to analyze
            measurements: [
                'Doorway Width', 'Hallway Width', 'Stair Width', 'Ramp Width',
                'Counter Height', 'Threshold Height', 'Step Height', 'Ramp Slope'
            ],
            // Room types for accessibility assessment
            rooms: [
                'Bathroom', 'Kitchen', 'Bedroom', 'Living Room', 'Hallway', 'Entrance',
                'Staircase', 'Basement', 'Attic', 'Garage', 'Laundry Room'
            ]
        };
    }

    /**
     * Analyze image for accessibility features using Rekognition
     * @param {string} base64Image - Base64 encoded image
     * @param {string} filename - Image filename
     * @returns {Promise<Object>} Analysis results
     */
    async analyzeAccessibility(base64Image, filename) {
        try {
            this.logger.info('Starting Rekognition analysis', { filename });

            // Convert base64 to buffer
            const imageBuffer = Buffer.from(base64Image, 'base64');

            const input = {
                Image: {
                    Bytes: imageBuffer
                },
                MaxLabels: 50,
                MinConfidence: 70
            };

            const command = new DetectLabelsCommand(input);
            const response = await this.rekognitionClient.send(command);

            // Process the labels
            const analysis = this.processLabels(response.Labels, filename);

            this.logger.info('Rekognition analysis completed', { 
                filename, 
                labelsFound: response.Labels.length,
                accessibilityScore: analysis.score
            });

            return analysis;

        } catch (error) {
            this.logger.error('Rekognition analysis failed', { 
                filename, 
                error: error.message 
            });
            throw new Error(`Rekognition analysis failed: ${error.message}`);
        }
    }

    generateMockLabels(filename) {
        // Generate realistic mock labels for testing
        const mockLabels = [
            { Name: 'Room', Confidence: 95.5 },
            { Name: 'Furniture', Confidence: 88.2 },
            { Name: 'Door', Confidence: 92.1 },
            { Name: 'Floor', Confidence: 96.8 }
        ];

        // Add some accessibility-related features randomly
        const accessibilityFeatures = [
            { Name: 'Ramp', Confidence: 85.3 },
            { Name: 'Handrail', Confidence: 78.9 },
            { Name: 'Wide Doorway', Confidence: 82.4 },
            { Name: 'Accessible Bathroom', Confidence: 76.1 },
            { Name: 'Elevator', Confidence: 89.2 },
            { Name: 'Good Lighting', Confidence: 91.5 },
            { Name: 'Clear Pathway', Confidence: 87.3 }
        ];

        // Add some barriers randomly
        const barriers = [
            { Name: 'Stairs', Confidence: 89.2 },
            { Name: 'Narrow Doorway', Confidence: 74.6 },
            { Name: 'High Threshold', Confidence: 81.3 },
            { Name: 'Step', Confidence: 86.7 },
            { Name: 'Narrow Hallway', Confidence: 79.4 }
        ];

        // Randomly add features or barriers based on filename
        const hash = filename.split('').reduce((a, b) => {
            a = ((a << 5) - a) + b.charCodeAt(0);
            return a & a;
        }, 0);

        // Add 2-4 accessibility features
        const numFeatures = 2 + (Math.abs(hash) % 3);
        for (let i = 0; i < numFeatures; i++) {
            const feature = accessibilityFeatures[Math.abs(hash + i) % accessibilityFeatures.length];
            mockLabels.push(feature);
        }

        // Add 1-2 barriers
        const numBarriers = 1 + (Math.abs(hash + 10) % 2);
        for (let i = 0; i < numBarriers; i++) {
            const barrier = barriers[Math.abs(hash + i + 20) % barriers.length];
            mockLabels.push(barrier);
        }

        return mockLabels;
    }

    /**
     * Process Rekognition labels and categorize them
     * @param {Array} labels - Labels from Rekognition
     * @param {string} filename - Image filename
     * @returns {Object} Processed analysis
     */
    processLabels(labels, filename) {
        const detectedObjects = {
            positive: [],
            negative: [],
            safety: [],
            measurements: [],
            rooms: [],
            general: []
        };

        let accessibilityScore = 50; // Base score
        const redFlags = [];
        const positiveFeatures = [];
        const measurements = [];
        const roomAnalysis = [];

        labels.forEach(label => {
            const name = label.Name;
            const confidence = label.Confidence;
            
            // Categorize the detected object
            const category = this.categorizeObject(name);
            detectedObjects[category].push({
                name: name,
                confidence: confidence
            });

            // Detailed scoring based on specific features
            if (category === 'positive') {
                const scoreBoost = this.getPositiveFeatureScore(name);
                accessibilityScore += scoreBoost;
                positiveFeatures.push(`${name} (${Math.round(confidence)}% confidence) - +${scoreBoost} points`);
            } else if (category === 'negative') {
                const scorePenalty = this.getNegativeFeaturePenalty(name);
                accessibilityScore -= scorePenalty;
                redFlags.push(`${name} - Barrier (${Math.round(confidence)}% confidence) - -${scorePenalty} points`);
            } else if (category === 'safety') {
                accessibilityScore += 8;
                positiveFeatures.push(`${name} - Safety feature (${Math.round(confidence)}% confidence) - +8 points`);
            } else if (category === 'measurements') {
                measurements.push(`${name} detected (${Math.round(confidence)}% confidence)`);
            } else if (category === 'rooms') {
                roomAnalysis.push(`${name} - Room type (${Math.round(confidence)}% confidence)`);
            }
        });

        // Ensure score is within 0-100 range
        accessibilityScore = Math.max(0, Math.min(100, accessibilityScore));

        // Generate detailed recommendations based on findings
        const recommendations = this.generateDetailedRecommendations(detectedObjects, redFlags, measurements, roomAnalysis);

        return {
            filename,
            score: Math.round(accessibilityScore),
            detectedObjects,
            positiveFeatures,
            redFlags,
            measurements,
            roomAnalysis,
            recommendations,
            totalLabels: labels.length,
            analysis: {
                accessibilityRating: this.getRatingFromScore(accessibilityScore),
                confidence: this.calculateOverallConfidence(labels),
                keyFindings: this.getDetailedFindings(detectedObjects, measurements, roomAnalysis),
                specificFeatures: this.analyzeSpecificFeatures(detectedObjects)
            }
        };
    }

    /**
     * Categorize detected objects into accessibility categories
     * @param {string} objectName - Name of detected object
     * @returns {string} Category (positive, negative, safety, measurements, rooms, general)
     */
    categorizeObject(objectName) {
        const name = objectName.toLowerCase();

        // Check for positive accessibility features
        for (const positive of this.accessibilityObjects.positive) {
            if (name.includes(positive.toLowerCase())) {
                return 'positive';
            }
        }

        // Check for negative barriers
        for (const negative of this.accessibilityObjects.negative) {
            if (name.includes(negative.toLowerCase())) {
                return 'negative';
            }
        }

        // Check for safety features
        for (const safety of this.accessibilityObjects.safety) {
            if (name.includes(safety.toLowerCase())) {
                return 'safety';
            }
        }

        // Check for measurement-related features
        for (const measurement of this.accessibilityObjects.measurements) {
            if (name.includes(measurement.toLowerCase())) {
                return 'measurements';
            }
        }

        // Check for room types
        for (const room of this.accessibilityObjects.rooms) {
            if (name.includes(room.toLowerCase())) {
                return 'rooms';
            }
        }

        return 'general';
    }

    /**
     * Get score boost for positive accessibility features
     * @param {string} featureName - Name of the feature
     * @returns {number} Score boost
     */
    getPositiveFeatureScore(featureName) {
        const name = featureName.toLowerCase();
        
        // High-impact accessibility features
        if (name.includes('ramp') || name.includes('elevator') || name.includes('lift')) {
            return 15; // Major accessibility feature
        }
        if (name.includes('wide doorway') || name.includes('wide hallway') || name.includes('accessible entrance')) {
            return 12; // Important for wheelchair access
        }
        if (name.includes('grab bar') || name.includes('handrail') || name.includes('safety rail')) {
            return 10; // Safety and support features
        }
        if (name.includes('accessible bathroom') || name.includes('accessible kitchen')) {
            return 8; // Room accessibility
        }
        if (name.includes('good lighting') || name.includes('clear pathway')) {
            return 6; // General accessibility improvements
        }
        
        return 5; // Default positive feature score
    }

    /**
     * Get score penalty for negative barriers
     * @param {string} barrierName - Name of the barrier
     * @returns {number} Score penalty
     */
    getNegativeFeaturePenalty(barrierName) {
        const name = barrierName.toLowerCase();
        
        // High-impact barriers
        if (name.includes('steep stair') || name.includes('narrow stair') || name.includes('high step')) {
            return 20; // Major accessibility barrier
        }
        if (name.includes('narrow doorway') || name.includes('narrow hallway') || name.includes('narrow corridor')) {
            return 15; // Significant barrier to wheelchair access
        }
        if (name.includes('high threshold') || name.includes('step') || name.includes('stair')) {
            return 12; // Common accessibility barriers
        }
        if (name.includes('trip hazard') || name.includes('slippery surface') || name.includes('uneven surface')) {
            return 10; // Safety concerns
        }
        if (name.includes('cluttered') || name.includes('poor lighting')) {
            return 8; // General accessibility issues
        }
        
        return 5; // Default barrier penalty
    }

    /**
     * Generate detailed recommendations based on detected objects
     * @param {Object} detectedObjects - Categorized objects
     * @param {Array} redFlags - List of red flags
     * @param {Array} measurements - Detected measurements
     * @param {Array} roomAnalysis - Room analysis
     * @returns {Array} Detailed recommendations
     */
    generateDetailedRecommendations(detectedObjects, redFlags, measurements, roomAnalysis) {
        const recommendations = [];

        // Stair and step recommendations
        if (redFlags.some(flag => flag.includes('Step') || flag.includes('Stair'))) {
            recommendations.push('🚨 CRITICAL: Install ramp for wheelchair access (ADA requires 1:12 slope)');
            recommendations.push('Consider stair lift or elevator for multi-level access');
        }

        // Doorway and hallway width recommendations
        if (redFlags.some(flag => flag.includes('Narrow'))) {
            recommendations.push('🚨 CRITICAL: Widen doorways to minimum 32 inches (ADA standard)');
            recommendations.push('Expand hallways to minimum 36 inches width');
            recommendations.push('Remove or relocate furniture blocking pathways');
        }

        // Lighting recommendations
        if (redFlags.some(flag => flag.includes('Poor Lighting'))) {
            recommendations.push('💡 Install brighter lighting throughout the property');
            recommendations.push('Add motion-activated lights in hallways and bathrooms');
            recommendations.push('Ensure emergency lighting is functional');
        }

        // Safety recommendations
        if (detectedObjects.safety.length === 0) {
            recommendations.push('🛡️ Install smoke detectors in all rooms');
            recommendations.push('Add fire extinguisher in kitchen and near exits');
            recommendations.push('Ensure emergency exits are clearly marked');
        }

        // Bathroom accessibility
        if (roomAnalysis.some(room => room.includes('Bathroom'))) {
            if (!detectedObjects.positive.some(obj => obj.name.includes('Grab Bar'))) {
                recommendations.push('🚿 Install grab bars in bathroom (near toilet and shower)');
            }
            if (!detectedObjects.positive.some(obj => obj.name.includes('Accessible'))) {
                recommendations.push('🚿 Consider accessible shower with no threshold');
            }
        }

        // Kitchen accessibility
        if (roomAnalysis.some(room => room.includes('Kitchen'))) {
            if (redFlags.some(flag => flag.includes('High Counter'))) {
                recommendations.push('🍳 Lower counter height or add adjustable counter sections');
            }
            recommendations.push('🍳 Ensure clear pathways around kitchen island');
        }

        // General accessibility improvements
        if (detectedObjects.positive.length === 0) {
            recommendations.push('♿ Add universal design features throughout the home');
            recommendations.push('Install lever-style door handles (easier than knobs)');
            recommendations.push('Ensure all rooms are accessible from main living areas');
        }

        return recommendations;
    }

    /**
     * Get detailed findings from analysis
     * @param {Object} detectedObjects - Categorized objects
     * @param {Array} measurements - Detected measurements
     * @param {Array} roomAnalysis - Room analysis
     * @returns {Array} Detailed findings
     */
    getDetailedFindings(detectedObjects, measurements, roomAnalysis) {
        const findings = [];

        if (detectedObjects.positive.length > 0) {
            findings.push(`✅ Found ${detectedObjects.positive.length} positive accessibility features`);
        }

        if (detectedObjects.negative.length > 0) {
            findings.push(`⚠️ Identified ${detectedObjects.negative.length} potential barriers`);
        }

        if (detectedObjects.safety.length > 0) {
            findings.push(`🛡️ Detected ${detectedObjects.safety.length} safety features`);
        }

        if (measurements.length > 0) {
            findings.push(`📏 Found ${measurements.length} measurable accessibility features`);
        }

        if (roomAnalysis.length > 0) {
            findings.push(`🏠 Analyzed ${roomAnalysis.length} room types for accessibility`);
        }

        return findings;
    }

    /**
     * Analyze specific accessibility features
     * @param {Object} detectedObjects - Categorized objects
     * @returns {Object} Specific feature analysis
     */
    analyzeSpecificFeatures(detectedObjects) {
        const analysis = {
            wheelchairAccess: false,
            safetyFeatures: false,
            lightingQuality: false,
            pathwayClarity: false,
            bathroomAccessibility: false,
            kitchenAccessibility: false
        };

        // Check for wheelchair accessibility features
        const wheelchairFeatures = ['ramp', 'elevator', 'lift', 'wide doorway', 'wide hallway'];
        analysis.wheelchairAccess = detectedObjects.positive.some(obj => 
            wheelchairFeatures.some(feature => obj.name.toLowerCase().includes(feature))
        );

        // Check for safety features
        const safetyFeatures = ['smoke detector', 'fire extinguisher', 'emergency exit', 'safety rail'];
        analysis.safetyFeatures = detectedObjects.safety.some(obj => 
            safetyFeatures.some(feature => obj.name.toLowerCase().includes(feature))
        );

        // Check for lighting quality
        analysis.lightingQuality = detectedObjects.positive.some(obj => 
            obj.name.toLowerCase().includes('good lighting')
        );

        // Check for pathway clarity
        analysis.pathwayClarity = detectedObjects.positive.some(obj => 
            obj.name.toLowerCase().includes('clear pathway')
        );

        return analysis;
    }

    /**
     * Get accessibility rating from score
     * @param {number} score - Accessibility score
     * @returns {string} Rating
     */
    getRatingFromScore(score) {
        if (score >= 90) return 'Excellent';
        if (score >= 80) return 'Good';
        if (score >= 70) return 'Fair';
        if (score >= 60) return 'Poor';
        return 'Very Poor';
    }

    /**
     * Calculate overall confidence from all labels
     * @param {Array} labels - All detected labels
     * @returns {number} Average confidence
     */
    calculateOverallConfidence(labels) {
        if (labels.length === 0) return 0;
        const totalConfidence = labels.reduce((sum, label) => sum + label.Confidence, 0);
        return Math.round(totalConfidence / labels.length);
    }

    /**
     * Get key findings from detected objects
     * @param {Object} detectedObjects - Categorized objects
     * @returns {Array} Key findings
     */
    getKeyFindings(detectedObjects) {
        const findings = [];

        if (detectedObjects.positive.length > 0) {
            findings.push(`Found ${detectedObjects.positive.length} positive accessibility features`);
        }

        if (detectedObjects.negative.length > 0) {
            findings.push(`Identified ${detectedObjects.negative.length} potential barriers`);
        }

        if (detectedObjects.safety.length > 0) {
            findings.push(`Detected ${detectedObjects.safety.length} safety features`);
        }

        return findings;
    }
}

module.exports = RekognitionService;
