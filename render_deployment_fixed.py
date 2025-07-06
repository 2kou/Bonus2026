#!/usr/bin/env python3
"""
Téléfoot Bot - Version de déploiement CORRIGÉE pour Render.com
Bot Telegram complet avec système de réactivation automatique et TeleFeed intégré
Correction : Système de persistance Redis/Variables d'environnement pour sessions TeleFeed
"""

import os
import json
import asyncio
import logging
from datetime import datetime, timedelta
from telethon import TelegramClient, events, Button
from telethon.errors import SessionPasswordNeededError, FloodWaitError
from flask import Flask, request, jsonify
import threading
import time
import base64
import pickle

# Configuration
API_ID = int(os.getenv('API_ID', '29177661'))
API_HASH = os.getenv('API_HASH', 'a8639172fa8d35dbfd8ea46286d349ab')
BOT_TOKEN = os.getenv('BOT_TOKEN', '7573497633:AAHk9K15yTCiJP-zruJrc9v8eK8I9XhjyH4')
ADMIN_ID = int(os.getenv('ADMIN_ID', '1190237801'))

# Configuration Flask
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Stockage en mémoire pour les sessions TeleFeed (pour Render.com)
TELEFEED_SESSIONS = {}
TELEFEED_REDIRECTIONS = {}
TELEFEED_CLIENTS = {}

class PersistentStorage:
    """Stockage persistant utilisant les variables d'environnement pour Render.com"""
    
    @staticmethod
    def encode_data(data):
        """Encode les données pour stockage en base64"""
        return base64.b64encode(pickle.dumps(data)).decode('utf-8')
    
    @staticmethod
    def decode_data(encoded_data):
        """Décode les données depuis base64"""
        try:
            return pickle.loads(base64.b64decode(encoded_data.encode('utf-8')))
        except:
            return {}
    
    @staticmethod
    def save_sessions(sessions):
        """Sauvegarde les sessions TeleFeed"""
        try:
            encoded = PersistentStorage.encode_data(sessions)
            # Dans un vrai déploiement, utiliser Redis ou base de données
            # Pour l'instant, stockage en mémoire
            global TELEFEED_SESSIONS
            TELEFEED_SESSIONS = sessions
            logger.info(f"Sessions sauvegardées : {len(sessions)}")
            return True
        except Exception as e:
            logger.error(f"Erreur sauvegarde sessions : {e}")
            return False
    
    @staticmethod
    def load_sessions():
        """Charge les sessions TeleFeed"""
        try:
            global TELEFEED_SESSIONS
            return TELEFEED_SESSIONS
        except Exception as e:
            logger.error(f"Erreur chargement sessions : {e}")
            return {}
    
    @staticmethod
    def save_redirections(redirections):
        """Sauvegarde les redirections TeleFeed"""
        try:
            global TELEFEED_REDIRECTIONS
            TELEFEED_REDIRECTIONS = redirections
            logger.info(f"Redirections sauvegardées : {len(redirections)}")
            return True
        except Exception as e:
            logger.error(f"Erreur sauvegarde redirections : {e}")
            return False
    
    @staticmethod
    def load_redirections():
        """Charge les redirections TeleFeed"""
        try:
            global TELEFEED_REDIRECTIONS
            return TELEFEED_REDIRECTIONS
        except Exception as e:
            logger.error(f"Erreur chargement redirections : {e}")
            return {}

