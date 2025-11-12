from django.shortcuts import render
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Assessment
from users.models import Artisan
from .serializers import AssessmentSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


#Load model once at startup
model_name = "microsoft/phi-3-mini-4k-instruct"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.float32)


#generate assessment
@swagger_auto_schema(
    method='post',
    operation_summary="Start an AI-powered assessment for an artisan",
    operation_description="""
    Generates trade-specific assessment questions using an open-source AI model.
    The artisan’s trade category is used to tailor the questions.
    """,
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['artisan_id', 'trade_category'],
        properties={
            'artisan_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Artisan ID'),
            'trade_category': openapi.Schema(type=openapi.TYPE_STRING, description='Trade category (e.g., plumber, tailor, carpenter)'),
        },
        example={
            "artisan_id": 1,
            "trade_category": "plumber"
        }
    ),
    responses={
        201: openapi.Response(
            description="Assessment started successfully",
            examples={
                "application/json": {
                    "message": "AI assessment started successfully.",
                    "assessment": {
                        "id": 5,
                        "artisan": 1,
                        "trade_category": "plumber",
                        "questions": [
                            "What are the tools used to fix a leaking pipe?",
                            "Explain one safety precaution while soldering a pipe."
                        ],
                        "status": "pending"
                    }
                }
            }
        ),
        400: "Invalid input",
        404: "Artisan not found",
        500: "Internal server error"
    }
)
@api_view(['POST'])
def start_assessment(request):
    try:
        artisan_id = request.data.get('artisan_id')
        trade_category = request.data.get('trade_category')

        if not artisan_id or not trade_category:
            return Response(
                {"error": "artisan_id and trade_category are required."}, 
                status=status.HTTP_400_BAD_REQUEST
                )

        artisan = Artisan.objects.filter(id=artisan_id).first()
        if not artisan:
            return Response(
                {"error": "Artisan not found."}, 
                status=status.HTTP_404_NOT_FOUND
                )

        prompt = f"Generate 3 short assessment questions for a skilled {trade_category} in Nigeria."
        inputs = tokenizer(prompt, return_tensors="pt")
        outputs = model.generate(**inputs, max_new_tokens=80)
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

        questions = [q.strip() for q in generated_text.split("\n") if q.strip() and "?" in q]
        if not questions:
            questions = [
                "Describe your trade expertise.",
                "Mention two key tools you use daily.",
                "Explain one safety precaution in your work."
            ]

        assessment = Assessment.objects.create(
            artisan=artisan,
            trade_category=trade_category,
            questions=questions
        )

        serializer = AssessmentSerializer(assessment)
        return Response({
            "message": "AI assessment started successfully.",
            "assessment": serializer.data
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

#Submit endpoint
@swagger_auto_schema(
    method='post',
    operation_summary="Submit AI assessment answers for scoring and feedback",
    operation_description="""
    Submits the artisan’s answers, then the AI model evaluates and provides feedback with a score.
    """,
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['assessment_id', 'answers'],
        properties={
            'assessment_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Assessment ID'),
            'answers': openapi.Schema(
                type=openapi.TYPE_OBJECT,
                description='Key-value pairs of answers',
                example={
                    "1": "I use a wrench and pliers to fix pipes.",
                    "2": "I always wear gloves when handling hot tools."
                }
            ),
        },
    ),
    responses={
        200: openapi.Response(
            description="Assessment submitted successfully",
            examples={
                "application/json": {
                    "message": "Assessment submitted successfully.",
                    "result": {
                        "id": 5,
                        "score": 87,
                        "ai_feedback": "Good understanding of safety and tools. Keep improving precision work.",
                        "status": "completed"
                    }
                }
            }
        ),
        400: "Missing assessment_id or answers",
        404: "Assessment not found",
        500: "Internal server error"
    }
)
@api_view(['POST'])
def submit_assessment(request):
    try:
        assessment_id = request.data.get('assessment_id')
        answers = request.data.get('answers')

        if not assessment_id or not answers:
            return Response({"error": "assessment_id and answers are required."}, status=status.HTTP_400_BAD_REQUEST)

        assessment = Assessment.objects.filter(id=assessment_id).first()
        if not assessment:
            return Response({"error": "Assessment not found."}, status=status.HTTP_404_NOT_FOUND)

        qa_text = ""
        for q, a in zip(assessment.questions, answers.values()):
            qa_text += f"Question: {q}\nAnswer: {a}\n"

        feedback_prompt = f"Review the following artisan answers for {assessment.trade_category} skill and give a short feedback and score out of 100:\n{qa_text}\nFeedback:"
        inputs = tokenizer(feedback_prompt, return_tensors="pt")
        outputs = model.generate(**inputs, max_new_tokens=120)
        feedback = tokenizer.decode(outputs[0], skip_special_tokens=True)

        import re
        match = re.search(r'(\d{1,3})', feedback)
        score = float(match.group(1)) if match else 60.0

        assessment.answers = answers
        assessment.ai_feedback = feedback
        assessment.score = score
        assessment.status = "completed"
        assessment.save()

        serializer = AssessmentSerializer(assessment)
        return Response({
            "message": "Assessment submitted successfully.",
            "result": serializer.data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
