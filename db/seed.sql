-- Reference data for Sistema Floreria
-- Ejecutar en este orden:
--   mysql -u user -p floreriadb < db/schema.sql
--   mysql -u user -p floreriadb < db/extension.sql
--   mysql -u user -p floreriadb < db/seed.sql

USE floreriadb;

INSERT INTO roles (name, description) VALUES
  ('ADMIN', 'Acceso completo al sistema'),
  ('SALES', 'Gestiona clientes, pedidos y cobros'),
  ('LOGISTICS', 'Gestiona envios y seguimiento')
ON DUPLICATE KEY UPDATE description = VALUES(description);

INSERT INTO users (
  role_id,
  first_name,
  last_name,
  email,
  password_hash,
  is_active,
  must_reset_password
) SELECT
  r.id,
  'Administrador',
  'Principal',
  'admin@floreria.local',
  '$2b$12$WwLyUGFogXNUermta5iMPOP05Kr8rBAU0XaCga07ik1N41OcOUyXa',
  1,
  0
FROM roles r
WHERE r.name = 'ADMIN'
ON DUPLICATE KEY UPDATE
  role_id = VALUES(role_id),
  first_name = VALUES(first_name),
  last_name = VALUES(last_name),
  is_active = VALUES(is_active);

INSERT INTO payment_methods (code, name, description) VALUES
  ('CASH', 'Efectivo', 'Pago presencial en efectivo'),
  ('CARD', 'Tarjeta de crédito/débito', 'Pago con tarjeta via POS o gateway'),
  ('BANK_TRANSFER', 'Transferencia bancaria', 'Transferencia a la cuenta bancaria'),
  ('MOBILE_WALLET', 'Billetera virtual', 'Pago con billetera virtual o QR')
ON DUPLICATE KEY UPDATE name = VALUES(name), description = VALUES(description);

INSERT INTO logistic_statuses (code, name, description) VALUES
  ('PENDING_PICKUP', 'Pendiente de retiro', 'Pedido listo esperando retiro del transportista'),
  ('IN_TRANSIT', 'En tránsito', 'Envío en camino al cliente'),
  ('DELIVERED', 'Entregado', 'Envío entregado al cliente'),
  ('RETURNED', 'Devuelto', 'El envío fue devuelto a origen'),
  ('CANCELLED', 'Cancelado', 'El envío fue cancelado antes de salir')
ON DUPLICATE KEY UPDATE name = VALUES(name), description = VALUES(description);

