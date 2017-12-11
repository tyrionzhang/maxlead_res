from django.contrib.auth.models import User, Group

class UserSecuirty:

    def user_secuity(self):
        user = self.user.is_anonymous()
        self.user_info = user
        if not user:
            group = Group.objects.get(user=self.user)
            self.group = group

