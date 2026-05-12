<?php
require_once __DIR__ . '/lib/auth.php';

if (current_user()) {
    redirect_to('dashboard.php');
}

redirect_to('login.php');
