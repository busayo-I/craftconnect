from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes,parser_classes
from rest_framework.response import Response
from rest_framework import status, permissions
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import check_password
from .models import Artisan, Client
from .serializers import ArtisanSerializer, ClientSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser


#Artisan Registration
@swagger_auto_schema(
    method='post',
    operation_description="Register a new Artisan user.",
    request_body=ArtisanSerializer,
    responses={
        201: "Artisan registered successfully",
        400: "Validation error",
        500: "Internal server error"
    }
)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def artisan_register(request):
    try:
        serializer = ArtisanSerializer(data=request.data)
        if serializer.is_valid():
            artisan = serializer.save()
            return Response({
                "message": "Artisan registered successfully",
                "artisan_id": artisan.id,
                "full_name": f"{artisan.first_name} {artisan.last_name}",
                "trade_category": artisan.trade_category.name if artisan.trade_category else None,
                "location": artisan.location,
                "language": artisan.language
            }, status=status.HTTP_201_CREATED)
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


#Client Registration
@swagger_auto_schema(
    method='post',
    operation_description="Register a new Client user.",
    request_body=ClientSerializer,
    responses={
        201: "Client registered successfully",
        400: "Validation error",
        500: "Internal server error"
    }
)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def client_register(request):
    try:
        serializer = ClientSerializer(data=request.data)
        if serializer.is_valid():
            client = serializer.save()
            return Response({
                "message": "Client registered successfully",
                "client_id": client.id,
                "full_name": f"{client.first_name} {client.last_name}",
                "location": client.location,
                "language": client.language
            }, status=status.HTTP_201_CREATED)
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



#login session
@swagger_auto_schema(
    method='post',
    operation_description="Login endpoint for both Artisan and Client users.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'email_address': openapi.Schema(type=openapi.TYPE_STRING, description='User email'),
            'password': openapi.Schema(type=openapi.TYPE_STRING, description='User password'),
        },
        required=['email_address', 'password'],
    ),
    responses={
        200: "Login successful, returns JWT tokens.",
        400: "Missing or invalid credentials.",
        401: "Invalid password.",
        404: "User not found.",
        500: "Internal server error."
    }
)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def user_login(request):
    try:
        email = request.data.get('email_address')
        password = request.data.get('password')

        if not email or not password:
            return Response(
                {'error': 'Email and password are required.'}, 
                status=status.HTTP_400_BAD_REQUEST
                )

        #check user in the Artisan table
        user = Artisan.objects.filter(email_address=email).first()
        user_type = "Artisan"

        #check user in the Client table
        if not user:
            user = Client.objects.filter(email_address=email).first()
            user_type = "Client"

        if not user:
            return Response(
                {'error': 'User not found.'}, 
                status=status.HTTP_404_NOT_FOUND
                )

        #Verify password
        if not check_password(password, user.password):
            return Response(
                {'error': 'Invalid credentials.'}, 
                status=status.HTTP_401_UNAUTHORIZED
                )

        #Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        #Get user data
        if user_type == "Artisan":
            serializer = ArtisanSerializer(user)
        else:
            serializer = ClientSerializer(user)

        #Remove password from response
        user_data = serializer.data
        if 'password' in user_data:
            user_data.pop('password')


        return Response({
            'message': f'{user_type} login successful.',
            'user_type': user_type,
            'user': user_data,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh)
                }, 
            }, 
            status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    


#Get all user
@swagger_auto_schema(
    method='get',
    operation_description="Get user information (Artisan or Client) by ID or token.",
    manual_parameters=[
        openapi.Parameter('user_type', openapi.IN_QUERY, description="Artisan or Client", type=openapi.TYPE_STRING),
        openapi.Parameter('user_id', openapi.IN_QUERY, description="User ID", type=openapi.TYPE_INTEGER)
    ],
    responses={
        200: "User details returned successfully.",
        404: "User not found."
        }
)
@api_view(['GET'])
#@permission_classes([IsAuthenticated])
def get_user_profile(request):
    try:
        user_type = request.query_params.get('user_type')
        user_id = request.query_params.get('user_id')

        if not user_type or not user_id:
            return Response(
                {'error': 'Please provide user_type and user_id.'}, 
                status=status.HTTP_400_BAD_REQUEST
                )

        if user_type.lower() == 'artisan':
            user = Artisan.objects.filter(id=user_id).first()
            if not user:
                return Response(
                    {'error': 'Artisan not found.'}, 
                    status=status.HTTP_404_NOT_FOUND
                    )
            serializer = ArtisanSerializer(user)
        else:
            user = Client.objects.filter(id=user_id).first()
            if not user:
                return Response(
                    {'error': 'Client not found.'}, 
                    status=status.HTTP_404_NOT_FOUND
                    )
            serializer = ClientSerializer(user)

        data = serializer.data
        data.pop('password', None)
        return Response(
            {'user': data}, 
            status=status.HTTP_200_OK
            )

    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


