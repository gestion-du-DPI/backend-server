from django.contrib import admin
from users.models import Hospital,Patient,Worker,Admin,AppUser
# Register your models here.
admin.site.register(Hospital)
admin.site.register(Patient)
admin.site.register(Worker)
admin.site.register(Admin)
admin.site.register(AppUser)