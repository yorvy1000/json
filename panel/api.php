<?php
ini_set('display_errors', 1);
error_reporting(E_ALL);

// Configurar sesion ANTES de session_start() para que coincida con index.php
ini_set('session.cookie_httponly', 1);
ini_set('session.use_strict_mode', 1);
ini_set('session.cookie_path', '/');
ini_set('session.cookie_samesite', 'Lax');
session_name('VIBRADEALS_SESS');
session_start();

header('Content-Type: text/plain; charset=utf-8');
header('Cache-Control: no-cache, no-store, must-revalidate');

// Validar inicio de sesion (excluir track_open de la autenticacion)
$action = isset($_GET['action']) ? $_GET['action'] : '';
if ($action !== 'track_open') {
    if (!isset($_SESSION['logged_in']) || $_SESSION['logged_in'] !== true) {
        http_response_code(401);
        echo json_encode(["success" => false, "error" => "Sesion no valida. Por favor recarga la pagina e inicia sesion de nuevo."]);
        exit;
    }
}

// Array para capturar logs de errores
$captured_logs = [];
set_error_handler(function($errno, $errstr, $errfile, $errline) use (&$captured_logs) {
    $log_message = "PHP Error [$errno]: $errstr in $errfile on line $errline";
    $captured_logs[] = $log_message;
    // También enviar al log estándar de PHP
    error_log($log_message);
    // No interrumpir la ejecución para errores no fatales y evitar que PHP imprima el warning
    return true;
});

// Leer cuerpo de la petición si es JSON
$input_json = file_get_contents('php://input');
$input_data = json_decode($input_json, true);
if (is_array($input_data)) {
    $_POST = array_merge($_POST, $input_data);
}

// Start output buffering to capture any errors before JSON output
ob_start();

// Determinar ruta de base de datos (con fallback local)
$db_path = "/home/u114856156/agente_dominio/domain_leads.db";
if (!file_exists($db_path)) {
    $db_path = __DIR__ . "/../domain_leads.db";
}

try {
    $db = new PDO("sqlite:" . $db_path);
    $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $db->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);
} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode(["success" => false, "error" => "Error al conectar a la base de datos: " . $e->getMessage()]);
    exit;
}

// Determinar ejecutable y ruta del script de Python CLI para envío de correos
$python_bin = "python3";
$script_path = "/home/u114856156/agente_dominio/send_email_cli.py";
if (!file_exists($script_path)) {
    $script_path = __DIR__ . "/../send_email_cli.py";
    $python_bin = "python"; // fallback Windows
}

/**
 * Ejecuta un comando usando proc_open de manera segura.
 * Útil cuando shell_exec() está deshabilitado en el hosting.
 */
function run_command_via_proc_open($cmd) {
    $descriptorspec = [
        0 => ["pipe", "r"], // stdin
        1 => ["pipe", "w"], // stdout
        2 => ["pipe", "w"]  // stderr
    ];
    
    $process = proc_open($cmd, $descriptorspec, $pipes);
    
    if (is_resource($process)) {
        fclose($pipes[0]); // Cerrar stdin inmediatamente
        
        $stdout = stream_get_contents($pipes[1]);
        fclose($pipes[1]);
        
        $stderr = stream_get_contents($pipes[2]);
        fclose($pipes[2]);
        
        $exit_code = proc_close($process);
        
        return [
            'success' => ($exit_code === 0),
            'stdout' => trim($stdout),
            'stderr' => trim($stderr),
            'exit_code' => $exit_code
        ];
    }
    
    return [
        'success' => false,
        'stdout' => '',
        'stderr' => 'Error: No se pudo iniciar el proceso con proc_open.',
        'exit_code' => -1
    ];
}

