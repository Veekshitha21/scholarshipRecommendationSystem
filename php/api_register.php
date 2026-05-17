<?php
require_once __DIR__ . '/db.php';
// Set session cookie lifetime to 24 hours for immediate login after register
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

// Accept JSON or form-encoded POST
$data = $_POST;
if (empty($data)) {
    $raw = file_get_contents('php://input');
    $decoded = json_decode($raw, true);
    if (is_array($decoded)) $data = $decoded;
}

$required = ['name','email','password'];
foreach ($required as $r) {
    if (empty($data[$r])) {
        http_response_code(400);
        echo json_encode(['success'=>false,'error'=>"Missing field: {$r}"]); exit;
    }
}

$name = trim($data['name']);
$email = trim($data['email']);
$password = $data['password'];

try {
    $db = get_db();
    // Ensure users table exists (simple schema)
    $db->exec("CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(191) NOT NULL,
        email VARCHAR(191) NOT NULL UNIQUE,
        password VARCHAR(255) NOT NULL,
        education VARCHAR(100) DEFAULT NULL,
        category VARCHAR(100) DEFAULT NULL,
        phone VARCHAR(32) DEFAULT NULL,
        income BIGINT DEFAULT NULL,
        disability VARCHAR(32) DEFAULT NULL,
        gender VARCHAR(32) DEFAULT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;");

    // check existing
    $stmt = $db->prepare('SELECT id FROM users WHERE email = :email OR name = :name LIMIT 1');
    $stmt->execute([':email'=>$email,':name'=>$name]);
    if ($stmt->fetch()) {
        http_response_code(409);
        echo json_encode(['success'=>false,'error'=>'User with same name or email already exists']); exit;
    }

    $hash = password_hash($password, PASSWORD_DEFAULT);
    $insert = $db->prepare('INSERT INTO users (name,email,password,education,category,phone,income,disability,gender) VALUES (:name,:email,:password,:education,:category,:phone,:income,:disability,:gender)');
    $insert->execute([
        ':name'=>$name,
        ':email'=>$email,
        ':password'=>$hash,
        ':education'=> $data['education'] ?? null,
        ':category'=> $data['category'] ?? null,
        ':phone'=> $data['phone'] ?? null,
        ':income'=> !empty($data['income']) ? $data['income'] : null,
        ':disability'=> $data['disability'] ?? null,
        ':gender'=> $data['gender'] ?? null,
    ]);

    $id = $db->lastInsertId();
    // Log user in immediately
    $_SESSION['user'] = ['id' => $id, 'name' => $name, 'email' => $email];
    echo json_encode(['success'=>true,'id'=>$id,'user'=>$_SESSION['user']]);
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(['success'=>false,'error'=>'Server error','message'=>$e->getMessage()]);
}
