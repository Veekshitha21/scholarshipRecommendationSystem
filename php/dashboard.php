<?php
require_once __DIR__ . '/lib/auth.php';
$user = require_login();

function display_value($value, string $fallback = 'Any'): string
{
    $value = trim((string) $value);
    return $value !== '' ? htmlspecialchars($value) : $fallback;
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>ScholarMatch - Dashboard</title>
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
        <strong>🎓 ScholarMatch</strong><br>
        <span class="small">Logged in as <?= htmlspecialchars($user['name']) ?></span>
      </div>
      <div class="top-actions">
        <a class="btn secondary" href="profile.php">Edit Profile</a>
        <a class="btn primary" href="logout.php">Logout</a>
      </div>
    </header>

    <section class="cards">
      <article class="panel">
        <h3>Your Profile</h3>
        <div class="profile-grid">
          <div class="profile-item"><span>Name</span><span><?= htmlspecialchars($user['name']) ?></span></div>
          <div class="profile-item"><span>Percentage</span><span><?= htmlspecialchars($user['marks']) ?>%</span></div>
          <div class="profile-item"><span>Family Income</span><span>₹<?= htmlspecialchars(number_format((float) $user['income'])) ?></span></div>
          <div class="profile-item"><span>Category</span><span><?= display_value($user['category']) ?></span></div>
          <div class="profile-item"><span>Gender</span><span><?= display_value($user['gender']) ?></span></div>
          <div class="profile-item"><span>Disability</span><span><?= display_value($user['disability'], 'No') ?></span></div>
          <div class="profile-item"><span>State</span><span><?= display_value($user['state']) ?></span></div>
          <div class="profile-item"><span>Education</span><span><?= display_value($user['education_level']) ?></span></div>
        </div>
        <p class="note">Your profile data is stored in MySQL and can be used for scholarship matching. Use the profile edit page if any input changes.</p>
      </article>

      <article class="panel">
        <h3>Model Inputs Saved</h3>
        <div class="profile-grid">
          <div class="profile-item"><span>Input set</span><span>Ready</span></div>
          <div class="profile-item"><span>Authentication</span><span>Session active</span></div>
          <div class="profile-item"><span>Recommendation data</span><span>Stored</span></div>
          <div class="profile-item"><span>Status</span><span style="color:#008B7F;">Active</span></div>
        </div>
        <p class="note">If you want the Python recommendation dashboard to use this profile automatically, connect its request body to this saved session data or expose a small PHP JSON endpoint.</p>
        <div class="actions" style="margin-top:18px;">
          <a class="btn primary full" href="profile.php">View / Update Profile</a>
        </div>
      </article>
    </section>
  </main>
</body>
</html>
