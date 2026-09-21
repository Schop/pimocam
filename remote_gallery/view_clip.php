<?php
require __DIR__ . '/auth.php';

$dir = rtrim($config['data_dir'], '/') . '/clips';
$filename = basename($_GET['name'] ?? '');

$videos = is_dir($dir) ? glob($dir . '/*.mp4') : [];
$videos = array_map('basename', $videos);
rsort($videos);

$current_index = array_search($filename, $videos, true);
if ($current_index === false) {
    http_response_code(404);
    die('Clip not found.');
}
$prev_video = $current_index > 0 ? $videos[$current_index - 1] : null;
$next_video = $current_index < count($videos) - 1 ? $videos[$current_index + 1] : null;
$mediaUrl = 'media.php?type=clips&name=' . rawurlencode($filename);
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>View Clip (Remote)</title>
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
        <?php if ($prev_video): ?>
        <div class="nav-buttons left">
            <a href="view_clip.php?name=<?= rawurlencode($prev_video) ?>" class="btn btn-primary btn-lg" title="Previous clip">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
                    <path fill-rule="evenodd" d="M11.354 1.646a.5.5 0 0 1 0 .708L5.707 8l5.647 5.646a.5.5 0 0 1-.708.708l-6-6a.5.5 0 0 1 0-.708l6-6a.5.5 0 0 1 .708 0z"/>
                </svg>
            </a>
        </div>
        <?php endif; ?>

        <?php if ($next_video): ?>
        <div class="nav-buttons right">
            <a href="view_clip.php?name=<?= rawurlencode($next_video) ?>" class="btn btn-primary btn-lg" title="Next clip">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
                    <path fill-rule="evenodd" d="M4.646 1.646a.5.5 0 0 1 .708 0l6 6a.5.5 0 0 1 0 .708l-6 6a.5.5 0 0 1-.708-.708L10.293 8 4.646 2.354a.5.5 0 0 1 0-.708z"/>
                </svg>
            </a>
        </div>
        <?php endif; ?>

        <div class="text-center">
            <video src="<?= htmlspecialchars($mediaUrl) ?>" class="img-fluid" controls autoplay></video>
        </div>
        <p class="mt-3 text-center"><?= htmlspecialchars($filename) ?></p>

        <script>
            document.addEventListener('keydown', function(e) {
                <?php if ($prev_video): ?>
                if (e.key === 'ArrowLeft') {
                    window.location.href = 'view_clip.php?name=<?= rawurlencode($prev_video) ?>';
                }
                <?php endif; ?>
                <?php if ($next_video): ?>
                if (e.key === 'ArrowRight') {
                    window.location.href = 'view_clip.php?name=<?= rawurlencode($next_video) ?>';
                }
                <?php endif; ?>
            });
        </script>
    </div>
</body>
</html>
