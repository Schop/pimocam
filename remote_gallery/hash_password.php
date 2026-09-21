<?php
// One-time-use utility: deploy this to the docroot, use it once to generate the
// password_hash value for config.php, then DELETE this file from the server.
$hash = null;
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['password']) && $_POST['password'] !== '') {
    $hash = password_hash($_POST['password'], PASSWORD_DEFAULT);
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generate password hash</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container py-4">
        <h1 class="mb-4">Generate password hash</h1>
        <p class="text-danger fw-bold">Delete this file from the server after use.</p>
        <form method="post" class="mb-4" style="max-width: 400px;">
            <div class="mb-3">
                <label class="form-label">Password</label>
                <input type="password" name="password" class="form-control" required>
            </div>
            <button type="submit" class="btn btn-primary">Generate hash</button>
        </form>
        <?php if ($hash): ?>
        <p>Paste this into <code>config.php</code> as <code>password_hash</code>:</p>
        <pre class="bg-light p-3 border"><?= htmlspecialchars($hash) ?></pre>
        <?php endif; ?>
    </div>
</body>
</html>
