import ollama

print("=" * 60)
print("🎵 Testing Ollama Connection")
print("=" * 60)

# Test simple chat
response = ollama.chat(
    model='llama3.1:8b',
    messages=[
        {'role': 'user', 'content': 'Say "MAESTRO is alive!" and nothing else.'}
    ]
)

print("\n✅ Response from AI:")
print(response['message']['content'])
print("\n" + "=" * 60)
print("🎉 SUCCESS! Ollama is working with Python!")
print("=" * 60)