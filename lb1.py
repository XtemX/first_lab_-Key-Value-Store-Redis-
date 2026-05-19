import redis
import json
import time

class RedisCacheSystem:
    def __init__(self):
        # Підключення до бази (стандартний порт 6379)
        self.client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

    # --- Керування користувачами (Вимога про доступ) ---
    def add_user(self, username):
        self.client.sadd("system:users", username)
        print(f"Користувач {username} доданий до системи.")

    def is_authorized(self, username):
        return self.client.sismember("system:users", username)

    # --- Робота з різними типами даних (Вимога ТЗ) ---
    
    def cache_object(self, user, obj_id, data_dict):
        """Зберігання ОБ'ЄКТА (Hash)"""
        if not self.is_authorized(user):
            return "Доступ заборонено!"
        
        key = f"cache:object:{obj_id}"
        self.client.hset(key, mapping=data_dict)
        self.client.expire(key, 600)  # TTL 10 хвилин
        return f"Об'єкт {obj_id} закешовано (Hash)."

    def cache_simple_value(self, user, key_name, value):
        """Зберігання СТРОКИ або ЧИСЛА (String)"""
        if not self.is_authorized(user):
            return "Доступ заборонено!"
        
        full_key = f"cache:simple:{key_name}"
        self.client.set(full_key, value, ex=300)
        return f"Значення {key_name} збережено."

    # --- Код для доступу до даних ---
    def get_data(self, user, category, item_id):
        if not self.is_authorized(user):
            return "Помилка: Користувач не авторизований."

        # Визначаємо шлях до даних
        if category == "object":
            key = f"cache:object:{item_id}"
            data = self.client.hgetall(key)
        else:
            key = f"cache:simple:{item_id}"
            data = self.client.get(key)

        if data:
            # Трекінг популярності (Розширені можливості)
            self.client.incr(f"stats:hits:{item_id}")
            return data
        
        return "Дані відсутні в кеші (Cache Miss)."

    def show_popular_metrics(self):
        """Показує статистику звернень"""
        keys = self.client.keys("stats:hits:*")
        print("\n--- Статистика використання кешу ---")
        for k in keys:
            print(f"Елемент {k.split(':')[-1]}: {self.client.get(k)} запитів")

# --- ДЕМОНСТРАЦІЯ РОБОТИ ---

if __name__ == "__main__":
    sys = RedisCacheSystem()
    sys.client.flushdb() # Очистка для демо

    # 1. Реєстрація користувачів
    sys.add_user("admin_ivan")
    sys.add_user("manager_olga")

    # 2. Завантаження різних типів даних
    # Кешуємо складний об'єкт (Наприклад, товар)
    product = {"name": "Laptop", "price": "1200", "stock": "5"}
    print(sys.cache_object("admin_ivan", "prod_55", product))

    # Кешуємо просте числове значення
    print(sys.cache_simple_value("admin_ivan", "exchange_rate", 41.5))

    # 3. Доступ до даних (авторизований і ні)
    print("\nСпроба доступу (Ольга):", sys.get_data("manager_olga", "object", "prod_55"))
    print("Спроба доступу (Анонім):", sys.get_data("unknown_user", "simple", "exchange_rate"))

    # 4. Перевірка продуктивності (імітація багаторазових запитів)
    sys.get_data("admin_ivan", "object", "prod_55")
    sys.get_data("admin_ivan", "object", "prod_55")
    
    sys.show_popular_metrics()