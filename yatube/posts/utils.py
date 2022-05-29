from django.conf import settings
from django.core.paginator import Paginator


def page(request, posts):
    paginator = Paginator(posts, settings.PAGES)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
