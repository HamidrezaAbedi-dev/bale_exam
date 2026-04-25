from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import User
from .serializers import UserSerializer


@api_view(["POST"])
def register_user(request):

    bale_id = request.data.get("bale_id")

    user, created = User.objects.get_or_create(
        bale_id=bale_id,
        defaults={
            "name": request.data.get("name"),
            "phone": request.data.get("phone")
        }
    )

    serializer = UserSerializer(user)

    return Response(serializer.data)


@api_view(["GET"])
def get_user(request, bale_id):

    try:
        user = User.objects.get(bale_id=bale_id)
    except User.DoesNotExist:
        return Response({"error": "user not found"}, status=404)

    serializer = UserSerializer(user)

    return Response(serializer.data)


@api_view(["PUT", "PATCH"])
def update_user(request, bale_id):

    try:
        user = User.objects.get(bale_id=bale_id)
    except User.DoesNotExist:
        return Response({"error": "user not found"}, status=404)

    serializer = UserSerializer(user, data=request.data, partial=True)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)

    return Response(serializer.errors, status=400)


@api_view(["POST"])
def save_exam_result(request):

    bale_id = request.data.get("bale_id")

    try:
        user = User.objects.get(bale_id=bale_id)
    except User.DoesNotExist:
        return Response({"error": "user not found"}, status=404)

    user.score = request.data.get("score")

    user.level = request.data.get("level")

    user.last_exam_level = request.data.get("exam_level")

    user.save()

    return Response({"status": "saved"})



