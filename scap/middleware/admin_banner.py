# your_app/middleware/admin_banner.py
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import User, Group
from django.utils import timezone
from datetime import timedelta
from django.db.models.functions import Length
from scap.models import UserMessage

class AdminBannerMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.user.is_authenticated and request.user.is_staff:
            seven_days_ago = timezone.now() - timedelta(days=7)

            # Define the groups to exclude
            excluded_groups = ["scap_contributors"]

            # Retrieve the groups
            excluded_group_objects = Group.objects.filter(name__in=excluded_groups)

            # Get users who joined in the last 7 days
            new_users = User.objects.filter(date_joined__gte=seven_days_ago)
            # Exclude users who belong to any of the excluded groups
            new_users = new_users.exclude(groups__in=excluded_group_objects).distinct()

            if new_users:
                if not hasattr(request, 'extras'):
                    request.extras = type('extras', (object,), {})()

                request.extras.new_users = new_users
        return None