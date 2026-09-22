<?php
require __DIR__ . '/auth.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    die('Method not allowed.');
}

if (!hash_equals($_SESSION['csrf_token'] ?? '', $_POST['csrf_token'] ?? '')) {
    http_response_code(403);
    die('Invalid CSRF token.');
}

$type = $_POST['type'] ?? '';
if (!in_array($type, ['photos', 'clips'], true)) {
    http_response_code(400);
    die('Invalid type.');
}

$dir = rtrim($config['data_dir'], '/') . '/' . $type;
$action = $_POST['action'] ?? '';

// basename() strips any directory components, same protection media.php relies on,
// so neither selected filenames nor the glob below can escape $dir.
if ($action === 'delete_all') {
    $ext = $type === 'photos' ? 'jpg' : 'mp4';
    $matches = is_dir($dir) ? glob($dir . '/*.' . $ext) : [];
    $names = array_map('basename', $matches);
} elseif ($action === 'delete_selected') {
    $names = array_map('basename', (array)($_POST['selected'] ?? []));
} else {
    http_response_code(400);
    die('Invalid action.');
}

$deleted = 0;
foreach ($names as $name) {
    $path = $dir . '/' . $name;
    if (is_file($path) && @unlink($path)) {
        $deleted++;
        if ($type === 'photos') {
            $jsonPath = $dir . '/' . pathinfo($name, PATHINFO_FILENAME) . '.json';
            if (is_file($jsonPath)) {
                @unlink($jsonPath);
            }
        }
    }
}

$_SESSION['flash'] = $deleted === 1 ? '1 file deleted.' : "$deleted files deleted.";

$page = max(1, (int)($_POST['page'] ?? 1));
$redirectTarget = $type === 'photos' ? 'index.php' : 'clips.php';
header('Location: ' . $redirectTarget . '?page=' . $page);
exit;
