import os
import subprocess
from datetime import datetime

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QMessageBox, QDialog,
    QCheckBox, QSystemTrayIcon, QMenu, QAction,
    QStyle, QApplication, QTextEdit
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QTimer

from paths import get_game_paths
from backup import create_backup
from restore import restore_backup
from config import (
    load_config, save_config,
    has_shown_disclaimer, mark_disclaimer_shown,
    is_startup_enabled, enable_startup, disable_startup
)
from process_watcher import GameProcessWatcher
from logger import log_event, read_log, clear_log
from links_manager import open_link
from app_paths import get_log_file


class DisclaimerDialog(QDialog):
    """Dialog de disclaimer mostrado na primeira execução - 2 etapas"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Aviso Importante")
        self.setModal(True)
        self.setGeometry(100, 100, 500, 400)
        self.accepted = False
        self.current_stage = 1

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        self.show_stage1()

    def clear_layout(self):
        """Limpa o layout atual"""
        while self.main_layout.count():
            child = self.main_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def show_stage1(self):
        """Primeira etapa: Aviso"""
        self.clear_layout()
        self.current_stage = 1

        # Título
        lbl_title = QLabel("⚠️ AVISO DE RESPONSABILIDADE")
        lbl_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.main_layout.addWidget(lbl_title)

        # Mensagem
        msg = QLabel(
            "Não nos responsabilizamos por qualquer falha ou perda de dados.\n\n"
            "Estamos entregando o software do jeito que ele está.\n\n"
            "Use com cautela!\n\n"
            "⚠️ Sempre puxe (restaure) backups com o jogo aberto mas no LOBBY\n"
            "para evitar problemas com a nuvem Steam."
        )
        msg.setWordWrap(True)
        msg.setStyleSheet("font-size: 11px; margin: 20px 0;")
        self.main_layout.addWidget(msg)

        self.main_layout.addStretch()

        # Botões
        layout_buttons = QHBoxLayout()

        btn_cancel = QPushButton("Cancelar / Não Aceito")
        btn_cancel.setStyleSheet("background-color: #f44336; color: white;")
        btn_cancel.clicked.connect(self.reject)

        btn_next = QPushButton("Avançar")
        btn_next.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        btn_next.clicked.connect(self.show_stage2)

        layout_buttons.addWidget(btn_cancel)
        layout_buttons.addStretch()
        layout_buttons.addWidget(btn_next)

        self.main_layout.addLayout(layout_buttons)

    def show_stage2(self):
        """Segunda etapa: Sarcasmo + Confirmação"""
        self.clear_layout()
        self.current_stage = 2

        # Título
        lbl_title = QLabel("😏 Entendido!")
        lbl_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.main_layout.addWidget(lbl_title)

        # Mensagem sarcástica
        msg = QLabel(
            "Eu sei que você não leu.\n\n"
            "Se você quiser voltar tem o botão abaixo.\n\n"
            "Caso contrário, clique em 'Entrar no app' para continuar."
        )
        msg.setWordWrap(True)
        msg.setStyleSheet("font-size: 11px; margin: 20px 0; font-style: italic; color: #666;")
        self.main_layout.addWidget(msg)

        self.main_layout.addStretch()

        # Seção de Créditos
        lbl_credits = QLabel("© Créditos")
        lbl_credits.setStyleSheet("font-weight: bold; font-size: 11px; margin-top: 15px;")
        self.main_layout.addWidget(lbl_credits)

        lbl_copyright = QLabel("O grupo meu carro anual (MCA)\nBy Valdemir do DSW")
        lbl_copyright.setStyleSheet("font-size: 10px; color: #666;")
        lbl_copyright.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(lbl_copyright)

        # Botões de redes sociais
        layout_social = QHBoxLayout()
        layout_social.addStretch()

        btn_hub = QPushButton("🔗 GITHub")
        btn_hub.setMaximumWidth(100)
        btn_hub.setStyleSheet("background-color: #673AB7; color: white; font-size: 10px;")
        btn_hub.clicked.connect(lambda: open_link("hub"))
        layout_social.addWidget(btn_hub)

        btn_discord = QPushButton("💬 Discord")
        btn_discord.setMaximumWidth(100)
        btn_discord.setStyleSheet("background-color: #7289DA; color: white; font-size: 10px;")
        btn_discord.clicked.connect(lambda: open_link("discord"))
        layout_social.addWidget(btn_discord)

        layout_social.addStretch()
        self.main_layout.addLayout(layout_social)

        self.main_layout.addSpacing(10)

        # Botões principais
        layout_buttons = QHBoxLayout()

        btn_back = QPushButton("Voltar")
        btn_back.setStyleSheet("color: #2196F3;")
        btn_back.clicked.connect(self.show_stage1)

        btn_enter = QPushButton("Entrar no app")
        btn_enter.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        btn_enter.clicked.connect(self.on_enter)

        layout_buttons.addWidget(btn_back)
        layout_buttons.addStretch()
        layout_buttons.addWidget(btn_enter)

        self.main_layout.addLayout(layout_buttons)

    def on_enter(self):
        """Aceita e marca como lido"""
        self.accepted = True
        self.accept()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        log_event("INFO", "====== APLICAÇÃO INICIADA ======")

        # Mostra disclaimer na primeira execução
        if not has_shown_disclaimer():
            dialog = DisclaimerDialog(self)
            dialog.exec_()
            
            # Se rejeitou, sai
            if not dialog.accepted:
                log_event("INFO", "Usuário rejeitou os termos")
                raise SystemExit
            
            # Marca como mostrado APENAS se aceitou
            mark_disclaimer_shown()

        self.setWindowTitle("MSC / MWC Backup Manager - By Valdemir")
        self.resize(540, 380)

        # Define o ícone da aplicação
        if os.path.exists("app.ico"):
            self.setWindowIcon(QIcon("app.ico"))

        self.games = get_game_paths()
        # Verificar quais jogos existem
        self.games_exist = {
            "MSC": os.path.exists(self.games["MSC"]),
            "MWC": os.path.exists(self.games["MWC"])
        }
        
        # Precisa ter pelo menos um jogo
        if not any(self.games_exist.values()):
            log_event("ERROR", "Nenhum jogo encontrado no sistema")
            QMessageBox.critical(
                None,
                "Nenhum jogo encontrado",
                "Abra o My Summer Car ou My Winter Car pelo menos uma vez\n"
                "antes de usar o sistema de backup."
            )
            raise SystemExit

        self.paused = True  # Por padrão sempre pausado
        self.auto_folder = None

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.init_backup_tab()
        self.init_restore_tab()
        self.init_auto_tab()
        self.init_logs_tab()
        self.init_tray()

        self.watcher = GameProcessWatcher(
            self.on_game_open,
            self.on_game_close
        )
        self.watcher.start()

        self.load_auto_config()
        self.load_pause_state()
        
        # Se foi iniciado com o sistema, abre minimizado na bandeja
        self.check_startup_and_minimize()

    # ================= SYSTEM TRAY =================
    def init_tray(self):
        self.tray = QSystemTrayIcon(self)
        
        # Define ícone da bandeja
        if os.path.exists("app.ico"):
            self.tray.setIcon(QIcon("app.ico"))
        else:
            self.tray.setIcon(self.style().standardIcon(QStyle.SP_DriveHDIcon))

        menu = QMenu()

        act_show = QAction("Abrir", self)
        act_show.triggered.connect(self.show_from_tray)

        self.act_pause = QAction("Pausar backups automáticos", self)
        self.act_pause.triggered.connect(self.toggle_pause)

        act_exit = QAction("Sair", self)
        act_exit.triggered.connect(self.force_exit)

        menu.addAction(act_show)
        menu.addAction(self.act_pause)
        menu.addSeparator()
        menu.addAction(act_exit)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self.on_tray_click)
        self.tray.show()

    def check_startup_and_minimize(self):
        """Verifica se foi iniciado com o sistema e minimiza para tray"""
        import sys
        # Se foi iniciado com argumentos ou com o sistema, minimiza
        if len(sys.argv) > 1 or os.environ.get('BECUPE_STARTUP'):
            self.hide()
            log_event("INFO", "Aplicação iniciada com o sistema - aberta na bandeja")
        else:
            # Caso contrário, mostra normalmente
            self.show()

    def on_tray_click(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.show_from_tray()

    def show_from_tray(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def force_exit(self):
        self.tray.hide()
        QApplication.quit()

    def closeEvent(self, event):
        event.ignore()
        self.hide()

    def toggle_pause(self):
        self.toggle_pause_ui()

    # ================= BACKUP MANUAL =================
    def init_backup_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        # Título
        lbl_title = QLabel("💾 Criar Backups Manuais")
        lbl_title.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 15px;")
        layout.addWidget(lbl_title)

        # Descrição
        lbl_desc = QLabel("Selecione um jogo para criar um backup manual agora:")
        lbl_desc.setStyleSheet("color: #666; margin-bottom: 20px;")
        layout.addWidget(lbl_desc)

        # Botão MSC
        btn_msc = QPushButton("🎮 Backup My Summer Car")
        btn_msc.setEnabled(self.games_exist["MSC"])
        btn_msc.setMinimumHeight(50)
        btn_msc.setStyleSheet(
            "QPushButton { background-color: #2196F3; color: white; font-weight: bold; border-radius: 5px; }"
            "QPushButton:hover:!disabled { background-color: #1976D2; }"
            "QPushButton:disabled { background-color: #ccc; color: #999; }"
        )
        btn_msc.clicked.connect(lambda: self.manual_backup("MSC"))
        layout.addWidget(btn_msc)

        # Botão MWC
        btn_mwc = QPushButton("🎮 Backup My Winter Car")
        btn_mwc.setEnabled(self.games_exist["MWC"])
        btn_mwc.setMinimumHeight(50)
        btn_mwc.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; font-weight: bold; border-radius: 5px; }"
            "QPushButton:hover:!disabled { background-color: #388E3C; }"
            "QPushButton:disabled { background-color: #ccc; color: #999; }"
        )
        btn_mwc.clicked.connect(lambda: self.manual_backup("MWC"))
        layout.addWidget(btn_mwc)

        layout.addStretch()

        # Nota
        lbl_note = QLabel("⚠️ Dica: Use o Auto Backup para criar backups automáticos ao abrir/fechar os jogos")
        lbl_note.setStyleSheet("color: #FF9800; font-size: 10px; margin-top: 10px;")
        layout.addWidget(lbl_note)

        tab.setLayout(layout)
        self.tabs.addTab(tab, "💾 Backup Manual")

    def manual_backup(self, game):
        dest = QFileDialog.getExistingDirectory(self, "Destino do Backup")
        if not dest:
            return
        log_event("BACKUP", f"Backup manual de {game} solicitado para: {dest}")
        create_backup(self.games[game], dest, game)
        log_event("BACKUP", f"Backup manual de {game} concluído")
        QMessageBox.information(self, "Sucesso", "Backup criado com sucesso.")

    # ================= RESTAURAÇÃO (SEPARADA) =================
    def init_restore_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        # Título
        lbl_title = QLabel("↩️ Restaurar Backups")
        lbl_title.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 15px;")
        layout.addWidget(lbl_title)

        # Descrição
        lbl_desc = QLabel("Selecione um jogo para restaurar um backup:")
        lbl_desc.setStyleSheet("color: #666; margin-bottom: 20px;")
        layout.addWidget(lbl_desc)

        # Botão MSC
        self.btn_restore_msc = QPushButton("📁 Restaurar My Summer Car")
        self.btn_restore_msc.setEnabled(self.games_exist["MSC"])
        self.btn_restore_msc.setMinimumHeight(50)
        self.btn_restore_msc.setStyleSheet(
            "QPushButton { background-color: #FF5722; color: white; font-weight: bold; border-radius: 5px; }"
            "QPushButton:hover:!disabled { background-color: #E64A19; }"
            "QPushButton:disabled { background-color: #ccc; color: #999; }"
        )
        self.btn_restore_msc.clicked.connect(
            lambda: self.restore_game("MSC")
        )
        layout.addWidget(self.btn_restore_msc)

        # Botão MWC
        self.btn_restore_mwc = QPushButton("📁 Restaurar My Winter Car")
        self.btn_restore_mwc.setEnabled(self.games_exist["MWC"])
        self.btn_restore_mwc.setMinimumHeight(50)
        self.btn_restore_mwc.setStyleSheet(
            "QPushButton { background-color: #9C27B0; color: white; font-weight: bold; border-radius: 5px; }"
            "QPushButton:hover:!disabled { background-color: #7B1FA2; }"
            "QPushButton:disabled { background-color: #ccc; color: #999; }"
        )
        self.btn_restore_mwc.clicked.connect(
            lambda: self.restore_game("MWC")
        )
        layout.addWidget(self.btn_restore_mwc)

        layout.addStretch()

        # Nota de aviso
        lbl_warning = QLabel("⚠️ Aviso: A restauração substitui seu save atual. Um backup de proteção será criado automaticamente.")
        lbl_warning.setStyleSheet("color: #f44336; font-size: 10px; margin-top: 10px;")
        lbl_warning.setWordWrap(True)
        layout.addWidget(lbl_warning)

        tab.setLayout(layout)
        self.tabs.addTab(tab, "↩️ Restaurar")

    def restore_game(self, game):
        file, _ = QFileDialog.getOpenFileName(
            self,
            f"Selecionar backup de {game}",
            "",
            "Backup (*.becupe)"
        )
        if not file:
            return

        log_event("RESTORE", f"Restauração de {game} iniciada: {file}")

        resp = QMessageBox.question(
            self,
            "Confirmação",
            "Isso substituirá o save atual.\nDeseja fazer backup antes?",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
        )

        if resp == QMessageBox.Cancel:
            log_event("RESTORE", f"Restauração de {game} cancelada pelo usuário")
            return

        if resp == QMessageBox.Yes:
            dest = QFileDialog.getExistingDirectory(
                self, "Destino do Backup Atual"
            )
            if dest:
                create_backup(
                    self.games[game],
                    dest,
                    f"{game}_PRE_RESTORE"
                )
                log_event("BACKUP", f"Backup de proteção criado antes de restaurar {game}")

        restore_backup(file, self.games[game])
        log_event("RESTORE", f"Restauração de {game} concluída com sucesso")
        QMessageBox.information(
            self,
            "Concluído",
            f"{game} restaurado com sucesso."
        )

    # ================= AUTO BACKUP =================
    def init_auto_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        # ===== CONTROLES =====
        lbl_controls = QLabel("⏸️ Controles")
        lbl_controls.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(lbl_controls)

        # Status de pausa (sempre pausado por padrão)
        self.lbl_pause_status = QLabel("Status: Backups PAUSADOS ⏸️")
        self.lbl_pause_status.setStyleSheet("color: red; font-weight: bold;")
        layout.addWidget(self.lbl_pause_status)

        # Layout do botão de pausa + botão abrir pasta
        layout_pause = QHBoxLayout()
        self.btn_toggle_pause = QPushButton("Despausar")
        self.btn_toggle_pause.clicked.connect(self.toggle_pause_ui)
        layout_pause.addWidget(self.btn_toggle_pause)

        btn_open_backup_folder = QPushButton("📁")
        btn_open_backup_folder.setMaximumWidth(40)
        btn_open_backup_folder.setToolTip("Abrir pasta de backups")
        btn_open_backup_folder.clicked.connect(self.open_backup_folder)
        layout_pause.addWidget(btn_open_backup_folder)
        layout_pause.addStretch()

        layout.addLayout(layout_pause)

        # ===== CONFIGURAÇÕES DE BACKUP =====
        lbl_backup = QLabel("⚙️ Configurações de Backup")
        lbl_backup.setStyleSheet("font-weight: bold; font-size: 12px; margin-top: 15px;")
        layout.addWidget(lbl_backup)

        self.chk_msc_open = QCheckBox("MSC - Backup ao abrir")
        self.chk_msc_close = QCheckBox("MSC - Backup ao fechar")
        self.chk_mwc_open = QCheckBox("MWC - Backup ao abrir")
        self.chk_mwc_close = QCheckBox("MWC - Backup ao fechar")

        for chk in (
            self.chk_msc_open, self.chk_msc_close,
            self.chk_mwc_open, self.chk_mwc_close
        ):
            chk.stateChanged.connect(lambda: self.auto_save_config())

        layout.addWidget(self.chk_msc_open)
        layout.addWidget(self.chk_msc_close)
        layout.addWidget(self.chk_mwc_open)
        layout.addWidget(self.chk_mwc_close)

        layout_folder = QHBoxLayout()
        btn_folder = QPushButton("Selecionar pasta de backup automático")
        btn_folder.clicked.connect(self.select_auto_folder)
        layout_folder.addWidget(btn_folder)
        layout.addLayout(layout_folder)

        # ===== STARTUP =====
        lbl_startup = QLabel("🚀 Sistema")
        lbl_startup.setStyleSheet("font-weight: bold; font-size: 12px; margin-top: 15px;")
        layout.addWidget(lbl_startup)

        layout_startup = QHBoxLayout()
        
        btn_startup_yes = QPushButton("✓ Abrir com Windows")
        btn_startup_yes.setStyleSheet("background-color: #4CAF50; color: white;")
        btn_startup_yes.clicked.connect(self.enable_startup_btn)
        layout_startup.addWidget(btn_startup_yes)

        btn_startup_no = QPushButton("✗ Não abrir com Windows")
        btn_startup_no.setStyleSheet("background-color: #f44336; color: white;")
        btn_startup_no.clicked.connect(self.disable_startup_btn)
        layout_startup.addWidget(btn_startup_no)

        layout.addLayout(layout_startup)

        layout.addStretch()

        tab.setLayout(layout)
        self.tabs.addTab(tab, "Auto Backup")

    def toggle_pause_ui(self):
        """Toggle de pausa com atualização visual"""
        # Se está pausado e quer despausar, valida pasta
        if self.paused and not self.auto_folder:
            QMessageBox.warning(
                self,
                "Pasta não configurada",
                "Você precisa selecionar uma pasta de backup antes de despausar os backups automáticos."
            )
            return

        self.paused = not self.paused
        self.save_pause_state()
        self.update_pause_ui()

    def update_pause_ui(self):
        """Atualiza a UI do status de pausa"""
        if self.paused:
            self.lbl_pause_status.setText("Status: Backups PAUSADOS ⏸️")
            self.lbl_pause_status.setStyleSheet("color: red; font-weight: bold;")
            self.btn_toggle_pause.setText("Despausar")
            self.act_pause.setText("Retomar backups automáticos")
        else:
            self.lbl_pause_status.setText("Status: Backups ATIVOS ✓")
            self.lbl_pause_status.setStyleSheet("color: green; font-weight: bold;")
            self.btn_toggle_pause.setText("Pausar")
            self.act_pause.setText("Pausar backups automáticos")

    def save_pause_state(self):
        """Salva o estado de pausa no JSON"""
        cfg = load_config()
        cfg["paused"] = self.paused
        save_config(cfg)
        status = "PAUSADO" if self.paused else "ATIVO"
        log_event("CONFIG", f"Backups automáticos {status}")

    def load_pause_state(self):
        """Carrega o estado de pausa do JSON"""
        cfg = load_config()
        self.paused = cfg.get("paused", True)
        self.update_pause_ui()

    def enable_startup_btn(self):
        """Ativa inicialização com Windows via botão"""
        if enable_startup():
            log_event("CONFIG", "Startup com Windows ativado")
            QMessageBox.information(
                self,
                "Sucesso",
                "App adicionado ao startup do Windows.\nIniciará automaticamente na próxima vez."
            )
        else:
            log_event("ERROR", "Falha ao ativar startup com Windows")
            QMessageBox.warning(
                self,
                "Erro",
                "Não foi possível adicionar ao startup."
            )

    def disable_startup_btn(self):
        """Desativa inicialização com Windows via botão"""
        if disable_startup():
            log_event("CONFIG", "Startup com Windows desativado")
            QMessageBox.information(
                self,
                "Sucesso",
                "App removido do startup do Windows."
            )
        else:
            log_event("ERROR", "Falha ao desativar startup com Windows")
            QMessageBox.warning(
                self,
                "Erro",
                "Não foi possível remover do startup."
            )

    def open_backup_folder(self):
        """Abre a pasta de backups no Explorer"""
        if not self.auto_folder:
            QMessageBox.information(
                self,
                "Pasta não configurada",
                "Selecione uma pasta de backup primeiro."
            )
            return

        if not os.path.exists(self.auto_folder):
            QMessageBox.warning(
                self,
                "Pasta não encontrada",
                f"A pasta {self.auto_folder} não existe."
            )
            return

        # Abre a pasta no Explorer
        os.startfile(self.auto_folder)

    def select_auto_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Pasta de Backup")
        if folder:
            self.auto_folder = folder
            log_event("CONFIG", f"Pasta de backup selecionada: {folder}")
            self.auto_save_config()

    def auto_save_config(self):
        cfg = load_config()
        if self.auto_folder:
            cfg["folder"] = self.auto_folder
        cfg["msc_open"] = self.chk_msc_open.isChecked()
        cfg["msc_close"] = self.chk_msc_close.isChecked()
        cfg["mwc_open"] = self.chk_mwc_open.isChecked()
        cfg["mwc_close"] = self.chk_mwc_close.isChecked()
        save_config(cfg)
        log_event("CONFIG", f"Backups automáticos alterados: MSC_open={cfg['msc_open']}, MSC_close={cfg['msc_close']}, MWC_open={cfg['mwc_open']}, MWC_close={cfg['mwc_close']}")

    def load_auto_config(self):
        cfg = load_config()
        if not cfg:
            return
        self.auto_folder = cfg.get("folder")
        # Desconecta os sinais para não chamar auto_save_config durante carregamento
        for chk in (self.chk_msc_open, self.chk_msc_close, self.chk_mwc_open, self.chk_mwc_close):
            chk.blockSignals(True)
        
        self.chk_msc_open.setChecked(cfg.get("msc_open", False))
        self.chk_msc_close.setChecked(cfg.get("msc_close", False))
        self.chk_mwc_open.setChecked(cfg.get("mwc_open", False))
        self.chk_mwc_close.setChecked(cfg.get("mwc_close", False))
        
        # Reconecta os sinais após carregamento
        for chk in (self.chk_msc_open, self.chk_msc_close, self.chk_mwc_open, self.chk_mwc_close):
            chk.blockSignals(False)

    # ================= EVENTOS =================
    def on_game_open(self, game):
        self.run_event_backup(game, "open")

    def on_game_close(self, game):
        self.run_event_backup(game, "close")

    def run_event_backup(self, game, event):
        if self.paused:
            return

        cfg = load_config()
        if not cfg or not cfg.get("folder"):
            return

        if not cfg.get(f"{game.lower()}_{event}"):
            return

        day_folder = datetime.now().strftime("%Y-%m-%d")
        final_folder = os.path.join(cfg["folder"], day_folder)
        os.makedirs(final_folder, exist_ok=True)

        create_backup(
            self.games[game],
            final_folder,
            f"{game}_{event.upper()}"
        )

    # ================= LOGS =================
    def init_logs_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        # Label
        lbl = QLabel("📋 Histórico de eventos")
        lbl.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(lbl)

        # Text editor para mostrar logs
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setStyleSheet("font-family: Courier; font-size: 10px;")
        layout.addWidget(self.log_display)

        # Layout dos botões - usando QVBoxLayout para 2 linhas
        buttons_container = QVBoxLayout()

        # Primeira linha de botões
        layout_buttons_line1 = QHBoxLayout()
        
        btn_refresh = QPushButton("🔄 Atualizar")
        btn_refresh.clicked.connect(self.refresh_logs)
        layout_buttons_line1.addWidget(btn_refresh)

        btn_clear = QPushButton("🗑️ Limpar logs")
        btn_clear.setStyleSheet("background-color: #f44336; color: white;")
        btn_clear.clicked.connect(self.clear_logs_btn)
        layout_buttons_line1.addWidget(btn_clear)

        layout_buttons_line1.addStretch()
        buttons_container.addLayout(layout_buttons_line1)

        # Segunda linha de botões
        layout_buttons_line2 = QHBoxLayout()
        
        btn_open_notepad = QPushButton("📄 Abrir com Bloco de Notas")
        btn_open_notepad.setStyleSheet("background-color: #4CAF50; color: white;")
        btn_open_notepad.clicked.connect(self.open_logs_notepad)
        layout_buttons_line2.addWidget(btn_open_notepad)

        layout_buttons_line2.addStretch()
        buttons_container.addLayout(layout_buttons_line2)

        layout.addLayout(buttons_container)

        tab.setLayout(layout)
        self.tabs.addTab(tab, "📋 Logs")

        # Timer para atualizar logs automaticamente
        self.log_timer = QTimer()
        self.log_timer.timeout.connect(self.refresh_logs)
        self.log_timer.start(2000)  # Atualiza a cada 2 segundos

        # Carrega logs na inicialização
        self.refresh_logs()

    def refresh_logs(self):
        """Atualiza o display de logs"""
        log_content = read_log()
        self.log_display.setText(log_content)
        # Scroll para o final
        self.log_display.verticalScrollBar().setValue(
            self.log_display.verticalScrollBar().maximum()
        )

    def clear_logs_btn(self):
        """Limpa os logs após confirmação"""
        reply = QMessageBox.question(
            self,
            "Confirmar limpeza",
            "Deseja limpar todos os logs?\nEsta ação não pode ser desfeita.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if clear_log():
                log_event("INFO", "Logs foram limpados pelo usuário")
                self.refresh_logs()
                QMessageBox.information(self, "Sucesso", "Logs foram limpos.")
            else:
                QMessageBox.warning(self, "Erro", "Não foi possível limpar os logs.")

    def open_logs_notepad(self):
        """Abre o arquivo de log com Bloco de Notas"""
        try:
            log_file = get_log_file()
            if os.path.exists(log_file):
                subprocess.Popen(['notepad', log_file])
                log_event("INFO", "Arquivo de log aberto no Bloco de Notas")
            else:
                QMessageBox.warning(self, "Erro", "Arquivo de log não encontrado.")
        except Exception as e:
            log_event("ERROR", f"Erro ao abrir log no Bloco de Notas: {str(e)}")
            QMessageBox.critical(self, "Erro", f"Não foi possível abrir o Bloco de Notas:\n{str(e)}")

