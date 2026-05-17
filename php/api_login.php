<?php
require_once __DIR__ . '/db.php';
// Set session cookie lifetime to 24 hours (86400 seconds)
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

$data = $_POST;
if (empty($data)) {
    $raw = file_get_contents('php://input');
    $decoded = json_decode($raw, true);
    if (is_array($decoded)) $data = $decoded;
}

if (empty($data['name']) || empty($data['password'])) {
    http_response_code(400);
    echo json_encode(['success'=>false,'error'=>'Missing credentials']); exit;
}

$name = trim($data['name']);
$password = $data['password'];

try {
    $db = get_db();
    $stmt = $db->prepare('SELECT id,name,email,password FROM users WHERE name = :name OR email = :name LIMIT 1');
    $stmt->execute([':name'=>$name]);
    $user = $stmt->fetch();
    if (!$user || !password_verify($password, $user['password'])) {
        http_response_code(401);
        echo json_encode(['success'=>false,'error'=>'Invalid credentials']); exit;
    }

    // remove password before storing in session
    unset($user['password']);
    $_SESSION['user'] = $user;
    // make session permanent for 24h
    // PHP session cookie already set with 24h lifetime above
    echo json_encode(['success'=>true,'user'=>$user]);
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(['success'=>false,'error'=>'Server error','message'=>$e->getMessage()]);
}
