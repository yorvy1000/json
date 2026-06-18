<?php
session_start();

// Helper to load environment variables from .env
function get_env_variable($name, $default = '') {
    if (isset($_ENV[$name])) return $_ENV[$name];
    if (isset($_SERVER[$name])) return $_SERVER[$name];
    $val = getenv($name);
    if ($val !== false) return $val;
    
    static $env = null;
    if ($env === null) {
        $env = [];
        $paths = [
            "/home/u114856156/agente_dominio/.env",
            __DIR__ . "/../.env",
            __DIR__ . "/../../../../agente_dominio/.env",
            __DIR__ . "/.env"
        ];
        foreach ($paths as $path) {
            if (file_exists($path)) {
                $lines = file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
                foreach ($lines as $line) {
                    $line = trim($line);
                    if (empty($line) || strpos($line, '#') === 0) continue;
                    if (strpos($line, '=') !== false) {
                        list($key, $value) = explode('=', $line, 2);
                        $key = trim($key);
                        $value = trim($value);
                        if (preg_match('/^"?(.*?)"?$/', $value, $matches)) {
                            $value = $matches[1];
                        }
                        $env[$key] = $value;
                    }
                }
                break;
            }
        }
    }
    return isset($env[$name]) ? $env[$name] : $default;
}

// Cerrar sesión
if (isset($_GET['logout'])) {
    session_destroy();
    header("Location: index.php");
    exit;
}

$error = '';
// Procesar login
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $username = isset($_POST['username']) ? $_POST['username'] : '';
    $password = isset($_POST['password']) ? $_POST['password'] : '';
    
    $admin_user = get_env_variable('ADMIN_USERNAME', 'admin');
    $admin_pass = get_env_variable('ADMIN_PASSWORD', 'admin123');
    
    if ($username === $admin_user && $password === $admin_pass) {
        $_SESSION['logged_in'] = true;
        header("Location: index.php");
        exit;
    } else {
        $error = "Usuario o contraseña incorrectos. Por favor, intenta de nuevo.";
    }
}

