import os
import tempfile

import telebot

from core import DocToPdfConverter
from core.cache import FileCache
from core.doc_converter import SUPPORTED_FORMATS

_SUPPORTED_EXT = ", ".join(sorted(SUPPORTED_FORMATS))


def create_bot(token: str, cache: FileCache) -> telebot.TeleBot:
    bot = telebot.TeleBot(token)
    converter = DocToPdfConverter()

    @bot.message_handler(commands=["start", "help"])
    def handle_start(message: telebot.types.Message) -> None:
        bot.reply_to(
            message,
            f"Пришли мне документ — отдам PDF.\n\nПоддерживаемые форматы: {_SUPPORTED_EXT}",
        )

    @bot.message_handler(content_types=["document"])
    def handle_document(message: telebot.types.Message) -> None:
        doc = message.document
        file_name: str = doc.file_name or "file"
        ext = os.path.splitext(file_name)[1].lower()

        if ext not in SUPPORTED_FORMATS:
            bot.reply_to(
                message,
                f"Формат {ext!r} не поддерживается.\nМожно: {_SUPPORTED_EXT}",
            )
            return

        status_msg = bot.reply_to(message, "Конвертирую...")

        try:
            cached = cache.get(doc.file_unique_id)
            if cached:
                with open(cached, "rb") as pdf:
                    bot.send_document(
                        message.chat.id,
                        pdf,
                        reply_to_message_id=message.message_id,
                        visible_file_name=os.path.splitext(file_name)[0] + ".pdf",
                    )
                return

            file_info = bot.get_file(doc.file_id)
            file_bytes = bot.download_file(file_info.file_path)

            with tempfile.TemporaryDirectory() as tmp_dir:
                input_path = os.path.join(tmp_dir, file_name)
                with open(input_path, "wb") as f:
                    f.write(file_bytes)

                output_path = converter.convert(input_path, tmp_dir)
                pdf_bytes = open(output_path, "rb").read()

            cached_path = cache.put(doc.file_unique_id, pdf_bytes)
            with open(cached_path, "rb") as pdf:
                bot.send_document(
                    message.chat.id,
                    pdf,
                    reply_to_message_id=message.message_id,
                    visible_file_name=os.path.splitext(file_name)[0] + ".pdf",
                )

        except Exception as e:
            bot.reply_to(message, f"Ошибка: {e}")
        finally:
            bot.delete_message(message.chat.id, status_msg.message_id)

    @bot.message_handler(func=lambda _: True)
    def handle_unknown(message: telebot.types.Message) -> None:
        bot.reply_to(message, "Пришли документ для конвертации в PDF.")

    return bot
