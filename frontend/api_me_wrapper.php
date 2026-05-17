<?php
// Direct wrapper for checking session
session_start();
header('Content-Type: application/json; charset=utf-8');
if (!empty($_SESSION['user'])) {
    echo json_encode(['authenticated' => true, 'user' => $_SESSION['user']]);
    exit;
}
http_response_code(401);
echo json_encode(['authenticated' => false]);
