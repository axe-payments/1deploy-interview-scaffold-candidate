<?php
// Logs Adminer straight in to the interview database, so http://localhost:8080 opens on
// the tables instead of a login form. The credentials are the ones docker-compose.yml
// gives Postgres. Adminer is published on 127.0.0.1 only and is never tunnelled.
//
// Adminer loads plugins before it handles the login form, so supplying the form's fields
// here is the same as filling them in and pressing Login. That happens on any page that
// would otherwise show the form: a URL with no user in it (Adminer always shows the form
// there, logged in or not, and Logout lands there too), or a session with no password
// yet (first visit, or after Adminer restarts).

$auth = [
    'driver' => 'pgsql',
    'server' => 'postgres', // the Compose service name
    'username' => getenv('POSTGRES_USER'),
    'password' => getenv('POSTGRES_PASSWORD'),
    'db' => getenv('POSTGRES_DB'),
];

$loggedIn = isset($_SESSION['pwds'][$auth['driver']][$auth['server']][$auth['username']]);
if (!$_POST && (!isset($_GET['username']) || !$loggedIn)) {
    $_POST['auth'] = $auth;
}

return new class extends \Adminer\Plugin {
};
