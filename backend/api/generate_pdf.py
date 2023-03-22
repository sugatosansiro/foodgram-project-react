from django.http.response import HttpResponse
from recipes.models import RecipeIngredients
from reportlab.pdfbase import pdfmetrics, ttfonts
from reportlab.pdfgen import canvas


def generate_pdf_shopping_cart(request):
    """Генерация списка покупок в виде PDF-файла"""
    response = HttpResponse(content_type='application/pdf')
    response['Content-Desposition'] = ('attachement; '
                                       'filename=shopping_cart.pdf')
    pdf = canvas.Canvas(response)
    arial = ttfonts.TTFont('Arial', '../data/arial.ttf')
    pdfmetrics.registerFont(arial)
    pdf.setFont('Arial', 14)
    print('Дошел до строчки 16')

    ingredients = RecipeIngredients.objects.filter(
        recipe__shopping_cart__user=request.user
    ).values_list(
        'ingredient__name', 'amount', 'ingredient__measurement_unit'
    )
    print('Дошел до строчки 23')
    ingr_list = {}
    for name, amount, unit in ingredients:
        if name not in ingr_list:
            ingr_list[name] = {'amount': amount, 'unit': unit}
        else:
            ingr_list[name]['amount'] += amount
    height = 700

    pdf.drawString(100, 750, 'Список покупок')
    for i, (name, data) in enumerate(ingr_list.items(), start=1):
        print(f'Дошел до строчки 34: {data}')
        pdf.drawString(
            80, height, f'{i}. {name} - {data["amount"]} {data["unit"]}'
        )
        height -= 20
    pdf.showPage()
    pdf.save()

    return response
