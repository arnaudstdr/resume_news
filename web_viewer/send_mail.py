#!/usr/bin/env python3
"""
Module d'envoi d'email pour les rapports de veille IA.
Gère l'envoi HTML et PDF par email avec configuration flexible.
"""

import os
import smtplib
import configparser
from pathlib import Path
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

try:
    import weasyprint
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
    print("⚠️  WeasyPrint non installé. Génération PDF désactivée.")
    print("💡 Installez avec: pip install weasyprint")


class EmailSender:
    """Gestionnaire d'envoi d'emails pour les rapports de veille."""
    
    def __init__(self, config_path=None):
        """
        Initialise le gestionnaire d'email.
        
        Args:
            config_path: Chemin vers le fichier de configuration (optionnel)
        """
        self.base_dir = Path(__file__).parent.parent
        self.outputs_dir = self.base_dir / "outputs"
        
        if config_path:
            self.config_path = Path(config_path)
        else:
            self.config_path = self.base_dir / "config" / "email_config.ini"
        
        self.config = self._load_email_config()
    
    def _load_email_config(self):
        """Charge la configuration email depuis un fichier."""
        if not self.config_path.exists():
            self._create_default_config()
            return None
        
        try:
            config = configparser.ConfigParser()
            config.read(self.config_path, encoding='utf-8')
            
            # Vérification des paramètres essentiels
            required_params = ['smtp_server', 'smtp_port', 'email_user', 'email_password', 'recipient_email']
            if 'EMAIL' in config:
                for param in required_params:
                    if not config['EMAIL'].get(param):
                        print(f"⚠️  Paramètre manquant dans la config: {param}")
                        return None
            
            return config
            
        except Exception as e:
            print(f"❌ Erreur lecture config: {e}")
            return None
    
    def _create_default_config(self):
        """Crée un fichier de configuration par défaut."""
        self.config_path.parent.mkdir(exist_ok=True)
        
        default_config = """[EMAIL]
# Configuration SMTP (exemple avec Gmail)
smtp_server = smtp.gmail.com
smtp_port = 587
email_user = votre_email@gmail.com
email_password = votre_mot_de_passe_d_application
recipient_email = votre_email_destinataire@example.com

# Options d'envoi
send_html = true
send_pdf = true
subject_prefix = [Veille IA]

# Options PDF
pdf_format = A4
pdf_margin = 2cm

[ADVANCED]
# Paramètres avancés (optionnels)
use_tls = true
timeout = 30
max_attachment_size_mb = 25
"""
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            f.write(default_config)
        
        print(f"📁 Fichier de configuration créé : {self.config_path}")
        print("🔧 Veuillez remplir vos informations email avant utilisation.")
        print("\n💡 Pour Gmail, utilisez un mot de passe d'application :")
        print("   https://support.google.com/accounts/answer/185833")
    
    def generate_pdf(self, html_content, filename=None):
        """
        Génère un PDF à partir du contenu HTML.
        
        Args:
            html_content: Contenu HTML à convertir
            filename: Nom du fichier PDF (optionnel)
            
        Returns:
            Path: Chemin vers le fichier PDF généré ou None si erreur
        """
        if not WEASYPRINT_AVAILABLE:
            print("❌ WeasyPrint non disponible pour la génération PDF")
            return None
        
        try:
            # CSS optimisé pour l'impression PDF
            pdf_format = 'A4'
            pdf_margin = '2cm'
            
            if self.config and 'EMAIL' in self.config:
                pdf_format = self.config.get('EMAIL', 'pdf_format', fallback='A4')
                pdf_margin = self.config.get('EMAIL', 'pdf_margin', fallback='2cm')
            
            pdf_css = f"""
            @page {{
                size: {pdf_format};
                margin: {pdf_margin};
            }}
            
            body {{
                font-size: 11pt;
                line-height: 1.4;
            }}
            
            .header {{
                background: #2563eb !important;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }}
            
            .article-item {{
                page-break-inside: avoid;
                margin-bottom: 1rem;
                border: 1px solid #e2e8f0 !important;
            }}
            
            .section {{
                page-break-inside: avoid;
                margin-bottom: 1.5rem;
            }}
            
            .stats {{
                page-break-after: avoid;
            }}
            
            .toc {{
                page-break-after: always;
            }}
            
            /* Améliorer la lisibilité des liens */
            a {{
                color: #2563eb !important;
                text-decoration: none !important;
            }}
            
            /* Afficher les URLs en impression */
            @media print {{
                a[href]:after {{
                    content: " (" attr(href) ")";
                    font-size: 0.8em;
                    color: #666;
                }}
            }}
            """
            
            # Injecter le CSS spécifique PDF
            html_with_pdf_css = html_content.replace(
                '</style>',
                pdf_css + '</style>'
            )
            
            # Nom du fichier
            if not filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M')
                filename = f"veille_ia_rapport_{timestamp}.pdf"
            
            pdf_path = self.outputs_dir / filename
            
            # Génération du PDF
            weasyprint.HTML(string=html_with_pdf_css).write_pdf(
                pdf_path,
                presentational_hints=True
            )
            
            # Vérifier la taille du fichier
            file_size_mb = pdf_path.stat().st_size / (1024 * 1024)
            max_size = 25  # Taille par défaut
            
            if self.config and 'ADVANCED' in self.config:
                max_size = float(self.config.get('ADVANCED', 'max_attachment_size_mb', fallback='25'))
            
            if file_size_mb > max_size:
                print(f"⚠️  PDF volumineux ({file_size_mb:.1f}MB > {max_size}MB)")
                print("💡 Considérez réduire le nombre d'articles ou la résolution")
            
            print(f"✅ PDF généré : {pdf_path} ({file_size_mb:.1f}MB)")
            return pdf_path
            
        except Exception as e:
            print(f"❌ Erreur génération PDF : {e}")
            return None
    
    def send_email(self, html_content, pdf_path=None, custom_subject=None):
        """
        Envoie le rapport par email.
        
        Args:
            html_content: Contenu HTML du rapport
            pdf_path: Chemin vers le PDF (optionnel)
            custom_subject: Sujet personnalisé (optionnel)
            
        Returns:
            bool: True si envoi réussi, False sinon
        """
        if not self.config or 'EMAIL' not in self.config:
            print("❌ Configuration email non trouvée")
            print(f"💡 Configurez le fichier : {self.config_path}")
            return False
        
        try:
            # Configuration SMTP
            smtp_server = self.config['EMAIL']['smtp_server']
            smtp_port = int(self.config['EMAIL']['smtp_port'])
            email_user = self.config['EMAIL']['email_user']
            email_password = self.config['EMAIL']['email_password']
            recipient = self.config['EMAIL']['recipient_email']
            use_tls = self.config.getboolean('ADVANCED', 'use_tls', fallback=True)
            timeout = int(self.config.get('ADVANCED', 'timeout', fallback='30'))
            
            # Création du message
            msg = MIMEMultipart('alternative')
            msg['From'] = email_user
            msg['To'] = recipient
            
            # Sujet
            if custom_subject:
                msg['Subject'] = custom_subject
            else:
                prefix = self.config['EMAIL'].get('subject_prefix', '[Veille IA]')
                date_str = datetime.now().strftime('%d/%m/%Y')
                msg['Subject'] = f"{prefix} Rapport du {date_str}"
            
            # Métadonnées
            msg['X-Mailer'] = 'Veille IA Reporter'
            msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
            
            # Version texte simple
            articles_count = html_content.count('class="article-item"')
            text_content = f"""
📰 Rapport de Veille Intelligence Artificielle
═══════════════════════════════════════════

📅 Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}
📊 {articles_count} articles collectés

Ce rapport contient les derniers articles et résumés de votre veille IA.
Consultez la version HTML ci-dessous ou le PDF en pièce jointe pour plus de détails.

───────────────────────────────────────────
🤖 Rapport généré automatiquement par le pipeline de Veille IA
            """
            
            # Attacher le contenu texte
            msg.attach(MIMEText(text_content, 'plain', 'utf-8'))
            
            # Version HTML si demandée
            if self.config.getboolean('EMAIL', 'send_html', fallback=True):
                msg.attach(MIMEText(html_content, 'html', 'utf-8'))
                print("📄 Version HTML incluse dans l'email")
            
            # Pièce jointe PDF si demandée et disponible
            if (self.config.getboolean('EMAIL', 'send_pdf', fallback=True) and 
                pdf_path and pdf_path.exists()):
                
                try:
                    with open(pdf_path, 'rb') as attachment:
                        part = MIMEBase('application', 'pdf')
                        part.set_payload(attachment.read())
                    
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename="{pdf_path.name}"'
                    )
                    msg.attach(part)
                    print(f"📎 PDF attaché : {pdf_path.name}")
                    
                except Exception as e:
                    print(f"⚠️  Erreur attachement PDF : {e}")
            
            # Connexion et envoi
            print(f"🔌 Connexion à {smtp_server}:{smtp_port}...")
            
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=timeout)
            
            if use_tls:
                server.starttls()
            
            server.login(email_user, email_password)
            
            # Envoi du message
            text = msg.as_string()
            server.sendmail(email_user, recipient, text)
            server.quit()
            
            print(f"✅ Email envoyé avec succès à {recipient}")
            print(f"📧 Sujet : {msg['Subject']}")
            return True
            
        except smtplib.SMTPAuthenticationError:
            print("❌ Erreur d'authentification SMTP")
            print("💡 Vérifiez vos identifiants et utilisez un mot de passe d'application")
            return False
            
        except smtplib.SMTPRecipientsRefused:
            print("❌ Adresse destinataire refusée")
            print("💡 Vérifiez l'adresse email du destinataire")
            return False
            
        except Exception as e:
            print(f"❌ Erreur envoi email : {e}")
            return False
    
    def send_report(self, html_content, generate_pdf=True, custom_subject=None):
        """
        Génère et envoie un rapport complet.
        
        Args:
            html_content: Contenu HTML du rapport
            generate_pdf: Générer et attacher le PDF
            custom_subject: Sujet personnalisé
            
        Returns:
            dict: Résultats de l'opération
        """
        results = {
            'pdf_generated': False,
            'pdf_path': None,
            'email_sent': False,
            'errors': []
        }
        
        # Génération PDF
        pdf_path = None
        send_pdf = False
        
        if self.config and 'EMAIL' in self.config:
            send_pdf = self.config.getboolean('EMAIL', 'send_pdf', fallback=True)
        
        if generate_pdf and send_pdf:
            pdf_path = self.generate_pdf(html_content)
            if pdf_path:
                results['pdf_generated'] = True
                results['pdf_path'] = pdf_path
            else:
                results['errors'].append('Échec génération PDF')
        
        # Envoi email
        email_success = self.send_email(html_content, pdf_path, custom_subject)
        results['email_sent'] = email_success
        
        if not email_success:
            results['errors'].append('Échec envoi email')
        
        return results
    
    def test_configuration(self):
        """
        Teste la configuration email.
        
        Returns:
            bool: True si la configuration est valide
        """
        if not self.config:
            print("❌ Aucune configuration trouvée")
            return False
        
        print("🔍 Test de la configuration email...")
        
        try:
            # Test connexion SMTP
            smtp_server = self.config['EMAIL']['smtp_server']
            smtp_port = int(self.config['EMAIL']['smtp_port'])
            email_user = self.config['EMAIL']['email_user']
            email_password = self.config['EMAIL']['email_password']
            
            print(f"📡 Test connexion {smtp_server}:{smtp_port}...")
            
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
            server.starttls()
            server.login(email_user, email_password)
            server.quit()
            
            print("✅ Configuration email valide")
            return True
            
        except Exception as e:
            print(f"❌ Erreur configuration : {e}")
            return False


def main():
    """Fonction de test du module."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test du module d\'envoi d\'email')
    parser.add_argument('--test-config', action='store_true', help='Tester la configuration')
    parser.add_argument('--send-test', action='store_true', help='Envoyer un email de test')
    
    args = parser.parse_args()
    
    sender = EmailSender()
    
    if args.test_config:
        sender.test_configuration()
    
    if args.send_test:
        test_html = """
        <html>
        <body>
        <h1>🧪 Test d'envoi d'email</h1>
        <p>Ceci est un email de test du système de veille IA.</p>
        <p>Envoyé le """ + datetime.now().strftime('%d/%m/%Y à %H:%M') + """</p>
        </body>
        </html>
        """
        
        results = sender.send_report(
            test_html, 
            generate_pdf=False,
            custom_subject="[Test] Veille IA - Email de test"
        )
        
        if results['email_sent']:
            print("✅ Email de test envoyé avec succès")
        else:
            print("❌ Échec envoi email de test")
            for error in results['errors']:
                print(f"   • {error}")


if __name__ == '__main__':
    main()
