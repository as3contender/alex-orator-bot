-- Инициализация базы данных пользовательских данных CloverdashBot
-- Этот скрипт выполняется автоматически при первом запуске PostgreSQL контейнера

-- Включение расширения для UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Создание примера таблиц для демонстрации
-- В реальном проекте эти таблицы будут содержать ваши бизнес-данные

-- Таблица клиентов
CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(50),
    city VARCHAR(100),
    country VARCHAR(100),
    registration_date DATE DEFAULT CURRENT_DATE,
    total_orders INTEGER DEFAULT 0,
    total_spent DECIMAL(10,2) DEFAULT 0.00,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица заказов
CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID REFERENCES customers(id),
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    payment_method VARCHAR(50),
    shipping_address TEXT,
    notes TEXT
);

-- Таблица товаров
CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    category VARCHAR(100),
    stock_quantity INTEGER DEFAULT 0,
    supplier VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица элементов заказа
CREATE TABLE IF NOT EXISTS order_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID REFERENCES orders(id),
    product_id UUID REFERENCES products(id),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    total_price DECIMAL(10,2) NOT NULL
);

-- Таблица пользователей (для демонстрации)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    registration_date DATE DEFAULT CURRENT_DATE,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    subscription_type VARCHAR(50) DEFAULT 'free'
);

-- Вставка демонстрационных данных

-- Клиенты
INSERT INTO customers (name, email, phone, city, country, total_orders, total_spent) VALUES
('Иван Петров', 'ivan@example.com', '+7-999-123-45-67', 'Москва', 'Россия', 15, 45000.00),
('Мария Сидорова', 'maria@example.com', '+7-999-234-56-78', 'Санкт-Петербург', 'Россия', 8, 22000.00),
('Алексей Козлов', 'alex@example.com', '+7-999-345-67-89', 'Екатеринбург', 'Россия', 23, 67000.00),
('Анна Морозова', 'anna@example.com', '+7-999-456-78-90', 'Новосибирск', 'Россия', 12, 34000.00),
('Дмитрий Волков', 'dmitry@example.com', '+7-999-567-89-01', 'Казань', 'Россия', 19, 52000.00),
('Елена Соколова', 'elena@example.com', '+7-999-678-90-12', 'Нижний Новгород', 'Россия', 6, 18000.00),
('Сергей Лебедев', 'sergey@example.com', '+7-999-789-01-23', 'Челябинск', 'Россия', 31, 89000.00),
('Ольга Новикова', 'olga@example.com', '+7-999-890-12-34', 'Самара', 'Россия', 14, 41000.00),
('Павел Медведев', 'pavel@example.com', '+7-999-901-23-45', 'Ростов-на-Дону', 'Россия', 27, 75000.00),
('Татьяна Козлова', 'tatyana@example.com', '+7-999-012-34-56', 'Уфа', 'Россия', 11, 32000.00);

-- Товары
INSERT INTO products (name, description, price, category, stock_quantity, supplier) VALUES
('Ноутбук Dell XPS 13', '13-дюймовый ноутбук с процессором Intel i7', 89999.00, 'Электроника', 25, 'Dell Inc.'),
('iPhone 15 Pro', 'Смартфон Apple с камерой 48 МП', 129999.00, 'Электроника', 15, 'Apple Inc.'),
('Samsung Galaxy S24', 'Android смартфон с AI функциями', 89999.00, 'Электроника', 20, 'Samsung Electronics'),
('MacBook Air M2', '13-дюймовый ноутбук на чипе M2', 109999.00, 'Электроника', 12, 'Apple Inc.'),
('Наушники Sony WH-1000XM5', 'Беспроводные наушники с шумоподавлением', 29999.00, 'Аксессуары', 30, 'Sony Corporation'),
('Планшет iPad Air', '10.9-дюймовый планшет Apple', 59999.00, 'Электроника', 18, 'Apple Inc.'),
('Умные часы Apple Watch', 'Смарт-часы с мониторингом здоровья', 39999.00, 'Аксессуары', 22, 'Apple Inc.'),
('Камера Canon EOS R6', 'Беззеркальная камера для профессионалов', 189999.00, 'Фототехника', 8, 'Canon Inc.'),
('Игровая консоль PlayStation 5', 'Новейшая игровая приставка Sony', 49999.00, 'Игры', 10, 'Sony Interactive Entertainment'),
('Электронная книга Kindle', 'Читалка с подсветкой и Wi-Fi', 15999.00, 'Электроника', 35, 'Amazon');