try {
    $action = isset($_GET['action']) ? $_GET['action'] : '';

    switch ($action) {
    case 'track_open':
        $lead_id = isset($_GET['lead_id']) ? (int)$_GET['lead_id'] : 0;
        if ($lead_id > 0) {
            try {
                // Actualizar estado de lectura en SQLite
                $stmt = $db->prepare("UPDATE clientes SET leido = 1 WHERE id = ?");
                $stmt->execute([$lead_id]);
            } catch (Exception $e) {
                error_log("API: Error in track_open: " . $e->getMessage());
            }
        }
        
        // Retornar una imagen GIF transparente de 1x1 pixel
        header('Content-Type: image/gif');
        header('Cache-Control: no-cache, no-store, must-revalidate');
        header('Pragma: no-cache');
        header('Expires: 0');
        echo base64_decode('R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7');
        exit;

    case 'get_stats':
        try {
            // Contar dominios en total
            $total_dominios = $db->query("SELECT COUNT(*) FROM dominios")->fetchColumn();
            
            // Contar leads por estado
            $stmt = $db->query("SELECT estado, COUNT(*) as qty FROM clientes GROUP BY estado");
            $rows = $stmt->fetchAll();
            
            // Contar leads leídos
            $total_leidos = $db->query("SELECT COUNT(*) FROM clientes WHERE leido = 1")->fetchColumn();

            $stats = [
                "total_dominios_venta" => (int)$total_dominios,
                "leads_pendiente" => 0,
                "leads_contactado" => 0,
                "leads_rechazado" => 0,
                "leads_leidos" => (int)$total_leidos
            ];
            
            foreach ($rows as $row) {
                if ($row['estado'] === 'PENDIENTE') {
                    $stats["leads_pendiente"] = (int)$row['qty'];
                } elseif ($row['estado'] === 'CONTACTADO') {
                    $stats["leads_contactado"] = (int)$row['qty'];
                } elseif ($row['estado'] === 'RECHAZADO') {
                    $stats["leads_rechazado"] = (int)$row['qty'];
                }
            }
            
            echo json_encode($stats);
        } catch (Exception $e) {
            http_response_code(500);
            echo json_encode(["success" => false, "error" => $e->getMessage()]);
        }
        break;

    case 'get_domains':
        try {
            // Obtener todos los dominios con conteo de leads
            $stmt = $db->query("
                SELECT d.*, 
                       (SELECT COUNT(*) FROM clientes c WHERE c.dominio_venta = d.dominio) as leads_count
                FROM dominios d
                ORDER BY d.score DESC, d.ano_registro ASC
            ");
            $domains = $stmt->fetchAll();
            echo json_encode($domains);
        } catch (Exception $e) {
            http_response_code(500);
            echo json_encode(["success" => false, "error" => $e->getMessage()]);
        }
        break;

    case 'get_leads':
        $domain = isset($_GET['domain']) ? $_GET['domain'] : '';
        if (empty($domain)) {
            http_response_code(400);
            echo json_encode(["success" => false, "error" => "Parámetro 'domain' es requerido."]);
            exit;
        }
        
        try {
            $stmt = $db->prepare("SELECT * FROM clientes WHERE dominio_venta = ? ORDER BY id DESC");
            $stmt->execute([$domain]);
            $leads = $stmt->fetchAll();
            echo json_encode($leads);
        } catch (Exception $e) {
            http_response_code(500);
            echo json_encode(["success" => false, "error" => $e->getMessage()]);
        }
        break;

    case 'update_lead_status':
        $lead_id = isset($_GET['lead_id']) ? (int)$_GET['lead_id'] : 0;
        $new_status = isset($_POST['estado']) ? $_POST['estado'] : '';
        
        if ($lead_id <= 0 || !in_array($new_status, ['PENDIENTE', 'CONTACTADO', 'RECHAZADO'])) {
            http_response_code(400);
            echo json_encode(["success" => false, "error" => "ID de lead o estado inválido."]);
            exit;
        }
        
        try {
            $stmt = $db->prepare("UPDATE clientes SET estado = ? WHERE id = ?");
            $stmt->execute([$new_status, $lead_id]);
            echo json_encode(["success" => true]);
        } catch (Exception $e) {
            http_response_code(500);
            echo json_encode(["success" => false, "error" => $e->getMessage()]);
        }
        break;

    case 'delete_lead':
        $lead_id = isset($_GET['lead_id']) ? (int)$_GET['lead_id'] : 0;
        
        if ($lead_id <= 0) {
            http_response_code(400);
            echo json_encode(["success" => false, "error" => "ID de lead inválido."]);
            exit;
        }
        
        try {
            $stmt = $db->prepare("DELETE FROM clientes WHERE id = ?");
            $stmt->execute([$lead_id]);
            echo json_encode(["success" => true]);
        } catch (Exception $e) {
            http_response_code(500);
            echo json_encode(["success" => false, "error" => $e->getMessage()]);
        }
        break;

    case 'send_email':
        $lead_id = isset($_GET['lead_id']) ? (int)$_GET['lead_id'] : 0;
        if ($lead_id <= 0) {
            http_response_code(400);
            echo json_encode(["success" => false, "error" => "ID de lead inválido."]);
            exit;
        }
        
        // Ejecutar script de Python para enviar correo
        $cmd = escapeshellcmd($python_bin) . " " . escapeshellarg($script_path) . " --lead_id " . escapeshellarg($lead_id);
        $res_proc = run_command_via_proc_open($cmd);
        $output = $res_proc['stdout'];
        
        if (empty($output)) {
            http_response_code(500);
            echo json_encode(["success" => false, "error" => "No se recibió respuesta del enviador de correos CLI. Stderr: " . $res_proc['stderr']]);
            exit;
        }
        
        $res = json_decode($output, true);
        if (isset($res['success']) && $res['success'] === true) {
            echo json_encode($res);
        } else {
            http_response_code(500);
            echo json_encode($res ? $res : ["success" => false, "error" => "Error al ejecutar el script de correos. Stderr: " . $res_proc['stderr'] . " | Output: " . $output]);
        }
        break;

    case 'send_custom_email':
        $lead_id = isset($_GET['lead_id']) ? (int)$_GET['lead_id'] : 0;
        $subject = isset($_POST['subject']) ? $_POST['subject'] : (isset($_POST['asunto']) ? $_POST['asunto'] : '');
        $body = isset($_POST['body']) ? $_POST['body'] : (isset($_POST['cuerpo']) ? $_POST['cuerpo'] : '');
        
        if ($lead_id <= 0 || empty($subject) || empty($body)) {
            http_response_code(400);
            echo json_encode(["success" => false, "error" => "Parámetros incompletos para el correo personalizado."]);
            exit;
        }
        
        // Ejecutar script de Python con asunto y cuerpo personalizados
        $cmd = escapeshellcmd($python_bin) . " " . 
               escapeshellarg($script_path) . 
               " --lead_id " . escapeshellarg($lead_id) . 
               " --subject " . escapeshellarg($subject) . 
               " --body " . escapeshellarg($body);
               
        $res_proc = run_command_via_proc_open($cmd);
        $output = $res_proc['stdout'];
        
        if (empty($output)) {
            http_response_code(500);
            echo json_encode(["success" => false, "error" => "No se recibió respuesta del enviador de correos CLI. Stderr: " . $res_proc['stderr']]);
            exit;
        }
        
        $res = json_decode($output, true);
        if (isset($res['success']) && $res['success'] === true) {
            echo json_encode($res);
        } else {
            http_response_code(500);
            echo json_encode($res ? $res : ["success" => false, "error" => "Error al ejecutar el script de correos. Stderr: " . $res_proc['stderr'] . " | Output: " . $output]);
        }
        break;

    case 'send_all_pending':
        $domain = isset($_GET['domain']) ? $_GET['domain'] : '';
        try {
            if (!empty($domain)) {
                $stmt = $db->prepare("SELECT id FROM clientes WHERE estado = 'PENDIENTE' AND dominio_venta = ? AND correo IS NOT NULL AND correo != ''");
                $stmt->execute([$domain]);
            } else {
                $stmt = $db->query("SELECT id FROM clientes WHERE estado = 'PENDIENTE' AND correo IS NOT NULL AND correo != ''");
            }
            $leads = $stmt->fetchAll();
            
            $sent_count = 0;
            $errors = [];
            
            foreach ($leads as $lead) {
                $lead_id = $lead['id'];
                $cmd = escapeshellcmd($python_bin) . " " . escapeshellarg($script_path) . " --lead_id " . escapeshellarg($lead_id);
                $res_proc = run_command_via_proc_open($cmd);
                $output = $res_proc['stdout'];
                $res = json_decode($output, true);
                
                if (isset($res['success']) && $res['success'] === true) {
                    $sent_count++;
                } else {
                    $errors[] = "Lead ID $lead_id: " . (isset($res['error']) ? $res['error'] : "Fallo desconocido. Stderr: " . $res_proc['stderr']);
                }
            }
            
            echo json_encode([
                "success" => true, 
                "sent_count" => $sent_count, 
                "errors" => $errors,
                "message" => "Proceso de envío masivo completado. Se enviaron $sent_count correos."
            ]);
        } catch (Exception $e) {
            http_response_code(500);
            echo json_encode(["success" => false, "error" => $e->getMessage()]);
        }
        break;

    case 'send_test_email':
        // Log the entry into the send_test_email case
        error_log("API: Entering send_test_email case.");

        try {
            // Obtener el primer lead disponible para usar como plantilla
            $stmt = $db->query("SELECT id FROM clientes LIMIT 1");
            $lead = $stmt->fetch(PDO::FETCH_ASSOC);
            
            if (!$lead) {
                error_log("API: No leads found for test email.");
                http_response_code(404);
                echo json_encode(["success" => false, "error" => "No hay leads en la base de datos para enviar un correo de prueba."]);
                exit;
            }
            
            $lead_id = $lead['id'];
            $test_email = "yorvygarcia@gmail.com"; // Correo del usuario para pruebas
            
            $cmd = escapeshellcmd($python_bin) . " " . 
                   escapeshellarg($script_path) . 
                   " --lead_id " . escapeshellarg($lead_id) . 
                   " --test_recipient " . escapeshellarg($test_email);
            
            error_log("API: Executing Python command: " . $cmd);
            $res_proc = run_command_via_proc_open($cmd);
            $output = $res_proc['stdout'];
            error_log("API: Python script raw output: " . var_export($output, true) . " | Stderr: " . var_export($res_proc['stderr'], true));
            
            if (empty($output)) {
                error_log("API: Python script returned empty output.");
                http_response_code(500);
                echo json_encode(["success" => false, "error" => "No se recibió respuesta del enviador de correos CLI. Stderr: " . $res_proc['stderr'], "php_logs" => $captured_logs]);
                exit;
            }
            
            $res = json_decode($output, true);
            error_log("API: Python script JSON response: " . var_export($res, true));
            if (isset($res['success']) && $res['success'] === true) {
                error_log("API: Test email sent successfully.");
                echo json_encode($res);
            } else {
                error_log("API: Test email sending failed. Error: " . ($res['error'] ?? 'Unknown') . " | Python Output: " . $output);
                http_response_code(500);
                echo json_encode(["success" => false, "error" => ($res['error'] ?? "Error desconocido") . " - Stderr: " . $res_proc['stderr'] . " - Raw Python Output: " . $output, "php_logs" => $captured_logs]);
            }
        } catch (Exception $e) {
            error_log("API: Exception caught during send_test_email: " . $e->getMessage());
            http_response_code(500);
            echo json_encode(["success" => false, "error" => $e->getMessage(), "php_logs" => $captured_logs]);
        }
        break;

    default:
        http_response_code(400);
        echo json_encode(["success" => false, "error" => "Acción inválida o no especificada.", "php_logs" => $captured_logs]);
        break;
}

} catch (Exception $e) {
    $buffered_output = ob_get_clean();
    error_log("API: Uncaught PHP Exception: " . $e->getMessage() . ", File: " . $e->getFile() . ", Line: " . $e->getLine() . ", Buffered Output: " . $buffered_output);
    http_response_code(500);
    echo json_encode(["success" => false, "error" => "Error interno del servidor: " . $e->getMessage(), "php_logs" => $captured_logs, "buffered_output" => $buffered_output]);
} finally {
    if (ob_get_level() > 0) {
        ob_end_flush();
    }
}
