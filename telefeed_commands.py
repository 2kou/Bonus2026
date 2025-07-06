"""
TeleFeed Commands Implementation for Téléfoot Bot
Integrates advanced message redirection and transformation features
"""

import json
import os
import re
import asyncio
from datetime import datetime
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError, PhoneCodeExpiredError
from telethon.tl.types import User, Chat, Channel

# Configuration des admins
ADMIN_IDS = ['1190237801']  # ID admin principal

# Configuration des fichiers de données
DATA_FILES = {
    'sessions': 'telefeed_sessions.json',
    'redirections': 'telefeed_redirections.json',
    'transformations': 'telefeed_transformations.json',
    'filters': 'telefeed_filters.json',
    'whitelist': 'telefeed_whitelist.json',
    'blacklist': 'telefeed_blacklist.json',
    'settings': 'telefeed_settings.json',
    'chats': 'telefeed_chats.json',
    'delay': 'telefeed_delay.json'
}

def load_json_data(filename):
    """Charge les données JSON"""
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"Erreur lors du chargement {filename}: {e}")
        return {}

def save_json_data(filename, data):
    """Sauvegarde les données JSON"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Erreur lors de la sauvegarde {filename}: {e}")
        return False

def is_user_authorized(user_id):
    """Vérifie si l'utilisateur est autorisé (a une licence active)"""
    try:
        with open('users.json', 'r', encoding='utf-8') as f:
            users = json.load(f)
        
        user_data = users.get(str(user_id))
        if not user_data:
            return False
            
        if user_data.get('status') != 'active':
            return False
            
        # Vérifier l'expiration
        expire_date = user_data.get('expires')
        if expire_date:
            expire_datetime = datetime.fromisoformat(expire_date)
            if datetime.now() > expire_datetime:
                return False
                
        return True
    except:
        return False

