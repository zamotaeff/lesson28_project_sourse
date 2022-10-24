import json

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DetailView, ListView, CreateView, DeleteView, UpdateView

from ads.models import Category, Ad
from users.models import User


def index_route(request):
    return JsonResponse({
        "status": "ok"
    })


@method_decorator(csrf_exempt, name='dispatch')
class CategoryListView(ListView):
    model = Category
    queryset = Category.objects.annotate(num_ads=Count('ad')).order_by('name')

    def get(self, request, *args, **kwargs):
        categories = self.get_queryset()

        response = []
        for category in categories:
            response.append({
                "id": category.id,
                "name": category.name,
                "ads_number": category.num_ads
            })

        return JsonResponse(response, safe=False, json_dumps_params={"ensure_ascii": False})


@method_decorator(csrf_exempt, name="dispatch")
class CategoryCreateView(CreateView):
    model = Category

    def post(self, request, *args, **kwargs):
        category_data = json.loads(request.body)

        category = Category(name=category_data.get('name'))
        category.save()

        return JsonResponse({
            "id": category.pk,
            "name": category.name
        })


class CategoryDetailView(DetailView):
    model = Category

    def get(self, request, *args, **kwargs):
        category = self.get_object()

        return JsonResponse({
            "id": category.id,
            "name": category.name,
        })


@method_decorator(csrf_exempt, name="dispatch")
class CategoryDeleteView(DeleteView):
    model = Category
    success_url = '/'

    def delete(self, request, *args, **kwargs):
        super().delete(request, *args, **kwargs)

        return JsonResponse(
            {
                "status": "ok"
            }
        )


@method_decorator(csrf_exempt, name="dispatch")
class CategoryUpdateView(UpdateView):
    model = Category
    fields = ['name']
    success_url = '/'

    def post(self, request, *args, **kwargs):
        super().post(request, *args, **kwargs)

        category_data = json.loads(request.body)

        self.object.name = category_data['name']

        try:
            self.object.full_clean()
        except ValidationError as e:
            return JsonResponse(e.message_dict, status=422)

        self.object.save()

        return JsonResponse(
            {
                "id": self.object.pk,
                "name": self.object.name
            }
        )


class AdListView(ListView):
    model = Ad
    queryset = Ad.objects.select_related('author').order_by('-price')

    def get(self, request, *args, **kwargs):
        super().get(request, *args, **kwargs)

        paginator = Paginator(self.object_list, settings.TOTAL_ON_PAGE)
        page = int(request.GET.get('page', 0))
        # IF ?page request param exist
        if page:
            obj = paginator.get_page(page)
        else:
            obj = self.object_list

        items = []

        for item in obj:
            items.append(
                {
                    "id": item.pk,
                    "name": item.name,
                    "author_id": item.author_id,
                    "author": item.author.first_name,
                    "price": item.price,
                    "description": item.description,
                    "is_published": item.is_published,
                    "category_id": item.category_id,
                    "image": item.image.url if item.image else None
                }
            )

        response = {
            "items": items,
            "total": self.object_list.count(),
            "num_pages": paginator.num_pages
        }

        return JsonResponse(response, safe=False, json_dumps_params={"ensure_ascii": False})


@method_decorator(csrf_exempt, name="dispatch")
class AdCreateView(CreateView):
    model = Ad
    fields = ['name', 'author', ]

    def post(self, request, *args, **kwargs):
        ad_data = json.loads(request.body)

        # User with admin role make to post ad
        author = get_object_or_404(User, pk=ad_data['author_id'], role='admin')
        category = get_object_or_404(Category, pk=ad_data.get('category_id'))

        ad = Ad(
            name=ad_data.get('name'),
            author=author,
            category=category,
            price=ad_data.get('price'),
            description=ad_data.get('description'),
            is_published=bool(ad_data.get('is_bublished'))
        )
        ad.save()

        return JsonResponse({
            "id": ad.pk,
            "name": ad.name,
            "author_id": ad.author_id,
            "author": ad.author.first_name,
            "price": ad.price,
            "description": ad.description,
            "is_published": ad.is_published,
            "category_id": ad.category_id,
            "image": ad.image.url if ad.image else None
        })


class AdDetailView(DetailView):
    model = Ad
    queryset = Ad.objects.select_related('author')

    def get(self, request, *args, **kwargs):
        ad = self.get_object()

        return JsonResponse({
            "id": ad.pk,
            "name": ad.name,
            "author_id": ad.author_id,
            "author": ad.author.first_name,
            "price": ad.price,
            "description": ad.description,
            "is_published": ad.is_published,
            "category_id": ad.category_id,
            "image": ad.image.url if ad.image else None
        })


@method_decorator(csrf_exempt, name="dispatch")
class AdDeleteView(DeleteView):
    model = Ad
    success_url = '/'

    def delete(self, request, *args, **kwargs):
        super().delete(request, *args, **kwargs)

        return JsonResponse(
            {
                "status": "ok"
            }
        )


@method_decorator(csrf_exempt, name="dispatch")
class AdUpdateView(UpdateView):
    model = Ad
    fields = ['name', 'author', 'price', 'description', 'category']
    success_url = '/'

    def post(self, request, *args, **kwargs):
        super().post(request, *args, **kwargs)

        ad_data = json.loads(request.body)

        # Only a user with the moderator status can update Ad
        author = get_object_or_404(User,
                                   role='moderator',
                                   pk=ad_data.get('author_id'))
        category = get_object_or_404(Category, pk=ad_data.get('category_id'))

        if 'name' in ad_data:
            self.object.name = ad_data['name']
        if 'author' in ad_data:
            self.object.author = author
        if 'price' in ad_data:
            self.object.price = ad_data['price']
        if 'description' in ad_data:
            self.object.description = ad_data['description']
        if 'category' in ad_data:
            self.object.category = category

        try:
            self.object.full_clean()
        except ValidationError as e:
            return JsonResponse(e.message_dict, status=422)

        self.object.save()

        return JsonResponse({
            "id": self.object.pk,
            "name": self.object.name,
            "author_id": self.object.author_id,
            "author": self.object.author.first_name,
            "price": self.object.price,
            "description": self.object.description,
            "is_published": self.object.is_published,
            "category_id": self.object.category_id,
            "image": self.object.image.url if self.object.image else None
        })


@method_decorator(csrf_exempt, name="dispatch")
class AdUploadImageView(UpdateView):
    model = Ad
    fields = ['image']
    success_url = '/'

    def post(self, request, *args, **kwargs):
        super().post(request, *args, **kwargs)

        self.object.image = request.FILES['image']

        try:
            self.object.full_clean()
        except ValidationError as e:
            return JsonResponse(e.message_dict, status=422)

        self.object.save()

        return JsonResponse({
            "id": self.object.pk,
            "name": self.object.name,
            "author_id": self.object.author_id,
            "author": self.object.author.first_name,
            "price": self.object.price,
            "description": self.object.description,
            "is_published": self.object.is_published,
            "category_id": self.object.category_id,
            "image": self.object.image.url if self.object.image else None
        })
