<?php
require __DIR__ . '/auth.php';

$dir = rtrim($config['data_dir'], '/') . '/photos';
$filename = basename($_GET['name'] ?? '');

$images = is_dir($dir) ? glob($dir . '/*.jpg') : [];
$images = array_map('basename', $images);
rsort($images);

$current_index = array_search($filename, $images, true);
if ($current_index === false) {
    http_response_code(404);
    die('Photo not found.');
}
$prev_image = $current_index > 0 ? $images[$current_index - 1] : null;
$next_image = $current_index < count($images) - 1 ? $images[$current_index + 1] : null;
$mediaUrl = 'media.php?type=photos&name=' . rawurlencode($filename);
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>View Photo (Remote)</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .nav-buttons {
            position: fixed;
            top: 50%;
            transform: translateY(-50%);
            z-index: 1000;
        }
        .nav-buttons.left { left: 20px; }
        .nav-buttons.right { right: 20px; }
    </style>
</head>
<body>
    <?php include __DIR__ . '/_nav.php'; ?>
    <div class="container">
        <?php if ($prev_image): ?>
        <div class="nav-buttons left">
            <a href="view.php?name=<?= rawurlencode($prev_image) ?>" class="btn btn-primary btn-lg" title="Previous photo">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
                    <path fill-rule="evenodd" d="M11.354 1.646a.5.5 0 0 1 0 .708L5.707 8l5.647 5.646a.5.5 0 0 1-.708.708l-6-6a.5.5 0 0 1 0-.708l6-6a.5.5 0 0 1 .708 0z"/>
                </svg>
            </a>
        </div>
        <?php endif; ?>

        <?php if ($next_image): ?>
        <div class="nav-buttons right">
            <a href="view.php?name=<?= rawurlencode($next_image) ?>" class="btn btn-primary btn-lg" title="Next photo">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
                    <path fill-rule="evenodd" d="M4.646 1.646a.5.5 0 0 1 .708 0l6 6a.5.5 0 0 1 0 .708l-6 6a.5.5 0 0 1-.708-.708L10.293 8 4.646 2.354a.5.5 0 0 1 0-.708z"/>
                </svg>
            </a>
        </div>
        <?php endif; ?>

        <div class="text-center">
            <img src="<?= htmlspecialchars($mediaUrl) ?>" class="img-fluid" alt="<?= htmlspecialchars($filename) ?>">
        </div>
        <p class="mt-3 text-center"><?= htmlspecialchars($filename) ?></p>

        <script>
            document.addEventListener('keydown', function(e) {
                <?php if ($prev_image): ?>
                if (e.key === 'ArrowLeft') {
                    window.location.href = 'view.php?name=<?= rawurlencode($prev_image) ?>';
                }
                <?php endif; ?>
                <?php if ($next_image): ?>
                if (e.key === 'ArrowRight') {
                    window.location.href = 'view.php?name=<?= rawurlencode($next_image) ?>';
                }
                <?php endif; ?>
            });
        </script>
    </div>
</body>
</html>
