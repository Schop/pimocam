<?php $current = basename($_SERVER['PHP_SELF']); ?>
<nav class="navbar navbar-expand-md navbar-dark bg-dark mb-4 sticky-top">
    <div class="container-fluid">
        <a class="navbar-brand" href="index.php">Door Camera (Remote)</a>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navContent">
            <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navContent">
            <div class="navbar-nav">
                <a class="nav-link <?= $current === 'index.php' ? 'active fw-bold' : '' ?>" href="index.php">Photos</a>
                <a class="nav-link <?= $current === 'clips.php' ? 'active fw-bold' : '' ?>" href="clips.php">Clips</a>
                <a class="nav-link" href="logout.php">Logout</a>
            </div>
        </div>
    </div>
</nav>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
