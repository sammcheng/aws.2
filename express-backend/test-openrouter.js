const OpenAI = require('openai');

async function testOpenRouterAPI() {
    try {
        const apiKey = process.env.OPENROUTER_API_KEY;
        if (!apiKey) {
            throw new Error('OPENROUTER_API_KEY is not set');
        }
        console.log('Testing OpenRouter API with environment-provided key...');
        
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
