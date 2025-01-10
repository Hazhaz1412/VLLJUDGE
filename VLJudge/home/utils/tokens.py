from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils import timezone
from datetime import timedelta

class ActivationTokenGenerator(PasswordResetTokenGenerator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token_lifetime = timedelta(minutes=15)  # Đặt thời gian hết hạn là 15 phút

    def _make_hash_value(self, user, timestamp):
        # Thêm thời gian hết hạn vào token để kiểm tra trong quá trình kích hoạt
        return f'{user.pk}{timestamp}{user.is_active}{self.token_lifetime}'

    def check_token_expired(self, token_timestamp):
        # Kiểm tra nếu token đã hết hạn
        return timezone.now() - token_timestamp > self.token_lifetime

# Sử dụng lớp TokenGenerator tùy chỉnh
activation_token_generator = ActivationTokenGenerator()
