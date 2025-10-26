const Groq = require('groq-sdk');

async function testGroqAPI() {
    try {
        const apiKey = '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';
        console.log('Testing Groq API with key:', apiKey.substring(0, 20) + '...');
        
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
