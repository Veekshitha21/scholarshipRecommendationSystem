<?php
require_once __DIR__ . '/lib/auth.php';
$user = require_login();
$error = null;
$success = null;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $marks = (float) ($_POST['marks'] ?? 0);
    $income = (float) ($_POST['income'] ?? 0);
    $category = normalize_select_value($_POST['category'] ?? 'any');
    $gender = normalize_select_value($_POST['gender'] ?? 'any');
    $disability = normalize_select_value($_POST['disability'] ?? 'no');
    $state = normalize_select_value($_POST['state'] ?? 'any');
    $education_level = normalize_select_value($_POST['education_level'] ?? 'any');

    $stmt = pdo()->prepare('UPDATE users SET marks = ?, income = ?, category = ?, gender = ?, disability = ?, state = ?, education_level = ? WHERE id = ?');
    $stmt->execute([$marks, $income, $category, $gender, $disability, $state, $education_level, $user['id']]);
    $success = 'Profile updated successfully.';
    $user = require_login();
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>ScholarMatch - Profile</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700;800&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="assets/auth.css" />
</head>
<body>
  <div class="bg-blobs"><div class="blob one"></div><div class="blob two"></div></div>
  <main class="dashboard">
    <header class="topbar">
      <div>
        <strong>🎓 ScholarMatch Profile</strong><br>
        <span class="small">Edit the model inputs tied to <?= htmlspecialchars($user['name']) ?></span>
      </div>
      <div class="top-actions">
        <a class="btn secondary" href="dashboard.php">Back to Dashboard</a>
        <a class="btn primary" href="logout.php">Logout</a>
      </div>
    </header>

    <section class="cards" style="grid-template-columns: 1fr;">
      <article class="panel">
        <h3>Update Profile</h3>
        <?php if ($error): ?><div class="alert error"><?= htmlspecialchars($error) ?></div><?php endif; ?>
        <?php if ($success): ?><div class="alert success"><?= htmlspecialchars($success) ?></div><?php endif; ?>
        <form class="profile-form" method="post" action="profile.php">
          <div class="split">
            <div class="field">
              <label for="marks">Percentage</label>
              <input id="marks" name="marks" type="number" min="0" max="100" step="0.1" value="<?= htmlspecialchars($user['marks']) ?>" required />
            </div>
            <div class="field">
              <label for="income">Family Income</label>
              <input id="income" name="income" type="number" min="0" step="1000" value="<?= htmlspecialchars($user['income']) ?>" required />
            </div>
          </div>
          <div class="split">
            <div class="field">
              <label for="category">Category</label>
              <select id="category" name="category">
                <option value="any" <?= $user['category'] === 'any' ? 'selected' : '' ?>>Any</option>
                <option value="general" <?= $user['category'] === 'general' ? 'selected' : '' ?>>General</option>
                <option value="obc" <?= $user['category'] === 'obc' ? 'selected' : '' ?>>OBC</option>
                <option value="sc" <?= $user['category'] === 'sc' ? 'selected' : '' ?>>SC</option>
                <option value="st" <?= $user['category'] === 'st' ? 'selected' : '' ?>>ST</option>
                <option value="minority" <?= $user['category'] === 'minority' ? 'selected' : '' ?>>Minority</option>
              </select>
            </div>
            <div class="field">
              <label for="gender">Gender</label>
              <select id="gender" name="gender">
                <option value="any" <?= $user['gender'] === 'any' ? 'selected' : '' ?>>Any</option>
                <option value="male" <?= $user['gender'] === 'male' ? 'selected' : '' ?>>Male</option>
                <option value="female" <?= $user['gender'] === 'female' ? 'selected' : '' ?>>Female</option>
              </select>
            </div>
          </div>
          <div class="split">
            <div class="field">
              <label for="disability">Disability</label>
              <select id="disability" name="disability">
                <option value="no" <?= $user['disability'] === 'no' ? 'selected' : '' ?>>No</option>
                <option value="yes" <?= $user['disability'] === 'yes' ? 'selected' : '' ?>>Yes</option>
              </select>
            </div>
            <div class="field">
              <label for="education_level">Education Level</label>
              <select id="education_level" name="education_level">
                <option value="school" <?= $user['education_level'] === 'school' ? 'selected' : '' ?>>1-10th</option>
                <option value="pu" <?= $user['education_level'] === 'pu' ? 'selected' : '' ?>>PU</option>
                <option value="diploma" <?= $user['education_level'] === 'diploma' ? 'selected' : '' ?>>Diploma</option>
                <option value="ug" <?= $user['education_level'] === 'ug' ? 'selected' : '' ?>>Degree (UG)</option>
                <option value="pg" <?= $user['education_level'] === 'pg' ? 'selected' : '' ?>>Masters (PG)</option>
              </select>
            </div>
          </div>
          <div class="field">
            <label for="state">State</label>
            <input id="state" name="state" type="text" value="<?= htmlspecialchars($user['state']) ?>" placeholder="e.g. Karnataka" />
          </div>
          <div class="actions">
            <button type="submit" class="btn primary">Save changes</button>
            <a href="dashboard.php" class="btn secondary">Cancel</a>
          </div>
        </form>
      </article>
    </section>
  </main>
</body>
</html>
