const { GoogleGenerativeAI } = require('@google/generative-ai');

async function testGeminiAPI() {
    try {
        const apiKey = process.env.OPENROUTER_API_KEY;
        if (!apiKey) {
            throw new Error('OPENROUTER_API_KEY is not set');
        }
        console.log('Testing Gemini API with environment-provided key...');
        
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
