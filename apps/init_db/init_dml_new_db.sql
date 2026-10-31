-- ============================================================
-- Тестовые данные для платформы умного дома (MVP)
-- Порядок: user_account → house → room → user_house_room
--          → device → device_state → telemetry_reading → command_log
-- ============================================================

BEGIN;

-- ============================================================
-- 1. user_account — пользователи
-- ============================================================
INSERT INTO user_account (id, name, email, password_hash, role) VALUES
    (1, 'Иван Петров',     'ivan@example.com',   '$2b$12$hash1...', 'admin'),
    (2, 'Мария Сидорова',  'maria@example.com',  '$2b$12$hash2...', 'operator'),
    (3, 'Алексей Кузнецов','alex@example.com',   '$2b$12$hash3...', 'resident'),
    (4, 'Ольга Смирнова',  'olga@example.com',   '$2b$12$hash4...', 'resident'),
    (5, 'Дмитрий Волков',  'dmitry@example.com', '$2b$12$hash5...', 'resident');

-- ============================================================
-- 2. house — дома
-- ============================================================
INSERT INTO house (id, name, address) VALUES
    (1, 'Дом на Ленина',   'г. Москва, ул. Ленина, д. 10'),
    (2, 'Дача в Подмосковье', 'МО, д. Сосновка, ул. Лесная, д. 5'),
    (3, 'Квартира на Невском', 'г. Санкт-Петербург, Невский пр., д. 100, кв. 42');

-- ============================================================
-- 3. room — комнаты
-- ============================================================
INSERT INTO room (id, house_id, name) VALUES
    -- Дом 1
    (1, 1, 'Гостиная'),
    (2, 1, 'Кухня'),
    (3, 1, 'Спальня'),
    (4, 1, 'Прихожая'),
    -- Дом 2
    (5, 2, 'Гостиная'),
    (6, 2, 'Кухня'),
    (7, 2, 'Терраса'),
    -- Дом 3
    (8, 3, 'Спальня'),
    (9, 3, 'Кухня');

-- ============================================================
-- 4. user_house_room — привязки пользователей к локациям
--    (NULL в room_id = доступ ко всему дому)
-- ============================================================
INSERT INTO user_house_room (id, user_account_id, house_id, room_id, is_active) VALUES
    -- Иван — админ всех трёх домов (доступ к дому целиком)
    (1, 1, 1, NULL, TRUE),
    (2, 1, 2, NULL, TRUE),
    (3, 1, 3, NULL, TRUE),
    -- Мария — оператор дома 1
    (4, 2, 1, NULL, TRUE),
    -- Алексей — житель дома 1, только гостиная и кухня
    (5, 3, 1, 1, TRUE),
    (6, 3, 1, 2, TRUE),
    -- Ольга — житель дома 2, только гостиная
    (7, 4, 2, 5, TRUE),
    -- Дмитрий — житель дома 3, вся квартира
    (8, 5, 3, NULL, TRUE);

