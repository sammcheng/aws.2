const { GoogleGenerativeAI } = require('@google/generative-ai');

async function testGeminiAPI() {
    try {
        const apiKey = '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';
        console.log('Testing Gemini API with key:', apiKey.substring(0, 20) + '...');
        
        const genAI = new GoogleGenerativeAI(apiKey);
        const model = genAI.getGenerativeModel({ model: "gemini-pro" });
        
        const result = await model.generateContent("Hello, are you working?");
        const response = await result.response;
        const text = response.text();
        
        console.log('✅ Gemini API is working! Response:', text);
        return true;
    } catch (error) {
        console.log('❌ Gemini API failed:', error.message);
        return false;
    }
}

testGeminiAPI();
