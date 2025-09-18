#!/usr/bin/env python3
"""
Скрипт для получения JWT токена СТЭККОМ API
"""

import requests
import json
import sys

def get_token(username, password, api_url="http://localhost:8000"):
    """Получить JWT токен"""
    try:
        response = requests.post(
            f"{api_url}/auth/login",
            json={"username": username, "password": password}
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data["access_token"]
            user_info = data["user_info"]
            
            print(f"✅ Успешная аутентификация!")
            print(f"👤 Пользователь: {user_info['username']} ({user_info['role']})")
            print(f"🏢 Компания: {user_info['company']}")
            print(f"⏰ Токен действителен: {data['expires_in']} секунд")
            print(f"\n🔑 JWT Token:")
            print(f"{token}")
            
            return token
        else:
            print(f"❌ Ошибка аутентификации: {response.status_code}")
            print(f"Ответ: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return None

def test_token(token, api_url="http://localhost:8000"):
    """Тестировать токен"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{api_url}/auth/me", headers=headers)
        
        if response.status_code == 200:
            user_info = response.json()
            print(f"\n✅ Токен работает!")
            print(f"👤 Текущий пользователь: {user_info['username']}")
            return True
        else:
            print(f"❌ Токен недействителен: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка тестирования токена: {e}")
        return False

if __name__ == "__main__":
    # Доступные пользователи
    users = {
        "staff1": "10176e7b7b24d317acfcf8d2064cfd2f24e154f7b5a96603077d5ef813d6a6b6",
        "arctic_user": "хеш_пароля_arctic",
        "desert_user": "хеш_пароля_desert"
    }
    
    if len(sys.argv) > 1:
        username = sys.argv[1]
        if username in users:
            password = users[username]
        else:
            print(f"❌ Пользователь {username} не найден")
            print(f"Доступные: {list(users.keys())}")
            sys.exit(1)
    else:
        print("🔐 Получение JWT токена для СТЭККОМ API")
        print("\nДоступные пользователи:")
        for i, user in enumerate(users.keys(), 1):
            print(f"  {i}. {user}")
        
        try:
            choice = int(input("\nВыберите пользователя (номер): ")) - 1
            username = list(users.keys())[choice]
            password = users[username]
        except (ValueError, IndexError):
            print("❌ Неверный выбор")
            sys.exit(1)
    
    # Получаем токен
    token = get_token(username, password)
    
    if token:
        # Тестируем токен
        test_token(token)
        
        print(f"\n📖 Документация API: http://localhost:8000/docs")
        print(f"🔧 ReDoc: http://localhost:8000/redoc")
        print(f"\n💡 Использование токена:")
        print(f"curl -H 'Authorization: Bearer {token[:50]}...' http://localhost:8000/agreements/current")
