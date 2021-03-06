from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from usersauth.models import WU_User


class WU_UserAdmin(UserAdmin):
    list_display = ("username", "first_name", "last_name",
                    "date_joined", "last_login", "is_student", "is_admin")
    search_fields = ("username", "first_name", "last_name",)
    readonly_fields = ("date_joined", "last_login")

    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()


admin.site.register(WU_User, WU_UserAdmin)
