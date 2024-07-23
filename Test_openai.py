import openai

system_content = "You are a travel agent. Be descriptive and helpful."
user_content = "Tell me about San Francisco"

client = openai.OpenAI(
    api_key=" 7ec5be264f854263a7b94e36b17a2967",
    base_url="https://api.aimlapi.com",
)

chat_completion = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ],
    temperature=0.7,
    max_tokens=128,
)

response = chat_completion.choices[0].message.content
print("AI/ML API:\n", response)