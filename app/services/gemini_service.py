"""
Gemini AI service for generating questions using Google Generative AI.
"""

import os
import json
import logging
from typing import List, Dict, Any
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logger
logger = logging.getLogger(__name__)

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
    genai.configure(api_key=GEMINI_API_KEY)


class GeminiService:
    """Service for generating questions using Google Gemini AI."""

    def __init__(self):
        self.model = genai.GenerativeModel('models/gemini-2.5-flash-lite')

    def _build_mcq_prompt(self, topic_name: str, chapter_name: str, subject_name: str, language: str, count: int) -> str:
        """Build prompt for MCQ question generation."""
        return f"""Generate {count} multiple-choice questions (MCQ) for the following context:

**Subject:** {subject_name}
**Chapter:** {chapter_name}
**Topic:** {topic_name}
**Programming Language/Technology:** {language}

Requirements:
1. Generate exactly {count} questions
2. Each question must have exactly 4 options
3. Specify the correct answer as an index (0-3)
4. Use proper markdown formatting in explanations
5. Use appropriate code syntax highlighting with language tags (```{language.lower()})
6. Make questions practical and educational
7. Explanations should be clear and informative with proper formatting (**bold**, headings, lists)

Return ONLY a valid JSON array with this exact structure:
[
  {{
    "question": "Question text here?",
    "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
    "correctAnswer": 2,
    "explanation": "Markdown formatted explanation with **bold**, headings, and code blocks"
  }}
]

Important:
- Use proper markdown in explanations (## headings, **bold**, lists, code blocks)
- correctAnswer must be 0, 1, 2, or 3 (zero-indexed)
- Code blocks must use ```{language.lower()} for syntax highlighting
- Return ONLY the JSON array, no additional text"""

    def _build_output_prompt(self, topic_name: str, chapter_name: str, subject_name: str, language: str, count: int) -> str:
        """Build prompt for Output question generation."""
        return f"""Generate {count} code output prediction questions for the following context:

**Subject:** {subject_name}
**Chapter:** {chapter_name}
**Topic:** {topic_name}
**Programming Language/Technology:** {language}

Requirements:
1. Generate exactly {count} questions
2. Each question must contain code with proper syntax highlighting
3. Provide the expected output
4. Include clear explanations with markdown formatting
5. Code blocks must use ```{language.lower()} for syntax highlighting
6. Output should be in ``` code blocks
7. Make questions practical and test real concepts

Return ONLY a valid JSON array with this exact structure:
[
  {{
    "question": "```{language.lower()}\\ncode here\\n```",
    "output": "```\\nexpected output\\n```",
    "explanation": "Markdown formatted explanation with **bold**, headings, and code blocks if needed"
  }}
]

Important:
- Question field must contain code with ```{language.lower()} syntax highlighting
- Output field must be in ``` code blocks
- Explanations should include **bold**, headings, and visual representations if helpful
- Return ONLY the JSON array, no additional text"""

    def _build_interview_prompt(self, topic_name: str, chapter_name: str, subject_name: str, language: str, count: int) -> str:
        """Build prompt for Interview question generation."""
        return f"""Generate {count} interview questions with detailed answers for the following context:

**Subject:** {subject_name}
**Chapter:** {chapter_name}
**Topic:** {topic_name}
**Programming Language/Technology:** {language}

Requirements:
1. Generate exactly {count} questions
2. Questions should be common interview questions
3. Answers must be comprehensive with proper markdown formatting
4. Use ## for main headings, ### for subheadings
5. Use **bold** for important terms
6. Include code examples with ```{language.lower()} syntax highlighting
7. Use lists, tables, and visual representations where helpful
8. Include practical examples

Return ONLY a valid JSON array with this exact structure:
[
  {{
    "question": "Interview question text?",
    "answer": "## Main Heading\\n\\nDetailed answer with **bold**, code blocks, lists, etc.",
    "explanation": "**Key points** to remember or additional context with proper formatting"
  }}
]

Important:
- Answers must be well-structured with ## headings and ### subheadings
- Use **bold** for emphasis on important concepts
- Include code examples with ```{language.lower()} syntax highlighting
- Use lists and visual representations
- Explanations should highlight key takeaways
- Return ONLY the JSON array, no additional text"""

    def generate_questions(
        self,
        topic_name: str,
        chapter_name: str,
        subject_name: str,
        question_type: str,
        count: int
    ) -> List[Dict[str, Any]]:
        """
        Generate questions using Gemini AI.

        Args:
            topic_name: Name of the topic
            chapter_name: Name of the chapter
            subject_name: Name of the subject
            question_type: Type of question (mcq, output, interview)
            count: Number of questions to generate

        Returns:
            List of generated questions in dictionary format

        Raises:
            Exception: If API call fails or response is invalid
        """
        if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
            raise Exception("GEMINI_API_KEY is not configured in environment variables")

        # Determine language/technology from subject or topic
        language = self._detect_language(subject_name, topic_name)

        # Build appropriate prompt based on question type
        if question_type == "mcq":
            prompt = self._build_mcq_prompt(topic_name, chapter_name, subject_name, language, count)
        elif question_type == "output":
            prompt = self._build_output_prompt(topic_name, chapter_name, subject_name, language, count)
        elif question_type == "interview":
            prompt = self._build_interview_prompt(topic_name, chapter_name, subject_name, language, count)
        else:
            raise ValueError(f"Invalid question type: {question_type}")

        try:
            # Generate content using Gemini
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()

            # Remove markdown code block markers if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            response_text = response_text.strip()

            # Parse JSON response
            questions = json.loads(response_text)

            if not isinstance(questions, list):
                raise ValueError("Response is not a JSON array")

            logger.info(f"Successfully generated {len(questions)} {question_type} questions")
            return questions

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {str(e)}")
            logger.error(f"Response text: {response_text[:500]}")
            raise Exception(f"Failed to parse AI response: {str(e)}")
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            raise Exception(f"Failed to generate questions: {str(e)}")

    def _detect_language(self, subject_name: str, topic_name: str) -> str:
        """Detect programming language/technology from subject or topic name."""
        combined = f"{subject_name} {topic_name}".lower()

        language_map = {
            "python": "python",
            "javascript": "javascript",
            "typescript": "typescript",
            "java": "java",
            "c++": "cpp",
            "c#": "csharp",
            "ruby": "ruby",
            "go": "go",
            "rust": "rust",
            "php": "php",
            "swift": "swift",
            "kotlin": "kotlin",
            "react": "jsx",
            "angular": "typescript",
            "vue": "javascript",
            "node": "javascript",
            "express": "javascript",
            "django": "python",
            "flask": "python",
            "spring": "java",
            ".net": "csharp",
        }

        for key, lang in language_map.items():
            if key in combined:
                return lang

        # Default to generic code if no specific language detected
        return "code"
