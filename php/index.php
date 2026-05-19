<?php
// Router for serving frontend and PHP API endpoints
$uri = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
$uri = trim($uri, '/');

// If the app is hosted in a subdirectory (e.g. /scholarshipRecommmendation),
// strip the directory name from the URI so routing works when served under
// Apache's subpath. This uses the current folder name as the base.
$baseDir = basename(dirname(__DIR__));
if ($baseDir && strpos($uri, $baseDir . '/') === 0) {
    $uri = substr($uri, strlen($baseDir) + 1);
} elseif ($uri === $baseDir) {
    $uri = '';
}

// Debug header to help diagnose serving under subdirectory
header('X-Debug-URI: ' . $uri);

// Serve PHP API endpoints
if (preg_match('#^php/(.+\.php)$#', $uri, $m)) {
    require __DIR__ . '/' . $m[1];
    exit;
}

// Serve frontend HTML/CSS/JS files
if (preg_match('#^frontend/(.+)$#', $uri, $m)) {
    $file = dirname(__DIR__) . '/frontend/' . $m[1];
    if (file_exists($file) && is_file($file)) {
        // Guess MIME type
        $ext = pathinfo($file, PATHINFO_EXTENSION);
        $mimes = [
            'html' => 'text/html',
            'css' => 'text/css',
            'js' => 'application/javascript',
            'json' => 'application/json',
            'png' => 'image/png',
            'jpg' => 'image/jpeg',
            'gif' => 'image/gif',
            'svg' => 'image/svg+xml',
            'woff' => 'font/woff',
            'woff2' => 'font/woff2',
        ];
        $mime = $mimes[$ext] ?? 'application/octet-stream';
        header('Content-Type: ' . $mime);
        readfile($file);
        exit;
    }
}

// Default to welcome page
if (!$uri || $uri === 'index.php') {
    readfile(dirname(__DIR__) . '/frontend/welcome.html');
    exit;
}

// Not found
http_response_code(404);
header('Content-Type: application/json');
echo json_encode(['error' => 'Not found']);