-- ============================================================
-- 5. device — устройства
-- ============================================================
INSERT INTO device (id, house_id, room_id, type, vendor, model, firmware_version, online, last_seen_at) VALUES
    -- Дом 1
    (1,  1, 1, 'sensor',   'Xiaomi',  'Mi Temperature 2', '1.0.3', TRUE,  NOW() - INTERVAL '2 minutes'),
    (2,  1, 1, 'actuator', 'Shelly',  'Plug S',           '2.1.0', TRUE,  NOW() - INTERVAL '1 minute'),
    (3,  1, 2, 'sensor',   'Aqara',   'Motion Sensor',    '1.2.1', TRUE,  NOW() - INTERVAL '5 minutes'),
    (4,  1, 2, 'actuator', 'Shelly',  'Relay 1',          '2.0.9', FALSE, NOW() - INTERVAL '3 hours'),
    (5,  1, 3, 'camera',   'TP-Link', 'Tapo C200',        '1.1.5', TRUE,  NOW() - INTERVAL '30 seconds'),
    (6,  1, 4, 'gateway',  'Zigbee',  'CC2531',           '3.0.0', TRUE,  NOW() - INTERVAL '1 minute'),
    -- Дом 2
    (7,  2, 5, 'sensor',   'Xiaomi',  'Mi Temperature 2', '1.0.3', TRUE,  NOW() - INTERVAL '4 minutes'),
    (8,  2, 7, 'sensor',   'Aqara',   'Motion Sensor',    '1.2.1', TRUE,  NOW() - INTERVAL '10 minutes'),
    (9,  2, 6, 'actuator', 'Shelly',  'Plug S',           '2.1.0', TRUE,  NOW() - INTERVAL '2 minutes'),
    -- Дом 3
    (10, 3, 8, 'sensor',   'Xiaomi',  'Mi Temperature 2', '1.0.3', TRUE,  NOW() - INTERVAL '1 minute'),
    (11, 3, 9, 'actuator', 'Shelly',  'Relay 1',          '2.0.9', TRUE,  NOW() - INTERVAL '3 minutes'),
    (12, 3, NULL, 'gateway','Zigbee', 'CC2531',           '3.0.0', FALSE, NOW() - INTERVAL '1 day');

-- ============================================================
-- 6. device_state — текущие показатели (key-value)
-- ============================================================
INSERT INTO device_state (device_id, property, value, updated_at) VALUES
    (1,  'temperature', '23.5',  NOW() - INTERVAL '2 minutes'),
    (1,  'humidity',    '45',    NOW() - INTERVAL '2 minutes'),
    (2,  'power',       '120.5', NOW() - INTERVAL '1 minute'),
    (2,  'switch',      'on',    NOW() - INTERVAL '1 minute'),
    (3,  'motion',      'false', NOW() - INTERVAL '5 minutes'),
    (4,  'switch',      'off',   NOW() - INTERVAL '3 hours'),
    (5,  'recording',   'true',  NOW() - INTERVAL '30 seconds'),
    (7,  'temperature', '19.0',  NOW() - INTERVAL '4 minutes'),
    (7,  'humidity',    '52',    NOW() - INTERVAL '4 minutes'),
    (8,  'motion',      'true',  NOW() - INTERVAL '10 minutes'),
    (9,  'power',       '85.0',  NOW() - INTERVAL '2 minutes'),
    (9,  'switch',      'on',    NOW() - INTERVAL '2 minutes'),
    (10, 'temperature', '22.0',  NOW() - INTERVAL '1 minute'),
    (11, 'switch',      'off',   NOW() - INTERVAL '3 minutes');

-- ============================================================
-- 7. telemetry_reading — сырые показания (append-only)
--    generate_series для реалистичного временного ряда
-- ============================================================

-- Датчик 1 (Дом 1, Гостиная): температура + влажность за последние 2 часа
INSERT INTO telemetry_reading (device_id, metric, value, unit, recorded_at)
SELECT
    1,
    'temperature',
    22.0 + random() * 4,          -- 22–26 °C
    '°C',
    NOW() - (INTERVAL '5 minutes' * g)
FROM generate_series(1, 24) AS g;

INSERT INTO telemetry_reading (device_id, metric, value, unit, recorded_at)
SELECT
    1,
    'humidity',
    40.0 + random() * 15,         -- 40–55 %
    '%',
    NOW() - (INTERVAL '5 minutes' * g)
FROM generate_series(1, 24) AS g;

-- Датчик 3 (Дом 1, Кухня): motion — 0/1
INSERT INTO telemetry_reading (device_id, metric, value, unit, recorded_at)
SELECT
    3,
    'motion',
    (random() < 0.3)::int,        -- 30% времени движение
    NULL,
    NOW() - (INTERVAL '10 minutes' * g)
FROM generate_series(1, 12) AS g;

