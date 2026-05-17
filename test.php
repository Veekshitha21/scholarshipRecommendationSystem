<?php
// Test file to verify setup
echo "PHP is working!<br>";
echo "Current directory: " . __DIR__ . "<br>";
echo "Session test: ";
session_start();
$_SESSION['test'] = 'working';
echo ($_SESSION['test'] === 'working' ? 'Sessions OK' : 'Session error') . "<br>";
echo "Database test:<br>";
try {
    $db = new PDO('mysql:host=127.0.0.1;port=3306;dbname=scholarMatch;charset=utf8mb4', 'root', '', [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
    ]);
    echo "✓ Database connection successful<br>";
    $result = $db->query("SHOW TABLES");
    $tables = $result->fetchAll();
    echo "Tables: " . count($tables) . " found<br>";
    if (count($tables) > 0) {
        echo "✓ Database has tables<br>";
    } else {
        echo "⚠ Database is empty (needs initialization)<br>";
    }
} catch (Exception $e) {
    echo "✗ Database error: " . $e->getMessage() . "<br>";
}
