import hashlib
import json
import requests
import uuid
from datetime import datetime, timedelta
from config import settings
from database import create_payment, update_payment_status, get_payment, set_premium

class TinkoffPaymentService:
    """Сервис для работы с платежами Tinkoff"""
    
    def __init__(self):
        self.terminal_key = settings.TINKOFF_TERMINAL_KEY
        self.secret_key = settings.TINKOFF_SECRET_KEY
        self.api_url = settings.TINKOFF_API_URL
        
        if not self.terminal_key or not self.secret_key:
            raise ValueError("Tinkoff API ключи не установлены в .env")
    
    def _generate_token(self, params):
        """Генерировать токен для запроса"""
        params_str = ''.join(f"{k}{v}" for k, v in sorted(params.items()))
        token = hashlib.sha256((params_str + self.secret_key).encode()).hexdigest()
        return token
    
    def init_payment(self, user_id, amount, order_description="Premium subscription"):
        """Инициировать платёж"""
        order_id = f"order_{user_id}_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
        
        params = {
            'TerminalKey': self.terminal_key,
            'Amount': amount * 100,  # Tinkoff принимает суммы в копейках
            'OrderID': order_id,
            'Description': order_description,
            'DATA': json.dumps({'UserId': str(user_id)}),
        }
        
        params['Token'] = self._generate_token(params)
        
        try:
            response = requests.post(
                f"{self.api_url}/Init",
                json=params,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get('Success'):
                payment_url = data.get('PaymentURL')
                payment_id = data.get('PaymentID')
                
                # Сохранить в БД
                create_payment(user_id, order_id, amount)
                
                return {
                    'success': True,
                    'order_id': order_id,
                    'payment_id': payment_id,
                    'payment_url': payment_url
                }
            else:
                return {
                    'success': False,
                    'error': data.get('Message', 'Unknown error')
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_payment_status(self, payment_id):
        """Получить статус платежа"""
        params = {
            'TerminalKey': self.terminal_key,
            'PaymentID': payment_id,
        }
        
        params['Token'] = self._generate_token(params)
        
        try:
            response = requests.post(
                f"{self.api_url}/GetState",
                json=params,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            return data
        except Exception as e:
            return {'error': str(e)}
    
    def confirm_payment(self, order_id):
        """Подтвердить платёж"""
        payment = get_payment(order_id)
        if not payment:
            return {'success': False, 'error': 'Payment not found'}
        
        status_data = self.get_payment_status(payment['payment_id'])
        
        if status_data.get('Status') == 'CONFIRMED':
            update_payment_status(order_id, 'CONFIRMED', payment['payment_id'])
            set_premium(payment['user_id'], days=settings.SUBSCRIPTION_DAYS)
            return {'success': True, 'user_id': payment['user_id']}
        
        return {'success': False, 'error': 'Payment not confirmed'}
    
    def process_notification(self, data):
        """Обработать уведомление от Tinkoff"""
        # Проверить то��ен
        token = data.pop('Token', None)
        expected_token = self._generate_token(data)
        
        if token != expected_token:
            return {'success': False, 'error': 'Invalid token'}
        
        order_id = data.get('OrderID')
        status = data.get('Status')
        
        if status == 'CONFIRMED':
            update_payment_status(order_id, 'CONFIRMED')
            payment = get_payment(order_id)
            if payment:
                set_premium(payment['user_id'], days=settings.SUBSCRIPTION_DAYS)
        elif status in ['CANCELED', 'REJECTED']:
            update_payment_status(order_id, 'FAILED')
        
        return {'success': True}

payment_service = TinkoffPaymentService()