class TeleFeedManager:
    """Gestionnaire principal pour les fonctionnalités TeleFeed"""
    
    def __init__(self):
        self.sessions = load_json_data(DATA_FILES['sessions'])
        self.redirections = load_json_data(DATA_FILES['redirections'])
        self.transformations = load_json_data(DATA_FILES['transformations'])
        self.filters = load_json_data(DATA_FILES['filters'])
        self.whitelist = load_json_data(DATA_FILES['whitelist'])
        self.blacklist = load_json_data(DATA_FILES['blacklist'])
        self.settings = load_json_data(DATA_FILES['settings'])
        self.chats = load_json_data(DATA_FILES['chats'])
        self.delay = load_json_data(DATA_FILES['delay'])
        
        # Mapping des messages pour édition
        self.message_mapping = load_json_data('telefeed_message_mapping.json')
        
        # Clients connectés
        self.clients = {}
        
        # Note: La restauration des sessions se fait lors du premier appel
        
    def save_all_data(self):
        """Sauvegarde toutes les données"""
        # Filtrer les sessions pour exclure les clients TelegramClient
        sessions_to_save = {}
        for phone, session_data in self.sessions.items():
            if isinstance(session_data, dict):
                # Créer une copie sans les objets TelegramClient
                filtered_session = {k: v for k, v in session_data.items() if k != 'client'}
                sessions_to_save[phone] = filtered_session
            else:
                sessions_to_save[phone] = session_data
        
        save_json_data(DATA_FILES['sessions'], sessions_to_save)
        save_json_data(DATA_FILES['redirections'], self.redirections)
        save_json_data(DATA_FILES['transformations'], self.transformations)
        save_json_data(DATA_FILES['filters'], self.filters)
        save_json_data(DATA_FILES['whitelist'], self.whitelist)
        save_json_data(DATA_FILES['blacklist'], self.blacklist)
        save_json_data(DATA_FILES['settings'], self.settings)
        save_json_data(DATA_FILES['chats'], self.chats)
        save_json_data(DATA_FILES['delay'], self.delay)
        save_json_data('telefeed_message_mapping.json', self.message_mapping)
    
    async def restore_existing_sessions(self):
        """Restaure automatiquement les sessions existantes"""
        print("🔄 Restauration des sessions existantes...")
        
        for phone_number, session_data in self.sessions.items():
            if isinstance(session_data, dict) and session_data.get('connected'):
                try:
                    # Créer le client avec le nom de session existant
                    session_name = f"telefeed_{phone_number}"
                    
                    # Vérifier si le fichier de session existe
                    if os.path.exists(f"{session_name}.session"):
                        # Utiliser API_ID et API_HASH par défaut (peuvent être modifiés)
                        from config import API_ID, API_HASH
                        client = TelegramClient(session_name, API_ID, API_HASH)
                        
                        await client.connect()
                        
                        # Vérifier si la session est toujours valide
                        if await client.is_user_authorized():
                            self.clients[phone_number] = client
                            # Marquer la session comme restaurée
                            self.sessions[phone_number]['restored_at'] = datetime.now().isoformat()
                            print(f"✅ Session restaurée pour {phone_number}")
                        else:
                            print(f"⚠️ Session expirée pour {phone_number}")
                            # Marquer la session comme expirée
                            self.sessions[phone_number]['connected'] = False
                            self.sessions[phone_number]['expired_at'] = datetime.now().isoformat()
                            pass
                    else:
                        print(f"⚠️ Fichier de session manquant pour {phone_number}")
                        # Marquer la session comme manquante
                        self.sessions[phone_number]['connected'] = False
                        self.sessions[phone_number]['missing_file'] = True
                        
                except Exception as e:
                    print(f"❌ Erreur lors de la restauration de {phone_number}: {e}")
                    # Marquer la session comme en erreur
                    self.sessions[phone_number]['connected'] = False
                    self.sessions[phone_number]['error'] = str(e)
        
        # Sauvegarder les changements
        self.save_all_data()
        print(f"🔄 {len(self.clients)} sessions restaurées")
    
    async def setup_redirection_handlers(self, client, phone_number):
        """Configure les gestionnaires de redirection pour un client TeleFeed"""
        from telethon import events
        
        async def message_handler(event, is_edit=False):
            """Gestionnaire des messages pour redirection"""
            # Vérifier les redirections pour ce numéro
            redirections = self.redirections.get(phone_number, {})
            
            for redir_id, redir_data in redirections.items():
                if not redir_data.get('active', True):
                    continue
                
                # Vérifier si ce chat est dans les sources
                if event.chat_id in redir_data.get('sources', []):
                    text = event.raw_text or ''
                    
                    # Vérifier les filtres
                    if not self.should_process_message(text, phone_number, redir_id):
                        continue
                    
                    # Appliquer les transformations
                    processed_text = self.apply_transformations(text, phone_number, redir_id)
                    
                    # Envoyer vers les destinations
                    for dest_id in redir_data.get('destinations', []):
                        try:
                            # Clé unique pour ce message source
                            source_key = f"{event.chat_id}_{event.id}"
                            
                            if is_edit:
                                # Message édité - essayer de modifier le message existant
                                dest_message_id = self.message_mapping.get(source_key, {}).get(str(dest_id))
                                if dest_message_id:
                                    try:
                                        # Éditer en tant que canal/groupe
                                        await client.edit_message(
                                            dest_id, 
                                            dest_message_id, 
                                            processed_text,
                                            schedule=None
                                        )
                                        print(f"✅ Message édité dans {dest_id}")
                                        continue
                                    except Exception as e:
                                        print(f"⚠️ Impossible d'éditer: {e}")
                                        # Si l'édition échoue, ne pas envoyer un nouveau message
                                        continue
                                else:
                                    # Pas de correspondance trouvée pour ce message édité
                                    print(f"⚠️ Aucune correspondance trouvée pour édition {source_key}")
                                    continue
                            else:
                                # Nouveau message - envoyer AUTHENTIQUEMENT comme le canal de destination
                                try:
                                    # Obtenir l'entité du canal de destination
                                    destination_entity = await client.get_entity(dest_id)
                                    
                                    # CORRECTION : Envoyer comme le canal lui-même (pas le client)
                                    if hasattr(destination_entity, 'broadcast') and destination_entity.broadcast:
                                        # Pour un canal : Utiliser send_message avec from_peer
                                        try:
                                            # Envoyer comme si c'était le canal qui poste
                                            sent_message = await client.send_message(
                                                destination_entity,
                                                processed_text,
                                                silent=False,
                                                from_peer=destination_entity  # CLEF : Envoyer AU NOM DU CANAL
                                            )
                                            print(f"✅ Message authentique envoyé par canal {dest_id}")
                                        except Exception as auth_error:
                                            print(f"⚠️ Échec authentique: {auth_error}")
                                            # Fallback : Message normal avec indication
                                            sent_message = await client.send_message(
                                                destination_entity,
                                                f"🔄 {processed_text}",
                                                silent=False
                                            )
                                            print(f"✅ Message normal envoyé vers canal {dest_id}")
                                    elif hasattr(destination_entity, 'megagroup') and destination_entity.megagroup:
                                        # Pour un supergroupe : Tenter envoi authentique
                                        try:
                                            sent_message = await client.send_message(
                                                destination_entity,
                                                processed_text,
                                                from_peer=destination_entity
                                            )
                                            print(f"✅ Message authentique envoyé par groupe {dest_id}")
                                        except Exception:
                                            # Fallback normal
                                            sent_message = await client.send_message(
                                                destination_entity,
                                                processed_text
                                            )
                                            print(f"✅ Message normal envoyé vers groupe {dest_id}")
                                    else:
                                        # Groupe normal : envoyer normalement
                                        sent_message = await client.send_message(
                                            destination_entity,
                                            processed_text
                                        )
                                        print(f"✅ Message envoyé vers groupe {dest_id}")
                                    
                                    # Sauvegarder la correspondance pour futures éditions
                                    if source_key not in self.message_mapping:
                                        self.message_mapping[source_key] = {}
                                    self.message_mapping[source_key][str(dest_id)] = sent_message.id
                                    self.save_all_data()
                                    
                                except Exception as e:
                                    print(f"❌ Erreur envoi: {e}")
                                    try:
                                        # Fallback: envoyer avec ID direct
                                        sent_message = await client.send_message(dest_id, processed_text)
                                        
                                        if source_key not in self.message_mapping:
                                            self.message_mapping[source_key] = {}
                                        self.message_mapping[source_key][str(dest_id)] = sent_message.id
                                        self.save_all_data()
                                        
                                        print(f"✅ Message envoyé vers {dest_id} (fallback)")
                                    except Exception as e2:
                                        print(f"❌ Erreur fallback: {e2}")
                            
                        except Exception as e:
                            print(f"❌ Erreur redirection vers {dest_id}: {e}")
        
        async def new_message_handler(event):
            """Gestionnaire spécifique pour nouveaux messages"""
            await message_handler(event, is_edit=False)
        
        async def edit_message_handler(event):
            """Gestionnaire spécifique pour messages édités"""
            await message_handler(event, is_edit=True)
        
        # Enregistrer les gestionnaires séparés sur ce client
        client.add_event_handler(new_message_handler, events.NewMessage)
        client.add_event_handler(edit_message_handler, events.MessageEdited)
        print(f"📡 Gestionnaire de redirection activé pour {phone_number} (messages + éditions)")
    
    async def connect_account(self, phone_number, api_id, api_hash):
        """Connecte un compte Telegram avec persistance automatique"""
        try:
            session_name = f"telefeed_{phone_number}"
            
            # Vérifier si une session existe déjà et est valide
            if phone_number in self.sessions and self.sessions[phone_number].get('connected'):
                if phone_number in self.clients:
                    # Session déjà active
                    return {'status': 'already_connected', 'client': self.clients[phone_number]}
                
                # Tentative de restauration de session existante
                if os.path.exists(f"{session_name}.session"):
                    try:
                        client = TelegramClient(session_name, api_id, api_hash)
                        await client.connect()
                        
                        if await client.is_user_authorized():
                            self.clients[phone_number] = client
                            self.sessions[phone_number]['restored_at'] = datetime.now().isoformat()
                            self.save_all_data()
                            
                            # Enregistrer le gestionnaire de redirection sur ce client restauré
                            await self.setup_redirection_handlers(client, phone_number)
                            
                            print(f"✅ Session restaurée automatiquement pour {phone_number}")
                            return {'status': 'restored', 'client': client}
                        else:
                            # Session expirée, continuer avec nouvelle connexion
                            pass
                    except Exception as e:
                        print(f"⚠️ Erreur lors de la restauration pour {phone_number}: {e}")
            
            # Nouvelle connexion ou restauration échouée
            client = TelegramClient(session_name, api_id, api_hash)
            await client.connect()
            
            if not await client.is_user_authorized():
                # Demander le code d'authentification
                result = await client.send_code_request(phone_number)
                return {
                    'status': 'code_sent',
                    'phone_code_hash': result.phone_code_hash,
                    'client': client
                }
            else:
                # Déjà autorisé (session valide)
                self.clients[phone_number] = client
                self.sessions[phone_number] = {
                    'connected': True,
                    'connected_at': datetime.now().isoformat(),
                    'session_file': f"{session_name}.session"
                }
                self.save_all_data()
                
                # Enregistrer le gestionnaire de redirection sur ce client
                await self.setup_redirection_handlers(client, phone_number)
                
                print(f"✅ Connexion réussie pour {phone_number}")
                return {'status': 'connected', 'client': client}
                
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    async def verify_code(self, phone_number, code, phone_code_hash, client):
        """Vérifie le code d'authentification avec persistance"""
        try:
            await client.sign_in(phone_number, code, phone_code_hash=phone_code_hash)
            
            # Enregistrer le client et la session
            self.clients[phone_number] = client
            session_name = f"telefeed_{phone_number}"
            self.sessions[phone_number] = {
                'connected': True,
                'connected_at': datetime.now().isoformat(),
                'session_file': f"{session_name}.session",
                'verified_with_code': True
            }
            self.save_all_data()
            
            # Enregistrer le gestionnaire de redirection sur ce client
            await self.setup_redirection_handlers(client, phone_number)
            
            print(f"✅ Session persistante créée pour {phone_number}")
            return {'status': 'connected'}
            
        except SessionPasswordNeededError:
            return {'status': 'password_needed'}
        except PhoneCodeExpiredError:
            return {'status': 'code_expired'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    async def get_chats(self, phone_number):
        """Récupère la liste des chats"""
        if phone_number not in self.clients:
            return {'status': 'not_connected'}
            
        try:
            client = self.clients[phone_number]
            chats = []
            
            async for dialog in client.iter_dialogs(limit=100):
                chat_data = {
                    'id': dialog.id,
                    'title': dialog.title or dialog.name,
                    'type': 'unknown'
                }
                
                if isinstance(dialog.entity, User):
                    # Détecter si c'est un bot
                    if hasattr(dialog.entity, 'bot') and dialog.entity.bot:
                        chat_data['type'] = 'bot'
                    else:
                        chat_data['type'] = 'user'
                elif isinstance(dialog.entity, Chat):
                    chat_data['type'] = 'group'
                elif isinstance(dialog.entity, Channel):
                    chat_data['type'] = 'channel' if dialog.entity.broadcast else 'supergroup'
                
                chats.append(chat_data)
            
            # Sauvegarder les chats
            self.chats[phone_number] = chats
            self.save_all_data()
            
            return {'status': 'success', 'chats': chats}
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def add_redirection(self, phone_number, redirection_id, sources, destinations):
        """Ajoute une redirection"""
        try:
            if phone_number not in self.redirections:
                self.redirections[phone_number] = {}
            
            self.redirections[phone_number][redirection_id] = {
                'sources': sources,
                'destinations': destinations,
                'created_at': datetime.now().isoformat(),
                'active': True
            }
            
            # Paramètres par défaut
            if phone_number not in self.settings:
                self.settings[phone_number] = {}
            
            self.settings[phone_number][redirection_id] = {
                'process_reply': True,
                'process_edit': True,
                'process_delete': True,
                'process_me': False,
                'process_forward': False,
                'process_raw': False,
                'process_duplicates': True,
                'delay_spread_mode': False
            }
            
            self.save_all_data()
            return True
            
        except Exception as e:
            print(f"Erreur lors de l'ajout de la redirection: {e}")
            return False
    
    def remove_redirection(self, phone_number, redirection_id):
        """Supprime une redirection"""
        try:
            if phone_number in self.redirections and redirection_id in self.redirections[phone_number]:
                del self.redirections[phone_number][redirection_id]
                
            if phone_number in self.settings and redirection_id in self.settings[phone_number]:
                del self.settings[phone_number][redirection_id]
                
            self.save_all_data()
            return True
        except:
            return False
    
    def apply_transformations(self, text, phone_number, redirection_id):
        """Applique les transformations sur le texte"""
        if not text:
            return text
            
        # Format transformation
        format_data = self.transformations.get(phone_number, {}).get(redirection_id, {}).get('format')
        if format_data:
            template = format_data.get('template', '[[Message.Text]]')
            text = template.replace('[[Message.Text]]', text)
        
        # Power transformation
        power_data = self.transformations.get(phone_number, {}).get(redirection_id, {}).get('power')
        if power_data:
            rules = power_data.get('rules', [])
            for rule in rules:
                if '=' in rule:
                    # Regex rule
                    pattern, replacement = rule.split('=', 1)
                    try:
                        text = re.sub(pattern, replacement, text, flags=re.MULTILINE | re.DOTALL)
                    except:
                        pass
                elif '","' in rule:
                    # Simple replacement
                    rule = rule.strip('"')
                    if '","' in rule:
                        old, new = rule.split('","', 1)
                        text = text.replace(old, new)
        
        # Remove lines transformation
        remove_lines_data = self.transformations.get(phone_number, {}).get(redirection_id, {}).get('removeLines')
        if remove_lines_data:
            keywords = remove_lines_data.get('keywords', [])
            lines = text.split('\n')
            filtered_lines = []
            
            for line in lines:
                should_remove = False
                for keyword in keywords:
                    if keyword in line:
                        should_remove = True
                        break
                if not should_remove:
                    filtered_lines.append(line)
            
            text = '\n'.join(filtered_lines)
        
        return text
    
    def should_process_message(self, text, phone_number, redirection_id):
        """Vérifie si le message doit être traité (whitelist/blacklist)"""
        # Vérifier la blacklist
        blacklist_data = self.blacklist.get(phone_number, {}).get(redirection_id, {})
        if blacklist_data and blacklist_data.get('active', False):
            patterns = blacklist_data.get('patterns', [])
            for pattern in patterns:
                if isinstance(pattern, str):
                    if pattern.startswith('"') and pattern.endswith('"'):
                        # Simple text match
                        if pattern[1:-1] in text:
                            return False
                    else:
                        # Regex match
                        try:
                            if re.search(pattern, text, re.MULTILINE | re.DOTALL):
                                return False
                        except:
                            pass
        
        # Vérifier la whitelist
        whitelist_data = self.whitelist.get(phone_number, {}).get(redirection_id, {})
        if whitelist_data and whitelist_data.get('active', False):
            patterns = whitelist_data.get('patterns', [])
            if patterns:
                for pattern in patterns:
                    if isinstance(pattern, str):
                        if pattern.startswith('"') and pattern.endswith('"'):
                            # Simple text match
                            if pattern[1:-1] in text:
                                return True
                        else:
                            # Regex match
                            try:
                                if re.search(pattern, text, re.MULTILINE | re.DOTALL):
                                    return True
                            except:
                                pass
                return False  # Whitelist active but no match
        
        return True
    
    def get_session_status(self, phone_number=None):
        """Récupère le statut des sessions"""
        if phone_number:
            # Statut d'une session spécifique
            session_data = self.sessions.get(phone_number, {})
            is_connected = phone_number in self.clients
            return {
                'phone_number': phone_number,
                'connected': is_connected,
                'session_data': session_data,
                'has_client': is_connected
            }
        else:
            # Statut de toutes les sessions
            status = {
                'total_sessions': len(self.sessions),
                'active_clients': len(self.clients),
                'sessions': {}
            }
            
            for phone, session_data in self.sessions.items():
                is_connected = phone in self.clients
                status['sessions'][phone] = {
                    'connected': is_connected,
                    'session_data': session_data,
                    'has_client': is_connected
                }
            
            return status

# Instance globale
telefeed_manager = TeleFeedManager()

async def register_all_handlers(bot, ADMIN_ID, api_id, api_hash):
    """Enregistre tous les handlers TeleFeed et les redirections."""
    
    @bot.on(events.NewMessage(pattern=r'/connect (\d+)'))
    async def connect_handler(event):
        """Handler pour connecter un compte"""
        if not is_user_authorized(event.sender_id):
            await event.reply("❌ Vous devez avoir une licence active pour utiliser TeleFeed.")
            return
        
        phone_number = event.pattern_match.group(1)
        
        await event.reply("🔌 Connexion en cours...")
        
        result = await telefeed_manager.connect_account(phone_number, api_id, api_hash)
        
        if result['status'] == 'code_sent':
            await event.reply(
                f"📱 Code d'authentification envoyé à {phone_number}\n"
                f"💡 Répondez avec: aa + votre code\n"
                f"📝 Exemple: aa12345"
            )
            
            # Stocker temporairement les données de connexion
            telefeed_manager.sessions[f"temp_{phone_number}"] = {
                'phone_code_hash': result['phone_code_hash'],
                'client': result['client'],
                'user_id': event.sender_id
            }
            
        elif result['status'] == 'connected':
            await event.reply(f"✅ Compte {phone_number} connecté avec succès!")
            
        else:
            error_msg = result.get('message', 'Connexion échouée')
            if 'A wait of' in error_msg and 'seconds is required' in error_msg:
                # Extraire le nombre de secondes
                import re
                seconds_match = re.search(r'A wait of (\d+) seconds', error_msg)
                if seconds_match:
                    seconds = int(seconds_match.group(1))
                    hours = seconds // 3600
                    minutes = (seconds % 3600) // 60
                    
                    await event.reply(
                        f"⏰ **Limitation Telegram détectée**\n\n"
                        f"Le numéro `{phone_number}` est temporairement bloqué.\n\n"
                        f"⏱️ **Temps d'attente:** {hours}h {minutes}min\n\n"
                        f"💡 **Solutions:**\n"
                        f"• Attendez la fin de la période\n"
                        f"• Utilisez un autre numéro\n"
                        f"• Essayez `/connect +33612345678`\n\n"
                        f"❓ Cette limitation vient de Telegram, pas du bot.",
                        parse_mode='markdown'
                    )
                else:
                    await event.reply(f"❌ Erreur: {error_msg}")
            else:
                await event.reply(f"❌ Erreur: {error_msg}")
    
    @bot.on(events.NewMessage(pattern=r'^aa(\d+)$'))
    async def verify_code_handler(event):
        """Handler pour vérifier le code d'authentification TeleFeed"""
        if not is_user_authorized(event.sender_id):
            return
        
        code = event.pattern_match.group(1)
        
        # Rechercher la session temporaire pour cet utilisateur
        temp_session = None
        phone_number = None
        
        for key, session in telefeed_manager.sessions.items():
            if key.startswith("temp_") and session.get('user_id') == event.sender_id:
                temp_session = session
                phone_number = key.replace("temp_", "")
                break
        
        if not temp_session:
            await event.reply("❌ Aucune connexion en attente trouvée.")
            return
        
        result = await telefeed_manager.verify_code(
            phone_number, code, 
            temp_session['phone_code_hash'], 
            temp_session['client']
        )
        
        if result['status'] == 'connected':
            await event.reply(f"✅ Compte {phone_number} connecté avec succès!")
            # Nettoyer la session temporaire
            del telefeed_manager.sessions[f"temp_{phone_number}"]
            
        elif result['status'] == 'password_needed':
            await event.reply("🔐 Authentification 2FA requise. Envoyez votre mot de passe.")
            
        else:
            await event.reply(f"❌ Erreur: {result.get('message', 'Code invalide')}")
    
    @bot.on(events.NewMessage(pattern=r'/sessions'))
    async def sessions_status_handler(event):
        """Handler pour afficher le statut des sessions (admin seulement)"""
        if event.sender_id != ADMIN_ID:
            return
        
        status = telefeed_manager.get_session_status()
        
        message = "📊 **STATUT DES SESSIONS TELEFEED**\n\n"
        message += f"📈 **Résumé:**\n"
        message += f"• Sessions enregistrées: {status['total_sessions']}\n"
        message += f"• Clients actifs: {status['active_clients']}\n\n"
        
        if status['sessions']:
            message += "📱 **Détails des sessions:**\n\n"
            for phone, session_info in status['sessions'].items():
                if phone.startswith('temp_'):
                    continue  # Ignorer les sessions temporaires
                    
                icon = "✅" if session_info['connected'] else "❌"
                message += f"{icon} **{phone}**\n"
                
                session_data = session_info['session_data']
                if 'connected_at' in session_data:
                    message += f"   📅 Connecté: {session_data['connected_at'][:16]}\n"
                if 'restored_at' in session_data:
                    message += f"   🔄 Restauré: {session_data['restored_at'][:16]}\n"
                if 'session_file' in session_data:
                    message += f"   💾 Fichier: {session_data['session_file']}\n"
                
                message += "\n"
        else:
            message += "📭 Aucune session enregistrée\n"
        
        message += "\n💡 **Utilisation:**\n"
        message += "• Sessions persistantes = pas besoin de se reconnecter\n"
        message += "• Utilisez `/connect NUMERO` pour ajouter un compte\n"
        message += "• Les sessions sont automatiquement restaurées au redémarrage"
        
        await event.reply(message, parse_mode='markdown')
    
    @bot.on(events.NewMessage(pattern=r'/permissions (-?\d+)'))
    async def check_permissions_handler(event):
        """Handler pour vérifier les permissions dans un canal (admin seulement)"""
        if event.sender_id != ADMIN_ID:
            return
        
        try:
            channel_id = int(event.pattern_match.group(1))
            
            # Vérifier les permissions pour tous les comptes connectés
            report = "🔧 **Vérification des permissions**\n\n"
            
            for phone_number, client in telefeed_manager.clients.items():
                try:
                    # Obtenir l'entité du canal
                    channel = await client.get_entity(channel_id)
                    
                    # Vérifier les permissions
                    permissions = await client.get_permissions(channel)
                    me = await client.get_me()
                    
                    report += f"📱 **{phone_number}** ({me.first_name})\n"
                    report += f"Canal : {channel.title}\n"
                    report += f"Type : {'Canal' if channel.broadcast else 'Groupe'}\n"
                    report += f"• Publier messages : {'✅' if permissions.post_messages else '❌'}\n"
                    report += f"• Modifier messages : {'✅' if permissions.edit_messages else '❌'}\n"
                    report += f"• Supprimer messages : {'✅' if permissions.delete_messages else '❌'}\n"
                    report += f"• Admin : {'✅' if permissions.is_admin else '❌'}\n\n"
                    
                except Exception as e:
                    report += f"📱 **{phone_number}** - ❌ Erreur : {e}\n\n"
            
            await event.reply(report, parse_mode='markdown')
            
        except ValueError:
            await event.reply("❌ ID de canal invalide")
        except Exception as e:
            await event.reply(f"❌ Erreur : {e}")
    
    @bot.on(events.NewMessage(pattern=r'/chats(?:\s+(.*))?'))
    async def chats_handler(event):
        """Handler pour lister les chats - Format identique aux captures d'écran"""
        if not is_user_authorized(event.sender_id):
            await event.reply("❌ Vous devez avoir une licence active pour utiliser TeleFeed.")
            return
        
        # Analyser les arguments
        args_text = event.pattern_match.group(1)
        
        if not args_text:
            # Afficher l'aide complète exactement comme dans les captures
            help_text = (
                "**Chats Help Menu**\n"
                "Use it for getting all chats ID for use with other commands. You can use a filter to tell TeleFeed what type of chats to show.\n\n"
                "**Command Arguments**\n"
                "`/chats PHONE_NUMBER`\n"
                "`/chats FILTER PHONE_NUMBER`\n\n"
                "**Get all chats from 2759205517**\n"
                "`/chats 2759205517`\n\n"
                "**Get specific chats from 2759205517**\n"
                "`/chats user 2759205517`\n"
                "`/chats bot 2759205517`\n"
                "`/chats group 2759205517`\n"
                "`/chats channel 2759205517`"
            )
            await event.reply(help_text, parse_mode='markdown')
            return
        
        args = args_text.split()
        
        if len(args) == 1:
            # Format: /chats PHONE_NUMBER
            phone_number = args[0]
            chat_filter = None
        elif len(args) == 2:
            # Format: /chats FILTER PHONE_NUMBER
            chat_filter = args[0].lower()
            phone_number = args[1]
        else:
            await event.reply("❌ Format incorrect. Tapez `/chats` pour voir l'aide.")
            return
        
        await event.reply("**Getting Chats!**\nPlease wait...")
        
        result = await telefeed_manager.get_chats(phone_number)
        
        if result['status'] == 'success':
            chats = result['chats']
            if not chats:
                await event.reply("📭 Aucun chat trouvé.")
                return
            
            # Appliquer le filtre si spécifié
            if chat_filter:
                if chat_filter == 'user':
                    filtered_chats = [c for c in chats if c['type'] == 'user']
                elif chat_filter == 'bot':
                    filtered_chats = [c for c in chats if c['type'] == 'bot']
                elif chat_filter == 'group':
                    filtered_chats = [c for c in chats if c['type'] == 'group']
                elif chat_filter == 'channel':
                    filtered_chats = [c for c in chats if c['type'] == 'channel']
                else:
                    await event.reply("❌ Filtre invalide. Utilisez: user, bot, group, channel")
                    return
                chats = filtered_chats
            
            # Formater le message exactement comme dans les captures d'écran
            if chat_filter:
                if chat_filter == 'group':
                    header = "**Group Title | ID**\n\n"
                elif chat_filter == 'user':
                    header = "**User Title | ID**\n\n"
                elif chat_filter == 'bot':
                    header = "**Bot Title | ID**\n\n"
                elif chat_filter == 'channel':
                    header = "**Channel Title | ID**\n\n"
                else:
                    header = f"**{chat_filter.title()} Title | ID**\n\n"
            else:
                header = "**Group Title | ID**\n\n"
            
            message = header
            
            for chat in chats:
                title = chat['title'] if 'title' in chat else 'Sans titre'
                chat_id = chat['id'] if 'id' in chat else 'N/A'
                
                # Nettoyer le titre pour éviter les problèmes de formatage
                if title:
                    title = str(title).replace('*', '').replace('_', '').replace('`', '')
                else:
                    title = 'Sans titre'
                
                # Format exact : Titre | ID (sans emoji, comme dans la capture)
                message += f"{title} | {chat_id}\n"
            
            # Diviser le message si trop long (plus de 4000 caractères)
            if len(message) > 4000:
                parts = []
                current_part = header
                
                for chat in chats:
                    title = chat['title'] if 'title' in chat else 'Sans titre'
                    if title:
                        title = str(title).replace('*', '').replace('_', '').replace('`', '')
                    else:
                        title = 'Sans titre'
                    chat_id = chat['id'] if 'id' in chat else 'N/A'
                    line = f"{title} | {chat_id}\n"
                    
                    if len(current_part + line) > 4000:
                        parts.append(current_part)
                        current_part = header + line
                    else:
                        current_part += line
                
                if current_part:
                    parts.append(current_part)
                
                for part in parts:
                    await event.reply(part, parse_mode='markdown')
            else:
                await event.reply(message, parse_mode='markdown')
            
        elif result['status'] == 'not_connected':
            await event.reply(f"❌ Compte {phone_number} non connecté. Utilisez /connect {phone_number}")
            
        else:
            await event.reply(f"❌ Erreur: {result.get('message', 'Impossible de récupérer les chats')}")
    
    @bot.on(events.NewMessage(pattern=r'/redirection add (\w+) on (\d+)'))
    async def add_redirection_handler(event):
        """Handler pour ajouter une redirection"""
        if not is_user_authorized(event.sender_id):
            await event.reply("❌ Vous devez avoir une licence active pour utiliser TeleFeed.")
            return
        
        redirection_id = event.pattern_match.group(1)
        phone_number = event.pattern_match.group(2)
        
        await event.reply(
            f"🔄 Configuration de la redirection **{redirection_id}**\n\n"
            f"📝 Envoyez maintenant les IDs au format:\n"
            f"**SOURCE - DESTINATION**\n\n"
            f"📋 Exemples:\n"
            f"• `123456789 - 987654321`\n"
            f"• `123,456 - 789,012`\n"
            f"• Utilisez /chats {phone_number} pour voir les IDs",
            parse_mode='markdown'
        )
        
        # Attendre la réponse
        # Variables pour stocker la réponse
        response_future = asyncio.Future()
        
        async def response_handler(response_event):
            if (response_event.sender_id == event.sender_id and 
                response_event.chat_id == event.chat_id and 
                ' - ' in response_event.raw_text):
                if not response_future.done():
                    response_future.set_result(response_event)
                    bot.remove_event_handler(response_handler)
        
        # Ajouter le gestionnaire temporaire
        bot.add_event_handler(response_handler, events.NewMessage)
        
        try:
            response = await asyncio.wait_for(response_future, timeout=60)
            
            # Parser la réponse
            parts = response.raw_text.split(' - ')
            if len(parts) != 2:
                await event.reply("❌ Format invalide. Utilisez: SOURCE - DESTINATION")
                return
            
            sources = [int(x.strip()) for x in parts[0].split(',')]
            destinations = [int(x.strip()) for x in parts[1].split(',')]
            
            if telefeed_manager.add_redirection(phone_number, redirection_id, sources, destinations):
                await event.reply(f"✅ Redirection **{redirection_id}** créée avec succès!")
            else:
                await event.reply("❌ Erreur lors de la création de la redirection.")
                
        except asyncio.TimeoutError:
            await event.reply("⏰ Timeout. Recommencez la configuration.")
        except ValueError:
            await event.reply("❌ IDs invalides. Utilisez uniquement des nombres.")
    
    @bot.on(events.NewMessage(pattern=r'/redirection remove (\w+) on (\d+)'))
    async def remove_redirection_handler(event):
        """Handler pour supprimer une redirection"""
        if not is_user_authorized(event.sender_id):
            await event.reply("❌ Vous devez avoir une licence active pour utiliser TeleFeed.")
            return
        
        redirection_id = event.pattern_match.group(1)
        phone_number = event.pattern_match.group(2)
        
        if telefeed_manager.remove_redirection(phone_number, redirection_id):
            await event.reply(f"✅ Redirection **{redirection_id}** supprimée.")
        else:
            await event.reply("❌ Redirection non trouvée.")
    
    @bot.on(events.NewMessage(pattern=r'/redirection (\d+)'))
    async def list_redirections_handler(event):
        """Handler pour lister les redirections"""
        if not is_user_authorized(event.sender_id):
            await event.reply("❌ Vous devez avoir une licence active pour utiliser TeleFeed.")
            return
        
        phone_number = event.pattern_match.group(1)
        
        redirections = telefeed_manager.redirections.get(phone_number, {})
        
        if not redirections:
            await event.reply(f"📭 Aucune redirection active pour {phone_number}")
            return
        
        message = f"🔄 **Redirections actives pour {phone_number}:**\n\n"
        
        for redir_id, data in redirections.items():
            status = "✅" if data.get('active', True) else "❌"
            sources = ', '.join(map(str, data.get('sources', [])))
            destinations = ', '.join(map(str, data.get('destinations', [])))
            
            message += f"{status} **{redir_id}**\n"
            message += f"📤 Sources: `{sources}`\n"
            message += f"📥 Destinations: `{destinations}`\n\n"
        
        await event.reply(message, parse_mode='markdown')
    
    @bot.on(events.NewMessage(pattern=r'/transformation add (\w+) (\w+) on (\d+)'))
    async def add_transformation_handler(event):
        """Handler pour ajouter une transformation"""
        if not is_user_authorized(event.sender_id):
            await event.reply("❌ Vous devez avoir une licence active pour utiliser TeleFeed.")
            return
        
        feature = event.pattern_match.group(1)
        redirection_id = event.pattern_match.group(2)
        phone_number = event.pattern_match.group(3)
        
        if feature not in ['format', 'power', 'removeLines']:
            await event.reply("❌ Fonctionnalité non supportée. Utilisez: format, power, removeLines")
            return
        
        await event.reply(
            f"⚙️ Configuration de la transformation **{feature}** pour **{redirection_id}**\n\n"
            f"📝 Envoyez maintenant votre configuration:"
        )
        
        # Variables pour stocker la réponse
        response_future = asyncio.Future()
        
        async def response_handler(response_event):
            if (response_event.sender_id == event.sender_id and 
                response_event.chat_id == event.chat_id):
                if not response_future.done():
                    response_future.set_result(response_event)
                    bot.remove_event_handler(response_handler)
        
        # Ajouter le gestionnaire temporaire
        bot.add_event_handler(response_handler, events.NewMessage)
        
        try:
            response = await asyncio.wait_for(response_future, timeout=120)
            
            # Initialiser la structure si nécessaire
            if phone_number not in telefeed_manager.transformations:
                telefeed_manager.transformations[phone_number] = {}
            if redirection_id not in telefeed_manager.transformations[phone_number]:
                telefeed_manager.transformations[phone_number][redirection_id] = {}
            
            # Configurer selon le type de transformation
            if feature == 'format':
                telefeed_manager.transformations[phone_number][redirection_id]['format'] = {
                    'template': response.raw_text,
                    'active': True
                }
            elif feature == 'power':
                rules = response.raw_text.split('\n')
                telefeed_manager.transformations[phone_number][redirection_id]['power'] = {
                    'rules': rules,
                    'active': True
                }
            elif feature == 'removeLines':
                keywords = [k.strip() for k in response.raw_text.split(',')]
                telefeed_manager.transformations[phone_number][redirection_id]['removeLines'] = {
                    'keywords': keywords,
                    'active': True
                }
            
            telefeed_manager.save_all_data()
            await event.reply(f"✅ Transformation **{feature}** configurée pour **{redirection_id}**!")
            
        except asyncio.TimeoutError:
            await event.reply("⏰ Timeout. Recommencez la configuration.")
    
    @bot.on(events.NewMessage(pattern=r'/whitelist add (\w+) on (\d+)'))
    async def add_whitelist_handler(event):
        """Handler pour ajouter une whitelist"""
        if not is_user_authorized(event.sender_id):
            await event.reply("❌ Vous devez avoir une licence active pour utiliser TeleFeed.")
            return
        
        redirection_id = event.pattern_match.group(1)
        phone_number = event.pattern_match.group(2)
        
        await event.reply(
            f"⚪ Configuration de la whitelist pour **{redirection_id}**\n\n"
            f"📝 Envoyez les mots-clés (un par ligne):"
        )
        
        # Variables pour stocker la réponse
        response_future = asyncio.Future()
        
        async def response_handler(response_event):
            if (response_event.sender_id == event.sender_id and 
                response_event.chat_id == event.chat_id):
                if not response_future.done():
                    response_future.set_result(response_event)
                    bot.remove_event_handler(response_handler)
        
        # Ajouter le gestionnaire temporaire
        bot.add_event_handler(response_handler, events.NewMessage)
        
        try:
            response = await asyncio.wait_for(response_future, timeout=60)
            
            patterns = response.raw_text.split('\n')
            
            if phone_number not in telefeed_manager.whitelist:
                telefeed_manager.whitelist[phone_number] = {}
            
            telefeed_manager.whitelist[phone_number][redirection_id] = {
                'patterns': patterns,
                'active': True
            }
            
            telefeed_manager.save_all_data()
            await event.reply(f"✅ Whitelist configurée pour **{redirection_id}**!")
            
        except asyncio.TimeoutError:
            await event.reply("⏰ Timeout. Recommencez la configuration.")
    
    @bot.on(events.NewMessage(pattern=r'/blacklist add (\w+) on (\d+)'))
    async def add_blacklist_handler(event):
        """Handler pour ajouter une blacklist"""
        if not is_user_authorized(event.sender_id):
            await event.reply("❌ Vous devez avoir une licence active pour utiliser TeleFeed.")
            return
        
        redirection_id = event.pattern_match.group(1)
        phone_number = event.pattern_match.group(2)
        
        await event.reply(
            f"⚫ Configuration de la blacklist pour **{redirection_id}**\n\n"
            f"📝 Envoyez les mots-clés à bloquer (un par ligne):"
        )
        
        # Variables pour stocker la réponse
        response_future = asyncio.Future()
        
        async def response_handler(response_event):
            if (response_event.sender_id == event.sender_id and 
                response_event.chat_id == event.chat_id):
                if not response_future.done():
                    response_future.set_result(response_event)
                    bot.remove_event_handler(response_handler)
        
        # Ajouter le gestionnaire temporaire
        bot.add_event_handler(response_handler, events.NewMessage)
        
        try:
            response = await asyncio.wait_for(response_future, timeout=60)
            
            patterns = response.raw_text.split('\n')
            
            if phone_number not in telefeed_manager.blacklist:
                telefeed_manager.blacklist[phone_number] = {}
            
            telefeed_manager.blacklist[phone_number][redirection_id] = {
                'patterns': patterns,
                'active': True
            }
            
            telefeed_manager.save_all_data()
            await event.reply(f"✅ Blacklist configurée pour **{redirection_id}**!")
            
        except asyncio.TimeoutError:
            await event.reply("⏰ Timeout. Recommencez la configuration.")
    
    @bot.on(events.NewMessage(pattern=r'/telefeed'))
    async def telefeed_help_handler(event):
        """Handler pour l'aide TeleFeed"""
        if not is_user_authorized(event.sender_id):
            await event.reply("❌ Vous devez avoir une licence active pour utiliser TeleFeed.")
            return
        
        help_message = """
🚀 **TeleFeed - Guide des commandes**

**📱 Connexion:**
• `/connect <numéro>` - Connecter un compte
• `/chats <numéro>` - Voir les chats disponibles

**🔄 Redirections:**
• `/redirection add <nom> on <numéro>` - Ajouter
• `/redirection remove <nom> on <numéro>` - Supprimer
• `/redirection <numéro>` - Lister les redirections

**⚙️ Transformations:**
• `/transformation add <type> <nom> on <numéro>`
• Types: format, power, removeLines

**🔍 Filtres:**
• `/whitelist add <nom> on <numéro>` - Mots autorisés
• `/blacklist add <nom> on <numéro>` - Mots bloqués

**💡 Exemple complet:**
1. `/connect 33123456789`
2. `aa12345` (après réception du code)
3. `/chats 33123456789`
4. `/redirection add test on 33123456789`
5. `123456789 - 987654321`

**📞 Support:** @SossouKouame
        """
        
        await event.reply(help_message, parse_mode='markdown')
    
    # Handler pour les messages redirigés
    async def handle_message_redirection(event):
        """Gestionnaire principal pour les redirections de messages"""
        # Vérifier tous les comptes connectés
        for phone_number, client in telefeed_manager.clients.items():
            if client == event.client:
                # Vérifier les redirections pour ce numéro
                redirections = telefeed_manager.redirections.get(phone_number, {})
                
                for redir_id, redir_data in redirections.items():
                    if not redir_data.get('active', True):
                        continue
                    
                    # Vérifier si ce chat est dans les sources
                    if event.chat_id in redir_data.get('sources', []):
                        text = event.raw_text or ''
                        
                        # Vérifier les filtres
                        if not telefeed_manager.should_process_message(text, phone_number, redir_id):
                            continue
                        
                        # Appliquer les transformations
                        processed_text = telefeed_manager.apply_transformations(text, phone_number, redir_id)
                        
                        # Envoyer vers les destinations
                        for dest_id in redir_data.get('destinations', []):
                            try:
                                await client.send_message(dest_id, processed_text)
                            except Exception as e:
                                print(f"Erreur lors de l'envoi vers {dest_id}: {e}")
    
    # Enregistrer le handler pour tous les messages
    @bot.on(events.NewMessage)
    async def handle_message_edited(event):
        """Gestionnaire des messages édités sans indication"""
        await handle_message_redirection(event)
    
    # Commande /export - Envoie tous les fichiers du projet (admin)
    @bot.on(events.NewMessage(pattern='/export'))
    async def export_command(event):
        user_id = str(event.sender_id)
        if user_id not in ADMIN_IDS:
            await event.respond("❌ Accès refusé")
            return
        
        await event.respond("📦 Préparation de l'export de tous les fichiers...")
        
        import os
        import zipfile
        import tempfile
        
        try:
            # Créer un fichier zip temporaire
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_zip:
                zip_path = tmp_zip.name
            
            # Créer l'archive avec tous les fichiers
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Parcourir tous les fichiers du projet
                for root, dirs, files in os.walk('.'):
                    # Ignorer certains dossiers
                    dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', '.pythonlibs', 'node_modules']]
                    
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Ignorer les fichiers système
                        if not file.startswith('.') and not file.endswith('.pyc'):
                            # Créer l'info du fichier avec un timestamp valide
                            info = zipfile.ZipInfo(file_path)
                            info.date_time = (1980, 1, 1, 0, 0, 0)  # Timestamp minimal valide
                            
                            # Lire le contenu du fichier
                            with open(file_path, 'rb') as f:
                                content = f.read()
                            
                            # Ajouter au zip
                            zipf.writestr(info, content)
            
            # Envoyer l'archive
            await event.respond(
                "📁 **Export du projet TeleFoot Bot**\n\n"
                "📦 Archive complète avec tous les fichiers sources",
                file=zip_path
            )
            
            # Nettoyer le fichier temporaire
            os.unlink(zip_path)
            
        except Exception as e:
            await event.respond(f"❌ Erreur lors de l'export: {str(e)}")
            print(f"Erreur export: {e}")

    # Commande /files - Liste tous les fichiers du projet (admin)
    @bot.on(events.NewMessage(pattern='/files'))
    async def files_command(event):
        user_id = str(event.sender_id)
        if user_id not in ADMIN_IDS:
            await event.respond("❌ Accès refusé")
            return
        
        import os
        
        files_list = []
        total_size = 0
        
        for root, dirs, files in os.walk('.'):
            # Ignorer certains dossiers
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', '.pythonlibs', 'node_modules']]
            
            for file in files:
                if not file.startswith('.') and not file.endswith('.pyc'):
                    file_path = os.path.join(root, file)
                    try:
                        size = os.path.getsize(file_path)
                        total_size += size
                        size_str = f"{size:,} bytes" if size < 1024 else f"{size//1024:,} KB"
                        files_list.append(f"📄 {file_path} ({size_str})")
                    except:
                        files_list.append(f"📄 {file_path}")
        
        # Diviser en messages si trop long
        message = f"📁 **Fichiers du projet TeleFoot Bot:**\n\n"
        message += f"📊 Total: {len(files_list)} fichiers ({total_size//1024:,} KB)\n\n"
        
        current_message = message
        for file_info in files_list:
            if len(current_message + file_info + "\n") > 4000:
                await event.respond(current_message)
                current_message = file_info + "\n"
            else:
                current_message += file_info + "\n"
        
        if current_message.strip():
            await event.respond(current_message)

    # Commande /backup - Sauvegarde de tous les fichiers de configuration (admin)
    @bot.on(events.NewMessage(pattern='/backup'))
    async def backup_command(event):
        user_id = str(event.sender_id)
        if user_id not in ADMIN_IDS:
            await event.respond("❌ Accès refusé")
            return
        
        await event.respond("💾 Création de la sauvegarde...")
        
        import os
        import zipfile
        import tempfile
        from datetime import datetime
        
        try:
            # Créer un nom de fichier avec la date
            now = datetime.now()
            backup_name = f"telefoot_backup_{now.strftime('%Y%m%d_%H%M%S')}.zip"
            
            # Créer un fichier zip temporaire
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_zip:
                zip_path = tmp_zip.name
            
            # Fichiers de configuration importants
            config_files = [
                'telefeed_redirections.json',
                'telefeed_transformations.json',
                'telefeed_filters.json',
                'telefeed_whitelist.json',
                'telefeed_blacklist.json',
                'telefeed_settings.json',
                'telefeed_sessions.json',
                'telefeed_chats.json',
                'telefeed_delay.json',
                'telefeed_message_mapping.json',
                'users.json',
                'redirections.json',
                'filters.json',
                'format.json',
                'delay.json',
                'pending_redirections.json',
                'config.py',
                'main.py',
                'telefeed_commands.py'
            ]
            
            # Créer l'archive avec les fichiers de configuration
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file in config_files:
                    if os.path.exists(file):
                        zipf.write(file, file)
            
            # Envoyer l'archive
            await event.respond(
                f"💾 **Sauvegarde TeleFoot Bot**\n\n"
                f"📅 Date: {now.strftime('%d/%m/%Y %H:%M:%S')}\n"
                f"📦 Fichiers de configuration sauvegardés",
                file=zip_path,
                attributes=[
                    ('DocumentAttributeFilename', {'file_name': backup_name})
                ]
            )
            
            # Nettoyer le fichier temporaire
            os.unlink(zip_path)
            
        except Exception as e:
            await event.respond(f"❌ Erreur lors de la sauvegarde: {str(e)}")
            print(f"Erreur backup: {e}")

    print("✅ Handlers TeleFeed enregistrés avec succès!")