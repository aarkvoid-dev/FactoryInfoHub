from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import JsonResponse
from .models import Category, SubCategory
from .forms import CategoryForm, SubCategoryForm


@login_required
def category_dashboard(request):
    """Dashboard showing category management overview"""
    context = {
        'categories_count': Category.objects.count(),
        'subcategories_count': SubCategory.objects.count(),
        'active_categories': Category.objects.filter(is_active=True).count(),
        'active_subcategories': SubCategory.objects.filter(is_active=True).count(),
        'recent_categories': Category.objects.order_by('-created_at')[:5],
        'recent_subcategories': SubCategory.objects.select_related('category').order_by('-created_at')[:5],
    }
    return render(request, 'category/dashboard.html', context)


# Category Views
@login_required
def category_list(request):
    categories = Category.objects.all()
    return render(request, 'category/category_list.html', {'categories': categories})


@login_required
def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    subcategories = category.subcategories.all()
    context = {
        'category': category,
        'subcategories': subcategories,
        'subcategories_count': subcategories.count(),
    }
    return render(request, 'category/category_detail.html', context)


@login_required
def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.name}" created successfully!')
            return redirect('category:category_detail', slug=category.slug)
    else:
        form = CategoryForm()
    return render(request, 'category/category_form.html', {'form': form, 'title': 'Add Category'})


@login_required
def category_update(request, slug):
    category = get_object_or_404(Category, slug=slug)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.name}" updated successfully!')
            return redirect('category:category_detail', slug=category.slug)
    else:
        form = CategoryForm(instance=category)
    return render(request, 'category/category_form.html', {'form': form, 'title': 'Edit Category', 'category': category})


@login_required
def category_delete(request, slug):
    category = get_object_or_404(Category, slug=slug)
    if request.method == 'POST':
        category_name = category.name
        category.delete()
        messages.success(request, f'Category "{category_name}" deleted successfully!')
        return redirect('category:category_list')
    return render(request, 'category/category_confirm_delete.html', {'category': category})


# SubCategory Views
@login_required
def subcategory_list(request):
    subcategories = SubCategory.objects.select_related('category')
    return render(request, 'category/subcategory_list.html', {'subcategories': subcategories})


@login_required
def subcategory_detail(request, slug):
    subcategory = get_object_or_404(SubCategory, slug=slug)
    return render(request, 'category/subcategory_detail.html', {'subcategory': subcategory})


@login_required
def subcategory_create(request):
    if request.method == 'POST':
        form = SubCategoryForm(request.POST)
        if form.is_valid():
            subcategory = form.save()
            messages.success(request, f'SubCategory "{subcategory.name}" created successfully!')
            return redirect('category:subcategory_detail', slug=subcategory.slug)
    else:
        form = SubCategoryForm()
    return render(request, 'category/subcategory_form.html', {'form': form, 'title': 'Add SubCategory'})


@login_required
def subcategory_update(request, slug):
    subcategory = get_object_or_404(SubCategory, slug=slug)
    if request.method == 'POST':
        form = SubCategoryForm(request.POST, instance=subcategory)
        if form.is_valid():
            subcategory = form.save()
            messages.success(request, f'SubCategory "{subcategory.name}" updated successfully!')
            return redirect('category:subcategory_detail', slug=subcategory.slug)
    else:
        form = SubCategoryForm(instance=subcategory)
    return render(request, 'category/subcategory_form.html', {'form': form, 'title': 'Edit SubCategory', 'subcategory': subcategory})


@login_required
def subcategory_delete(request, slug):
    subcategory = get_object_or_404(SubCategory, slug=slug)
    if request.method == 'POST':
        subcategory_name = subcategory.name
        subcategory.delete()
        messages.success(request, f'SubCategory "{subcategory_name}" deleted successfully!')
        return redirect('category:subcategory_list')
    return render(request, 'category/subcategory_confirm_delete.html', {'subcategory': subcategory})


# AJAX Views for dynamic dropdowns
@login_required
def ajax_load_subcategories(request, category_id):
    subcategories = SubCategory.objects.filter(category_id=category_id).values('id', 'name')
    return JsonResponse(list(subcategories), safe=False)
