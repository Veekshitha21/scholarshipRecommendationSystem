<?php
require_once __DIR__ . '/db.php';

if (session_status() !== PHP_SESSION_ACTIVE) {
    session_start();
}

function redirect_to(string $path): void
{
    header('Location: ' . $path);
    exit;
}

function current_user(): ?array
{
    if (empty($_SESSION['user_id'])) {
        return null;
    }

    $stmt = pdo()->prepare('SELECT id, name, marks, income, category, gender, disability, state, education_level, created_at, updated_at FROM users WHERE id = ? LIMIT 1');
    $stmt->execute([$_SESSION['user_id']]);
    $user = $stmt->fetch();

    return $user ?: null;
}

function require_login(): array
{
    $user = current_user();
    if (!$user) {
        redirect_to('login.php');
    }
    return $user;
}

function remember_user(array $user): void
{
    $_SESSION['user_id'] = (int) $user['id'];
    $_SESSION['user_name'] = $user['name'];
}

function normalize_select_value(?string $value, string $default = 'any'): string
{
    $value = strtolower(trim((string) $value));
    return $value !== '' ? $value : $default;
}
