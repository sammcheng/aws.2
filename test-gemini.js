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
