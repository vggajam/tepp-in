CREATE TABLE `stations` (
  `stn_code` varchar(12) NOT NULL,
  `stn_name` varchar(50) DEFAULT NULL,
  `trains_cnt` int(11) DEFAULT '0',
  PRIMARY KEY (`stn_code`),
  UNIQUE KEY `stn_code_UNIQUE` (`stn_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8

CREATE TABLE `trains` (
  `train_no` varchar(7) NOT NULL,
  `train_name` varchar(100) NOT NULL DEFAULT 'NA',
  `src_stn_code` varchar(10) NOT NULL,
  `dest_stn_code` varchar(10) NOT NULL,
  `MON` tinyint(4) NOT NULL DEFAULT '0',
  `TUE` tinyint(4) NOT NULL DEFAULT '0',
  `WED` tinyint(4) NOT NULL DEFAULT '0',
  `THU` tinyint(4) NOT NULL DEFAULT '0',
  `FRI` tinyint(4) NOT NULL DEFAULT '0',
  `SAT` tinyint(4) NOT NULL DEFAULT '0',
  `SUN` tinyint(4) NOT NULL DEFAULT '0',
  PRIMARY KEY (`train_no`),
  KEY `src_stn_idx` (`src_stn_code`),
  KEY `dest_stn_code_idx` (`dest_stn_code`),
  CONSTRAINT `dest_stn_code` FOREIGN KEY (`dest_stn_code`) REFERENCES `stations` (`stn_code`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `src_stn_code` FOREIGN KEY (`src_stn_code`) REFERENCES `stations` (`stn_code`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
CREATE TABLE `hops` (
  `train_no` varchar(7) NOT NULL,
  `stn_code` varchar(10) NOT NULL,
  `arr_time` time NOT NULL,
  `dept_time` time NOT NULL,
  `hop_index` int(32) unsigned NOT NULL,
  `day` int(32) NOT NULL,
  PRIMARY KEY (`train_no`,`stn_code`),
  KEY `stn_code_idx` (`stn_code`),
  CONSTRAINT `stn_code` FOREIGN KEY (`stn_code`) REFERENCES `stations` (`stn_code`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `train_no` FOREIGN KEY (`train_no`) REFERENCES `trains` (`train_no`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
