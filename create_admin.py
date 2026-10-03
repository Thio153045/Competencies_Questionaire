"""Buat akun admin HR.

Jalankan: python create_admin.py
"""

import getpass

import db


def main():
    print("=== Buat Akun Admin HR ===")
    username = input("Username: ").strip()
    nama = input("Nama lengkap: ").strip()
    password = getpass.getpass("Password (min. 8 karakter): ")
    ulang = getpass.getpass("Ulangi password: ")

    if not username or not nama:
        print("Username dan nama wajib diisi.")
        return
    if len(password) < 8:
        print("Password minimal 8 karakter.")
        return
    if password != ulang:
        print("Password tidak sama.")
        return

    try:
        db.create_admin(username, password, nama)
    except Exception as exc:  # noqa: BLE001
        print(f"Gagal membuat admin: {exc}")
        return
    print(f"Admin '{username}' berhasil dibuat.")


if __name__ == "__main__":
    main()
