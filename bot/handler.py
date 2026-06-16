import os
import tempfile

import telebot

from core import DocToPdfConverter
from core.cache import FileCache, sha256
from core.doc_converter import SUPPORTED_FORMATS
from core.stats import BotStats

_SUPPORTED_EXT = ", ".join(sorted(SUPPORTED_FORMATS))


def create_bot(token: str, cache: FileCache, stats: BotStats) -> telebot.TeleBot:
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
            # 1. быстрый путь: hit по file_unique_id (без скачивания)
            cached = cache.get_by_id(doc.file_unique_id)
            print(f"[cache] unique_id={doc.file_unique_id!r} id_hit={cached is not None}")
            if cached:
                stats.record_hit()
                _send_pdf(bot, message, cached, file_name)
                return

            # 2. скачиваем файл
            file_info = bot.get_file(doc.file_id)
            file_bytes = bot.download_file(file_info.file_path)
            hash_key = sha256(file_bytes)

            # 3. hit по контенту (тот же файл от другого пользователя)
            cached = cache.get_by_hash(hash_key)
            print(f"[cache] hash={hash_key[:12]}… hash_hit={cached is not None}")
            if cached:
                stats.record_hit()
                cache.link_id(doc.file_unique_id, hash_key)
                _send_pdf(bot, message, cached, file_name)
                return

            # 4. miss — конвертируем
            stats.record_miss()
            with tempfile.TemporaryDirectory() as tmp_dir:
                input_path = os.path.join(tmp_dir, file_name)
                with open(input_path, "wb") as f:
                    f.write(file_bytes)
                output_path = converter.convert(input_path, tmp_dir)
                pdf_bytes = open(output_path, "rb").read()

            cached_path = cache.put(doc.file_unique_id, hash_key, pdf_bytes)
            _send_pdf(bot, message, cached_path, file_name)

        except Exception as e:
            bot.reply_to(message, f"Ошибка: {e}")
        finally:
            bot.delete_message(message.chat.id, status_msg.message_id)

    @bot.message_handler(func=lambda _: True)
    def handle_unknown(message: telebot.types.Message) -> None:
        bot.reply_to(message, "Пришли документ для конвертации в PDF.")

    return bot


def _send_pdf(
    bot: telebot.TeleBot,
    message: telebot.types.Message,
    pdf_path,
    original_name: str,
) -> None:
    pdf_name = os.path.splitext(original_name)[0] + ".pdf"
    with open(pdf_path, "rb") as pdf:
        bot.send_document(
            message.chat.id,
            pdf,
            reply_to_message_id=message.message_id,
            visible_file_name=pdf_name,
        )
