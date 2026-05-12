<?php
require_once __DIR__ . '/lib/auth.php';

if (current_user()) {
    redirect_to('dashboard.php');
}

$error = null;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $name = trim((string) ($_POST['name'] ?? ''));
    $password = (string) ($_POST['password'] ?? '');

    if ($name === '' || $password === '') {
        $error = 'Please enter your name and password.';
    } else {
        $stmt = pdo()->prepare('SELECT * FROM users WHERE name = ? LIMIT 1');
        $stmt->execute([$name]);
        $user = $stmt->fetch();

        if ($user && password_verify($password, $user['password_hash'])) {
            remember_user($user);
            redirect_to('dashboard.php');
        }

        $error = 'Invalid name or password.';
    }
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>ScholarMatch - Login</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700;800&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="assets/auth.css" />
</head>
<body>
  <div class="bg-blobs"><div class="blob one"></div><div class="blob two"></div></div>
  <main class="auth-shell">
    <section class="auth-card">
      <div class="auth-hero">
        <a class="brand" href="login.php"><span class="brand-mark">🎓</span>ScholarMatch</a>
        <h1 class="hero-title">Welcome back to <span class="gradient-text">ScholarMatch</span></h1>
        <p class="hero-copy">Log in with your name and password to open your dashboard and profile summary instantly.</p>
        <ul class="bullets">
          <li><span class="bullet-dot"></span><span>Your profile stays in MySQL and is restored on every login.</span></li>
          <li><span class="bullet-dot"></span><span>After login, you land on the dashboard page with your data visible.</span></li>
          <li><span class="bullet-dot"></span><span>Keep using the same matching model inputs you registered with.</span></li>
        </ul>
        <div class="metric-row">
          <div class="metric"><strong>Secure</strong><span>Password hashing</span></div>
          <div class="metric"><strong>Fast</strong><span>Session login</span></div>
          <div class="metric"><strong>Profile</strong><span>Ready to view</span></div>
        </div>
      </div>
      <div class="auth-panel">
        <h2>Login</h2>
        <p class="sub">Enter your name and password.</p>
        <?php if ($error): ?><div class="alert error"><?= htmlspecialchars($error) ?></div><?php endif; ?>
        <form class="form-grid" method="post" action="login.php">
          <div class="field">
            <label for="name">Name</label>
            <input id="name" name="name" type="text" placeholder="Your registered name" required />
          </div>
          <div class="field">
            <label for="password">Password</label>
            <input id="password" name="password" type="password" placeholder="Your password" required />
          </div>
          <div class="actions">
            <button type="submit" class="btn primary full">Login</button>
          </div>
          <p class="small">New here? <a href="register.php">Create an account</a>.</p>
        </form>
      </div>
    </section>
  </main>
</body>
</html>
