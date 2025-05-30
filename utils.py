import os

from flask.cli import load_dotenv
from openai import OpenAI

load_dotenv()

def llm_chat(prompt):
    llm_base_url = os.environ.get('LLM_BASE_URL', 'https://api.deepseek.com/v1')
    llm_model_name = os.environ.get('LLM_MODEL_NAME', 'deepseek-chat')
    llm_api_key = os.environ.get('LLM_API_KEY', '')

    messages = []
    messages.append({"role": "user", "content": prompt})

    data = {
        "model": llm_model_name,
        "messages": messages,
        "stream": False
    }
    print(data)
    try:
        client = OpenAI(
            base_url=llm_base_url,
            api_key=llm_api_key,
        )

        chat_completion = client.chat.completions.create(**data)
        return chat_completion.choices[0].message.content

    except Exception as e:
        print(e)

    return ''


