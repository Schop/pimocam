<?php
define('CONFIG_PATH', require __DIR__ . '/config_path.php');

session_start();

if (!file_exists(CONFIG_PATH)) {
    http_response_code(500);
    die('config.php not found - set CONFIG_PATH in auth.php');
}
$config = require CONFIG_PATH;

if (empty($_SESSION['authenticated'])) {
    header('Location: login.php');
    exit;
}

if (empty($_SESSION['csrf_token'])) {
    $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
}
