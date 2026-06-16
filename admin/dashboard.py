import os
import time

import requests
import streamlit as st

API_URL = os.environ.get("API_URL", "http://localhost:8000")

st.set_page_config(page_title="PDF Bot Admin", layout="centered")
st.title("PDF Bot — Admin")

auto_refresh = st.sidebar.checkbox("Авто-обновление (5с)", value=True)

col1, col2 = st.columns(2)

try:
    bot = requests.get(f"{API_URL}/api/bot/status", timeout=3).json()
    cache = requests.get(f"{API_URL}/api/cache/stats", timeout=3).json()

    with col1:
        st.subheader("Бот")
        uptime = bot["uptime_seconds"]
        h, m, s = uptime // 3600, uptime % 3600 // 60, uptime % 60
        st.metric("Статус", "🟢 Online")
        st.metric("Uptime", f"{h:02d}:{m:02d}:{s:02d}")
        st.metric("Конвертаций", bot["conversions_total"])
        st.metric("Cache hit / miss", f"{bot['cache_hits']} / {bot['cache_misses']}")

    with col2:
        st.subheader("Кэш")
        st.metric("Файлов", cache["files"])
        st.metric("Занято", f"{cache['size_mb']} MB")
        st.metric("Лимит", f"{cache['max_size_mb']} MB")
        st.progress(min(cache["fill_pct"] / 100, 1.0), text=f"{cache['fill_pct']}%")

    st.divider()
    if st.button("Очистить кэш", type="primary"):
        requests.delete(f"{API_URL}/api/cache", timeout=3)
        st.success("Кэш очищен")
        st.rerun()

except requests.exceptions.ConnectionError:
    st.error(f"Не могу подключиться к API: {API_URL}")

if auto_refresh:
    time.sleep(5)
    st.rerun()
