<?php
require __DIR__ . '/auth.php';

$dir = rtrim($config['data_dir'], '/') . '/clips';
$files = is_dir($dir) ? glob($dir . '/*.mp4') : [];
usort($files, fn($a, $b) => filemtime($b) - filemtime($a));
$files = array_slice($files, 0, 25);
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Door Camera - Clips (Remote)</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <?php include __DIR__ . '/_nav.php'; ?>
    <div class="container">
        <h1 class="mb-4">Door Camera - Clips (Remote Backup)</h1>
        <p class="text-muted">Showing <?= count($files) ?> most recent clips</p>
        <div class="row">
            <?php foreach ($files as $path):
                $name = basename($path);
                $mtime = date('Y-m-d H:i:s', filemtime($path));
                $mediaUrl = 'media.php?type=clips&name=' . rawurlencode($name);
            ?>
            <div class="col-md-4 mb-3">
                <div class="card">
                    <a href="<?= htmlspecialchars($mediaUrl) ?>" target="_blank">
                        <video class="card-img-top" style="height: 200px; object-fit: cover;" muted>
                            <source src="<?= htmlspecialchars($mediaUrl) ?>" type="video/mp4">
                        </video>
                    </a>
                    <div class="card-body">
                        <h3 class="card-title text-center"><?= htmlspecialchars($mtime) ?></h3>
                        <p class="card-text">File: <?= htmlspecialchars($name) ?></p>
                    </div>
                </div>
            </div>
            <?php endforeach; ?>
        </div>
    </div>
</body>
</html>
