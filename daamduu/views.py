from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def save_menu(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        # Assuming you have a model called MenuItem
        from .models import MenuItem  # Import your model here

        # Create a new menu item
        menu_item = MenuItem(
            name=data.get('name'),
            calorie=data.get('calorie'),
            image=data.get('image'),
            date=data.get('date')
        )
        menu_item.save()

        return JsonResponse({'status': 'success'}, status=201)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400) 