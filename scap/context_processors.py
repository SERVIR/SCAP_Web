def user_groups(request):
    """
    Adds the user's groups to the context.
    """
    groups = []
    if request.user.is_authenticated:
        groups = request.user.groups.all()
    return {'user_groups': groups}


def approver_group(request):
    if request.user.is_authenticated:
        return {'is_approver': request.user.groups.filter(name='scap_sysadmins').exists()}
    return {'is_approver': False}