// Si no está logueado, mostrar pantalla de login
if (!isset($_SESSION['logged_in']) || $_SESSION['logged_in'] !== true) {
?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vibra Deals - Iniciar Sesión</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-main: #0b0f19;
            --bg-card: rgba(31, 41, 55, 0.45);
            --accent-primary: #8b5cf6;
            --accent-secondary: #6366f1;
            --text-main: #f9fafb;
            --text-muted: #9ca3af;
            --border-color: rgba(255, 255, 255, 0.08);
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Outfit', sans-serif;
            background: radial-gradient(circle at top right, rgba(139, 92, 246, 0.15), transparent 40%),
                        radial-gradient(circle at bottom left, rgba(99, 102, 241, 0.15), transparent 40%),
                        var(--bg-main);
            color: var(--text-main);
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
        }

        .login-container {
            background: var(--bg-card);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid var(--border-color);
            border-radius: 1.5rem;
            padding: 3rem 2.5rem;
            width: 100%;
            max-width: 420px;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.4);
            display: flex;
            flex-direction: column;
            gap: 2rem;
            animation: fadeIn 0.6s cubic-bezier(0.16, 1, 0.3, 1);
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .logo-section {
            text-align: center;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 0.75rem;
        }

        .logo-section img {
            height: 50px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }

        .logo-section h1 {
            font-size: 1.75rem;
            font-weight: 800;
            background: linear-gradient(135deg, #a78bfa, #818cf8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .logo-section p {
            font-size: 0.85rem;
            color: var(--text-muted);
        }

        form {
            display: flex;
            flex-direction: column;
            gap: 1.25rem;
        }

        .form-group {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }

        .form-group label {
            font-size: 0.8rem;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .form-control {
            background-color: rgba(11, 15, 25, 0.6);
            border: 1px solid var(--border-color);
            border-radius: 0.75rem;
            color: var(--text-main);
            padding: 0.85rem 1.1rem;
            font-family: inherit;
            font-size: 0.95rem;
            outline: none;
            transition: all 0.3s ease;
        }

        .form-control:focus {
            border-color: var(--accent-primary);
            box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.15);
            background-color: rgba(11, 15, 25, 0.8);
        }

        .btn {
            background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
            color: white;
            border: none;
            padding: 0.9rem;
            border-radius: 0.75rem;
            font-size: 1rem;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 4px 14px rgba(139, 92, 246, 0.3);
            font-family: inherit;
            margin-top: 0.5rem;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(139, 92, 246, 0.5);
        }

        .btn:active {
            transform: translateY(0);
        }

        .error-message {
            background-color: rgba(239, 68, 68, 0.15);
            border: 1px solid rgba(239, 68, 68, 0.3);
            color: #f87171;
            padding: 0.75rem;
            border-radius: 0.5rem;
            font-size: 0.85rem;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo-section">
            <img src="/static/logo.png" alt="MySmartDomains Logo" onerror="this.style.display='none'">
            <h1>Vibra Deals</h1>
            <p>Panel de Control de Prospección de Dominios</p>
        </div>
        
        <?php if (!empty($error)): ?>
        <div class="error-message">
            <?php echo htmlspecialchars($error); ?>
        </div>
        <?php endif; ?>
        
        <form method="POST" action="index.php">
            <div class="form-group">
                <label for="username">Usuario:</label>
                <input type="text" id="username" name="username" class="form-control" placeholder="Ingresa tu usuario" required autocomplete="username">
            </div>
            
            <div class="form-group">
                <label for="password">Contraseña:</label>
                <input type="password" id="password" name="password" class="form-control" placeholder="Ingresa tu contraseña" required autocomplete="current-password">
            </div>
            
            <button type="submit" class="btn">Iniciar Sesión</button>
        </form>
    </div>
</body>
</html>
<?php
    exit;
}

// Determinar si estamos ejecutando directamente en Hostinger
$is_hostinger = (strpos($_SERVER['HTTP_HOST'], 'mysmartdomains.com') !== false || file_exists("/home/u114856156"));
?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vibra Deals - Domain Prospector Panel</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-main: #0b0f19;
            --bg-sidebar: #111827;
            --bg-card: #1f2937;
            --bg-card-hover: #374151;
            --accent-primary: #8b5cf6;
            --accent-secondary: #6366f1;
            --text-main: #f9fafb;
            --text-muted: #9ca3af;
            --status-pending: #f59e0b;
            --status-contacted: #10b981;
            --status-rejected: #ef4444;
            --border-color: #374151;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Outfit', sans-serif;
            background-color: var(--bg-main);
            color: var(--text-main);
            height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        /* Top Header */
        header {
            background-color: var(--bg-sidebar);
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border-color);
            z-index: 10;
            flex-shrink: 0;
        }

        .logo-section {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .logo-section img {
            height: 38px;
            border-radius: 6px;
        }

        .header-title h1 {
            font-size: 1.4rem;
            font-weight: 800;
            background: linear-gradient(135deg, #a78bfa, #818cf8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .header-title h1 span {
            font-size: 0.85rem;
            font-weight: 400;
            color: var(--text-muted);
            -webkit-text-fill-color: var(--text-muted);
            border-left: 1px solid var(--border-color);
            padding-left: 0.5rem;
            margin-left: 0.5rem;
        }

        .header-actions {
            display: flex;
            gap: 1rem;
            align-items: center;
        }

        /* Botones */
        .btn {
            background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
            color: white;
            border: none;
            padding: 0.6rem 1.2rem;
            border-radius: 0.5rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 4px 14px rgba(139, 92, 246, 0.3);
            font-family: inherit;
        }

        .btn:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(139, 92, 246, 0.5);
        }

        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            box-shadow: none;
        }

        .btn-secondary {
            background: transparent;
            border: 1px solid var(--border-color);
            color: var(--text-main);
            box-shadow: none;
        }

        .btn-secondary:hover:not(:disabled) {
            background: var(--bg-card);
            box-shadow: none;
            transform: translateY(-1px);
        }

        /* Main Workspace Container */
        .workspace {
            display: flex;
            flex: 1;
            overflow: hidden;
            position: relative;
        }

        /* Sidebar: Dominios List */
        .sidebar {
            width: 360px;
            background-color: var(--bg-sidebar);
            border-right: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
            flex-shrink: 0;
        }

        .sidebar-header {
            padding: 1rem;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }

        .search-container {
            position: relative;
        }

        .search-input {
            width: 100%;
            background-color: var(--bg-main);
            border: 1px solid var(--border-color);
            color: var(--text-main);
            padding: 0.6rem 1rem;
            border-radius: 0.5rem;
            font-family: inherit;
            outline: none;
            font-size: 0.9rem;
        }

        .search-input:focus {
            border-color: var(--accent-primary);
        }

        .domain-list {
            flex: 1;
            overflow-y: auto;
            padding: 0.5rem;
        }

        .domain-item {
            padding: 0.85rem 1rem;
            border-radius: 0.5rem;
            margin-bottom: 0.5rem;
            cursor: pointer;
            transition: all 0.2s;
            border: 1px solid transparent;
            display: flex;
            flex-direction: column;
            gap: 0.35rem;
        }

        .domain-item:hover {
            background-color: rgba(255, 255, 255, 0.03);
            border-color: var(--border-color);
        }

        .domain-item.active {
            background-color: rgba(139, 92, 246, 0.12);
            border-color: rgba(139, 92, 246, 0.4);
        }

        .domain-item-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .domain-name {
            font-weight: 600;
            font-size: 0.95rem;
            color: var(--text-main);
        }

        .domain-item.active .domain-name {
            color: #c084fc;
        }

        .badge-leads {
            font-size: 0.75rem;
            background-color: var(--bg-card);
            padding: 0.15rem 0.45rem;
            border-radius: 1rem;
            font-weight: 500;
            color: var(--text-muted);
        }

        .domain-item.active .badge-leads {
            background-color: var(--accent-primary);
            color: white;
        }

        .domain-meta {
            display: flex;
            gap: 0.5rem;
            font-size: 0.75rem;
            color: var(--text-muted);
            flex-wrap: wrap;
        }

        .badge-category {
            background-color: rgba(55, 65, 81, 0.5);
            padding: 0.05rem 0.35rem;
            border-radius: 0.25rem;
            color: #cbd5e1;
        }

        .badge-year {
            color: #10b981;
        }

        .badge-score {
            color: #6366f1;
        }

        /* Main Panel Content: Leads for selected domain */
        .content-panel {
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow-y: auto;
            background-color: var(--bg-main);
            padding: 2rem;
        }

        .welcome-view {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100%;
            color: var(--text-muted);
            gap: 1rem;
        }

        .welcome-view svg {
            width: 64px;
            height: 64px;
            stroke: var(--border-color);
        }

        .domain-detail-header {
            margin-bottom: 2rem;
            padding-bottom: 1.5rem;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
        }

        .domain-title-section h2 {
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }

        .domain-detail-meta {
            display: flex;
            gap: 1.5rem;
            font-size: 0.95rem;
            color: var(--text-muted);
        }

        .domain-detail-meta strong {
            color: var(--text-main);
        }

        .leads-grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 1.5rem;
        }

        .lead-card {
            background-color: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 0.75rem;
            padding: 1.5rem;
            transition: all 0.3s;
            position: relative;
        }

        .lead-card.sent-border {
            border-left: 4px solid var(--status-contacted);
        }

        .lead-card:hover {
            border-color: var(--accent-primary);
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        }

        .lead-card-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 1rem;
        }

        .lead-title h3 {
            font-size: 1.2rem;
            font-weight: 600;
            color: var(--text-main);
        }

        .lead-title a {
            color: var(--accent-primary);
            text-decoration: none;
            font-size: 0.85rem;
        }

        .lead-title a:hover {
            text-decoration: underline;
        }

        .sent-indicator {
            background-color: rgba(16, 185, 129, 0.15);
            color: var(--status-contacted);
            border: 1px solid var(--status-contacted);
            padding: 0.2rem 0.6rem;
            border-radius: 0.25rem;
            font-size: 0.75rem;
            font-weight: 600;
        }

        .lead-contacts {
            display: flex;
            gap: 1.5rem;
            flex-wrap: wrap;
            margin-bottom: 1rem;
            background-color: rgba(0,0,0,0.15);
            padding: 0.75rem 1rem;
            border-radius: 0.5rem;
            font-size: 0.9rem;
        }

        .contact-field span {
            color: var(--text-muted);
            margin-right: 0.25rem;
        }

        .contact-field a {
            color: var(--text-main);
            text-decoration: none;
            font-weight: 600;
        }

        .contact-field a:hover {
            text-decoration: underline;
            color: #c084fc;
        }

        .proposal-box {
            background-color: rgba(11, 15, 25, 0.6);
            border: 1px dashed var(--border-color);
            border-radius: 0.5rem;
            padding: 1.2rem;
            margin-bottom: 1rem;
        }

        .proposal-box-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.8rem;
            color: var(--text-muted);
            margin-bottom: 0.5rem;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            padding-bottom: 0.5rem;
        }

        .proposal-box-body {
            font-size: 0.875rem;
            white-space: pre-wrap;
            color: #e5e7eb;
            max-height: 160px;
            overflow-y: auto;
            line-height: 1.5;
        }

        .card-actions {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 1rem;
            flex-wrap: wrap;
            gap: 1rem;
        }

        .send-actions {
            display: flex;
            gap: 0.5rem;
        }

        /* Selectores de Estado */
        .status-group {
            display: flex;
            gap: 0.4rem;
        }

        .status-pill {
            padding: 0.35rem 0.75rem;
            border-radius: 0.25rem;
            font-size: 0.75rem;
            font-weight: 600;
            cursor: pointer;
            border: 1px solid var(--border-color);
            background: transparent;
            color: var(--text-muted);
            transition: all 0.2s;
        }

        .status-pill.pending.active {
            background-color: rgba(245, 158, 11, 0.15);
            color: var(--status-pending);
            border-color: var(--status-pending);
        }

        .status-pill.contacted.active {
            background-color: rgba(16, 185, 129, 0.15);
            color: var(--status-contacted);
            border-color: var(--status-contacted);
        }

        .status-pill.rejected.active {
            background-color: rgba(239, 68, 68, 0.15);
            color: var(--status-rejected);
            border-color: var(--status-rejected);
        }

        /* Toast */
        .copy-toast {
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            background-color: var(--accent-secondary);
            color: white;
            padding: 0.8rem 1.5rem;
            border-radius: 0.5rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.4);
            transform: translateY(150%);
            transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            z-index: 1000;
        }

        .copy-toast.show {
            transform: translateY(0);
        }

        .loading {
            text-align: center;
            padding: 3rem;
            color: var(--text-muted);
        }

        .spinner {
            border: 4px solid rgba(255,255,255,0.1);
            width: 36px;
            height: 36px;
            border-radius: 50%;
            border-left-color: var(--accent-primary);
            animation: spin 1s linear infinite;
            margin: 0 auto 1rem;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        /* Modal Styles */
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(11, 15, 25, 0.8);
            backdrop-filter: blur(8px);
            align-items: center;
            justify-content: center;
            padding: 1rem;
        }

        .modal-content {
            background-color: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 1rem;
            width: 100%;
            max-width: 680px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.5);
            animation: modalSlideIn 0.3s cubic-bezier(0.16, 1, 0.3, 1);
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }

        @keyframes modalSlideIn {
            from {
                transform: translateY(-20px) scale(0.95);
                opacity: 0;
            }
            to {
                transform: translateY(0) scale(1);
                opacity: 1;
            }
        }

        .modal-header {
            padding: 1.25rem 1.5rem;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            justify-content: space-between;
            align-items: center;
            background-color: rgba(0,0,0,0.15);
        }

        .modal-header h3 {
            font-size: 1.25rem;
            font-weight: 700;
            background: linear-gradient(135deg, #a78bfa, #818cf8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .close-modal {
            background: none;
            border: none;
            color: var(--text-muted);
            font-size: 1.5rem;
            cursor: pointer;
            transition: color 0.2s;
            line-height: 1;
        }

        .close-modal:hover {
            color: var(--text-main);
        }

        .modal-body {
            padding: 1.5rem;
            display: flex;
            flex-direction: column;
            gap: 1.25rem;
        }

        .form-group {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }

        .form-group label {
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .form-control {
            background-color: var(--bg-main);
            border: 1px solid var(--border-color);
            border-radius: 0.5rem;
            color: var(--text-main);
            padding: 0.75rem 1rem;
            font-family: inherit;
            font-size: 0.95rem;
            outline: none;
            transition: border-color 0.2s;
        }

        .form-control:focus {
            border-color: var(--accent-primary);
        }

        .modal-footer {
            padding: 1.25rem 1.5rem;
            border-top: 1px solid var(--border-color);
            display: flex;
            justify-content: flex-end;
            gap: 1rem;
            background-color: rgba(0,0,0,0.15);
        }

        /* Language Tab Buttons */
        .language-tabs {
            display: flex;
            gap: 0.25rem;
            margin-bottom: 0.75rem;
            background-color: var(--bg-main);
            padding: 0.2rem;
            border-radius: 0.5rem;
            border: 1px solid var(--border-color);
        }

        .tab-btn {
            flex: 1;
            border: none;
            background: transparent;
            color: var(--text-muted);
            padding: 0.45rem;
            font-family: inherit;
            font-size: 0.75rem;
            font-weight: 700;
            border-radius: 0.35rem;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .tab-btn:hover {
            color: var(--text-main);
            background-color: rgba(255, 255, 255, 0.03);
        }

        .tab-btn.active {
            background-color: var(--accent-primary) !important;
            color: white !important;
            box-shadow: 0 2px 6px rgba(139, 92, 246, 0.3);
        }

        /* Stats Cards Styles */
        .stats-row {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }

        .stat-card {
            background-color: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 0.75rem;
            padding: 1rem 1.25rem;
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: transform 0.2s;
        }

        .stat-card:hover {
            transform: translateY(-2px);
            border-color: rgba(139, 92, 246, 0.3);
        }

        .stat-title {
            font-size: 0.8rem;
            color: var(--text-muted);
            text-transform: uppercase;
            font-weight: 600;
            letter-spacing: 0.05em;
        }

        .stat-value {
            font-size: 1.6rem;
            font-weight: 800;
        }
    </style>
</head>
<body>
    <header>
        <div class="logo-section">
            <img src="/static/logo.png" alt="MySmartDomains Logo" onerror="this.style.display='none'">
            <div class="header-title">
                <h1>Vibra Deals <span>Domain Flipping Prospector</span></h1>
            </div>
        </div>
        <div class="header-actions">
            <button class="btn" id="sync-btn" style="background: linear-gradient(135deg, #3b82f6, #2563eb); box-shadow: 0 4px 12px rgba(59,130,246,0.2);" onclick="syncFromServer(event)">Sincronizar Hostinger</button>
            <button class="btn" style="background: linear-gradient(135deg, #10b981, #059669); box-shadow: 0 4px 12px rgba(16,185,129,0.2);" onclick="sendAllPending()">Enviar Todo Pendiente (Auto)</button>
            <button class="btn" id="run-scraper-btn" onclick="toggleScraper()">Iniciar Prospección 24/7</button>
            <button class="btn btn-secondary" onclick="loadDashboard()">Refrescar Datos</button>
            <a class="btn btn-secondary" style="color: var(--status-rejected); border-color: rgba(239, 68, 68, 0.3); text-decoration: none;" href="index.php?logout=1">Cerrar Sesión</a>
        </div>
    </header>

    <div class="workspace">
        <!-- Sidebar - Dominios -->
        <div class="sidebar">
            <div class="sidebar-header">
                <div class="language-tabs">
                    <button class="tab-btn active" id="tab-all" onclick="switchLanguageFilter('all')">Todos</button>
                    <button class="tab-btn" id="tab-en" onclick="switchLanguageFilter('en')">English</button>
                    <button class="tab-btn" id="tab-es" onclick="switchLanguageFilter('es')">Español</button>
                </div>
                <div class="search-container">
                    <input type="text" id="search-domains" class="search-input" placeholder="Buscar dominio o nicho..." oninput="filterDomains()">
                </div>
            </div>
            <div class="domain-list" id="domain-items-container">
                <!-- Se inyecta dinámicamente -->
            </div>
        </div>

        <!-- Main Panel Content -->
        <div class="content-panel" style="overflow: hidden; display: flex; flex-direction: column;">
            <!-- Stats Bar -->
            <div class="stats-row">
                <div class="stat-card">
                    <span class="stat-title">Dominios Registrados</span>
                    <span id="stat-total-domains" class="stat-value" style="color: #a78bfa;">0</span>
                </div>
                <div class="stat-card">
                    <span class="stat-title">Leads Pendientes</span>
                    <span id="stat-pending-leads" class="stat-value" style="color: var(--status-pending);">0</span>
                </div>
                <div class="stat-card">
                    <span class="stat-title">Leads Contactados</span>
                    <span id="stat-contacted-leads" class="stat-value" style="color: var(--status-contacted);">0</span>
                </div>
                <div class="stat-card">
                    <span class="stat-title">Leads Descartados</span>
                    <span id="stat-rejected-leads" class="stat-value" style="color: var(--status-rejected);">0</span>
                </div>
            </div>

            <!-- Dynamic Content Area -->
            <div id="content-panel-view" style="flex: 1; overflow-y: auto; display: flex; flex-direction: column; margin-top: 1rem;">
                <div class="welcome-view">
                    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3.75 3v11.25A2.25 2.25 0 006 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0118 16.5h-2.25m-7.5 0h7.5m-7.5 0l-1 3m8.5-3l1 3m0 0l.5 1.5m-.5-1.5h-9.5m0 0l-.5 1.5m.75-9l3-3 2.148 2.148A12.061 12.061 0 0116.5 7.605"></path>
                    </svg>
                    <p>Selecciona un dominio de la barra lateral para auditar sus leads y propuestas en detalle.</p>
                </div>
            </div>
        </div>
    </div>

    <div id="toast" class="copy-toast">¡Texto de propuesta copiado al portapapeles!</div>

    <!-- Modal de Edición de Correo (Caja SMTP) -->
    <div id="email-modal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h3>Editar Propuesta Comercial (SMTP)</h3>
                <button class="close-modal" onclick="closeEmailModal()">&times;</button>
            </div>
            <div class="modal-body">
                <input type="hidden" id="modal-lead-id">
                <div class="form-group">
                    <label for="modal-to-email">Destinatario (Email):</label>
                    <input type="text" id="modal-to-email" class="form-control" readonly>
                </div>
                <div class="form-group">
                    <label for="modal-subject">Asunto del Correo:</label>
                    <input type="text" id="modal-subject" class="form-control" placeholder="Asunto...">
                </div>
                <div class="form-group">
                    <label for="modal-body">Cuerpo del Mensaje (Se enviará con el logo, header y footer):</label>
                    <textarea id="modal-body" class="form-control" style="height: 250px; resize: vertical;" placeholder="Cuerpo de la propuesta..."></textarea>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="closeEmailModal()">Cancelar</button>
                <button class="btn" id="modal-send-btn" style="background: linear-gradient(135deg, #10b981, #059669); box-shadow: 0 4px 12px rgba(16,185,129,0.2);" onclick="sendCustomModalEmail()">Enviar Correo (Manual)</button>
            </div>
        </div>
    </div>

    <script>
        const isHostinger = <?php echo $is_hostinger ? 'true' : 'false'; ?>;
        
        let allDomains = [];
        let currentLeads = [];
        let selectedDomain = null;
        let isScrapingActive = false;
        let activeLanguageFilter = 'all';

        // Adapt UI if running on Hostinger
        if (isHostinger) {
            // Hide sync button
            const syncBtn = document.getElementById('sync-btn');
            if (syncBtn) syncBtn.style.display = 'none';

            // Change Scraper control to show it runs via Cron
            const scraperBtn = document.getElementById('run-scraper-btn');
            if (scraperBtn) {
                scraperBtn.textContent = "Prospección: Activa (Cron)";
                scraperBtn.style.background = "linear-gradient(135deg, #10b981, #059669)";
                scraperBtn.disabled = true;
                scraperBtn.style.cursor = "default";
                scraperBtn.style.boxShadow = "none";
            }
        }

        async function syncFromServer(event) {
            if (isHostinger) return;
            const btn = event.target;
            const originalText = btn.textContent;
            btn.disabled = true;
            btn.textContent = 'Sincronizando...';
            
            try {
                const response = await fetch('api.php?action=sync_from_server', {
                    method: 'POST'
                });
                const resData = await response.json();
                if (resData.success) {
                    const toast = document.getElementById('toast');
                    toast.textContent = "¡Base de datos sincronizada desde Hostinger!";
                    toast.classList.add('show');
                    setTimeout(() => {
                        toast.classList.remove('show');
                        setTimeout(() => { toast.textContent = "¡Texto de propuesta copiado al portapapeles!"; }, 300);
                    }, 3000);
                    await loadDashboard();
                } else {
                    alert("Error al sincronizar: " + resData.error);
                }
            } catch (err) {
                console.error("Error de red al sincronizar:", err);
                alert("Error de red al intentar sincronizar con Hostinger.");
            } finally {
                btn.disabled = false;
                btn.textContent = originalText;
            }
        }

        async function loadDashboard() {
            await fetchDomains();
            await updateStatsUI();
            if (selectedDomain) {
                await selectDomain(selectedDomain);
            }
        }

        async function updateStatsUI() {
            try {
                const response = await fetch('api.php?action=get_stats');
                const stats = await response.json();
                document.getElementById('stat-total-domains').textContent = stats.total_dominios_venta || 0;
                document.getElementById('stat-pending-leads').textContent = stats.leads_pendiente || 0;
                document.getElementById('stat-contacted-leads').textContent = stats.leads_contactado || 0;
                document.getElementById('stat-rejected-leads').textContent = stats.leads_rechazado || 0;
            } catch (err) {
                console.error("Error al obtener estadísticas:", err);
            }
        }

        function switchLanguageFilter(lang) {
            activeLanguageFilter = lang;
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            document.getElementById(`tab-${lang}`).classList.add('active');
            filterDomains();
        }

        async function fetchDomains() {
            try {
                const response = await fetch('api.php?action=get_domains');
                allDomains = await response.json();
                renderDomainsList(allDomains);
            } catch (err) {
                console.error("Error al obtener dominios:", err);
            }
        }

        function renderDomainsList(domains) {
            const container = document.getElementById('domain-items-container');
            container.innerHTML = '';
            
            if (domains.length === 0) {
                container.innerHTML = '<div style="padding: 1rem; color: var(--text-muted); text-align: center;">No hay dominios registrados</div>';
                return;
            }

            domains.forEach(dom => {
                const item = document.createElement('div');
                item.className = `domain-item ${selectedDomain === dom.dominio ? 'active' : ''}`;
                item.onclick = () => selectDomain(dom.dominio);
                
                const catBadge = dom.categoria ? `<span class="badge-category">${dom.categoria}</span>` : '<span class="badge-category" style="font-style: italic;">Sin analizar</span>';
                const yearBadge = dom.ano_registro ? `<span class="badge-year">📅 ${dom.ano_registro}</span>` : '';
                const scoreBadge = dom.score ? `<span class="badge-score">📈 ${dom.score}</span>` : '';
                
                let flag = '🇺🇸';
                if (dom.idioma === 'es') {
                    flag = (dom.pais_region === 'ES') ? '🇪🇸' : '🌎';
                } else {
                    flag = (dom.pais_region === 'UK') ? '🇬🇧' : '🇺🇸';
                }
                const langBadge = dom.idioma ? 
                    `<span class="badge-category" style="background-color: rgba(139, 92, 246, 0.08); color: #cbd5e1; border: 1px solid rgba(139, 92, 246, 0.15); font-size: 0.7rem; font-weight: 600; padding: 0.05rem 0.25rem;">${flag} ${dom.idioma.toUpperCase()}/${dom.pais_region}</span>` : '';
                
                item.innerHTML = `
                    <div class="domain-item-header">
                        <span class="domain-name">${dom.dominio}</span>
                        <span class="badge-leads">${dom.leads_count} leads</span>
                    </div>
                    <div class="domain-meta">
                        ${catBadge}
                        ${langBadge}
                        ${yearBadge}
                        ${scoreBadge}
                    </div>
                `;
                container.appendChild(item);
            });
        }

        function filterDomains() {
            const query = document.getElementById('search-domains').value.toLowerCase();
            const filtered = allDomains.filter(dom => {
                const nameMatch = dom.dominio.toLowerCase().includes(query);
                const catMatch = dom.categoria && dom.categoria.toLowerCase().includes(query);
                const textMatch = nameMatch || catMatch;
                
                let langMatch = true;
                if (activeLanguageFilter === 'en') {
                    langMatch = (dom.idioma === 'en');
                } else if (activeLanguageFilter === 'es') {
                    langMatch = (dom.idioma === 'es');
                }
                
                return textMatch && langMatch;
            });
            renderDomainsList(filtered);
        }

        async function selectDomain(domainName) {
            selectedDomain = domainName;
            
            // Marcar activo en la lista lateral
            const items = document.querySelectorAll('.domain-item');
            items.forEach(item => {
                const name = item.querySelector('.domain-name').textContent;
                if (name === domainName) {
                    item.classList.add('active');
                } else {
                    item.classList.remove('active');
                }
            });

            const panel = document.getElementById('content-panel-view');
            panel.innerHTML = `
                <div class="loading">
                    <div class="spinner"></div>
                    Obteniendo candidatos de contacto...
                </div>
            `;

            // Buscar metadatos del dominio seleccionado
            const domInfo = allDomains.find(d => d.dominio === domainName);
            
            try {
                const response = await fetch(`api.php?action=get_leads&domain=${encodeURIComponent(domainName)}`);
                currentLeads = await response.json();
                
                let leadsHTML = '';
                if (currentLeads.length === 0) {
                    leadsHTML = `
                        <div style="text-align: center; padding: 4rem; color: var(--text-muted); border: 1px dashed var(--border-color); border-radius: 0.5rem; background-color: var(--bg-sidebar);">
                            <p style="font-size: 1.1rem; font-weight: 500; margin-bottom: 0.5rem;">Ningún prospecto calificado aún</p>
                            <p style="font-size: 0.9rem;">El escáner aún no ha recolectado contactos con email o teléfono válidos para este dominio.</p>
                        </div>
                    `;
                } else {
                    leadsHTML = '<div class="leads-grid">';
                    currentLeads.forEach(lead => {
                        const isSent = lead.estado === 'CONTACTADO';
                        
                        leadsHTML += `
                            <div class="lead-card ${isSent ? 'sent-border' : ''}" id="lead-card-${lead.id}">
                                <div class="lead-card-header">
                                    <div class="lead-title">
                                        <h3>${lead.empresa_nombre}</h3>
                                        ${lead.sitio_web_actual !== 'Sin sitio web' ? 
                                            `<a href="${lead.sitio_web_actual}" target="_blank">${lead.sitio_web_actual} &nearr;</a>` : 
                                            `<span style="color: var(--status-pending); font-size: 0.85rem; font-style: italic;">Sin Sitio Web Registrado</span>`
                                        }
                                    </div>
                                    ${isSent ? `<span class="sent-indicator">PROPUESTA ENVIADA</span>` : ''}
                                </div>

                                <div class="lead-contacts">
                                    <div class="contact-field">
                                        <span>📧 Emails:</span>
                                        ${lead.correo ? lead.correo.split(', ').map(email => `<a href="mailto:${email}">${email}</a>`).join(', ') : '<i>Ninguno</i>'}
                                    </div>
                                    <div class="contact-field">
                                        <span>📞 Teléfonos / WhatsApp:</span>
                                        ${lead.telefono ? lead.telefono.split(', ').map(tel => {
                                            const cleanTel = tel.replace(/[^+\d]/g, '');
                                            return `<a href="https://wa.me/${cleanTel}" target="_blank">💬 ${tel}</a>`;
                                        }).join(', ') : '<i>Ninguno</i>'}
                                    </div>
                                </div>

                                <div class="proposal-box">
                                    <div class="proposal-box-header">
                                        <span>Propuesta Comercial (Vibra Deals)</span>
                                        <button class="btn btn-secondary" style="padding: 0.15rem 0.5rem; font-size: 0.75rem;" onclick="copyLeadProposal(${lead.id})">Copiar</button>
                                    </div>
                                    <div class="proposal-box-body" id="proposal-body-${lead.id}">${lead.propuesta_texto}</div>
                                </div>

                                <div class="card-actions">
                                    <div class="status-group">
                                        <button class="status-pill pending ${lead.estado === 'PENDIENTE' ? 'active' : ''}" onclick="updateStatus(${lead.id}, 'PENDIENTE', this)">Pendiente</button>
                                        <button class="status-pill contacted ${lead.estado === 'CONTACTADO' ? 'active' : ''}" onclick="updateStatus(${lead.id}, 'CONTACTADO', this)">Contactado</button>
                                        <button class="status-pill rejected ${lead.estado === 'RECHAZADO' ? 'active' : ''}" onclick="updateStatus(${lead.id}, 'RECHAZADO', this)">Descartar</button>
                                    </div>
                                    
                                    <div class="send-actions">
                                        <button class="btn btn-secondary" style="padding: 0.4rem 0.85rem; font-size: 0.8rem;" onclick="openEditModal(${lead.id})" ${!lead.correo ? 'disabled' : ''}>Editar y Enviar (Caja)</button>
                                        <button class="btn" style="padding: 0.4rem 0.85rem; font-size: 0.8rem; background: linear-gradient(135deg, #10b981, #059669); box-shadow: 0 4px 12px rgba(16,185,129,0.2);" onclick="sendEmail(${lead.id}, this)" ${!lead.correo || isSent ? 'disabled' : ''}>
                                            ${isSent ? 'Reenviar' : 'Enviar Auto (Directo)'}
                                        </button>
                                        <button class="btn btn-secondary" style="color: var(--status-rejected); border-color: rgba(239, 68, 68, 0.3); padding: 0.35rem 0.85rem; font-size: 0.8rem; margin-left: 0.5rem;" onclick="deleteLead(${lead.id})">Eliminar</button>
                                    </div>
                                </div>
                            </div>
                        `;
                    });
                    leadsHTML += '</div>';
                }

                panel.innerHTML = `
                    <div class="domain-detail-header">
                        <div class="domain-title-section">
                            <h2>${domainName}</h2>
                            <div class="domain-detail-meta">
                                <span>Categoría: <strong>${domInfo.categoria || 'Sin clasificar'}</strong></span>
                                <span>Antigüedad: <strong>${domInfo.ano_registro || 'N/A'}</strong></span>
                                <span>Score: <strong>${domInfo.score || 'N/A'}</strong></span>
                            </div>
                        </div>
                    </div>
                    ${leadsHTML}
                `;

            } catch (err) {
                console.error("Error al cargar leads de dominio:", err);
            }
        }

        async function updateStatus(id, newStatus, btn) {
            try {
                const response = await fetch(`api.php?action=update_lead_status&lead_id=${id}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ estado: newStatus })
                });
                const res = await response.json();
                if (res.success) {
                    const group = btn.parentElement;
                    group.querySelectorAll('.status-pill').forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    
                    // Si se marca como contactado, añadir borde y badge
                    const card = document.getElementById(`lead-card-${id}`);
                    if (newStatus === 'CONTACTADO') {
                        card.classList.add('sent-border');
                    } else {
                        card.classList.remove('sent-border');
                    }
                    
                    fetchDomains();
                }
            } catch (err) {
                console.error(err);
            }
        }

        async function sendAllPending() {
            if (!confirm("¿Deseas enviar en AUTOMÁTICO todas las propuestas comerciales que están PENDIENTES con correo electrónico?")) return;
            
            const btn = document.querySelector('button[onclick="sendAllPending()"]');
            const originalText = btn.textContent;
            btn.textContent = "Enviando masivo...";
            btn.disabled = true;
            
            try {
                const response = await fetch('api.php?action=send_all_pending', { method: 'POST' });
                const res = await response.json();
                alert(res.message);
                loadDashboard();
            } catch (err) {
                alert("Error de red al intentar conectar con el servidor SMTP.");
            } finally {
                btn.textContent = originalText;
                btn.disabled = false;
            }
        }

        async function sendEmail(leadId, btn) {
            const originalText = btn.textContent;
            btn.textContent = "Enviando...";
            btn.disabled = true;
            try {
                const response = await fetch(`api.php?action=send_email&lead_id=${leadId}`, { method: 'POST' });
                const res = await response.json();
                if (res.success) {
                    btn.textContent = "¡Enviado!";
                    btn.style.background = "#10b981";
                    alert("¡Propuesta enviada correctamente por correo electrónico!");
                    selectDomain(selectedDomain);
                    fetchDomains();
                } else {
                    btn.textContent = originalText;
                    btn.disabled = false;
                    alert("Error al enviar correo: " + res.error);
                }
            } catch (err) {
                btn.textContent = originalText;
                btn.disabled = false;
                alert("Error de red al intentar conectarse al servidor SMTP.");
            }
        }

        function openEditModal(leadId) {
            const lead = currentLeads.find(l => l.id === leadId);
            if (!lead) return;
            
            document.getElementById('modal-lead-id').value = leadId;
            document.getElementById('modal-to-email').value = lead.correo.split(', ')[0];
            
            let body = lead.propuesta_texto;
            let subject = `Oportunidad de adquisición de marca - ${lead.dominio_venta}`;
            
            // Intentar extraer asunto
            if (body.includes("Asunto:") || body.includes("Subject:")) {
                const lines = body.split('\n');
                for (let i = 0; i < lines.length; i++) {
                    if (lines[i].startsWith("Asunto:") || lines[i].startsWith("Subject:")) {
                        subject = lines[i].replace("Asunto:", "").replace("Subject:", "").trim();
                        body = lines.slice(i + 1).join('\n').trim();
                        break;
                    }
                }
            }
            
            document.getElementById('modal-subject').value = subject;
            document.getElementById('modal-body').value = body;
            
            // Mostrar modal
            const modal = document.getElementById('email-modal');
            modal.style.display = 'flex';
        }

        function closeEmailModal() {
            const modal = document.getElementById('email-modal');
            modal.style.display = 'none';
        }

        async function sendCustomModalEmail() {
            const leadId = document.getElementById('modal-lead-id').value;
            const subject = document.getElementById('modal-subject').value;
            const body = document.getElementById('modal-body').value;
            const btn = document.getElementById('modal-send-btn');
            
            const originalText = btn.textContent;
            btn.textContent = "Enviando...";
            btn.disabled = true;
            
            try {
                const response = await fetch(`api.php?action=send_custom_email&lead_id=${leadId}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ subject: subject, body: body })
                });
                const res = await response.json();
                if (res.success) {
                    alert("¡Propuesta de correo enviada correctamente!");
                    closeEmailModal();
                    selectDomain(selectedDomain);
                    fetchDomains();
                } else {
                    alert("Error al enviar correo: " + res.error);
                    btn.textContent = originalText;
                    btn.disabled = false;
                }
            } catch (err) {
                alert("Error de red al intentar conectarse al servidor SMTP.");
                btn.textContent = originalText;
                btn.disabled = false;
            }
        }

        // Cerrar modal al hacer clic fuera del contenido
        window.onclick = function(event) {
            const modal = document.getElementById('email-modal');
            if (event.target == modal) {
                modal.style.display = "none";
            }
        }

        async function deleteLead(id) {
            if (!confirm("¿Seguro que deseas eliminar este prospecto?")) return;
            try {
                const response = await fetch(`api.php?action=delete_lead&lead_id=${id}`, { method: 'POST' });
                const res = await response.json();
                if (res.success) {
                    selectDomain(selectedDomain);
                    fetchDomains();
                }
            } catch (err) {
                console.error(err);
            }
        }

        function copyLeadProposal(leadId) {
            const lead = currentLeads.find(l => l.id === leadId);
            if (lead) {
                navigator.clipboard.writeText(lead.propuesta_texto);
                const toast = document.getElementById('toast');
                toast.classList.add('show');
                setTimeout(() => toast.classList.remove('show'), 2000);
            }
        }

        async function toggleScraper() {
            if (isHostinger) return;
            const btn = document.getElementById('run-scraper-btn');
            try {
                const response = await fetch('api.php?action=toggle_scraper', { method: 'POST' });
                const status = await response.json();
                
                isScrapingActive = status.active;
                if (isScrapingActive) {
                    btn.textContent = "Escaneando... (Pausar)";
                    btn.style.background = "linear-gradient(135deg, var(--status-rejected), #dc2626)";
                    alert("Se ha iniciado la prospección en segundo plano. Los dominios se irán analizando progresivamente.");
                } else {
                    btn.textContent = "Iniciar Prospección 24/7";
                    btn.style.background = "linear-gradient(135deg, var(--accent-primary), var(--accent-secondary))";
                }
                loadDashboard();
            } catch (err) {
                console.error(err);
            }
        }

        async function checkScraperStatus() {
            if (isHostinger) return;
            try {
                const response = await fetch('api.php?action=scraper_status');
                const status = await response.json();
                const btn = document.getElementById('run-scraper-btn');
                isScrapingActive = status.active;
                if (isScrapingActive) {
                    btn.textContent = "Escaneando en segundo plano...";
                    btn.style.background = "linear-gradient(135deg, var(--status-pending), #d97706)";
                } else {
                    btn.textContent = "Iniciar Prospección 24/7";
                    btn.style.background = "linear-gradient(135deg, var(--accent-primary), var(--accent-secondary))";
                }
            } catch (err) {}
        }

        // Arranque Inicial
        fetchDomains();
        if (!isHostinger) {
            checkScraperStatus();
            setInterval(checkScraperStatus, 4000);
            setInterval(() => {
                if (isScrapingActive) {
                    loadDashboard();
                }
            }, 8000);
        }
    </script>
</body>
</html>
