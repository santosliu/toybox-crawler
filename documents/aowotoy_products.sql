CREATE TABLE `aowotoy_products` (
	`id` INT(11) NOT NULL AUTO_INCREMENT,
	`product_id` VARCHAR(30) NOT NULL DEFAULT '',
	`option_id` VARCHAR(30) NOT NULL DEFAULT '',
	`url` VARCHAR(250) NULL DEFAULT '0',
	`name` VARCHAR(250) NOT NULL DEFAULT '0',
	`summary` TEXT NOT NULL,
	`price` INT(11) NOT NULL DEFAULT 0,
	`option` VARCHAR(250) NOT NULL DEFAULT '',
	`detail` TEXT NOT NULL,
	`created_at` DATETIME NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
	PRIMARY KEY (`id`),
	UNIQUE INDEX `option_id` (`option_id`),
	INDEX `pid` (`product_id`)
)
COLLATE='utf8mb4_general_ci'
ENGINE=InnoDB
AUTO_INCREMENT=6343
;
