import os
import base64
import json
from groq import Groq
from dotenv import load_dotenv

class ExpenseAgent:
    def __init__(self):
        load_dotenv()
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "meta-llama/llama-4-scout-17b-16e-instruct"

        with open("context.txt", "r") as f:
            self.system_prompt = f.read()

        with open("prompt.txt", "r") as f:
            self.user_prompt = f.read()

    def extract_from_bytes(self, image_bytes: bytes, media_type: str) -> dict:
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")

        response = self.client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": self.system_prompt},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{image_b64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": self.user_prompt
                        }
                    ]
                }
            ]
        )

        return json.loads(response.choices[0].message.content)

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage : python backend.py <chemin_image>")
        sys.exit(1)

    image_path = sys.argv[1]
    media_type = "image/jpeg"

    if image_path.endswith(".png"):
        media_type = "image/png"
    elif image_path.endswith(".webp"):
        media_type = "image/webp"

    with open(image_path, "rb") as f:
        image_bytes = f.read()

    agent = ExpenseAgent()
    result = agent.extract_from_bytes(image_bytes, media_type)

    print(json.dumps(result, indent=2, ensure_ascii=False))