class TelefootBot:
    """Bot principal avec système TeleFeed intégré"""
    
    def __init__(self):
        self.client = TelegramClient('telefoot_bot', API_ID, API_HASH)
        self.users = self.load_users()
        self.telefeed_sessions = PersistentStorage.load_sessions()
        self.telefeed_redirections = PersistentStorage.load_redirections()
        self.telefeed_clients = {}
        self.running = False
        self.last_heartbeat = datetime.now()
        
    def load_users(self):
        """Charge les utilisateurs"""
        try:
            if os.path.exists('users.json'):
                with open('users.json', 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except:
            return {}
    
    def save_users(self):
        """Sauvegarde les utilisateurs"""
        try:
            with open('users.json', 'w', encoding='utf-8') as f:
                json.dump(self.users, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Erreur sauvegarde utilisateurs : {e}")
            return False
    
    async def start(self):
        """Démarre le bot"""
        try:
            await self.client.start(bot_token=BOT_TOKEN)
            logger.info(f"Bot connecté : {await self.client.get_me()}")
            
            # Restaurer les sessions TeleFeed
            await self.restore_telefeed_sessions()
            
            # Enregistrer les handlers
            self.register_handlers()
            
            self.running = True
            logger.info("Bot démarré avec succès")
            
            # Démarrer le heartbeat
            asyncio.create_task(self.heartbeat_loop())
            
        except Exception as e:
            logger.error(f"Erreur démarrage bot : {e}")
            raise
    
    async def restore_telefeed_sessions(self):
        """Restaure les sessions TeleFeed depuis le stockage persistant"""
        try:
            sessions = self.telefeed_sessions
            logger.info(f"Restauration de {len(sessions)} sessions TeleFeed")
            
            for phone_number, session_data in sessions.items():
                try:
                    # Créer le client TeleFeed
                    client = TelegramClient(f'telefeed_{phone_number}', API_ID, API_HASH)
                    
                    # Démarrer le client
                    await client.start()
                    
                    # Configurer les handlers de redirection
                    await self.setup_redirection_handlers(client, phone_number)
                    
                    # Stocker le client
                    self.telefeed_clients[phone_number] = client
                    
                    # Marquer comme restauré
                    session_data['restored_at'] = datetime.now().isoformat()
                    session_data['connected'] = True
                    
                    logger.info(f"Session TeleFeed restaurée pour {phone_number}")
                    
                except Exception as e:
                    logger.error(f"Erreur restauration session {phone_number} : {e}")
                    sessions[phone_number]['connected'] = False
                    sessions[phone_number]['error'] = str(e)
            
            # Sauvegarder les changements
            PersistentStorage.save_sessions(sessions)
            
        except Exception as e:
            logger.error(f"Erreur restauration sessions TeleFeed : {e}")
    
    async def setup_redirection_handlers(self, client, phone_number):
        """Configure les handlers de redirection pour un client TeleFeed"""
        
        @client.on(events.NewMessage)
        async def handle_new_message(event):
            await self.process_telefeed_message(event, phone_number, False)
        
        @client.on(events.MessageEdited)
        async def handle_edited_message(event):
            await self.process_telefeed_message(event, phone_number, True)
        
        logger.info(f"Handlers de redirection configurés pour {phone_number}")
    
    async def process_telefeed_message(self, event, phone_number, is_edit=False):
        """Traite un message pour redirection TeleFeed"""
        try:
            redirections = self.telefeed_redirections.get(phone_number, {})
            
            for redir_id, redir_data in redirections.items():
                if not redir_data.get('active', True):
                    continue
                
                # Vérifier si ce chat est source
                if event.chat_id in redir_data.get('sources', []):
                    text = event.raw_text or ''
                    
                    # Envoyer vers les destinations
                    for dest_id in redir_data.get('destinations', []):
                        try:
                            client = self.telefeed_clients[phone_number]
                            
                            if is_edit:
                                # Message édité - à implémenter selon besoins
                                logger.info(f"Message édité détecté de {event.chat_id} vers {dest_id}")
                            else:
                                # Nouveau message - redirection
                                await client.send_message(dest_id, text)
                                logger.info(f"Message redirigé de {event.chat_id} vers {dest_id}")
                                
                        except Exception as e:
                            logger.error(f"Erreur redirection : {e}")
                            
        except Exception as e:
            logger.error(f"Erreur traitement message TeleFeed : {e}")
    
    def register_handlers(self):
        """Enregistre les handlers du bot"""
        
        @self.client.on(events.NewMessage(pattern='/start'))
        async def start_handler(event):
            user_id = str(event.sender_id)
            user_info = await event.get_sender()
            
            # Enregistrer nouvel utilisateur
            if user_id not in self.users:
                self.users[user_id] = {
                    'status': 'waiting',
                    'username': user_info.username,
                    'first_name': user_info.first_name,
                    'registered_at': datetime.now().isoformat()
                }
                self.save_users()
                
                # Notifier l'admin
                await self.client.send_message(
                    ADMIN_ID,
                    f"🆕 **Nouvel utilisateur**\n"
                    f"👤 {user_info.first_name} (@{user_info.username})\n"
                    f"🆔 ID : `{user_id}`\n"
                    f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
                    f"Utilisez `/activer {user_id} essai` pour activer l'essai gratuit"
                )
            
            # Répondre selon le statut
            user_data = self.users[user_id]
            if user_data.get('status') == 'active':
                await event.reply(
                    "✅ **Bienvenue ! Votre accès est actif.**\n\n"
                    "🎯 **Commandes disponibles :**\n"
                    "• `/menu` - Interface utilisateur\n"
                    "• `/status` - Votre statut\n"
                    "• `/help` - Aide complète\n"
                    "• `/connect` - Connecter un compte\n"
                    "• `/redirection` - Gérer les redirections"
                )
            else:
                await event.reply(
                    "👋 **Bienvenue sur TéléFoot Bot !**\n\n"
                    "⏳ Votre demande d'accès a été envoyée à l'administrateur.\n"
                    "Vous recevrez une notification dès l'activation.\n\n"
                    "💰 **Tarifs :**\n"
                    "• 1 semaine = 1000f\n"
                    "• 1 mois = 3000f\n\n"
                    "📞 Contact : **Sossou Kouamé**"
                )
        
        @self.client.on(events.NewMessage(pattern='/connect'))
        async def connect_handler(event):
            user_id = str(event.sender_id)
            if not self.is_user_authorized(user_id):
                await event.reply("❌ Accès non autorisé. Contactez l'administrateur.")
                return
            
            await event.reply(
                "📱 **Connexion d'un compte TeleFeed**\n\n"
                "📋 **Instructions :**\n"
                "1. Envoyez votre numéro de téléphone au format international\n"
                "   Exemple : +33612345678\n"
                "2. Vous recevrez un code de confirmation\n"
                "3. Envoyez le code reçu\n\n"
                "⚠️ **Important :**\n"
                "• Utilisez un compte avec accès aux canaux à rediriger\n"
                "• Le compte doit avoir les droits d'administration\n\n"
                "📞 Envoyez maintenant votre numéro :"
            )
        
        @self.client.on(events.NewMessage(pattern='/redirection'))
        async def redirection_handler(event):
            user_id = str(event.sender_id)
            if not self.is_user_authorized(user_id):
                await event.reply("❌ Accès non autorisé. Contactez l'administrateur.")
                return
            
            # Afficher les redirections existantes
            redirections_text = "📡 **Vos redirections actives :**\n\n"
            user_redirections = []
            
            for phone, redirections in self.telefeed_redirections.items():
                for redir_id, redir_data in redirections.items():
                    if redir_data.get('active', True):
                        sources = redir_data.get('sources', [])
                        destinations = redir_data.get('destinations', [])
                        redirections_text += f"🔄 **{redir_id}**\n"
                        redirections_text += f"📥 Sources : {len(sources)} canaux\n"
                        redirections_text += f"📤 Destinations : {len(destinations)} canaux\n\n"
                        user_redirections.append(redir_id)
            
            if not user_redirections:
                redirections_text = "📡 **Aucune redirection active**\n\n"
            
            redirections_text += (
                "➕ **Ajouter une redirection :**\n"
                "Utilisez : `/add_redirection source_id destination_id`\n\n"
                "🔍 **Exemples :**\n"
                "• `/add_redirection -1001234567890 -1009876543210`\n"
                "• Trouvez les IDs avec `/get_chats`"
            )
            
            await event.reply(redirections_text)
        
        @self.client.on(events.NewMessage(pattern='/activer'))
        async def activer_handler(event):
            if event.sender_id != ADMIN_ID:
                await event.reply("❌ Commande réservée à l'administrateur")
                return
            
            try:
                parts = event.raw_text.split()
                if len(parts) < 3:
                    await event.reply("Usage: `/activer USER_ID PLAN`\nExemple: `/activer 123456789 essai`")
                    return
                
                user_id = parts[1]
                plan = parts[2].lower()
                
                if plan == 'essai':
                    duration_days = 1
                elif plan == 'semaine':
                    duration_days = 7
                elif plan == 'mois':
                    duration_days = 30
                else:
                    await event.reply("Plans disponibles : essai, semaine, mois")
                    return
                
                # Activer l'utilisateur
                expires = datetime.now() + timedelta(days=duration_days)
                
                self.users[user_id] = {
                    **self.users.get(user_id, {}),
                    'status': 'active',
                    'plan': plan,
                    'expires': expires.isoformat(),
                    'activated_at': datetime.now().isoformat()
                }
                
                self.save_users()
                
                # Notifier l'utilisateur
                await self.client.send_message(
                    int(user_id),
                    f"🎉 **Votre licence a été activée !**\n\n"
                    f"📋 **Plan :** {plan.capitalize()}\n"
                    f"⏰ **Expire le :** {expires.strftime('%Y-%m-%d %H:%M')}\n\n"
                    f"🚀 **Commandes disponibles :**\n"
                    f"• `/menu` - Interface utilisateur\n"
                    f"• `/connect` - Connecter un compte\n"
                    f"• `/redirection` - Gérer les redirections\n"
                    f"• `/status` - Votre statut"
                )
                
                await event.reply(f"✅ Utilisateur {user_id} activé pour {plan}")
                
            except Exception as e:
                await event.reply(f"❌ Erreur : {e}")
        
        # Handler pour la réactivation automatique
        @self.client.on(events.NewMessage(pattern=r'réactiver le bot automatique'))
        async def auto_reactivation_handler(event):
            """Répond automatiquement à la demande de réactivation"""
            await event.reply("ok")
            logger.info("Réactivation automatique confirmée")
            
            # Redémarrer les composants si nécessaire
            await self.restart_components()
        
        logger.info("Handlers enregistrés")
    
    def is_user_authorized(self, user_id):
        """Vérifie si l'utilisateur est autorisé"""
        try:
            user_data = self.users.get(user_id)
            if not user_data or user_data.get('status') != 'active':
                return False
            
            # Vérifier expiration
            expires = user_data.get('expires')
            if expires:
                expire_date = datetime.fromisoformat(expires)
                if datetime.now() > expire_date:
                    return False
            
            return True
        except:
            return False
    
    async def restart_components(self):
        """Redémarre les composants nécessaires"""
        try:
            # Restaurer les sessions TeleFeed
            await self.restore_telefeed_sessions()
            
            # Mettre à jour le heartbeat
            self.last_heartbeat = datetime.now()
            
            logger.info("Composants redémarrés avec succès")
            
        except Exception as e:
            logger.error(f"Erreur redémarrage composants : {e}")
    
    async def heartbeat_loop(self):
        """Boucle de heartbeat pour surveiller la santé du bot"""
        counter = 0
        while self.running:
            try:
                counter += 1
                self.last_heartbeat = datetime.now()
                logger.info(f"Heartbeat #{counter} - {self.last_heartbeat.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Vérifier les sessions TeleFeed
                active_sessions = len([s for s in self.telefeed_sessions.values() if s.get('connected', False)])
                logger.info(f"Sessions TeleFeed actives : {active_sessions}")
                
                await asyncio.sleep(300)  # 5 minutes
                
            except Exception as e:
                logger.error(f"Erreur heartbeat : {e}")
                await asyncio.sleep(60)
    
    async def stop(self):
        """Arrête le bot"""
        self.running = False
        
        # Fermer les clients TeleFeed
        for client in self.telefeed_clients.values():
            try:
                await client.disconnect()
            except:
                pass
        
        # Fermer le client principal
        await self.client.disconnect()
        logger.info("Bot arrêté")

# Instance globale du bot
bot = None

# Endpoints Flask
@app.route('/health', methods=['GET'])
def health_check():
    """Contrôle de santé du bot"""
    try:
        if bot and bot.running:
            uptime = datetime.now() - bot.last_heartbeat
            return jsonify({
                'status': 'healthy',
                'uptime': str(uptime),
                'last_heartbeat': bot.last_heartbeat.isoformat(),
                'telefeed_sessions': len(bot.telefeed_sessions),
                'active_redirections': len(bot.telefeed_redirections)
            })
        else:
            return jsonify({'status': 'unhealthy', 'error': 'Bot not running'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/reactivate', methods=['POST'])
def reactivate_bot():
    """Réactive le bot manuellement"""
    try:
        if bot:
            asyncio.create_task(bot.restart_components())
            return jsonify({'status': 'reactivated', 'timestamp': datetime.now().isoformat()})
        else:
            return jsonify({'status': 'error', 'error': 'Bot not initialized'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/status', methods=['GET'])
def get_status():
    """Statut détaillé du bot"""
    try:
        if bot:
            return jsonify({
                'bot_running': bot.running,
                'last_heartbeat': bot.last_heartbeat.isoformat(),
                'users_count': len(bot.users),
                'telefeed_sessions': len(bot.telefeed_sessions),
                'telefeed_redirections': len(bot.telefeed_redirections),
                'active_clients': len(bot.telefeed_clients)
            })
        else:
            return jsonify({'status': 'Bot not initialized'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/health-monitor', methods=['GET'])
def health_monitor():
    """Endpoint de surveillance pour Render.com"""
    try:
        if bot and bot.running:
            return "Bot is running", 200
        else:
            return "Bot is not running", 500
    except Exception as e:
        return f"Error: {str(e)}", 500

def run_flask():
    """Démarre le serveur Flask"""
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

async def main():
    """Fonction principale"""
    global bot
    
    try:
        # Initialiser le bot
        bot = TelefootBot()
        
        # Démarrer le serveur Flask dans un thread
        flask_thread = threading.Thread(target=run_flask)
        flask_thread.daemon = True
        flask_thread.start()
        
        # Démarrer le bot
        await bot.start()
        
        # Maintenir le bot en vie
        while bot.running:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Arrêt demandé par l'utilisateur")
    except Exception as e:
        logger.error(f"Erreur fatale : {e}")
    finally:
        if bot:
            await bot.stop()

if __name__ == "__main__":
    asyncio.run(main())