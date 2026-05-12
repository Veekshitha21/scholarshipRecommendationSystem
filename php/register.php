<?php
require_once __DIR__ . '/lib/auth.php';

if (current_user()) {
    redirect_to('dashboard.php');
}

$error = null;
$success = null;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $name = trim((string) ($_POST['name'] ?? ''));
    $password = (string) ($_POST['password'] ?? '');
    $marks = (float) ($_POST['marks'] ?? 0);
    $income = (float) ($_POST['income'] ?? 0);
    $category = normalize_select_value($_POST['category'] ?? 'any');
    $gender = normalize_select_value($_POST['gender'] ?? 'any');
    $disability = normalize_select_value($_POST['disability'] ?? 'no');
    $state = normalize_select_value($_POST['state'] ?? 'any');
    $education_level = normalize_select_value($_POST['education_level'] ?? 'any');

    if ($name === '' || $password === '') {
        $error = 'Please enter your name and password.';
    } elseif (mb_strlen($password) < 6) {
        $error = 'Password must be at least 6 characters.';
    } else {
        $stmt = pdo()->prepare('SELECT id FROM users WHERE name = ? LIMIT 1');
        $stmt->execute([$name]);

        if ($stmt->fetch()) {
            $error = 'That name is already registered. Please log in.';
        } else {
            $hash = password_hash($password, PASSWORD_DEFAULT);
            $stmt = pdo()->prepare('INSERT INTO users (name, password_hash, marks, income, category, gender, disability, state, education_level) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)');
            $stmt->execute([$name, $hash, $marks, $income, $category, $gender, $disability, $state, $education_level]);
            $success = 'Registration completed. Please log in.';
        }
    }
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>ScholarMatch - Register</title>
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
        <h1 class="hero-title">Create your <span class="gradient-text">student profile</span></h1>
        <p class="hero-copy">Register once with your name, password, and the model inputs. After login, the dashboard will show your saved profile and keep the scholarship flow connected to your data.</p>
        <ul class="bullets">
          <li><span class="bullet-dot"></span><span>Stores your profile safely in MySQL using PHP sessions.</span></li>
          <li><span class="bullet-dot"></span><span>Uses the same orange/teal visual style as the rest of ScholarMatch.</span></li>
          <li><span class="bullet-dot"></span><span>Saves the exact inputs needed by the recommendation model.</span></li>
        </ul>
        <div class="metric-row">
          <div class="metric"><strong>Login</strong><span>Name + password</span></div>
          <div class="metric"><strong>Register</strong><span>Name + password + profile</span></div>
          <div class="metric"><strong>Storage</strong><span>MySQL / PHP</span></div>
        </div>
      </div>
      <div class="auth-panel">
        <h2>Register</h2>
        <p class="sub">Fill in the profile your model needs.</p>
        <?php if ($error): ?><div class="alert error"><?= htmlspecialchars($error) ?></div><?php endif; ?>
        <?php if ($success): ?><div class="alert success"><?= htmlspecialchars($success) ?></div><?php endif; ?>
        <form class="form-grid" method="post" action="register.php">
          <div class="field">
            <label for="name">Name</label>
            <input id="name" name="name" type="text" placeholder="Enter your name" required />
          </div>
          <div class="field">
            <label for="password">Password</label>
            <input id="password" name="password" type="password" placeholder="Create a password" required />
          </div>
          <div class="split">
            <div class="field">
              <label for="marks">Percentage</label>
              <input id="marks" name="marks" type="number" min="0" max="100" step="0.1" placeholder="e.g. 87.5" required />
            </div>
            <div class="field">
              <label for="income">Family Income</label>
              <input id="income" name="income" type="number" min="0" step="1000" placeholder="e.g. 240000" required />
            </div>
          </div>
          <div class="split">
            <div class="field">
              <label for="category">Category</label>
              <select id="category" name="category">
                <option value="any">Any</option>
                <option value="general">General</option>
                <option value="obc">OBC</option>
                <option value="sc">SC</option>
                <option value="st">ST</option>
                <option value="minority">Minority</option>
              </select>
            </div>
            <div class="field">
              <label for="gender">Gender</label>
              <select id="gender" name="gender">
                <option value="any">Any</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
              </select>
            </div>
          </div>
          <div class="split">
            <div class="field">
              <label for="disability">Disability</label>
              <select id="disability" name="disability">
                <option value="no">No</option>
                <option value="yes">Yes</option>
              </select>
            </div>
            <div class="field">
              <label for="education_level">Education Level</label>
              <select id="education_level" name="education_level">
                <option value="school">1-10th</option>
                <option value="pu">PU</option>
                <option value="diploma">Diploma</option>
                <option value="ug" selected>Degree (UG)</option>
                <option value="pg">Masters (PG)</option>
              </select>
            </div>
          </div>
          <div class="field">
            <label for="state">State</label>
            <input id="state" name="state" type="text" placeholder="e.g. Karnataka" />
          </div>
          <div class="actions">
            <button type="submit" class="btn primary full">Create account</button>
          </div>
          <p class="small">Already registered? <a href="login.php">Log in here</a>.</p>
        </form>
      </div>
    </section>
  </main>
</body>
</html>
