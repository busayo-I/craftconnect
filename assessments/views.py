# assessments/views.py

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import json

from .models import Assessment
from .serializers import AssessmentSerializer
from users.models import Artisan
from assessments.groq_client import groq_generate

# --------------------------------------------------------
# START ASSESSMENT
# --------------------------------------------------------
@swagger_auto_schema(
    method='post',
    operation_summary="Start AI Assessment",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['trade_category', 'artisan'],
        properties={
            'trade_category': openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Trade category e.g. Tailor, Welder"
            ),
            'artisan': openapi.Schema(
                type=openapi.TYPE_INTEGER,
                description="Artisan ID"
            ),
        }
    )
)
@api_view(['POST'])
def start_assessment(request):
    try:
        trade_category = request.data.get("trade_category")
        artisan = request.data.get("artisan")

        # Input validation
        if not trade_category or not artisan:
            return Response(
                {"error": "trade_category and artisan are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Updated strict prompt to match submit endpoint requirements
        prompt = f"""
Generate EXACTLY 5 exam-style multiple-choice questions for the trade: "{trade_category}".

STRICT RULES:
- Only JSON output.
- No explanation or extra text.
- Each question must have options A–D.
- "answer" MUST be one of: "A", "B", "C", or "D".
- Output MUST MATCH this structure:

{{
  "questions": [
    {{
      "question": "string",
      "options": {{
        "A": "string",
        "B": "string",
        "C": "string",
        "D": "string"
      }},
      "answer": "A"
    }}
  ]
}}
"""

        # Call Groq AI
        try:
            output = groq_generate(prompt)
        except Exception as e:
            return Response(
                {"error": "AI generation failed", "details": str(e)},
                status=status.HTTP_502_BAD_GATEWAY
            )

        # Parse AI JSON
        try:
            data = json.loads(output)
        except json.JSONDecodeError:
            return Response(
                {"error": "Invalid JSON returned by AI", "raw_output": output},
                status=status.HTTP_502_BAD_GATEWAY
            )

        questions = data.get("questions")

        # Validate questions
        if (
            not questions
            or not isinstance(questions, list)
            or len(questions) != 5
        ):
            return Response(
                {
                    "error": "AI did not return 5 valid questions",
                    "raw_output": data
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Extra validation of structure (to prevent malformed data)
        for q in questions:
            if (
                "question" not in q or
                "options" not in q or
                "answer" not in q or
                not isinstance(q["options"], dict) or
                set(q["options"].keys()) != {"A", "B", "C", "D"} or
                q["answer"] not in ["A", "B", "C", "D"]
            ):
                return Response(
                    {"error": "AI returned questions in an invalid structure", "details": q},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        # Save assessment
        assessment = Assessment.objects.create(
            trade_category=trade_category,
            artisan_id=artisan,
            questions=questions,
            status="pending"
        )

        return Response({
            "message": "AI assessment started successfully.",
            "assessment": AssessmentSerializer(assessment).data
        })

    except Exception as e:
        return Response({"error": str(e)}, status=500)



# --------------------------------------------------------
# SUBMIT ASSESSMENT
# --------------------------------------------------------
@swagger_auto_schema(
    method='post',
    operation_summary="Submit completed AI assessment",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=["assessment_id", "answers"],
        properties={
            "assessment_id": openapi.Schema(
                type=openapi.TYPE_INTEGER,
                description="The ID of the assessment"
            ),
            "answers": openapi.Schema(
                type=openapi.TYPE_ARRAY,
                description="User's selected answers in order (A, B, C, or D)",
                items=openapi.Items(type=openapi.TYPE_STRING)
            ),
        }
    )
)
@api_view(["POST"])
def submit_assessment(request):
    try:
        assessment_id = request.data.get("assessment_id")
        answers = request.data.get("answers")

        # Validate input
        if not assessment_id or not isinstance(answers, list):
            return Response(
                {"error": "assessment_id and answers(list) are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get assessment
        assessment = Assessment.objects.filter(id=assessment_id).first()
        if not assessment:
            return Response({"error": "Assessment not found"}, status=404)

        questions = assessment.questions
        total = len(questions)

        if len(answers) != total:
            return Response(
                {"error": f"You must submit exactly {total} answers"},
                status=400
            )

        # Auto-score locally
        correct_count = 0
        wrong_list = []

        for idx, q in enumerate(questions):
            correct = q["answer"]
            user_ans = answers[idx]

            if user_ans == correct:
                correct_count += 1
            else:
                wrong_list.append({
                    "question_number": idx + 1,
                    "question": q["question"],
                    "correct_answer": correct,
                    "user_answer": user_ans
                })

        score = int((correct_count / total) * 100)

        # Build AI evaluation input
        qa_text = ""
        for idx, q in enumerate(questions, start=1):
            qa_text += f"""
Q{idx}: {q['question']}
Correct: {q['answer']}
User: {answers[idx-1]}
"""

        # Build AI prompt
        prompt = f"""
You are evaluating an artisan's skill assessment. 
Analyze each question and the user's answers.

Return **detailed JSON only**, no extra text.

Required JSON format:
{{
  "score": {score},
  "feedback": {{
    "summary": "string",
    "strengths": "string",
    "weaknesses": "string",
    "wrong_questions": [
        {{
          "question_number": number,
          "correct_answer": "A/B/C/D",
          "user_answer": "A/B/C/D",
          "explanation": "string"
        }}
    ],
    "recommendation": "string"
  }}
}}

Here are the user's answers:
{qa_text}
"""

        # Call Groq AI
        try:
            ai_output = groq_generate(prompt)
        except Exception as e:
            return Response(
                {"error": "AI evaluation failed", "details": str(e)},
                status=500
            )

        # Parse returned JSON
        try:
            result = json.loads(ai_output)
        except:
            return Response(
                {"error": "Invalid AI JSON response", "raw_output": ai_output},
                status=500
            )

        # Save results
        assessment.answers = answers
        assessment.score = result.get("score", score)
        assessment.ai_feedback = result.get("feedback", {})
        assessment.status = "completed"
        assessment.save()

        return Response({
            "message": "Assessment submitted.",
            "result": AssessmentSerializer(assessment).data
        })

    except Exception as e:
        return Response({"error": str(e)}, status=500)