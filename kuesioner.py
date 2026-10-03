"""Aplikasi Kuesioner Kompetensi.

Jalankan: streamlit run app.py
"""

import streamlit as st

st.set_page_config(page_title="Kuesioner Kompetensi", page_icon="📝", layout="centered")

halaman = st.navigation([
    st.Page("views/kuesioner.py", title="Isi Kuesioner", icon="📝", default=True),
    st.Page("views/admin.py", title="Admin HR", icon="🔒"),
])
halaman.run()
