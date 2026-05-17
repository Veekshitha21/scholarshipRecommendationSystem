<?php
// Direct wrapper in frontend folder to handle login
require_once __DIR__ . '/../php/db.php';
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

    unset($user['password']);
    $_SESSION['user'] = $user;
    echo json_encode(['success'=>true,'user'=>$user]);
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(['success'=>false,'error'=>'Server error']);
}