-- Заказы
INSERT INTO orders (customer_id, total_amount, status, payment_method) VALUES
((SELECT id FROM customers WHERE email = 'ivan@example.com'), 89999.00, 'completed', 'card'),
((SELECT id FROM customers WHERE email = 'maria@example.com'), 29999.00, 'completed', 'card'),
((SELECT id FROM customers WHERE email = 'alex@example.com'), 129999.00, 'completed', 'card'),
((SELECT id FROM customers WHERE email = 'anna@example.com'), 59999.00, 'pending', 'card'),
((SELECT id FROM customers WHERE email = 'dmitry@example.com'), 189999.00, 'completed', 'card'),
((SELECT id FROM customers WHERE email = 'elena@example.com'), 39999.00, 'completed', 'card'),
((SELECT id FROM customers WHERE email = 'sergey@example.com'), 49999.00, 'completed', 'card'),
((SELECT id FROM customers WHERE email = 'olga@example.com'), 89999.00, 'completed', 'card'),
((SELECT id FROM customers WHERE email = 'pavel@example.com'), 109999.00, 'completed', 'card'),
((SELECT id FROM customers WHERE email = 'tatyana@example.com'), 15999.00, 'completed', 'card');

-- Элементы заказов
INSERT INTO order_items (order_id, product_id, quantity, unit_price, total_price) VALUES
((SELECT id FROM orders LIMIT 1), (SELECT id FROM products WHERE name LIKE '%Dell%'), 1, 89999.00, 89999.00),
((SELECT id FROM orders LIMIT 1 OFFSET 1), (SELECT id FROM products WHERE name LIKE '%Sony%'), 1, 29999.00, 29999.00),
((SELECT id FROM orders LIMIT 1 OFFSET 2), (SELECT id FROM products WHERE name LIKE '%iPhone%'), 1, 129999.00, 129999.00),
((SELECT id FROM orders LIMIT 1 OFFSET 3), (SELECT id FROM products WHERE name LIKE '%iPad%'), 1, 59999.00, 59999.00),
((SELECT id FROM orders LIMIT 1 OFFSET 4), (SELECT id FROM products WHERE name LIKE '%Canon%'), 1, 189999.00, 189999.00),
((SELECT id FROM orders LIMIT 1 OFFSET 5), (SELECT id FROM products WHERE name LIKE '%Apple Watch%'), 1, 39999.00, 39999.00),
((SELECT id FROM orders LIMIT 1 OFFSET 6), (SELECT id FROM products WHERE name LIKE '%PlayStation%'), 1, 49999.00, 49999.00),
((SELECT id FROM orders LIMIT 1 OFFSET 7), (SELECT id FROM products WHERE name LIKE '%Samsung%'), 1, 89999.00, 89999.00),
((SELECT id FROM orders LIMIT 1 OFFSET 8), (SELECT id FROM products WHERE name LIKE '%MacBook%'), 1, 109999.00, 109999.00),
((SELECT id FROM orders LIMIT 1 OFFSET 9), (SELECT id FROM products WHERE name LIKE '%Kindle%'), 1, 15999.00, 15999.00);

-- Пользователи
INSERT INTO users (username, email, subscription_type) VALUES
('john_doe', 'john@example.com', 'premium'),
('jane_smith', 'jane@example.com', 'free'),
('bob_wilson', 'bob@example.com', 'premium'),
('alice_brown', 'alice@example.com', 'free'),
('charlie_davis', 'charlie@example.com', 'premium'),
('diana_evans', 'diana@example.com', 'free'),
('edward_frank', 'edward@example.com', 'premium'),
('fiona_garcia', 'fiona@example.com', 'free'),
('george_harris', 'george@example.com', 'premium'),
('helen_ivanov', 'helen@example.com', 'free');

-- Создание индексов для оптимизации
CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);
CREATE INDEX IF NOT EXISTS idx_customers_city ON customers(city);
CREATE INDEX IF NOT EXISTS idx_customers_country ON customers(country);
CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_order_date ON orders(order_date);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_price ON products(price);
CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product_id ON order_items(product_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_subscription_type ON users(subscription_type);

-- Создание представлений для удобства
CREATE OR REPLACE VIEW customer_orders_summary AS
SELECT 
    c.id,
    c.name,
    c.email,
    c.city,
    c.country,
    COUNT(o.id) as total_orders,
    SUM(o.total_amount) as total_spent,
    AVG(o.total_amount) as avg_order_amount,
    MAX(o.order_date) as last_order_date
FROM customers c
LEFT JOIN orders o ON c.id = o.customer_id
GROUP BY c.id, c.name, c.email, c.city, c.country;

CREATE OR REPLACE VIEW product_sales_summary AS
SELECT 
    p.id,
    p.name,
    p.category,
    p.price,
    COUNT(oi.id) as times_ordered,
    SUM(oi.quantity) as total_quantity_sold,
    SUM(oi.total_price) as total_revenue
FROM products p
LEFT JOIN order_items oi ON p.id = oi.product_id
GROUP BY p.id, p.name, p.category, p.price;

-- Логирование успешной инициализации
DO $$
BEGIN
    RAISE NOTICE 'CloverdashBot data database initialized successfully with sample data';
    RAISE NOTICE 'Created % customers, % products, % orders, % users', 
        (SELECT COUNT(*) FROM customers),
        (SELECT COUNT(*) FROM products),
        (SELECT COUNT(*) FROM orders),
        (SELECT COUNT(*) FROM users);
END $$; 