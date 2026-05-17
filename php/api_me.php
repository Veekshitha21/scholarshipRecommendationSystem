<?php
// Ensure cookie/session lifetime matches auth endpoints
$lifetime = 86400;
ini_set('session.gc_maxlifetime', $lifetime);
session_set_cookie_params([
    'lifetime' => $lifetime,
    'path' => '/',
    'secure' => isset($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off',
    'httponly' => true,
    'samesite' => 'Lax',
]);
session_start();
header('Content-Type: application/json; charset=utf-8');
if (!empty($_SESSION['user'])) {
    echo json_encode(['authenticated' => true, 'user' => $_SESSION['user']]);
    exit;
}
http_response_code(401);
echo json_encode(['authenticated' => false]);
exit;
