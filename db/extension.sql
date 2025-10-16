-- Extension schema for inventory tracking and lost order analytics

USE floreriadb;

CREATE TABLE IF NOT EXISTS inventory_movements (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  product_id INT NOT NULL,
  type ENUM('IN','OUT','ADJUST') NOT NULL,
  qty DECIMAL(12,3) NOT NULL,
  unit_cost DECIMAL(12,2) DEFAULT NULL,
  reference VARCHAR(120),
  notes VARCHAR(255),
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  created_by INT DEFAULT NULL,
  CONSTRAINT fk_inventory_movements_product FOREIGN KEY (product_id) REFERENCES products(id),
  CONSTRAINT fk_inventory_movements_user FOREIGN KEY (created_by) REFERENCES users(id)
    ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE INDEX idx_inventory_movements_product_created_at
  ON inventory_movements(product_id, created_at);

CREATE TABLE IF NOT EXISTS inventory_levels (
  product_id INT PRIMARY KEY,
  on_hand DECIMAL(12,3) NOT NULL DEFAULT 0,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_inventory_levels_product FOREIGN KEY (product_id) REFERENCES products(id)
    ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS product_price_history (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  product_id INT NOT NULL,
  price DECIMAL(12,2) NOT NULL,
  cost DECIMAL(12,2) DEFAULT NULL,
  source ENUM('manual','rule','import') NOT NULL DEFAULT 'manual',
  effective_date DATE NOT NULL,
  notes VARCHAR(255),
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_product_price_history_product FOREIGN KEY (product_id) REFERENCES products(id)
    ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE INDEX idx_product_price_history_product_date
  ON product_price_history(product_id, effective_date);

CREATE TABLE IF NOT EXISTS lost_orders (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  date DATE NOT NULL,
  customer_id INT DEFAULT NULL,
  product_id INT NOT NULL,
  qty DECIMAL(12,3) NOT NULL,
  expected_unit_price DECIMAL(12,2) NOT NULL,
  reason ENUM('OUT_OF_STOCK','CANCELLED','OTHER') NOT NULL DEFAULT 'OUT_OF_STOCK',
  notes VARCHAR(255),
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_lost_orders_customer FOREIGN KEY (customer_id) REFERENCES customers(id)
    ON DELETE SET NULL,
  CONSTRAINT fk_lost_orders_product FOREIGN KEY (product_id) REFERENCES products(id)
) ENGINE=InnoDB;

CREATE INDEX idx_lost_orders_product_date
  ON lost_orders(product_id, date);

