import os
import threading
import subprocess
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from flask import Flask, jsonify, request, render_template_string, session, redirect, url_for
from flask_cors import CORS
import db_helper
import config

app = Flask(__name__)
app.secret_key = config.SECRET_KEY
CORS(app)

@app.before_request
def check_login():
    """Protege todas las rutas de la app y la API para requerir inicio de sesión."""
    # Excluir la pantalla de login, estáticos y favicon
    if request.path == '/login' or request.path.startswith('/static') or request.path == '/favicon.ico':
        return None
        
    if not session.get('logged_in'):
        # Si la petición es una petición de API (JSON), retornar 401
        if request.path.startswith('/api/'):
            return jsonify({"success": False, "error": "Unauthorized"}), 401
        # De lo contrario, redirigir a la pantalla de login
        return redirect(url_for('login_page'))

# Variable global para rastrear si el script de scraping está activo
scraping_active = False
scraping_thread = None

# Plantilla HTML con diseño split-pane dinámico, responsivo y ultra premium
INDEX_HTML = """
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
            <button class="btn" style="background: linear-gradient(135deg, #3b82f6, #2563eb); box-shadow: 0 4px 12px rgba(59,130,246,0.2);" onclick="syncFromServer(event)">Sincronizar Hostinger</button>
            <button class="btn" style="background: linear-gradient(135deg, #10b981, #059669); box-shadow: 0 4px 12px rgba(16,185,129,0.2);" onclick="sendAllPending()">Enviar Todo Pendiente (Auto)</button>
            <button class="btn" id="run-scraper-btn" onclick="toggleScraper()">Iniciar Prospección 24/7</button>
            <button class="btn btn-secondary" onclick="loadDashboard()">Refrescar Datos</button>
            <a class="btn btn-secondary" style="color: var(--status-rejected); border-color: rgba(239, 68, 68, 0.3); text-decoration: none;" href="/logout">Cerrar Sesión</a>
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
        let allDomains = [];
        let currentLeads = [];
        let selectedDomain = null;
        let isScrapingActive = false;
        let activeLanguageFilter = 'all';

        async function syncFromServer(event) {
            const btn = event.target;
            const originalText = btn.textContent;
            btn.disabled = true;
            btn.textContent = 'Sincronizando...';
            
            try {
                const response = await fetch('/api/sync_from_server', {
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
                const response = await fetch('/api/stats');
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
                const response = await fetch('/api/domains');
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
                const response = await fetch(`/api/domains/${domainName}/leads`);
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
                                    ${isSent ? `<span class="sent-indicator">PROPUSTA ENVIADA</span>` : ''}
                                </div>

                                <div class="lead-contacts">
                                    <div class="contact-field">
                                        <span>📧 Emails:</span>
                                        ${lead.correo ? lead.correo.split(', ').map(email => `<a href="mailto:${email}">${email}</a>`).join(', ') : '<i>Ninguno</i>'}
                                    </div>
                                    <div class="contact-field">
                                        <span>📞 Teléfonos / WhatsApp:</span>
                                        ${lead.telefono ? lead.telefono.split(', ').map(tel => {
                                            const cleanTel = tel.replace(/[^+\\d]/g, '');
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
                const response = await fetch(`/api/leads/${id}/status`, {
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
                const response = await fetch('/api/leads/send_all_pending', { method: 'POST' });
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
                const response = await fetch(`/api/leads/${leadId}/send_email`, { method: 'POST' });
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
                const lines = body.split('\\n');
                for (let i = 0; i < lines.length; i++) {
                    if (lines[i].startsWith("Asunto:") || lines[i].startsWith("Subject:")) {
                        subject = lines[i].replace("Asunto:", "").replace("Subject:", "").trim();
                        body = lines.slice(i + 1).join('\\n').trim();
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
                const response = await fetch(`/api/leads/${leadId}/send_custom_email`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ asunto: subject, cuerpo: body })
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
                const response = await fetch(`/api/leads/${id}`, { method: 'DELETE' });
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
            const btn = document.getElementById('run-scraper-btn');
            try {
                const response = await fetch('/api/toggle_scraper', { method: 'POST' });
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
            try {
                const response = await fetch('/api/scraper_status');
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
        checkScraperStatus();
        setInterval(checkScraperStatus, 4000);
        // Autorefrescar listados cada 8 segundos si está escaneando
        setInterval(() => {
            if (isScrapingActive) {
                loadDashboard();
            }
        }, 8000);
    </script>
</body>
</html>
"""

