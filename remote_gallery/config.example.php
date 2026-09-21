<?php
// Copy this file OUTSIDE the web docroot (e.g. a sibling of public_html) and fill in
// real values, then point auth.php's CONFIG_PATH constant at it. Never deploy a
// filled-in copy of this file inside the docroot - it holds the login credentials.
return [
    // Absolute path to the directory that holds the photos/ and clips/ subfolders
    // (this is what the Pi's SFTP_REMOTE_DIR env var should point to).
    'data_dir' => '/absolute/path/outside/docroot',
    'username' => 'change_me',
    // Generate with hash_password.php, then delete that file from the server.
    'password_hash' => 'REPLACE_ME',
];
