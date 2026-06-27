from wagtail import hooks
from wagtail.admin.ui.tables import Column, DateColumn
from wagtail.admin.ui.tables.pages import (
    BulkActionsColumn,
    PageStatusColumn,
    PageTitleColumn,
)
from wagtail.admin.viewsets.pages import PageViewSet

from courses.models import SegmentPage


class SegmentPageViewSet(PageViewSet):
    model = SegmentPage
    columns = [
        BulkActionsColumn("bulk_actions"),
        PageTitleColumn("title", label="Title", sort_key="title", classname="title"),
        DateColumn(
            "latest_revision_created_at",
            label="Updated",
            sort_key="latest_revision_created_at",
            width="12%",
        ),
        PageStatusColumn("status", label="Status", sort_key="live", width="12%"),
        Column("video_url", label="Video URL", width="25%"),
    ]


@hooks.register("register_admin_viewset")
def register_segment_page_viewset():
    return SegmentPageViewSet()
