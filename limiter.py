from database import is_premium, get_usage_today, get_weekly_usage, increment_usage
from config import settings

def get_limits(user_id):
    """Получить лимиты для пользователя"""
    if is_premium(user_id):
        return {
            'text_weekly': settings.PREMIUM_TEXT_WEEKLY_LIMIT,
            'image_daily': settings.PREMIUM_IMAGE_DAILY_LIMIT,
            'video_daily': settings.PREMIUM_VIDEO_DAILY_LIMIT
        }
    else:
        return {
            'text_weekly': settings.FREE_TEXT_WEEKLY_LIMIT,
            'image_daily': settings.FREE_IMAGE_DAILY_LIMIT,
            'video_daily': settings.FREE_VIDEO_DAILY_LIMIT
        }

def can_use_text(user_id):
    """Проверить, может ли пользователь генерировать текст"""
    if is_premium(user_id):
        return True, None
    
    limits = get_limits(user_id)
    weekly_used = get_weekly_usage(user_id)
    
    if weekly_used >= limits['text_weekly']:
        remaining = 0
    else:
        remaining = limits['text_weekly'] - weekly_used
    
    if weekly_used >= limits['text_weekly']:
        return False, f"❌ Лимит текстов исчерпан. Осталось: 0/{limits['text_weekly']} на неделю.\n💳 Подписка Premium: {settings.SUBSCRIPTION_PRICE_RUB}₽/мес."
    
    return True, f"ℹ️ Текстов осталось: {remaining}/{limits['text_weekly']} на неделю."

def can_use_image(user_id):
    """Проверить, может ли пользователь генерировать изображения"""
    if is_premium(user_id):
        return True, None
    
    limits = get_limits(user_id)
    today_used = get_usage_today(user_id, 'image')
    
    if today_used >= limits['image_daily']:
        return False, f"❌ Лимит изображений на сегодня исчерпан. Осталось: 0/{limits['image_daily']}.\n💳 Подписка Premium: {settings.SUBSCRIPTION_PRICE_RUB}₽/мес."
    
    remaining = limits['image_daily'] - today_used
    return True, f"ℹ️ Изображений осталось: {remaining}/{limits['image_daily']} на сегодня."

def can_use_video(user_id):
    """Проверить, может ли пользователь генерировать видео"""
    if is_premium(user_id):
        return True, None
    
    limits = get_limits(user_id)
    today_used = get_usage_today(user_id, 'video')
    
    if today_used >= limits['video_daily']:
        return False, f"❌ Лимит видео на сегодня исчерпан. Осталось: 0/{limits['video_daily']}.\n💳 Подписка Premium: {settings.SUBSCRIPTION_PRICE_RUB}₽/мес."
    
    remaining = limits['video_daily'] - today_used
    return True, f"ℹ️ Видео осталось: {remaining}/{limits['video_daily']} на сегодня."

def can_use(user_id, action):
    """Универсальная проверка лимитов"""
    if action == 'text':
        return can_use_text(user_id)
    elif action == 'image':
        return can_use_image(user_id)
    elif action == 'video':
        return can_use_video(user_id)
    else:
        return True, None

def consume(user_id, action):
    """Потребить использование"""
    increment_usage(user_id, action)
