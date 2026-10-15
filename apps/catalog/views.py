from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Avg, Count
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from .models import Category, Product, ProductImage, ProductReview

def home_view(request):
    """
    Storefront homepage featuring hero banner, featured categories,
    best sellers, new arrivals, promotional highlights, and top testimonials.
    """
    featured_categories = Category.objects.filter(is_featured=True)[:6]
    if not featured_categories.exists():
        featured_categories = Category.objects.all()[:6]

    featured_products = Product.objects.filter(is_active=True, is_featured=True)[:8]
    best_sellers = Product.objects.filter(is_active=True, is_bestseller=True)[:8]
    new_arrivals = Product.objects.filter(is_active=True, is_new_arrival=True).order_by('-created_at')[:8]

    # Fallback to general products if flags are sparse
    if not featured_products.exists():
        featured_products = Product.objects.filter(is_active=True)[:8]
    if not best_sellers.exists():
        best_sellers = Product.objects.filter(is_active=True).order_by('-rating_average')[:8]
    if not new_arrivals.exists():
        new_arrivals = Product.objects.filter(is_active=True).order_by('-created_at')[:8]

    recent_reviews = ProductReview.objects.filter(is_approved=True, rating__gte=4).select_related('user', 'product')[:6]

    context = {
        'featured_categories': featured_categories,
        'featured_products': featured_products,
        'best_sellers': best_sellers,
        'new_arrivals': new_arrivals,
        'recent_reviews': recent_reviews,
    }
    return render(request, 'catalog/home.html', context)


def product_list_view(request, category_slug=None):
    """
    Product listing page with full search, category filtering,
    price range slider, stock availability, sorting, and pagination.
    """
    queryset = Product.objects.filter(is_active=True).select_related('category')
    current_category = None

    # Filter by category from URL or query parameter
    if category_slug:
        current_category = get_object_or_404(Category, slug=category_slug)
        queryset = queryset.filter(category=current_category)
    else:
        cat_param = request.GET.get('category')
        if cat_param:
            current_category = Category.objects.filter(slug=cat_param).first()
            if current_category:
                queryset = queryset.filter(category=current_category)

    # Search keyword
    query = request.GET.get('q', '').strip()
    if query:
        queryset = queryset.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(short_description__icontains=query) |
            Q(sku__icontains=query) |
            Q(category__name__icontains=query)
        )

    # Filter by minimum price
    min_price = request.GET.get('min_price')
    if min_price:
        try:
            queryset = queryset.filter(price__gte=Decimal(min_price))
        except (ValueError, TypeError):
            pass

    # Filter by maximum price
    max_price = request.GET.get('max_price')
    if max_price:
        try:
            queryset = queryset.filter(price__lte=Decimal(max_price))
        except (ValueError, TypeError):
            pass

    # Filter by In-Stock only
    in_stock = request.GET.get('in_stock')
    if in_stock == '1':
        queryset = queryset.filter(stock__gt=0)

    # Sorting
    sort_by = request.GET.get('sort', 'newest')
    if sort_by == 'price_low':
        queryset = queryset.order_by('price')
    elif sort_by == 'price_high':
        queryset = queryset.order_by('-price')
    elif sort_by == 'rating':
        queryset = queryset.order_by('-rating_average', '-rating_count')
    elif sort_by == 'popular':
        queryset = queryset.order_by('-rating_count', '-created_at')
    else:  # newest
        queryset = queryset.order_by('-created_at')

    # Total matching count before pagination
    total_count = queryset.count()

    # Pagination: 12 products per page
    paginator = Paginator(queryset, 12)
    page_number = request.GET.get('page', 1)
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    # Categories for filter sidebar
    categories = Category.objects.annotate(active_count=Count('products', filter=Q(products__is_active=True))).order_by('name')

    context = {
        'page_obj': page_obj,
        'products': page_obj.object_list,
        'current_category': current_category,
        'categories': categories,
        'query': query,
        'min_price': min_price or '',
        'max_price': max_price or '',
        'in_stock': in_stock or '',
        'sort_by': sort_by,
        'total_count': total_count,
    }
    return render(request, 'catalog/product_list.html', context)


def product_detail_view(request, slug):
    """
    Detailed product showcase: gallery, stock status, specs, ratings,
    review submission, and related items.
    """
    product = get_object_or_404(Product, slug=slug, is_active=True)
    gallery_images = product.gallery_images.all()
    reviews = product.reviews.filter(is_approved=True).select_related('user')
    related_products = Product.objects.filter(
        category=product.category, 
        is_active=True
    ).exclude(id=product.id)[:4]

    # Check if logged in user has already reviewed this product
    user_review = None
    if request.user.is_authenticated:
        user_review = product.reviews.filter(user=request.user).first()

    # Parse specifications (format: "Key: Value" per line)
    specs_list = []
    if product.specifications:
        for line in product.specifications.splitlines():
            line = line.strip()
            if line:
                if ':' in line:
                    key, val = line.split(':', 1)
                    specs_list.append((key.strip(), val.strip()))
                elif '|' in line:
                    parts = line.split('|')
                    for p in parts:
                        if ':' in p:
                            k, v = p.split(':', 1)
                            specs_list.append((k.strip(), v.strip()))
                else:
                    specs_list.append((line, ''))

    context = {
        'product': product,
        'gallery_images': gallery_images,
        'reviews': reviews,
        'related_products': related_products,
        'specs_list': specs_list,
        'user_review': user_review,
    }
    return render(request, 'catalog/product_detail.html', context)


@login_required
def add_review_view(request, slug):
    """
    Allows customers to submit star ratings and text feedback.
    """
    product = get_object_or_404(Product, slug=slug, is_active=True)

    if request.method == 'POST':
        rating = request.POST.get('rating')
        title = request.POST.get('title', '').strip()
        comment = request.POST.get('comment', '').strip()

        if not rating or not title or not comment:
            messages.error(request, "Please provide a star rating, review headline, and detailed feedback.")
            return redirect('catalog:product_detail', slug=product.slug)

        try:
            rating_val = int(rating)
            if rating_val < 1 or rating_val > 5:
                raise ValueError
        except ValueError:
            messages.error(request, "Rating must be an integer between 1 and 5.")
            return redirect('catalog:product_detail', slug=product.slug)

        review, created = ProductReview.objects.update_or_create(
            product=product,
            user=request.user,
            defaults={
                'rating': rating_val,
                'title': title,
                'comment': comment,
                'is_approved': True,
            }
        )

        # Recalculate average rating
        product.update_rating_stats()

        if created:
            messages.success(request, "Thank you! Your product review has been submitted successfully.")
        else:
            messages.success(request, "Your review has been updated.")

    return redirect('catalog:product_detail', slug=product.slug)


def search_suggestions_api(request):
    """
    AJAX endpoint for instant search autosuggestion.
    """
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'results': []})

    products = Product.objects.filter(
        Q(name__icontains=query) | Q(category__name__icontains=query),
        is_active=True
    )[:6]

    results = []
    for p in products:
        results.append({
            'name': p.name,
            'url': f"/products/{p.slug}/",
            'price': str(p.price),
            'image': p.cover_image.url if p.cover_image else '/static/images/placeholder.svg',
            'category': p.category.name,
        })

    return JsonResponse({'results': results})
