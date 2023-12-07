import os
import requests
from rest_framework.response import Response
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework import status
from django.utils.text import slugify

from .models import AI, ChatHistory
from .serializers import ChatHistorySerializer, AiTutorSerializer, AIDataSerializer


from langchain.chains import ConversationalRetrievalChain
from langchain.chat_models import ChatOpenAI
from langchain.document_loaders import DirectoryLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.indexes import VectorstoreIndexCreator
from langchain.indexes.vectorstore import VectorStoreIndexWrapper
from langchain.llms import OpenAI
from langchain.vectorstores.chroma import Chroma

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_APIKEY")


@api_view(['GET','POST'])
def ai_view(request):
    if request.method == 'GET':
        ai = AI.objects.all()
        serializer = AiTutorSerializer(ai, many=True)
        return Response(serializer.data)
    if request.method == 'POST':
        serializer = AiTutorSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
@api_view(['POST'])
@parser_classes([MultiPartParser])
def upload_file(request, ai_id):
    ai = AI.objects.get(pk=ai_id)
    if request.method == 'POST':
        serializer = AIDataSerializer(data=request.data)
        if serializer.is_valid():
            serializer.validated_data['ai'] = ai
            serializer.save()

            # Assuming the file's upload path is based on the AI's name
            ai_name = slugify(ai.name)
            upload_path = f'ai_files/{ai_name}/'

            persist_directory_path = f'chromaDB/vector/{ai_name}'

            # print("Creating new embeddings for the uploaded file...\n")
            loader = DirectoryLoader(upload_path)
            VectorstoreIndexCreator(vectorstore_kwargs={"persist_directory": persist_directory_path}).from_loaders([loader])

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET','POST'])
def ai_request(request):
    if request.method == 'POST':
        # Retrieve 'message' from the POST data
        message = request.data.get('message')  # Use `request.data` instead of `request.POST` in DRF
        user_id = request.data.get('user_id')  # Use `request.data` instead of `request.POST` in DRF
        ai = request.data.get('ai_id')  # Use `request.data` instead of `request.POST` in DRF
        chat_id = request.data.get('chat_id')

        chat_history = get_chat_history(user_id, ai)

        # Fetch the AI instance with the given ID
        ai_instance = AI.objects.get(pk=ai)  # Assuming the AI's ID is 1

        ChatHistory.objects.create(
            user_id=user_id,  # You need to have the customer instance here
            ai=ai_instance,      # You need to have the AI instance here
            message=message,     # User's message
            from_ai=False,        # Set to False as this entry is for the user's message
            chat_id=chat_id
        )
        chat = process_chat(message, chat_history, ai_instance)
        
        # If you want to save the AI's message as a separate entry:
        ChatHistory.objects.create(
            user_id=user_id,
            ai=ai_instance,
            message=chat,
            from_ai=True,
            chat_id=chat_id

        )

        # Now make the POST request to the external API
        url = 'https://sbe.dxtsolution.online/api/v1/ai/received'
        data = {
            'user_id': user_id,
            'message': chat,
            'ai_chat_id': chat_id  # Assuming the API expects the AI's response as well
        }
        headers = {
            'Content-Type': 'application/json',
            # Add any other necessary headers here
        }
        
        requests.post(url, json=data, headers=headers)

        return Response({'reply': 'chat'})
    
    return Response({'error': 'This is the ai_request view, and you used a method other than POST.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)



def process_chat(message, chatHistory, ai_instance):

    ai_name = slugify(ai_instance.name)
    print(ai_name)

    persist_directory_path = f'chromaDB/vector/{ai_name}'

    vectorstore = Chroma(persist_directory=persist_directory_path, embedding_function=OpenAIEmbeddings())
    index = VectorStoreIndexWrapper(vectorstore=vectorstore)

    chain = ConversationalRetrievalChain.from_llm(
      llm=ChatOpenAI(model="gpt-3.5-turbo"),
      retriever=index.vectorstore.as_retriever(search_kwargs={"k": 1}),
    )

    result = chain({"question": message, "chat_history": chatHistory})


    return result['answer']

def get_chat_history(user_id, ai):
    # Retrieve chat history for the specified user and AI from the database
    chatHistories = ChatHistory.objects.filter(user_id=user_id, ai_id=ai).order_by('-id')
    # print(chatHistories)
    serializer = ChatHistorySerializer(chatHistories, many=True)

    # Convert serialized data into a list of tuples (user message, AI response)
    chat_history = []
    previous_customer_message = None
    for chat in serializer.data:
        if not chat['from_ai']:  # If the message is from the user
            previous_customer_message = chat['message']
        else:  # If the message is from the AI
            ai_response = chat['message']
            if previous_customer_message:
                chat_history.append((previous_customer_message, ai_response))
                previous_customer_message = None  # reset after appending

    return chat_history