from openai import OpenAI
import os

SECRET_KEY = os.getenv('OPEN_AI_SECRET_KEY', 'defaultsecretkey')

client = OpenAI(api_key=SECRET_KEY)


def generate_response(role, content):
    
    completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
      {"role": "system", "content": role},
      {"role": "user", "content": content}
    ],
    max_tokens=1000
    )
    return completion.choices[0].message.content


def get_embedding(message):
    response = client.embeddings.create(
        input=message,
        model="text-embedding-ada-002"
    )

    return response.data[0].embedding