<?php
define('CONFIG_PATH', require __DIR__ . '/config_path.php');

session_start();

if (!file_exists(CONFIG_PATH)) {
    http_response_code(500);
    die('config.php not found - set CONFIG_PATH in login.php');
}
$config = require CONFIG_PATH;

if (!empty($_SESSION['authenticated'])) {
    header('Location: index.php');
    exit;
}

$error = null;
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $username = $_POST['username'] ?? '';
    $password = $_POST['password'] ?? '';
    if (hash_equals($config['username'], $username) && password_verify($password, $config['password_hash'])) {
        session_regenerate_id(true);
        $_SESSION['authenticated'] = true;
        header('Location: index.php');
        exit;
    }
    $error = 'Invalid username or password.';
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Door Camera - Login</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container py-5" style="max-width: 400px;">
        <h1 class="mb-4">Door Camera Login</h1>
        <?php if ($error): ?>
        <div class="alert alert-danger"><?= htmlspecialchars($error) ?></div>
        <?php endif; ?>
        <form method="post">
            <div class="mb-3">
                <label class="form-label">Username</label>
                <input type="text" name="username" class="form-control" required autofocus>
            </div>
            <div class="mb-3">
                <label class="form-label">Password</label>
                <input type="password" name="password" class="form-control" required>
            </div>
            <button type="submit" class="btn btn-primary">Log in</button>
        </form>
    </div>
</body>
</html>
