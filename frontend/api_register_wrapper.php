<?php
// Direct wrapper in frontend folder to handle registration
require_once __DIR__ . '/../php/db.php';
session_start();

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

    $stmt = $db->prepare('SELECT id FROM users WHERE email = :email OR name = :name LIMIT 1');
    $stmt->execute([':email'=>$email,':name'=>$name]);
    if ($stmt->fetch()) {
        http_response_code(409);
        echo json_encode(['success'=>false,'error'=>'User already exists']); exit;
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
    $_SESSION['user'] = ['id'=>$id, 'name'=>$name, 'email'=>$email];
    echo json_encode(['success'=>true,'id'=>$id]);
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(['success'=>false,'error'=>'Server error']);
}
