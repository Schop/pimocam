<?php
require __DIR__ . '/auth.php';

$dir = rtrim($config['data_dir'], '/') . '/photos';
$files = is_dir($dir) ? glob($dir . '/*.jpg') : [];
usort($files, fn($a, $b) => filemtime($b) - filemtime($a));
$files = array_slice($files, 0, 25);
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Door Camera - Photos (Remote)</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <?php include __DIR__ . '/_nav.php'; ?>
    <div class="container">
        <h1 class="mb-4">Door Camera - Photos (Remote Backup)</h1>
        <p class="text-muted">Showing <?= count($files) ?> most recent photos</p>
        <div class="row">
            <?php foreach ($files as $path):
                $name = basename($path);
                $mtime = date('Y-m-d H:i:s', filemtime($path));
                $json_path = $dir . '/' . pathinfo($name, PATHINFO_FILENAME) . '.json';
                $trigger = is_file($json_path) ? json_decode(file_get_contents($json_path), true) : null;
                $mediaUrl = 'media.php?type=photos&name=' . rawurlencode($name);
            ?>
            <div class="col-md-3 mb-3">
                <div class="card">
                    <a href="<?= htmlspecialchars($mediaUrl) ?>" target="_blank">
                        <img src="<?= htmlspecialchars($mediaUrl) ?>" class="card-img-top" style="height: 150px; object-fit: cover;">
                    </a>
                    <div class="card-body">
                        <h3 class="card-title text-center"><?= htmlspecialchars($mtime) ?></h3>
                        <p class="card-text">
                            File: <?= htmlspecialchars($name) ?>
                            <?php if ($trigger): ?>
                            <br>
                            <span class="text-muted">
                                Triggered at area <?= (int)$trigger['contour_area'] ?>
                                (threshold <?= htmlspecialchars($trigger['contour_threshold']) ?>, sensitivity <?= htmlspecialchars($trigger['thresh_value']) ?>)
                                <?php if (!empty($trigger['bbox'])): ?>
                                <br>Location: (<?= htmlspecialchars(implode(', ', $trigger['bbox'])) ?>)
                                <?php endif; ?>
                            </span>
                            <?php endif; ?>
                        </p>
                    </div>
                </div>
            </div>
            <?php endforeach; ?>
        </div>
    </div>
</body>
</html>
