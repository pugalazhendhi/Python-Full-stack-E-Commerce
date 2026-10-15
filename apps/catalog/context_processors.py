from .models import Category

def categories_processor(request):
    """
    Exposes all categories to templates for global navigation and footer.
    """
    categories = Category.objects.all().order_by('name')
    return {
        'nav_categories': categories
    }
