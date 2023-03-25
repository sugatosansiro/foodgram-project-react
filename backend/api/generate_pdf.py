from django.http.response import HttpResponse
from recipes.models import RecipeIngredients
from reportlab.pdfbase import pdfmetrics, ttfonts
from reportlab.pdfgen import canvas

FONT_SIZE = 14
HEIGHT = 700
HEIGHT_REDUCTION = 20
INDENT_X = 100
INDENT_Y = 750
STRING_INDENT_X = 80


def generate_pdf_shopping_cart(request):
    """Генерация списка покупок в виде PDF-файла"""
    response = HttpResponse(content_type='application/pdf')
    response['Content-Desposition'] = ('attachement; '
                                       'filename=shopping_cart.pdf')
    pdf = canvas.Canvas(response)
    arial = ttfonts.TTFont('Arial', '../data/arial.ttf')
    pdfmetrics.registerFont(arial)
    pdf.setFont('Arial', FONT_SIZE)
    ingredients = RecipeIngredients.objects.filter(
        recipe__shopping_cart__user=request.user
    ).values_list(
        'ingredient__name', 'amount', 'ingredient__measurement_unit'
    )
    ingr_list = {}
    for name, amount, unit in ingredients:
        if name not in ingr_list:
            ingr_list[name] = {'amount': amount, 'unit': unit}
        else:
            ingr_list[name]['amount'] += amount
    height = HEIGHT

    pdf.drawString(INDENT_X, INDENT_Y, 'Список покупок')
    for i, (name, data) in enumerate(ingr_list.items(), start=1):
        pdf.drawString(
            STRING_INDENT_X,
            height,
            f'{i}. {name} - {data["amount"]} {data["unit"]}'
        )
        height -= HEIGHT_REDUCTION
    pdf.showPage()
    pdf.save()

    return response
