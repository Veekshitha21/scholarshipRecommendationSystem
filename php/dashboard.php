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
        <strong>
          <svg aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="vertical-align:middle;margin-right:6px;">
            <path d="M12 2L4 5v6c0 5 3.58 9.74 8 11 4.42-1.26 8-6 8-11V5l-8-3z" fill="#FF8A5B"/>
            <path d="M10 13l2 2 5-5" stroke="#fff" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          ScholarMatch
        </strong><br>
        <span class="small">Logged in as <?= htmlspecialchars($user['name']) ?></span>
      </div>
      <div class="top-actions">
        <a class="btn secondary" href="profile.php">Edit Profile</a>
        <a class="btn primary" href="logout.php">Logout</a>
      </div>
    </header>

    <section class="scholarship-launch-section">
      <a class="scholarship-launch-card" href="http://127.0.0.1:5000/eligibility" aria-label="Check scholarship eligibility">
        <div class="scholarship-launch-copy">
          <span class="launch-eyebrow">3D Scholarship Model</span>
          <h2>Launch the eligibility checker</h2>
          <p>Tap the scholarship model to open ScholarMatch eligibility and see your best matches instantly.</p>
          <div class="launch-action">
            <span class="launch-button">Check Eligibility</span>
            <span class="launch-note">Built for session-based profile matching</span>
          </div>
        </div>
        <div class="scholarship-launch-visual" aria-hidden="true">
          <div class="launch-orbit launch-orbit-a"></div>
          <div class="launch-orbit launch-orbit-b"></div>
          <div class="launch-card-stack stack-one"></div>
          <div class="launch-card-stack stack-two"></div>
          <div class="launch-cube">
            <div class="cube-face cube-face-top"></div>
            <div class="cube-face cube-face-left"></div>
            <div class="cube-face cube-face-right"></div>
          </div>
          <div class="launch-ribbon">Scholarship</div>
        </div>
      </a>
    </section>

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
