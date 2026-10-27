-- Проверенные запросы системы управления очередью.
-- Параметры ? передаются отдельно; примеры значений указаны в комментариях.

-- 1. Услуги со временем обслуживания не более заданного.
-- catalog/views.py; пример параметров: (7,)
SELECT id, name, average_service_time, is_available
FROM services
WHERE average_service_time <= ?
ORDER BY average_service_time, id;

-- 2. Полный список услуг по названию.
-- catalog/views.py; пример параметров: ()
SELECT id, name, average_service_time, is_available
FROM services
ORDER BY name, id;

-- 3. Услуга по идентификатору.
-- catalog/views.py; пример параметров: (1,)
SELECT id, name, average_service_time, is_available
FROM services WHERE id = ?;

-- 4. Очереди выбранной услуги.
-- catalog/views.py; пример параметров: (1,)
SELECT id, name FROM queues
WHERE service_id = ? ORDER BY name, id;

-- 5. Список очередей с названиями услуг.
-- catalog/views.py; пример параметров: ()
SELECT q.id, q.name, q.is_open, s.name AS service_name
FROM queues AS q
JOIN services AS s ON q.service_id = s.id
ORDER BY q.name, q.id;

-- 6. Карточка очереди и количество активных талонов.
-- catalog/views.py; пример параметров: (1,)
SELECT q.id, q.name, q.service_id, q.is_open,
       s.name AS service_name,
       (q.is_open AND s.is_available) AS can_issue_ticket,
       (SELECT COUNT(*) FROM tickets AS t
        WHERE t.queue_id = q.id
          AND t.status IN ('waiting', 'called')) AS active_count
FROM queues AS q
JOIN services AS s ON q.service_id = s.id
WHERE q.id = ?;

-- 7. Пользователь по идентификатору.
-- catalog/views.py; пример параметров: (1,)
SELECT id, name, role FROM users WHERE id = ?;

-- 8. Доступные очереди без активного талона посетителя.
-- catalog/views.py; пример параметров: (1,)
SELECT q.id, q.name, s.name AS service_name
FROM queues AS q
JOIN services AS s ON q.service_id = s.id
WHERE q.is_open = 1 AND s.is_available = 1
  AND q.id NOT IN (
      SELECT queue_id FROM tickets
      WHERE user_id = ?
        AND status IN ('waiting', 'called')
  )
ORDER BY q.name, q.id;

-- 9. Талоны с фильтром состояния и связанными данными.
-- ticket_pages/views.py; пример параметров: ('active', 'active', 'active')
SELECT t.id, t.status, t.issued_at,
       q.prefix || t.number AS display_number,
       u.name AS user_name, s.name AS service_name
FROM tickets AS t
JOIN queues AS q ON t.queue_id = q.id
JOIN users AS u ON t.user_id = u.id
JOIN services AS s ON t.service_id = s.id
WHERE ? = 'all'
   OR (? = 'active' AND t.status IN ('waiting', 'called'))
   OR (? = 'cancelled' AND t.status = 'cancelled')
ORDER BY t.issued_at, t.id;

-- 10. Карточка талона со сведениями о пользователе, услуге и очереди.
-- ticket_pages/views.py; пример параметров: (1,)
SELECT t.id, t.number, t.queue_id, t.service_id, t.status,
       t.issued_at, q.prefix || t.number AS display_number,
       q.name AS queue_name, s.name AS service_name,
       s.average_service_time, u.name AS user_name
FROM tickets AS t
JOIN queues AS q ON t.queue_id = q.id
JOIN services AS s ON t.service_id = s.id
JOIN users AS u ON t.user_id = u.id
WHERE t.id = ?;

-- 11. Количество активных талонов перед выбранным талоном.
-- ticket_pages/views.py; пример параметров: (1, 25)
SELECT COUNT(*) AS people_ahead FROM tickets
WHERE queue_id = ? AND number < ?
  AND status IN ('waiting', 'called');

-- 12. Общее число активных талонов.
-- ticket_pages/views.py; пример параметров: ()
SELECT COUNT(*) AS active_count FROM tickets
WHERE status IN ('waiting', 'called');

-- 13. Среднее время доступных услуг.
-- ticket_pages/views.py; пример параметров: ()
SELECT AVG(average_service_time) AS average_minutes
FROM services WHERE is_available = 1;

-- 14. Число активных талонов по очередям с порогом нагрузки.
-- ticket_pages/views.py; пример параметров: (0,)
SELECT q.id, q.name, COUNT(t.id) AS ticket_count
FROM queues AS q
LEFT JOIN tickets AS t ON t.queue_id = q.id
    AND t.status IN ('waiting', 'called')
GROUP BY q.id, q.name
HAVING COUNT(t.id) >= ?
ORDER BY ticket_count DESC, q.id;

-- 15. Число активных талонов по услугам.
-- ticket_pages/views.py; пример параметров: ()
SELECT s.id, s.name, COUNT(t.id) AS ticket_count
FROM services AS s
LEFT JOIN tickets AS t ON t.service_id = s.id
    AND t.status IN ('waiting', 'called')
GROUP BY s.id, s.name
ORDER BY ticket_count DESC, s.id;
