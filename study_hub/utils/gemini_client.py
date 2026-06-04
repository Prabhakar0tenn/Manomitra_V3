import logging
import json
import re
import google.generativeai as genai
from config import settings

logger = logging.getLogger("study_hub.gemini")

# Initialize Gemini Client
try:
    genai.configure(api_key=settings.GEMINI_API_KEY)
    logger.info("Gemini client successfully configured.")
except Exception as e:
    logger.error(f"Error configuring Gemini client: {e}")


def clean_json_response(raw_text: str) -> str:
    """Helper to remove markdown backticks (like ```json ... ```) from LLM output."""
    cleaned = raw_text.strip()
    # Remove leading ```json or ```
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    # Remove trailing ```
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def answer_from_context(question: str, context: str, doc_name: str) -> dict:
    """
    Asks Gemini to answer the question using ONLY the provided document context.
    """
    truncated_context = context[:settings.MAX_CONTEXT_CHARS]

    prompt = f"""You are a study assistant. You must answer the question using ONLY the document text provided below.

STRICT RULES:
- If the answer is clearly present in the text, answer it accurately
- If the answer is NOT in the text, respond with exactly: "This information is not available in the uploaded document."
- Do NOT use any external knowledge
- Do NOT make up information
- Keep answer concise and clear
- After your answer, extract 2-3 most relevant sentences from the text that support your answer (label them as "Source excerpts:")

Document: {doc_name}

Document Text:
{truncated_context}

Question: {question}"""

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")  # ✅ Free tier available

        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.2
            )
        )

        raw_answer = response.text.strip()

        match = re.split(r"(?i)source\s+excerpts\s*:", raw_answer)

        if len(match) > 1:
            answer = match[0].strip()
            excerpts_part = match[1].strip()

            sources = []

            for line in excerpts_part.splitlines():
                line = line.strip()

                if not line:
                    continue

                cleaned = re.sub(
                    r'^[\-\*\+\d\.\s"\'`\-]+',
                    '',
                    line
                ).strip()

                cleaned = cleaned.strip('"\'`')

                if cleaned:
                    sources.append(cleaned)

        else:
            answer = raw_answer
            sources = []

            if "This information is not available in the uploaded document" in answer:
                sources = []

        return {
            "answer": answer,
            "sources": sources,
            "document_name": doc_name
        }

    except Exception as e:
        logger.exception("FULL GEMINI ERROR")

        return {
            "answer": str(e),
            "sources": [],
            "document_name": doc_name
        }


def generate_notes(context: str, doc_name: str, detail_level: str) -> dict:
    """
    Generates structured study notes from the document context.
    """
    truncated_context = context[:settings.MAX_CONTEXT_CHARS]

    prompt = f"""You are a study assistant. Generate structured study notes from the document text below. Use ONLY information present in the text.

Create:
1. A brief summary (3-4 sentences)
2. Key concepts list (bullet points, each with one line explanation)
3. Important bullet points (main ideas from the document)

Detail level: {detail_level} (brief = 5-8 bullets, detailed = 15-20 bullets)

Document: {doc_name}

Document Text:
{truncated_context}

Return response in this EXACT JSON format:
{{
  "summary": "...",
  "key_concepts": ["concept1", "concept2", ...],
  "bullet_points": ["point1", "point2", ...]
}}

Return ONLY the JSON, no other text."""

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")  # ✅ Free tier available

        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.2
            )
        )

        cleaned_text = clean_json_response(response.text)
        data = json.loads(cleaned_text)

        return {
            "document_name": doc_name,
            "summary": data.get("summary", ""),
            "key_concepts": data.get("key_concepts", []),
            "bullet_points": data.get("bullet_points", [])
        }

    except Exception as e:
        logger.exception("FULL GEMINI ERROR")

        return {
            "document_name": doc_name,
            "summary": str(e),
            "key_concepts": [],
            "bullet_points": []
        }


def generate_quiz(context: str, doc_name: str, num_questions: int, difficulty: str) -> list:
    """
    Generates multiple choice questions (MCQs) from the document context.
    """
    truncated_context = context[:settings.MAX_CONTEXT_CHARS]

    prompt = f"""You are a quiz generator. Create {num_questions} multiple choice questions from the document text below.

STRICT RULES:
- Every question must be based ONLY on information in the text
- Do not create questions about topics not covered in the text
- Difficulty: {difficulty}
- Each question must have exactly 4 options (A, B, C, D)
- Only one correct answer per question
- Include a brief explanation for the correct answer

Document: {doc_name}

Document Text:
{truncated_context}

Return ONLY this JSON, no other text:
{{
  "questions": [
    {{
      "id": 1,
      "question": "...",
      "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
      "correct_answer": "A",
      "explanation": "..."
    }}
  ]
}}"""

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")  # ✅ Free tier available

        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.5
            )
        )

        cleaned_text = clean_json_response(response.text)
        data = json.loads(cleaned_text)

        questions = data.get("questions", [])
        return questions

    except Exception as e:
        logger.exception("FULL GEMINI ERROR")

        return [{
            "id": 0,
            "question": str(e),
            "options": {
                "A": "",
                "B": "",
                "C": "",
                "D": ""
            },
            "correct_answer": "A",
            "explanation": ""
        }]
