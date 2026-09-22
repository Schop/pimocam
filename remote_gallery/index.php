<?php
require __DIR__ . '/auth.php';

$perPage = 24;
$dir = rtrim($config['data_dir'], '/') . '/photos';
$files = is_dir($dir) ? glob($dir . '/*.jpg') : [];
usort($files, fn($a, $b) => filemtime($b) - filemtime($a));

$total = count($files);
$totalPages = max(1, (int)ceil($total / $perPage));
$page = max(1, min($totalPages, (int)($_GET['page'] ?? 1)));
$pageFiles = array_slice($files, ($page - 1) * $perPage, $perPage);

$flash = $_SESSION['flash'] ?? null;
unset($_SESSION['flash']);
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
        <?php if ($flash): ?>
        <div class="alert alert-success"><?= htmlspecialchars($flash) ?></div>
        <?php endif; ?>
        <p class="text-muted">
            Showing <?= count($pageFiles) ?> of <?= $total ?> photos
            (page <?= $page ?> of <?= $totalPages ?>)
        </p>

        <form method="post" action="delete.php" id="deleteForm">
            <input type="hidden" name="type" value="photos">
            <input type="hidden" name="page" value="<?= $page ?>">
            <input type="hidden" name="csrf_token" value="<?= htmlspecialchars($_SESSION['csrf_token']) ?>">

            <div class="d-flex align-items-center gap-3 mb-3">
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" id="selectAll">
                    <label class="form-check-label" for="selectAll">Select all on this page</label>
                </div>
                <button type="submit" name="action" value="delete_selected" class="btn btn-danger btn-sm" onclick="return confirmDeleteSelected()">Delete Selected</button>
                <button type="submit" name="action" value="delete_all" class="btn btn-outline-danger btn-sm" onclick="return confirm('Delete ALL <?= $total ?> photos? This cannot be undone.')">Delete All (<?= $total ?>)</button>
            </div>

            <div class="row">
                <?php foreach ($pageFiles as $path):
                    $name = basename($path);
                    $mtime = date('M j, Y \a\t H:i', filemtime($path));
                    $json_path = $dir . '/' . pathinfo($name, PATHINFO_FILENAME) . '.json';
                    $trigger = is_file($json_path) ? json_decode(file_get_contents($json_path), true) : null;
                    $mediaUrl = 'media.php?type=photos&name=' . rawurlencode($name);
                    $viewUrl = 'view.php?name=' . rawurlencode($name);
                ?>
                <div class="col-md-3 mb-3">
                    <div class="card">
                        <div class="position-absolute top-0 start-0 m-2 bg-white bg-opacity-75 rounded p-1">
                            <input class="form-check-input select-photo" type="checkbox" name="selected[]" value="<?= htmlspecialchars($name) ?>" form="deleteForm">
                        </div>
                        <a href="<?= htmlspecialchars($viewUrl) ?>">
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
                                    (threshold <?= htmlspecialchars($trigger['contour_threshold']) ?>, max <?= htmlspecialchars($trigger['max_contour_area'] ?? '?') ?>,
                                    sensitivity <?= htmlspecialchars($trigger['thresh_value']) ?>)
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
        </form>

        <?php if ($totalPages > 1): ?>
        <nav aria-label="Photo pages">
            <ul class="pagination">
                <li class="page-item <?= $page <= 1 ? 'disabled' : '' ?>">
                    <a class="page-link" href="?page=<?= $page - 1 ?>">Previous</a>
                </li>
                <li class="page-item disabled"><span class="page-link">Page <?= $page ?> of <?= $totalPages ?></span></li>
                <li class="page-item <?= $page >= $totalPages ? 'disabled' : '' ?>">
                    <a class="page-link" href="?page=<?= $page + 1 ?>">Next</a>
                </li>
            </ul>
        </nav>
        <?php endif; ?>
    </div>

    <script>
        document.getElementById('selectAll').addEventListener('change', function () {
            document.querySelectorAll('.select-photo').forEach(cb => cb.checked = this.checked);
        });

        function confirmDeleteSelected() {
            var checked = document.querySelectorAll('.select-photo:checked').length;
            if (checked === 0) {
                alert('Select at least one photo to delete.');
                return false;
            }
            return confirm('Delete ' + checked + ' selected photo(s)? This cannot be undone.');
        }
    </script>
</body>
</html>
