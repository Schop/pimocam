<?php
require __DIR__ . '/auth.php';

$type = $_GET['type'] ?? '';
$name = $_GET['name'] ?? '';

if (!in_array($type, ['photos', 'clips'], true) || $name === '') {
    http_response_code(404);
    exit;
}

// basename() strips any directory components, so a ../ traversal attempt just
// collapses to a plain filename that (almost certainly) won't exist.
$safeName = basename($name);
$path = rtrim($config['data_dir'], '/') . '/' . $type . '/' . $safeName;

if (!is_file($path)) {
    http_response_code(404);
    exit;
}

$ext = strtolower(pathinfo($safeName, PATHINFO_EXTENSION));
$mimeTypes = [
    'jpg' => 'image/jpeg',
    'jpeg' => 'image/jpeg',
    'png' => 'image/png',
    'mp4' => 'video/mp4',
];
if (!isset($mimeTypes[$ext])) {
    http_response_code(404);
    exit;
}

$size = filesize($path);
$start = 0;
$end = $size - 1;

header('Accept-Ranges: bytes');
header('Content-Type: ' . $mimeTypes[$ext]);

if (isset($_SERVER['HTTP_RANGE'])) {
    if (!preg_match('/bytes=(\d*)-(\d*)/', $_SERVER['HTTP_RANGE'], $matches) || ($matches[1] === '' && $matches[2] === '')) {
        http_response_code(416);
        header('Content-Range: bytes */' . $size);
        exit;
    }
    if ($matches[1] !== '') {
        $start = (int)$matches[1];
    }
    if ($matches[2] !== '') {
        $end = (int)$matches[2];
    }
    if ($start > $end || $start >= $size) {
        http_response_code(416);
        header('Content-Range: bytes */' . $size);
        exit;
    }
    $end = min($end, $size - 1);
    http_response_code(206);
    header('Content-Range: bytes ' . $start . '-' . $end . '/' . $size);
}

$length = $end - $start + 1;
header('Content-Length: ' . $length);

$fp = fopen($path, 'rb');
fseek($fp, $start);
$bytesLeft = $length;
$chunkSize = 8192;
while ($bytesLeft > 0 && !feof($fp)) {
    $read = min($chunkSize, $bytesLeft);
    echo fread($fp, $read);
    flush();
    $bytesLeft -= $read;
}
fclose($fp);
