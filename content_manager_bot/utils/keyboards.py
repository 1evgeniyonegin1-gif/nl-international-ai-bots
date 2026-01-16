"""
Inline клавиатуры для контент-менеджер бота
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import Optional


class Keyboards:
    """Клавиатуры для взаимодействия с администратором"""

    @staticmethod
    def post_moderation(post_id: int) -> InlineKeyboardMarkup:
        """
        Клавиатура для модерации поста

        Args:
            post_id: ID поста в базе данных

        Returns:
            InlineKeyboardMarkup
        """
        builder = InlineKeyboardBuilder()

        builder.row(
            InlineKeyboardButton(
                text="✅ Опубликовать",
                callback_data=f"publish:{post_id}"
            ),
            InlineKeyboardButton(
                text="📅 Запланировать",
                callback_data=f"schedule:{post_id}"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="📝 Редактировать",
                callback_data=f"edit:{post_id}"
            ),
            InlineKeyboardButton(
                text="🔄 Перегенерировать",
                callback_data=f"regenerate:{post_id}"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="❌ Отклонить",
                callback_data=f"reject:{post_id}"
            )
        )

        return builder.as_markup()

    @staticmethod
    def post_type_selection() -> InlineKeyboardMarkup:
        """
        Клавиатура для выбора типа поста

        Returns:
            InlineKeyboardMarkup
        """
        builder = InlineKeyboardBuilder()

        builder.row(
            InlineKeyboardButton(
                text="📦 О продуктах",
                callback_data="gen_type:product"
            ),
            InlineKeyboardButton(
                text="💪 Мотивация",
                callback_data="gen_type:motivation"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="📰 Новости",
                callback_data="gen_type:news"
            ),
            InlineKeyboardButton(
                text="💡 Советы",
                callback_data="gen_type:tips"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="🌟 История успеха",
                callback_data="gen_type:success_story"
            ),
            InlineKeyboardButton(
                text="🎁 Промо/Акция",
                callback_data="gen_type:promo"
            )
        )

        return builder.as_markup()

    @staticmethod
    def confirm_action(action: str, post_id: int) -> InlineKeyboardMarkup:
        """
        Клавиатура подтверждения действия

        Args:
            action: Действие (publish, reject, delete)
            post_id: ID поста

        Returns:
            InlineKeyboardMarkup
        """
        builder = InlineKeyboardBuilder()

        builder.row(
            InlineKeyboardButton(
                text="✅ Да, подтверждаю",
                callback_data=f"confirm_{action}:{post_id}"
            ),
            InlineKeyboardButton(
                text="❌ Отмена",
                callback_data=f"cancel:{post_id}"
            )
        )

        return builder.as_markup()

    @staticmethod
    def schedule_time_selection(post_id: int) -> InlineKeyboardMarkup:
        """
        Клавиатура для выбора времени публикации

        Args:
            post_id: ID поста

        Returns:
            InlineKeyboardMarkup
        """
        builder = InlineKeyboardBuilder()

        builder.row(
            InlineKeyboardButton(
                text="⏰ Через 1 час",
                callback_data=f"sched_time:1h:{post_id}"
            ),
            InlineKeyboardButton(
                text="⏰ Через 3 часа",
                callback_data=f"sched_time:3h:{post_id}"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="🌅 Завтра 9:00",
                callback_data=f"sched_time:tomorrow_9:{post_id}"
            ),
            InlineKeyboardButton(
                text="🌆 Завтра 18:00",
                callback_data=f"sched_time:tomorrow_18:{post_id}"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="📅 Указать время",
                callback_data=f"sched_time:custom:{post_id}"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="❌ Отмена",
                callback_data=f"cancel:{post_id}"
            )
        )

        return builder.as_markup()

    @staticmethod
    def pending_posts_navigation(
        current_page: int,
        total_pages: int,
        post_id: Optional[int] = None
    ) -> InlineKeyboardMarkup:
        """
        Навигация по списку постов на модерации

        Args:
            current_page: Текущая страница
            total_pages: Всего страниц
            post_id: ID текущего поста (для действий)

        Returns:
            InlineKeyboardMarkup
        """
        builder = InlineKeyboardBuilder()

        # Кнопки действий для текущего поста
        if post_id:
            builder.row(
                InlineKeyboardButton(
                    text="✅ Опубликовать",
                    callback_data=f"publish:{post_id}"
                ),
                InlineKeyboardButton(
                    text="❌ Отклонить",
                    callback_data=f"reject:{post_id}"
                )
            )

        # Навигация
        nav_buttons = []
        if current_page > 1:
            nav_buttons.append(
                InlineKeyboardButton(
                    text="◀️ Назад",
                    callback_data=f"pending_page:{current_page - 1}"
                )
            )
        if current_page < total_pages:
            nav_buttons.append(
                InlineKeyboardButton(
                    text="Вперёд ▶️",
                    callback_data=f"pending_page:{current_page + 1}"
                )
            )

        if nav_buttons:
            builder.row(*nav_buttons)

        return builder.as_markup()

    @staticmethod
    def back_to_menu() -> InlineKeyboardMarkup:
        """Кнопка возврата в меню"""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text="🔙 В меню",
                callback_data="back_to_menu"
            )
        )
        return builder.as_markup()

    @staticmethod
    def auto_schedule_settings() -> InlineKeyboardMarkup:
        """Настройки автоматической генерации"""
        builder = InlineKeyboardBuilder()

        builder.row(
            InlineKeyboardButton(
                text="📦 Продукты",
                callback_data="autosched:product"
            ),
            InlineKeyboardButton(
                text="💪 Мотивация",
                callback_data="autosched:motivation"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="📊 Статус расписания",
                callback_data="autosched:status"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="🔙 Назад",
                callback_data="back_to_menu"
            )
        )

        return builder.as_markup()
