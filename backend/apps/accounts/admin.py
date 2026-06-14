from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import ProjectMembership, Role, RoleAssignment, User

admin.site.register(User, UserAdmin)
admin.site.register(Role)
admin.site.register(RoleAssignment)
admin.site.register(ProjectMembership)