# Plantilla HTML para la pantalla de inicio de sesión premium con diseño glassmorphism
LOGIN_HTML = """
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
        
        {% if error %}
        <div class="error-message">
            {{ error }}
        </div>
        {% endif %}
        
        <form method="POST" action="/login">
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
"""

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    """Muestra y procesa la pantalla de inicio de sesión."""
    if session.get('logged_in'):
        return redirect(url_for('home'))
        
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == config.ADMIN_USERNAME and password == config.ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('home'))
        else:
            error = "Usuario o contraseña incorrectos. Por favor, intenta de nuevo."
            
    return render_template_string(LOGIN_HTML, error=error)

@app.route('/logout')
def logout():
    """Cierra la sesión del administrador."""
    session.pop('logged_in', None)
    return redirect(url_for('login_page'))

@app.route('/')
def home():
    """Renderiza la interfaz principal directamente desde memoria."""
    return render_template_string(INDEX_HTML)

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Retorna las estadísticas del dashboard."""
    conn = db_helper.get_db_connection()
    cursor = conn.cursor()
    
    # Conteos por estado en clientes
    cursor.execute("SELECT estado, COUNT(*) FROM clientes GROUP BY estado")
    rows = cursor.fetchall()
    stats = {f"leads_{row[0].lower()}": row[1] for row in rows}
    
    # Total dominios
    cursor.execute("SELECT COUNT(*) FROM dominios")
    stats["total_dominios_venta"] = cursor.fetchone()[0]
    
    # Listado de dominios distintos procesados
    cursor.execute("SELECT DISTINCT dominio FROM dominios WHERE estado = 'COMPLETADO'")
    stats["dominios_completados"] = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    return jsonify(stats)

@app.route('/api/domains', methods=['GET'])
def get_domains():
    """Retorna el listado de todos los dominios con la cantidad de leads encontrados."""
    conn = db_helper.get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT d.*, 
               (SELECT COUNT(*) FROM clientes c WHERE c.dominio_venta = d.dominio) as leads_count
        FROM dominios d
        ORDER BY d.score DESC, d.ano_registro ASC
    ''')
    rows = cursor.fetchall()
    domains = [dict(row) for row in rows]
    conn.close()
    return jsonify(domains)

@app.route('/api/domains/<path:domain_name>/leads', methods=['GET'])
def get_domain_leads(domain_name):
    """Retorna los leads calificados de un dominio específico."""
    conn = db_helper.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clientes WHERE dominio_venta = ? ORDER BY created_at DESC", (domain_name,))
    rows = cursor.fetchall()
    leads = [dict(row) for row in rows]
    conn.close()
    return jsonify(leads)

@app.route('/api/leads/<int:lead_id>/status', methods=['POST'])
def update_status(lead_id):
    """Actualiza el estado de un lead específico (PENDIENTE, CONTACTADO, RECHAZADO)."""
    data = request.get_json()
    new_status = data.get('estado')
    
    if new_status not in ['PENDIENTE', 'CONTACTADO', 'RECHAZADO']:
        return jsonify({"success": False, "error": "Estado inválido"}), 400
        
    conn = db_helper.get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE clientes SET estado = ? WHERE id = ?", (new_status, lead_id))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/leads/<int:lead_id>', methods=['DELETE'])
def delete_lead(lead_id):
    """Elimina permanentemente un lead de la base de datos."""
    conn = db_helper.get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM clientes WHERE id = ?", (lead_id,))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        conn.close()

def send_html_email_via_smtp(lead, smtp_server, smtp_port, smtp_user, smtp_password, custom_subject=None, custom_body=None):
    """Auxiliar para enviar una propuesta de correo HTML con diseño profesional y logo."""
    from email.mime.multipart import MIMEMultipart
    from email.mime.image import MIMEImage

    body = custom_body if custom_body is not None else lead['propuesta_texto']
    subject = custom_subject if custom_subject is not None else f"Oportunidad de adquisición de marca - {lead['dominio_venta']}"
    
    # Intentar extraer el asunto automático de la IA si está estructurado en el texto
    if custom_subject is None:
        lines = body.split('\n')
        for line in lines:
            if line.startswith("Asunto:") or line.startswith("Subject:"):
                subject = line.replace("Asunto:", "").replace("Subject:", "").strip()
                body = "\n".join(lines[lines.index(line)+1:]).strip()
                break
            
    # Convertir saltos de línea dobles del cuerpo en párrafos HTML
    paragraphs = body.split('\n\n')
    body_html = ""
    for p in paragraphs:
        if p.strip():
            p_clean = p.strip().replace('\n', '<br>')
            body_html += f"<p style='margin-bottom: 15px; color: #374151; font-size: 15px; line-height: 1.6;'>{p_clean}</p>"
            
    # Plantilla HTML con cabecera corporativa y pie con logo para MySmartDomains
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
                color: #374151;
                background-color: #f3f4f6;
                margin: 0;
                padding: 0;
            }}
            .email-container {{
                max-width: 600px;
                margin: 20px auto;
                background-color: #ffffff;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
                border: 1px solid #e5e7eb;
            }}
            .email-header {{
                background: linear-gradient(135deg, #0b0f19, #111827);
                padding: 25px 20px;
                text-align: center;
                border-bottom: 3px solid #8b5cf6;
            }}
            .email-body {{
                padding: 35px 30px;
                line-height: 1.6;
            }}
            .domain-badge-box {{
                text-align: center;
                margin: 25px 0;
            }}
            .domain-badge {{
                display: inline-block;
                background-color: rgba(139, 92, 246, 0.08);
                color: #6d28d9;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 18px;
                border: 1px solid rgba(139, 92, 246, 0.15);
                letter-spacing: 0.5px;
            }}
            .email-footer {{
                background-color: #f9fafb;
                padding: 25px 30px;
                border-top: 1px solid #e5e7eb;
                font-size: 13px;
                color: #6b7280;
            }}
            .footer-title {{
                font-weight: bold;
                color: #1f2937;
                margin-bottom: 5px;
            }}
            .footer-info {{
                margin-top: 10px;
                line-height: 1.5;
            }}
            .footer-info a {{
                color: #6366f1;
                text-decoration: none;
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="email-header">
                <img src="cid:logo_img" alt="MySmartDomains.com" style="max-height: 60px; border-radius: 4px; display: block; margin: 0 auto;">
            </div>
            <div class="email-body">
                {body_html}
                <div class="domain-badge-box">
                    <div class="domain-badge">{lead['dominio_venta']}</div>
                </div>
            </div>
            <div class="email-footer">
                <div class="footer-title">Vibra Deals Brokerage Services</div>
                <div>Aviso informativo sobre activos de marca digital y adquisición de dominios.</div>
                <div class="footer-info">
                    Teléfono comercial: <strong>(813) 842-5302</strong><br>
                    Email: <a href="mailto:vibradeals@gmail.com">vibradeals@gmail.com</a><br>
                    Catálogo oficial: <a href="https://mysmartdomains.com/" target="_blank">mysmartdomains.com</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    to_email = lead['correo'].split(', ')[0] if lead['correo'] else ""
    if not to_email:
        raise ValueError("El lead no tiene correo de contacto registrado.")

    # Configurar MIME con soporte para adjuntos en línea (relacionados)
    msg = MIMEMultipart('related')
    msg['Subject'] = Header(subject, 'utf-8')
    msg['From'] = f"Vibra Deals <{smtp_user}>"
    msg['To'] = to_email
    
    msg_alternative = MIMEMultipart('alternative')
    msg.attach(msg_alternative)
    
    html_part = MIMEText(html_content, 'html', 'utf-8')
    msg_alternative.attach(html_part)
    
    # Adjuntar logo.png localmente usando CID
    logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'logo.png')
    if os.path.exists(logo_path):
        try:
            with open(logo_path, 'rb') as f:
                img_data = f.read()
            msg_image = MIMEImage(img_data)
            msg_image.add_header('Content-ID', '<logo_img>')
            msg_image.add_header('Content-Disposition', 'inline', filename='logo.png')
            msg.attach(msg_image)
        except Exception as img_err:
            print(f"Error al adjuntar imagen de logo al correo: {img_err}")
    else:
        print(f"No se encontró el logo en la ruta: {logo_path}")
    
    # Enviar
    server = smtplib.SMTP(smtp_server, int(smtp_port))
    server.starttls()
    server.login(smtp_user, smtp_password)
    server.sendmail(smtp_user, [to_email], msg.as_string())
    server.quit()

@app.route('/api/leads/<int:lead_id>/send_email', methods=['POST'])
def send_email(lead_id):
    """Envía la propuesta comercial por correo utilizando el servidor SMTP del .env."""
    conn = db_helper.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clientes WHERE id = ?", (lead_id,))
    lead = cursor.fetchone()
    conn.close()
    
    if not lead:
        return jsonify({"success": False, "error": "Lead no encontrado"}), 404
        
    if not lead['correo']:
        return jsonify({"success": False, "error": "El lead no tiene correo electrónico de contacto registrado."}), 400
        
    # Cargar configuraciones SMTP desde variables de entorno (.env)
    smtp_server = os.environ.get("SMTP_SERVER")
    smtp_port = os.environ.get("SMTP_PORT")
    smtp_user = os.environ.get("SMTP_USER") or os.environ.get("SMTP_EMAIL")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    
    if not smtp_server or not smtp_port or not smtp_user or not smtp_password:
        return jsonify({
            "success": False, 
            "error": "Servidor SMTP no configurado. Por favor, edita tu archivo '.env' y añade las variables: SMTP_SERVER, SMTP_PORT, SMTP_USER y SMTP_PASSWORD."
        }), 400
        
    try:
        send_html_email_via_smtp(lead, smtp_server, smtp_port, smtp_user, smtp_password)
        
        # Guardar estado a CONTACTADO en base de datos para prevenir envíos duplicados
        conn = db_helper.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE clientes SET estado = 'CONTACTADO' WHERE id = ?", (lead_id,))
        conn.commit()
        conn.close()
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": f"Error SMTP al enviar: {str(e)}"}), 500

@app.route('/api/leads/<int:lead_id>/send_custom_email', methods=['POST'])
def send_custom_email(lead_id):
    """Envía un correo con asunto y cuerpo editados manualmente por el usuario."""
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No se recibieron datos de correo."}), 400
        
    custom_subject = data.get("asunto")
    custom_body = data.get("cuerpo")
    
    if not custom_subject or not custom_body:
        return jsonify({"success": False, "error": "El asunto y el cuerpo del correo son obligatorios."}), 400
        
    conn = db_helper.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clientes WHERE id = ?", (lead_id,))
    lead = cursor.fetchone()
    conn.close()
    
    if not lead:
        return jsonify({"success": False, "error": "Lead no encontrado"}), 404
        
    if not lead['correo']:
        return jsonify({"success": False, "error": "El lead no tiene correo electrónico de contacto registrado."}), 400
        
    smtp_server = os.environ.get("SMTP_SERVER")
    smtp_port = os.environ.get("SMTP_PORT")
    smtp_user = os.environ.get("SMTP_USER") or os.environ.get("SMTP_EMAIL")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    
    if not smtp_server or not smtp_port or not smtp_user or not smtp_password:
        return jsonify({
            "success": False, 
            "error": "Servidor SMTP no configurado. Por favor, edita tu archivo '.env' y añade las variables: SMTP_SERVER, SMTP_PORT, SMTP_USER y SMTP_PASSWORD."
        }), 400
        
    try:
        send_html_email_via_smtp(
            lead, 
            smtp_server, 
            smtp_port, 
            smtp_user, 
            smtp_password, 
            custom_subject=custom_subject, 
            custom_body=custom_body
        )
        
        # Guardar estado a CONTACTADO y guardar la propuesta modificada en SQLite
        conn = db_helper.get_db_connection()
        cursor = conn.cursor()
        nueva_propuesta = f"Asunto: {custom_subject}\n\n{custom_body}"
        cursor.execute("UPDATE clientes SET estado = 'CONTACTADO', propuesta_texto = ? WHERE id = ?", 
                       (nueva_propuesta, lead_id))
        conn.commit()
        conn.close()
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": f"Error SMTP al enviar: {str(e)}"}), 500

@app.route('/api/leads/send_all_pending', methods=['POST'])
def send_all_pending():
    """Envía todas las propuestas en estado PENDIENTE de forma masiva/automática en formato HTML."""
    smtp_server = os.environ.get("SMTP_SERVER")
    smtp_port = os.environ.get("SMTP_PORT")
    smtp_user = os.environ.get("SMTP_USER") or os.environ.get("SMTP_EMAIL")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    
    if not smtp_server or not smtp_port or not smtp_user or not smtp_password:
        return jsonify({
            "success": False, 
            "error": "Servidor SMTP no configurado en el archivo '.env'. Registra tus credenciales SMTP para habilitar el envío masivo automático."
        }), 400
        
    conn = db_helper.get_db_connection()
    cursor = conn.cursor()
    # Obtener todos los leads con correo que están PENDIENTES
    cursor.execute("SELECT * FROM clientes WHERE estado = 'PENDIENTE' AND correo IS NOT NULL AND correo != ''")
    pending_leads = cursor.fetchall()
    conn.close()
    
    if len(pending_leads) == 0:
        return jsonify({"success": True, "sent_count": 0, "message": "No hay correos pendientes en estado PENDIENTE por enviar."})
        
    sent_count = 0
    errors = []
    
    for lead in pending_leads:
        try:
            send_html_email_via_smtp(lead, smtp_server, smtp_port, smtp_user, smtp_password)
            
            # Actualizar estado del lead a CONTACTADO
            conn = db_helper.get_db_connection()
            db_cursor = conn.cursor()
            db_cursor.execute("UPDATE clientes SET estado = 'CONTACTADO' WHERE id = ?", (lead['id'],))
            conn.commit()
            conn.close()
            
            sent_count += 1
        except Exception as e:
            errors.append(f"Error enviando a {lead['empresa_nombre']} ({lead['correo']}): {str(e)}")
            
    if errors:
        return jsonify({
            "success": True,
            "sent_count": sent_count,
            "warnings": errors,
            "message": f"Se enviaron {sent_count} propuestas comerciales. Ocurrieron {len(errors)} errores de envío."
        })
        
    return jsonify({
        "success": True, 
        "sent_count": sent_count,
        "message": f"¡Se enviaron con éxito {sent_count} propuestas comerciales en formato HTML!"
    })

def run_scraper_agent():
    """Ejecuta el script de prospección principal continuamente en segundo plano (24/7)."""
    global scraping_active
    import time
    while scraping_active:
        try:
            print("Iniciando ciclo automático de prospección (main.py)...")
            subprocess.run(["python", "main.py"], check=True)
        except Exception as e:
            print(f"Error en el ciclo de prospección: {e}")
            
        print("Ciclo de prospección completado. Esperando 5 minutos para el siguiente ciclo...")
        # Dormir en intervalos cortos para permitir apagado rápido
        for _ in range(300):
            if not scraping_active:
                break
            time.sleep(1)

@app.route('/api/sync_from_server', methods=['POST'])
def sync_from_server():
    """Descarga la base de datos domain_leads.db desde el servidor Hostinger por SFTP."""
    import paramiko
    import shutil
    
    ssh_host = os.environ.get("SSH_HOST")
    ssh_port = os.environ.get("SSH_PORT", "65002")
    ssh_user = os.environ.get("SSH_USER")
    ssh_password = os.environ.get("SSH_PASSWORD")
    remote_db_path = os.environ.get("SSH_REMOTE_DB_PATH", "/home/u114856156/agente_dominio/domain_leads.db")
    
    if not ssh_host or not ssh_user or not ssh_password:
        return jsonify({"success": False, "error": "Credenciales SSH de Hostinger no configuradas en el archivo .env"}), 400
        
    try:
        # Hacer copia de seguridad de la base de datos local actual antes de reemplazarla
        local_db = config.DB_PATH
        if os.path.exists(local_db):
            shutil.copy2(local_db, local_db + ".bak")
            
        # Conectar por SSH
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ssh_host, port=int(ssh_port), username=ssh_user, password=ssh_password, timeout=15)
        
        # Descargar el archivo de base de datos
        sftp = ssh.open_sftp()
        print(f"Descargando {remote_db_path} a {local_db}...")
        sftp.get(remote_db_path, local_db)
        sftp.close()
        ssh.close()
        
        return jsonify({"success": True, "message": "Base de datos sincronizada con éxito desde Hostinger."})
    except Exception as e:
        # Restaurar copia de seguridad si falla
        local_db = config.DB_PATH
        if os.path.exists(local_db + ".bak") and os.path.exists(local_db):
            try:
                shutil.copy2(local_db + ".bak", local_db)
            except Exception:
                pass
        return jsonify({"success": False, "error": f"Error al sincronizar desde Hostinger: {str(e)}"}), 500

@app.route('/api/toggle_scraper', methods=['POST'])
def toggle_scraper():
    """Enciende o apaga el agente de scraping en segundo plano."""
    global scraping_active, scraping_thread
    if not scraping_active:
        scraping_active = True
        scraping_thread = threading.Thread(target=run_scraper_agent)
        scraping_thread.daemon = True
        scraping_thread.start()
    else:
        scraping_active = False
        
    return jsonify({"active": scraping_active})

@app.route('/api/scraper_status', methods=['GET'])
def scraper_status():
    """Retorna si el agente de scraping se encuentra activo."""
    global scraping_active
    return jsonify({"active": scraping_active})

if __name__ == '__main__':
    # Inicializar la base de datos por seguridad
    db_helper.init_db()
    
    # Iniciar el agente de prospección automáticamente al arrancar
    # Evitamos doble ejecución en modo debug verificando WERKZEUG_RUN_MAIN
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug:
        scraping_active = True
        scraping_thread = threading.Thread(target=run_scraper_agent)
        scraping_thread.daemon = True
        scraping_thread.start()
        print(">>> Agente de prospección 24/7 INICIADO AUTOMÁTICAMENTE en segundo plano.")
        
    # Levantar el servidor en el puerto 5000
    print("Levantando Panel Visual en: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
