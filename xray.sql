-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: May 13, 2026 at 07:13 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `xray`
--

-- --------------------------------------------------------

--
-- Table structure for table `history`
--

CREATE TABLE `history` (
  `id` int(11) NOT NULL,
  `patient_id` int(11) NOT NULL,
  `patient_name` varchar(255) NOT NULL,
  `room_id` int(11) NOT NULL,
  `room_name` varchar(50) NOT NULL,
  `exam_type` varchar(50) NOT NULL,
  `modality_type` enum('DX','CR') NOT NULL,
  `predicted_duration` int(11) DEFAULT NULL,
  `actual_duration` int(11) DEFAULT NULL,
  `is_urgent` tinyint(1) DEFAULT 0,
  `user_id` int(11) DEFAULT NULL,
  `completed_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Dumping data for table `history`
--

INSERT INTO `history` (`id`, `patient_id`, `patient_name`, `room_id`, `room_name`, `exam_type`, `modality_type`, `predicted_duration`, `actual_duration`, `is_urgent`, `completed_at`) VALUES
(1, 2, 'Sara Al-Otaibi', 1, 'X-Ray-1 - Room 1A', 'Chest', 'DX', 6, 19, 1, '2026-05-13 13:24:19'),
(2, 1, 'Nora Al-Ghamdi', 2, 'X-Ray-2 - Room 2B', 'Pelvis', 'DX', 15, 19, 0, '2026-05-13 13:24:24'),
(3, 3, 'Hana Al-Zahrani', 1, 'X-Ray-1 - Room 1A', 'Shoulder', 'CR', 19, 1, 1, '2026-05-13 13:30:24'),
(4, 9, 'Ali Hassan', 1, 'X-Ray-1 - Room 1A', 'Spine', 'DX', 19, 1, 0, '2026-05-13 14:11:17'),
(5, 14, 'Ahmed Al-Rashid', 1, 'X-Ray-1 - Room 1A', 'Hand', 'DX', 9, 9, 0, '2026-05-13 14:21:43'),
(6, 15, 'Ahmed Al-Rashid', 1, 'X-Ray-1 - Room 1A', 'Hand', 'DX', 9, 3, 0, '2026-05-13 14:27:12'),
(7, 4, 'Hana Ibrahim', 2, 'X-Ray-2 - Room 2B', 'Spine', 'CR', 26, 23, 0, '2026-05-13 14:27:15'),
(8, 10, 'Nora Al-Ghamdi', 3, 'X-Ray-3 - Room 1C', 'Spine', 'CR', 26, 23, 0, '2026-05-13 14:27:20'),
(9, 12, 'Omar Al-Qahtani', 4, 'X-Ray-4 - Room 3D', 'Spine', 'DX', 23, 3, 0, '2026-05-13 14:27:23'),
(10, 13, 'Omar Al-Qahtani', 1, 'X-Ray-1 - Room 1A', 'Spine', 'DX', 23, 1, 0, '2026-05-13 14:29:45'),
(11, 11, 'Nora Al-Ghamdi', 2, 'X-Ray-2 - Room 2B', 'Spine', 'CR', 26, 1, 0, '2026-05-13 14:29:51'),
(12, 6, 'Ali Saleh', 3, 'X-Ray-3 - Room 1C', 'Shoulder', 'DX', 14, 1, 0, '2026-05-13 14:29:54'),
(13, 7, 'Ali Saleh', 4, 'X-Ray-4 - Room 3D', 'Shoulder', 'DX', 14, 1, 0, '2026-05-13 14:29:57'),
(14, 19, 'Mohammed Saleh', 4, 'X-Ray-4 - Room 3D', 'Chest', 'DX', 14, 2, 0, '2026-05-13 14:32:14'),
(15, 18, 'Mohammed Saleh', 1, 'X-Ray-1 - Room 1A', 'Chest', 'DX', 14, 2, 0, '2026-05-13 14:32:15'),
(16, 43, 'Khalid Al-Qahtani', 1, 'X-Ray-1 - Room 1A', 'Knee', 'DX', 10, 7, 1, '2026-05-13 14:50:45'),
(17, 50, 'Hana Saleh', 2, 'X-Ray-2 - Room 2B', 'Chest', 'CR', 14, 7, 1, '2026-05-13 14:50:46'),
(18, 51, 'Hana Saleh', 3, 'X-Ray-3 - Room 1C', 'Chest', 'CR', 14, 7, 1, '2026-05-13 14:50:49'),
(19, 42, 'Khalid Al-Qahtani', 4, 'X-Ray-4 - Room 3D', 'Knee', 'DX', 10, 7, 1, '2026-05-13 14:50:50'),
(20, 61, 'Ali Ibrahim', 3, 'X-Ray-3 - Room 1C', 'Chest', 'DX', 12, 10, 1, '2026-05-13 15:02:02'),
(21, 58, 'Nora Abdullah', 4, 'X-Ray-4 - Room 3D', 'Abdomen', 'DX', 16, 8, 0, '2026-05-13 15:02:03'),
(22, 55, 'Sara Al-Qahtani', 1, 'X-Ray-1 - Room 1A', 'Shoulder', 'DX', 14, 9, 0, '2026-05-13 15:02:06'),
(23, 53, 'Maha Al-Zahrani', 2, 'X-Ray-2 - Room 2B', 'Shoulder', 'CR', 22, 10, 0, '2026-05-13 15:02:07');

-- --------------------------------------------------------

--
-- Table structure for table `patients`
--

CREATE TABLE `patients` (
  `id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `patient_age_group` enum('Child','Adult','Elderly') DEFAULT 'Adult',
  `exam_type` varchar(50) NOT NULL,
  `body_part` varchar(50) NOT NULL,
  `modality_type` enum('DX','CR') NOT NULL,
  `is_urgent` tinyint(1) DEFAULT 0,
  `urgency_score` int(11) DEFAULT 5,
  `status` enum('WAITING','ASSIGNED','SCANNING','COMPLETED') DEFAULT 'WAITING',
  `assigned_room_id` int(11) DEFAULT NULL,
  `predicted_duration` int(11) DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  `request_time` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Dumping data for table `patients`
--

INSERT INTO `patients` (`id`, `name`, `patient_age_group`, `exam_type`, `body_part`, `modality_type`, `is_urgent`, `urgency_score`, `status`, `assigned_room_id`, `predicted_duration`, `request_time`) VALUES
(1, 'Nora Al-Ghamdi', 'Adult', 'Pelvis', 'Lower_Limb', 'DX', 0, 4, 'COMPLETED', 2, 15, '2026-05-13 13:04:42'),
(2, 'Sara Al-Otaibi', 'Adult', 'Chest', 'Thorax', 'DX', 1, 9, 'COMPLETED', 1, 6, '2026-05-13 13:04:48'),
(3, 'Hana Al-Zahrani', 'Child', 'Shoulder', 'Upper_Limb', 'CR', 1, 9, 'COMPLETED', 1, 19, '2026-05-13 13:29:38'),
(4, 'Hana Ibrahim', 'Child', 'Spine', 'Spine', 'CR', 0, 2, 'COMPLETED', 2, 26, '2026-05-13 13:36:21'),
(5, 'Hana Al-Rashid', 'Adult', 'Chest', 'Thorax', 'DX', 1, 9, 'COMPLETED', 1, 6, '2026-05-13 13:36:27'),
(6, 'Ali Saleh', 'Adult', 'Shoulder', 'Upper_Limb', 'DX', 0, 2, 'COMPLETED', 3, 14, '2026-05-13 13:41:46'),
(7, 'Ali Saleh', 'Adult', 'Shoulder', 'Upper_Limb', 'DX', 0, 2, 'COMPLETED', 4, 14, '2026-05-13 13:41:46'),
(8, 'Ali Hassan', 'Adult', 'Spine', 'Spine', 'DX', 0, 6, 'COMPLETED', 4, 19, '2026-05-13 13:41:49'),
(9, 'Ali Hassan', 'Adult', 'Spine', 'Spine', 'DX', 0, 6, 'COMPLETED', 1, 19, '2026-05-13 13:41:49'),
(10, 'Nora Al-Ghamdi', 'Adult', 'Spine', 'Spine', 'CR', 0, 1, 'COMPLETED', 3, 26, '2026-05-13 13:41:49'),
(11, 'Nora Al-Ghamdi', 'Adult', 'Spine', 'Spine', 'CR', 0, 1, 'COMPLETED', 2, 26, '2026-05-13 13:41:50'),
(12, 'Omar Al-Qahtani', 'Elderly', 'Spine', 'Spine', 'DX', 0, 3, 'COMPLETED', 4, 23, '2026-05-13 13:41:53'),
(13, 'Omar Al-Qahtani', 'Elderly', 'Spine', 'Spine', 'DX', 0, 3, 'COMPLETED', 1, 23, '2026-05-13 13:41:53'),
(14, 'Ahmed Al-Rashid', 'Adult', 'Hand', 'Upper_Limb', 'DX', 0, 4, 'COMPLETED', 1, 9, '2026-05-13 13:41:53'),
(15, 'Ahmed Al-Rashid', 'Adult', 'Hand', 'Upper_Limb', 'DX', 0, 4, 'COMPLETED', 1, 9, '2026-05-13 13:41:53'),
(16, 'Yusuf Al-Otaibi', 'Adult', 'Shoulder', 'Upper_Limb', 'CR', 0, 5, 'COMPLETED', 3, 22, '2026-05-13 13:41:53'),
(17, 'Yusuf Al-Otaibi', 'Adult', 'Shoulder', 'Upper_Limb', 'CR', 0, 5, 'COMPLETED', 2, 22, '2026-05-13 13:41:53'),
(18, 'Mohammed Saleh', 'Elderly', 'Chest', 'Thorax', 'DX', 0, 1, 'COMPLETED', 1, 14, '2026-05-13 13:41:54'),
(19, 'Mohammed Saleh', 'Elderly', 'Chest', 'Thorax', 'DX', 0, 1, 'COMPLETED', 4, 14, '2026-05-13 13:41:54'),
(20, 'Maha Al-Ghamdi', 'Adult', 'Hand', 'Upper_Limb', 'DX', 1, 9, 'COMPLETED', 4, 7, '2026-05-13 13:41:54'),
(21, 'Maha Al-Ghamdi', 'Adult', 'Hand', 'Upper_Limb', 'DX', 1, 9, 'COMPLETED', 1, 7, '2026-05-13 13:41:54'),
(22, 'Yusuf Al-Rashid', 'Child', 'Abdomen', 'Abdomen', 'DX', 1, 10, 'COMPLETED', 1, 12, '2026-05-13 13:41:57'),
(23, 'Yusuf Al-Rashid', 'Child', 'Abdomen', 'Abdomen', 'DX', 1, 10, 'COMPLETED', 4, 12, '2026-05-13 13:41:57'),
(24, 'Hana Al-Zahrani', 'Adult', 'Knee', 'Lower_Limb', 'DX', 1, 8, 'COMPLETED', NULL, 10, '2026-05-13 14:33:56'),
(25, 'Hana Al-Zahrani', 'Adult', 'Knee', 'Lower_Limb', 'DX', 1, 8, 'COMPLETED', NULL, 10, '2026-05-13 14:33:56'),
(30, 'Maha Al-Otaibi', 'Elderly', 'Hand', 'Upper_Limb', 'CR', 0, 5, 'COMPLETED', NULL, 20, '2026-05-13 14:33:57'),
(31, 'Maha Al-Otaibi', 'Elderly', 'Hand', 'Upper_Limb', 'CR', 0, 5, 'COMPLETED', NULL, 20, '2026-05-13 14:33:57'),
(42, 'Khalid Al-Qahtani', 'Adult', 'Knee', 'Lower_Limb', 'DX', 1, 10, 'COMPLETED', 4, 10, '2026-05-13 14:42:47'),
(43, 'Khalid Al-Qahtani', 'Adult', 'Knee', 'Lower_Limb', 'DX', 1, 10, 'COMPLETED', 1, 10, '2026-05-13 14:42:47'),
(50, 'Hana Saleh', 'Child', 'Chest', 'Thorax', 'CR', 1, 9, 'COMPLETED', 2, 14, '2026-05-13 14:42:48'),
(51, 'Hana Saleh', 'Child', 'Chest', 'Thorax', 'CR', 1, 9, 'COMPLETED', 3, 14, '2026-05-13 14:42:48'),
(53, 'Maha Al-Zahrani', 'Adult', 'Shoulder', 'Upper_Limb', 'CR', 0, 3, 'COMPLETED', 2, 22, '2026-05-13 14:51:05'),
(54, 'Maha Mansour', 'Adult', 'Spine', 'Spine', 'DX', 1, 9, 'COMPLETED', 1, 14, '2026-05-13 14:51:05'),
(55, 'Sara Al-Qahtani', 'Adult', 'Shoulder', 'Upper_Limb', 'DX', 0, 6, 'COMPLETED', 1, 14, '2026-05-13 14:51:06'),
(58, 'Nora Abdullah', 'Adult', 'Abdomen', 'Abdomen', 'DX', 0, 5, 'COMPLETED', 4, 16, '2026-05-13 14:51:19'),
(60, 'Ali Ibrahim', 'Elderly', 'Chest', 'Thorax', 'DX', 1, 7, 'COMPLETED', 4, 12, '2026-05-13 14:51:19'),
(61, 'Ali Ibrahim', 'Elderly', 'Chest', 'Thorax', 'DX', 1, 7, 'COMPLETED', 3, 12, '2026-05-13 14:51:19'),
(77, 'Ahmed Hassan', 'Adult', 'Knee', 'Lower_Limb', 'DX', 0, 6, 'COMPLETED', NULL, 10, '2026-05-13 15:22:31'),
(79, 'Omar Mansour', 'Adult', 'Shoulder', 'Upper_Limb', 'DX', 1, 10, 'COMPLETED', NULL, 7, '2026-05-13 15:22:32'),
(82, 'Maha Al-Otaibi', 'Adult', 'Chest', 'Thorax', 'CR', 0, 3, 'COMPLETED', NULL, 14, '2026-05-13 15:22:32'),
(83, 'Maha Al-Otaibi', 'Adult', 'Chest', 'Thorax', 'CR', 0, 3, 'COMPLETED', NULL, 14, '2026-05-13 15:22:32'),
(84, 'Ahmed Ibrahim', 'Adult', 'Chest', 'Thorax', 'DX', 0, 2, 'SCANNING', 1, 9, '2026-05-13 15:37:24'),
(85, 'Sara Saleh', 'Adult', 'Shoulder', 'Upper_Limb', 'DX', 0, 3, 'COMPLETED', 4, 14, '2026-05-13 15:37:25'),
(86, 'Fatima Abdullah', 'Adult', 'Chest', 'Thorax', 'DX', 1, 8, 'COMPLETED', 1, 5, '2026-05-13 15:37:25'),
(87, 'Khalid Hassan', 'Adult', 'Shoulder', 'Upper_Limb', 'CR', 0, 4, 'COMPLETED', 2, 20, '2026-05-13 15:37:25'),
(88, 'Maha Al-Otaibi', 'Adult', 'Hand', 'Upper_Limb', 'CR', 0, 1, 'COMPLETED', 3, 15, '2026-05-13 15:37:26'),
(89, 'Maha Al-Otaibi', 'Adult', 'Hand', 'Upper_Limb', 'CR', 0, 1, 'COMPLETED', 1, 15, '2026-05-13 15:37:26');

-- --------------------------------------------------------

--
-- Table structure for table `rooms`
--

CREATE TABLE `rooms` (
  `id` int(11) NOT NULL,
  `name` varchar(50) NOT NULL,
  `modality_type` enum('DX','CR') NOT NULL,
  `status` enum('IDLE','SCANNING','CLEANING') DEFAULT 'IDLE',
  `current_patient_id` int(11) DEFAULT NULL,
  `predicted_end_time` datetime DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Dumping data for table `rooms`
--

INSERT INTO `rooms` (`id`, `name`, `modality_type`, `status`, `current_patient_id`, `predicted_end_time`, `user_id`, `created_at`) VALUES
(1, 'X-Ray-1 - Room 1A', 'DX', 'IDLE', NULL, NULL, 1, '2026-05-07 04:39:33'),
(2, 'X-Ray-2 - Room 2B', 'CR', 'IDLE', NULL, NULL, 1, '2026-05-07 04:39:33'),
(3, 'X-Ray-3 - Room 1C', 'CR', 'IDLE', NULL, NULL, 1, '2026-05-07 04:39:33'),
(4, 'X-Ray-4 - Room 3D', 'DX', 'IDLE', NULL, NULL, 1, '2026-05-07 04:39:33');

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `email` varchar(255) NOT NULL,
  `password` varchar(255) NOT NULL,
  `phone_number` varchar(20) DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `profile_image` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id`, `name`, `email`, `password`, `phone_number`, `created_at`, `updated_at`, `profile_image`) VALUES
(1, 'Umar Hasnat', 'umarhasnat3456@gmail.com', 'pbkdf2:sha256:1000000$DRCAKD281Xq6s907$570c2486358480f1f67f01d7bd6682736139ee3a79440981e214f1c9bc659c20', '+923490899512', '2026-04-28 15:18:27', '2026-05-07 03:07:39', NULL),
(2, 'Hamza Hasnat', 'hamzahasnat812@gmail.com', 'pbkdf2:sha256:1000000$z1HEVYINioJKoNtf$c92131d9124a4a7c8b68b0bf95dcf8e0591d5b87aa88cf781bd60fdacfe32c74', '03490899512', '2026-05-13 12:55:23', '2026-05-13 12:55:23', NULL);

-- --------------------------------------------------------

--
-- Table structure for table `user_profile`
--

CREATE TABLE `user_profile` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `profile_picture` varchar(255) DEFAULT NULL,
  `bio` text DEFAULT NULL,
  `phone_number` varchar(20) DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Dumping data for table `user_profile`
--

INSERT INTO `user_profile` (`id`, `user_id`, `profile_picture`, `bio`, `phone_number`, `created_at`, `updated_at`) VALUES
(1, 1, NULL, NULL, NULL, '2026-04-28 15:18:27', '2026-04-28 15:18:27'),
(2, 2, NULL, NULL, NULL, '2026-05-13 12:55:23', '2026-05-13 12:55:23');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `history`
--
ALTER TABLE `history`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `patients`
--
ALTER TABLE `patients`
  ADD PRIMARY KEY (`id`),
  ADD KEY `assigned_room_id` (`assigned_room_id`);

--
-- Indexes for table `rooms`
--
ALTER TABLE `rooms`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `email` (`email`);

--
-- Indexes for table `user_profile`
--
ALTER TABLE `user_profile`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `history`
--
ALTER TABLE `history`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=24;

--
-- AUTO_INCREMENT for table `patients`
--
ALTER TABLE `patients`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=90;

--
-- AUTO_INCREMENT for table `rooms`
--
ALTER TABLE `rooms`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `user_profile`
--
ALTER TABLE `user_profile`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `patients`
--
ALTER TABLE `patients`
  ADD CONSTRAINT `patients_ibfk_1` FOREIGN KEY (`assigned_room_id`) REFERENCES `rooms` (`id`) ON DELETE SET NULL;

--
-- Constraints for table `user_profile`
--
ALTER TABLE `user_profile`
  ADD CONSTRAINT `user_profile_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
