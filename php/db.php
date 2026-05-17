<?php
// Database connection helper (PDO)
// Update $DB_PASS if your root user has a password
$DB_HOST = '127.0.0.1';
$DB_PORT = 3306;
$DB_NAME = 'scholarMatch';
$DB_USER = 'root';
$DB_PASS = '';

function get_db() {
    global $DB_HOST, $DB_PORT, $DB_NAME, $DB_USER, $DB_PASS;
    static $pdo = null;
    if ($pdo) return $pdo;
    $dsn = "mysql:host={$DB_HOST};port={$DB_PORT};dbname={$DB_NAME};charset=utf8mb4";
    try {
        $pdo = new PDO($dsn, $DB_USER, $DB_PASS, [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES => false,
        ]);
        return $pdo;
    } catch (PDOException $e) {
        http_response_code(500);
        echo json_encode(['error' => 'Database connection failed', 'message' => $e->getMessage()]);
        exit;
    }
}

// Helper to ensure CORS/JSON responses for simple API usage
header('Content-Type: application/json; charset=utf-8');
