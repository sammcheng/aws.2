const OpenAI = require('openai');

async function testOpenRouterAPI() {
    try {
        const apiKey = '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';
        console.log('Testing OpenRouter API with key:', apiKey.substring(0, 20) + '...');
        
        const openai = new OpenAI({
            apiKey: apiKey,
            baseURL: 'https://openrouter.ai/api/v1',
            defaultHeaders: {
                'HTTP-Referer': 'http://localhost:3000',
                'X-Title': 'Accessibility Checker'
            }
        });
        
        const response = await openai.chat.completions.create({
            model: "openai/gpt-4o",
            messages: [
                {
                    role: "user",
                    content: "Hello, are you working? Please respond with a short message."
                }
            ],
            max_tokens: 100
        });
        
        const text = response.choices[0].message.content;
        console.log('✅ OpenRouter API is working! Response:', text);
        return true;
    } catch (error) {
        console.log('❌ OpenRouter API failed:', error.message);
        return false;
    }
}

testOpenRouterAPI();
