from wagtail import hooks

from courses.models import ChapterPage, CoursePage


@hooks.register("construct_explorer_page_queryset")
def order_chapters_and_segments_by_sort_order(parent_page, pages, request):
    if parent_page.specific_class in (CoursePage, ChapterPage):
        if not request.GET.get("ordering"):
            pages = pages.order_by("path")
    return pages
