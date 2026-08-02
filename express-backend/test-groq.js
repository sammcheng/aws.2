const Groq = require('groq-sdk');

async function testGroqAPI() {
    try {
        const apiKey = process.env.GROQ_API_KEY;
        if (!apiKey) {
            throw new Error('GROQ_API_KEY is not set');
        }
        console.log('Testing Groq API with environment-provided key...');
        
        const groq = new Groq({
            apiKey: apiKey,
        });
        
        const chatCompletion = await groq.chat.completions.create({
            messages: [
                {
                    role: "user",
                    content: "Hello, are you working?"
                }
            ],
            model: "llama-3.1-70b-versatile",
        });
        
        const response = chatCompletion.choices[0]?.message?.content || "";
        console.log('✅ Groq API is working! Response:', response);
        return true;
    } catch (error) {
        console.log('❌ Groq API failed:', error.message);
        return false;
    }
}

testGroqAPI();
