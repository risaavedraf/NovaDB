from google import genai
from dotenv import load_dotenv

load_dotenv()
client = genai.Client()

print("Buscando todos los modelos de embedding disponibles...")
for m in client.models.list():
    if "embedding" in m.name.lower():
        print(m.name)
