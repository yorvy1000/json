<?php
header('Content-Type: application/json');

// Habilitar sesiones
session_start();

// Validar inicio de sesión
if (!isset($_SESSION['logged_in']) || $_SESSION['logged_in'] !== true) {
    http_response_code(401);
    echo json_encode(["success" => false, "error" => "Unauthorized"]);
    exit;
}

// Leer cuerpo de la petición si es JSON
$input_json = file_get_contents('php://input');
$input_data = json_decode($input_json, true);
if (is_array($input_data)) {
    $_POST = array_merge($_POST, $input_data);
}

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

$action = isset($_GET['action']) ? $_GET['action'] : '';

switch ($action) {
    case 'get_stats':
        try {
            // Contar dominios en total
            $total_dominios = $db->query("SELECT COUNT(*) FROM dominios")->fetchColumn();
            
            // Contar leads por estado
            $stmt = $db->query("SELECT estado, COUNT(*) as qty FROM clientes GROUP BY estado");
            $rows = $stmt->fetchAll();
            
            $stats = [
                "total_dominios_venta" => (int)$total_dominios,
                "leads_pendiente" => 0,
                "leads_contactado" => 0,
                "leads_rechazado" => 0
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
        $output = shell_exec($cmd);
        
        if (empty($output)) {
            http_response_code(500);
            echo json_encode(["success" => false, "error" => "No se recibió respuesta del enviador de correos CLI."]);
            exit;
        }
        
        $res = json_decode($output, true);
        if (isset($res['success']) && $res['success'] === true) {
            echo json_encode($res);
        } else {
            http_response_code(500);
            echo json_encode($res ? $res : ["success" => false, "error" => "Error desconocido al ejecutar el script de correos. Salida: " . $output]);
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
               
        $output = shell_exec($cmd);
        
        if (empty($output)) {
            http_response_code(500);
            echo json_encode(["success" => false, "error" => "No se recibió respuesta del enviador de correos CLI."]);
            exit;
        }
        
        $res = json_decode($output, true);
        if (isset($res['success']) && $res['success'] === true) {
            echo json_encode($res);
        } else {
            http_response_code(500);
            echo json_encode($res ? $res : ["success" => false, "error" => "Error desconocido al ejecutar el script de correos. Salida: " . $output]);
        }
        break;

    case 'send_all_pending':
        try {
            // Buscar todos los leads pendientes que tienen correo electrónico
            $stmt = $db->query("SELECT id FROM clientes WHERE estado = 'PENDIENTE' AND correo IS NOT NULL AND correo != ''");
            $leads = $stmt->fetchAll();
            
            $sent_count = 0;
            $errors = [];
            
            foreach ($leads as $lead) {
                $lead_id = $lead['id'];
                $cmd = escapeshellcmd($python_bin) . " " . escapeshellarg($script_path) . " --lead_id " . escapeshellarg($lead_id);
                $output = shell_exec($cmd);
                $res = json_decode($output, true);
                
                if (isset($res['success']) && $res['success'] === true) {
                    $sent_count++;
                } else {
                    $errors[] = "Lead ID $lead_id: " . (isset($res['error']) ? $res['error'] : "Fallo desconocido");
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

    default:
        http_response_code(400);
        echo json_encode(["success" => false, "error" => "Acción inválida o no especificada."]);
        break;
}