-- Датчик 2 (Дом 1, Гостиная): power
INSERT INTO telemetry_reading (device_id, metric, value, unit, recorded_at)
SELECT
    2,
    'power',
    100.0 + random() * 50,        -- 100–150 Вт
    'W',
    NOW() - (INTERVAL '15 minutes' * g)
FROM generate_series(1, 8) AS g;

-- Датчик 7 (Дом 2, Гостиная): температура
INSERT INTO telemetry_reading (device_id, metric, value, unit, recorded_at)
SELECT
    7,
    'temperature',
    18.0 + random() * 3,
    '°C',
    NOW() - (INTERVAL '5 minutes' * g)
FROM generate_series(1, 24) AS g;

-- Датчик 10 (Дом 3, Спальня): температура
INSERT INTO telemetry_reading (device_id, metric, value, unit, recorded_at)
SELECT
    10,
    'temperature',
    21.0 + random() * 3,
    '°C',
    NOW() - (INTERVAL '10 minutes' * g)
FROM generate_series(1, 12) AS g;

-- ============================================================
-- 8. command_log — журнал команд устройству
-- ============================================================
INSERT INTO command_log (device_id, command, status, reason, created_at, executed_at) VALUES
    -- Успешные команды
    (2, 'switch_on',  'executed', NULL,                  NOW() - INTERVAL '2 hours',  NOW() - INTERVAL '2 hours' + INTERVAL '2 seconds'),
    (4, 'switch_off', 'executed', NULL,                  NOW() - INTERVAL '3 hours',  NOW() - INTERVAL '3 hours' + INTERVAL '1 second'),
    (9, 'switch_on',  'executed', NULL,                  NOW() - INTERVAL '1 hour',   NOW() - INTERVAL '1 hour' + INTERVAL '3 seconds'),
    (11, 'switch_off', 'executed', NULL,                  NOW() - INTERVAL '30 minutes', NOW() - INTERVAL '30 minutes' + INTERVAL '2 seconds'),
    -- Проваленные
    (4, 'switch_on',  'failed',   'Device offline',      NOW() - INTERVAL '4 hours',  NOW() - INTERVAL '4 hours' + INTERVAL '5 seconds'),
    (12, 'reboot',     'failed',   'Gateway not responding', NOW() - INTERVAL '1 day', NOW() - INTERVAL '1 day' + INTERVAL '10 seconds'),
    -- Таймауты
    (4, 'toggle',     'timeout',  'No response in 30s',  NOW() - INTERVAL '5 hours',  NOW() - INTERVAL '5 hours' + INTERVAL '30 seconds'),
    (12, 'ping',       'timeout',  'No response in 30s',  NOW() - INTERVAL '2 days',   NOW() - INTERVAL '2 days' + INTERVAL '30 seconds');

-- ============================================================
-- Сброс последовательностей, чтобы BIGSERIAL продолжил
-- с корректного значения после явных id
-- ============================================================
SELECT setval(pg_get_serial_sequence('user_account',      'id'), (SELECT MAX(id) FROM user_account));
SELECT setval(pg_get_serial_sequence('house',             'id'), (SELECT MAX(id) FROM house));
SELECT setval(pg_get_serial_sequence('room',              'id'), (SELECT MAX(id) FROM room));
SELECT setval(pg_get_serial_sequence('user_house_room',   'id'), (SELECT MAX(id) FROM user_house_room));
SELECT setval(pg_get_serial_sequence('device',            'id'), (SELECT MAX(id) FROM device));
SELECT setval(pg_get_serial_sequence('device_state',      'id'), (SELECT MAX(id) FROM device_state));
SELECT setval(pg_get_serial_sequence('telemetry_reading', 'id'), (SELECT MAX(id) FROM telemetry_reading));
SELECT setval(pg_get_serial_sequence('command_log',       'id'), (SELECT MAX(id) FROM command_log));

COMMIT;
