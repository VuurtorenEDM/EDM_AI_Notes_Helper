import openai
import re

openai.api_key = "YOUR_API_KEY"

def summarize_text(text):
    prompt = f"Summarize the following study notes into 3-4 concise bullet points:\n\n{text}"
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response["choices"][0]["message"]["content"]

def generate_quiz(text):
    prompt = (
        "Generate 3 multiple-choice questions based on the following text. "
        "Each question should have 1 correct answer and 3 wrong options. "
        "Format as: Q1: [question]\\nA) ...\\nB) ...\\nC) ...\\nD) ...\\nAnswer: [letter]\n\n"
        f"{text}"
    )
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response["choices"][0]["message"]["content"]
