from django.shortcuts import render
from .serializers import OrderSerializer 
from rest_framework import viewsets      
from rest_framework.views import APIView
from .models import Order                 
from rest_framework.response import Response
from util_functions.get_twitter_images import get_user_id

from util_functions.collage_creator import create_collage_v2

class OrderView(viewsets.ModelViewSet):  
    serializer_class = OrderSerializer   
    queryset = Order.objects.all()     

#http://127.0.0.1:8000/api/verify/elonmusk
class VerifyView(APIView):
    def get(self, request, *args, **kwargs):
        if kwargs.get("handle", None) is not None:
            twitterHandle = kwargs["handle"]

            user_id = get_user_id(twitterHandle)

            if user_id != 0:
                return Response({'result': 'valid'})
            else:
                return Response({'result': 'invalid'})

#http://127.0.0.1:8000/api/process/1

class ProcessView(APIView):
    def get(self, request, *args, **kwargs):
        if kwargs.get("order_id", None) is not None:
            order_id = kwargs['order_id']
            theOrder = Order.objects.get(pk=order_id)


            if(theOrder):
                create_collage_v2(theOrder)
                return Response({'result': 'valid'})
            else:
                return Response({'result': 'invalid'})