#Update user information
@swagger_auto_schema(
    method='put',
    manual_parameters=[
        openapi.Parameter('user_type', openapi.IN_FORM, description="Type of user (Artisan or Client)", type=openapi.TYPE_STRING, required=True),
        openapi.Parameter('user_id', openapi.IN_FORM, description="User ID", type=openapi.TYPE_INTEGER, required=True),
        openapi.Parameter('first_name', openapi.IN_FORM, description="First name", type=openapi.TYPE_STRING),
        openapi.Parameter('last_name', openapi.IN_FORM, description="Last name", type=openapi.TYPE_STRING),
        openapi.Parameter('phone_number', openapi.IN_FORM, description="Phone number", type=openapi.TYPE_STRING),
        openapi.Parameter('bio', openapi.IN_FORM, description="Short bio", type=openapi.TYPE_STRING),
        openapi.Parameter('business_name', openapi.IN_FORM, description="Business name", type=openapi.TYPE_STRING),
        openapi.Parameter('location', openapi.IN_FORM, description="User location", type=openapi.TYPE_STRING),
        openapi.Parameter('language', openapi.IN_FORM, description="Preferred language", type=openapi.TYPE_STRING),
        openapi.Parameter('profile_picture', openapi.IN_FORM, description="Profile picture file", type=openapi.TYPE_FILE),
    ],
    responses={
        200: "Profile updated successfully.",
        400: "Validation error.",
        404: "User not found.",
    },
    consumes=["multipart/form-data"]
)


@api_view(['PUT'])
#@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def update_user_profile(request):
    try:
        user_type = request.data.get('user_type')
        user_id = request.data.get('user_id')

        if not user_type or not user_id:
            return Response({'error': 'user_type and user_id are required.'}, status=status.HTTP_400_BAD_REQUEST)

        if user_type.lower() == 'artisan':
            user = Artisan.objects.filter(id=user_id).first()
            serializer_class = ArtisanSerializer
        else:
            user = Client.objects.filter(id=user_id).first()
            serializer_class = ClientSerializer

        if not user:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = serializer_class(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            data = serializer.data
            data.pop('password', None)
            if user.profile_picture:
                data['profile_picture'] = request.build_absolute_uri(user.profile_picture.url)
            return Response({'message': 'Profile updated successfully.', 'user': data}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


#Get user that is currently login
@swagger_auto_schema(
    method='get',
    operation_description="Retrieve the profile of the currently logged-in user (Artisan or Client).",
    responses={
        200: openapi.Response(
            description="Profile retrieved successfully.",
            examples={
                "application/json": {
                    "user": {
                        "id": 1,
                        "first_name": "Ibrahim",
                        "last_name": "Busayo",
                        "email_address": "ibrahimbusayo2018@gmail.com",
                        "phone_number": "08012345678",
                        "bio": "Professional electrician",
                        "business_name": "IB Tech Repairs",
                        "location": "Abuja",
                        "language": "English",
                        "profile_picture": "http://127.0.0.1:8000/media/profiles/ibrahim.jpg"
                    }
                }
            }
        ),
        401: "Unauthorized - Missing or invalid token.",
        404: "User not found."
    }
)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_logged_in_user(request):
    """
    Returns the profile details of the currently logged-in user.
    """
    try:
        email = request.user.email
        user = Artisan.objects.filter(email_address=email).first()
        serializer_class = ArtisanSerializer

        if not user:
            user = Client.objects.filter(email_address=email).first()
            serializer_class = ClientSerializer

        if not user:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = serializer_class(user)
        data = serializer.data
        data.pop('password', None)

        if hasattr(user, 'profile_picture') and user.profile_picture:
            data['profile_picture'] = request.build_absolute_uri(user.profile_picture.url)

        return Response({'user': data}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
