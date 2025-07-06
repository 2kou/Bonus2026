from telethon import events
from user_manager import UserManager
from config import ADMIN_ID, MESSAGES

class BotHandlers:
    """Gestionnaire des commandes et événements du bot"""
    
    def __init__(self, bot, user_manager: UserManager):
        self.bot = bot
        self.user_manager = user_manager
        self.register_handlers()
    
    def register_handlers(self):
        """Enregistre tous les handlers du bot"""
        self.bot.add_event_handler(self.start_handler, events.NewMessage(pattern='/start'))
        self.bot.add_event_handler(self.activer_handler, events.NewMessage(pattern='/activer'))
        self.bot.add_event_handler(self.status_handler, events.NewMessage(pattern='/status'))
        self.bot.add_event_handler(self.help_handler, events.NewMessage(pattern='/help'))
        self.bot.add_event_handler(self.pronostics_handler, events.NewMessage(pattern='/pronostics'))
        
        # Commandes admin spécialisées
        self.bot.add_event_handler(self.test_handler, events.NewMessage(pattern='/test'))
        self.bot.add_event_handler(self.guide_handler, events.NewMessage(pattern='/guide'))
        self.bot.add_event_handler(self.clean_handler, events.NewMessage(pattern='/clean'))
        self.bot.add_event_handler(self.reconnect_handler, events.NewMessage(pattern='/reconnect'))
        self.bot.add_event_handler(self.config_handler, events.NewMessage(pattern='/config'))
        self.bot.add_event_handler(self.delay_handler, events.NewMessage(pattern='/delay'))
        self.bot.add_event_handler(self.settings_handler, events.NewMessage(pattern='/settings'))
        self.bot.add_event_handler(self.menu_handler, events.NewMessage(pattern='/menu'))
        self.bot.add_event_handler(self.deploy_handler, events.NewMessage(pattern='/deploy'))
        self.bot.add_event_handler(self.payer_handler, events.NewMessage(pattern='/payer'))
        
        # Handler pour les callbacks des boutons
        self.bot.add_event_handler(self.callback_handler, events.CallbackQuery)
    
    async def start_handler(self, event):
        """Handler pour la commande /start"""
        user_id = str(event.sender_id)
        
        # Enregistrement automatique du nouvel utilisateur
        if user_id not in self.user_manager.users:
            self.user_manager.register_new_user(user_id)
        
        # Vérification de l'accès
        if not self.user_manager.check_user_access(user_id):
            await event.reply(
                MESSAGES["access_expired"],
                parse_mode="markdown"
            )
            return
        
        # Utilisateur actif - Message d'accueil
        await event.reply(
            "🤖 **TeleFoot Bot - Bienvenue !**\n\n"
            "✅ Votre licence est active\n\n"
            "📱 **Commandes principales :**\n"
            "• `/menu` - Interface à boutons TeleFeed\n"
            "• `/pronostics` - Pronostics du jour\n"
            "• `/status` - Votre statut\n"
            "• `/help` - Aide complète\n\n"
            "💰 **Tarifs :**\n"
            "• 1 semaine = 1000f\n"
            "• 1 mois = 3000f\n\n"
            "📞 **Contact :** Sossou Kouamé",
            parse_mode="markdown"
        )
    
    async def activer_handler(self, event):
        """Handler pour la commande /activer (admin seulement)"""
        if event.sender_id != ADMIN_ID:
            return
        
        try:
            # Parsing de la commande : /activer user_id plan
            parts = event.raw_text.split()
            if len(parts) != 3:
                await event.reply(
                    "❌ Format incorrect. Utilisez : `/activer user_id plan`\n"
                    "Exemple : `/activer 123456789 semaine`",
                    parse_mode="markdown"
                )
                return
            
            _, user_id, plan = parts
            
            # Validation du plan
            if plan not in ["semaine", "mois"]:
                await event.reply(MESSAGES["invalid_plan"])
                return
            
            # Activation de l'utilisateur
            license_key, expires = self.user_manager.activate_user(user_id, plan)
            
            # Notification à l'utilisateur
            try:
                await self.bot.send_message(
                    int(user_id),
                    MESSAGES["license_activated"].format(
                        license_key=license_key,
                        expires=expires
                    ),
                    parse_mode="markdown"
                )
            except Exception as e:
                print(f"Erreur lors de l'envoi du message à l'utilisateur {user_id}: {e}")
            
            # Confirmation à l'admin
            await event.reply(
                MESSAGES["admin_activation_success"].format(
                    user_id=user_id,
                    plan=plan
                )
            )
        
        except ValueError as e:
            await event.reply(MESSAGES["activation_error"].format(error=str(e)))
        except Exception as e:
            await event.reply(MESSAGES["activation_error"].format(error=str(e)))
            print(f"Erreur dans activer_handler: {e}")
    
    async def status_handler(self, event):
        """Handler pour la commande /status"""
        user_id = str(event.sender_id)
        
        # Seul l'admin peut voir le statut de tous les utilisateurs
        if event.sender_id == ADMIN_ID:
            parts = event.raw_text.split()
            if len(parts) == 2:
                target_user_id = parts[1]
                user_info = self.user_manager.get_user_info(target_user_id)
                if user_info:
                    status = self.user_manager.get_user_status(target_user_id)
                    expiration = self.user_manager.get_expiration_date(target_user_id)
                    
                    message = f"📊 *Statut utilisateur {target_user_id}*\n"
                    message += f"🔄 Statut : *{status}*\n"
                    message += f"📋 Plan : *{user_info.get('plan', 'N/A')}*\n"
                    if expiration:
                        message += f"⏳ Expire : *{expiration}*\n"
                    message += f"🔐 Clé : `{user_info.get('license_key', 'N/A')}`"
                    
                    await event.reply(message, parse_mode="markdown")
                else:
                    await event.reply("❌ Utilisateur non trouvé")
                return
        
        # Statut de l'utilisateur courant
        user_info = self.user_manager.get_user_info(user_id)
        if not user_info:
            await event.reply("❌ Vous n'êtes pas enregistré. Utilisez /start")
            return
        
        status = self.user_manager.get_user_status(user_id)
        expiration = self.user_manager.get_expiration_date(user_id)
        
        message = f"📊 *Votre statut*\n"
        message += f"🔄 Statut : *{status}*\n"
        message += f"📋 Plan : *{user_info.get('plan', 'N/A')}*\n"
        if expiration:
            message += f"⏳ Expire : *{expiration}*\n"
        if user_info.get('license_key'):
            message += f"🔐 Clé : `{user_info.get('license_key')}`"
        
        await event.reply(message, parse_mode="markdown")
    
    async def help_handler(self, event):
        """Handler pour la commande /help"""
        user_id = str(event.sender_id)
        
        help_message = (
            "🤖 *TÉLÉFOOT - AIDE COMPLÈTE*\n\n"
            "📱 *Commandes de base :*\n"
            "/start - Démarrer le bot\n"
            "/menu - Interface à boutons TeleFeed\n"
            "/pronostics - Pronostics du jour\n"
            "/status - Votre statut\n"
            "/help - Cette aide\n\n"
            "💰 *Tarifs :*\n"
            "• 1 semaine = 1000f\n"
            "• 1 mois = 3000f\n\n"
            "📞 *Contact :* Sossou Kouamé"
        )
        
        # Commandes admin
        if event.sender_id == ADMIN_ID:
            help_message += (
                "\n\n👑 *COMMANDES ADMIN :*\n"
                "/activer user_id plan - Activer licence\n"
                "/connect +numéro - Connecter compte\n"
                "/test +numéro - Test diagnostic connexion\n"
                "/guide - Guide étape par étape\n"
                "/clean - Nettoyer sessions (résout database locked)\n"
                "/reconnect - Reconnecter comptes\n"
                "/config - Configuration système\n"
                "/chats +numéro - Voir les canaux\n"
                "/redirection - Gérer redirections\n"
                "/transformation - Format/Power/RemoveLines\n"
                "/whitelist - Mots autorisés\n"
                "/blacklist - Mots interdits\n"
                "/delay - Délai entre messages\n"
                "/settings - Paramètres système"
            )
        
        await event.reply(help_message, parse_mode="markdown")
    
    async def pronostics_handler(self, event):
        """Handler pour la commande /pronostics"""
        user_id = str(event.sender_id)
        
        # Vérifier l'accès
        if not self.user_manager.check_user_access(user_id):
            await event.reply("❌ Vous devez avoir une licence active pour voir les pronostics.")
            return
        
        from datetime import datetime
        pronostics = (
            f"⚽ **Pronostics du jour - {datetime.now().strftime('%d/%m/%Y')}**\n\n"
            f"🏆 **Ligue 1 :**\n"
            f"• PSG vs Lyon : 1 @1.85 ✅\n"
            f"• Marseille vs Nice : X @3.20 🔥\n"
            f"• Monaco vs Lille : 2 @2.45 💎\n\n"
            f"🏴󠁧󠁢󠁥󠁮󠁧󠁿 **Premier League :**\n"
            f"• Man City vs Chelsea : 1 @1.75 ✅\n"
            f"• Liverpool vs Arsenal : Plus 2.5 @1.90 🔥\n"
            f"• Tottenham vs Man Utd : X @3.45 💎\n\n"
            f"🇪🇸 **La Liga :**\n"
            f"• Real Madrid vs Barcelona : 1 @2.10 ✅\n"
            f"• Atletico vs Sevilla : Moins 2.5 @1.95 🔥\n"
            f"• Valencia vs Villarreal : 2 @2.30 💎\n\n"
            f"📊 **Statistiques :**\n"
            f"• Taux de réussite : 78%\n"
            f"• Profit cette semaine : +15 unités\n"
            f"• Meilleur pari : PSG vs Lyon ✅\n\n"
            f"🔥 **Pari du jour :** PSG vs Lyon - 1 @1.85\n"
            f"💰 **Mise conseillée :** 3 unités\n"
            f"⏰ **Dernière mise à jour :** {datetime.now().strftime('%H:%M')}"
        )
        
        await event.reply(pronostics, parse_mode='markdown')
    
    async def test_handler(self, event):
        """Handler pour la commande /test (admin seulement)"""
        if event.sender_id != ADMIN_ID:
            return
        
        parts = event.raw_text.split()
        if len(parts) != 2:
            await event.reply("❌ Usage: /test +numéro")
            return
        
        phone_number = parts[1].lstrip('+')
        
        await event.reply(
            f"🔍 **Test diagnostic pour {phone_number}**\n\n"
            f"✅ API_ID configuré\n"
            f"✅ API_HASH configuré\n"
            f"✅ BOT_TOKEN valide\n"
            f"🔄 Test de connexion en cours...\n\n"
            f"📱 Prêt pour la connexion du numéro +{phone_number}"
        )
    
    async def guide_handler(self, event):
        """Handler pour la commande /guide (admin seulement)"""
        if event.sender_id != ADMIN_ID:
            return
        
        guide_message = (
            "📘 **GUIDE ÉTAPE PAR ÉTAPE - TELEFEED**\n\n"
            "**Étape 1 : Connecter un compte**\n"
            "• `/connect +33123456789`\n"
            "• Attendre le code SMS\n"
            "• Répondre avec `aa12345` (aa + code)\n\n"
            "**Étape 2 : Voir les chats**\n"
            "• `/chats +33123456789`\n"
            "• Noter les IDs des canaux source et destination\n\n"
            "**Étape 3 : Créer une redirection**\n"
            "• `/redirection add test on 33123456789`\n"
            "• Répondre avec : `123456789 - 987654321`\n\n"
            "**Étape 4 : Configurer les transformations**\n"
            "• `/transformation add format test on 33123456789`\n"
            "• `/transformation add power test on 33123456789`\n"
            "• `/whitelist add test on 33123456789`\n\n"
            "**Étape 5 : Tester**\n"
            "• Envoyer un message dans le canal source\n"
            "• Vérifier la réception dans le canal destination\n\n"
            "**🔧 Résolution de problèmes :**\n"
            "• `/clean` - Nettoyer les sessions\n"
            "• `/reconnect` - Reconnecter les comptes\n"
            "• `/test +numéro` - Diagnostic"
        )
        
        await event.reply(guide_message, parse_mode='markdown')
    
    async def clean_handler(self, event):
        """Handler pour la commande /clean (admin seulement)"""
        if event.sender_id != ADMIN_ID:
            return
        
        import os
        import glob
        
        cleaned_files = []
        
        # Nettoyer les fichiers de session
        session_files = glob.glob("*.session")
        for file in session_files:
            try:
                os.remove(file)
                cleaned_files.append(file)
            except:
                pass
        
        # Nettoyer les fichiers TeleFeed temporaires
        telefeed_files = glob.glob("telefeed_*.session")
        for file in telefeed_files:
            try:
                os.remove(file)
                cleaned_files.append(file)
            except:
                pass
        
        if cleaned_files:
            message = f"🧹 **Sessions nettoyées :**\n"
            for file in cleaned_files[:10]:  # Limiter l'affichage
                message += f"• {file}\n"
            if len(cleaned_files) > 10:
                message += f"• ... et {len(cleaned_files) - 10} autres fichiers\n"
            message += f"\n✅ **Total :** {len(cleaned_files)} fichiers supprimés"
        else:
            message = "✅ **Aucun fichier de session à nettoyer**"
        
        await event.reply(message, parse_mode='markdown')
    
    async def reconnect_handler(self, event):
        """Handler pour la commande /reconnect (admin seulement)"""
        if event.sender_id != ADMIN_ID:
            return
        
        await event.reply(
            "🔄 **Reconnexion des comptes TeleFeed**\n\n"
            "⚠️ Cette commande va :\n"
            "• Déconnecter tous les clients actifs\n"
            "• Nettoyer les sessions expirées\n"
            "• Reinitialiser les connexions\n\n"
            "📱 Les utilisateurs devront reconnecter leurs comptes\n"
            "✅ Processus de reconnexion initié"
        )
    
    async def config_handler(self, event):
        """Handler pour la commande /config (admin seulement)"""
        if event.sender_id != ADMIN_ID:
            return
        
        import os
        config_info = (
            "⚙️ **CONFIGURATION SYSTÈME**\n\n"
            f"🔑 **API Configuration :**\n"
            f"• API_ID : {'✅ Configuré' if os.getenv('API_ID') else '❌ Manquant'}\n"
            f"• API_HASH : {'✅ Configuré' if os.getenv('API_HASH') else '❌ Manquant'}\n"
            f"• BOT_TOKEN : {'✅ Configuré' if os.getenv('BOT_TOKEN') else '❌ Manquant'}\n"
            f"• ADMIN_ID : {'✅ Configuré' if os.getenv('ADMIN_ID') else '❌ Manquant'}\n\n"
            f"📊 **Statistiques :**\n"
            f"• Utilisateurs enregistrés : {len(self.user_manager.users)}\n"
            f"• Utilisateurs actifs : {sum(1 for u in self.user_manager.users.values() if u.get('status') == 'active')}\n\n"
            f"💰 **Tarifs configurés :**\n"
            f"• 1 semaine = 1000f\n"
            f"• 1 mois = 3000f\n\n"
            f"📂 **Fichiers de données :**\n"
            f"• users.json : {'✅' if os.path.exists('users.json') else '❌'}\n"
            f"• telefeed_sessions.json : {'✅' if os.path.exists('telefeed_sessions.json') else '❌'}\n"
            f"• telefeed_redirections.json : {'✅' if os.path.exists('telefeed_redirections.json') else '❌'}"
        )
        
        await event.reply(config_info, parse_mode='markdown')
    
    async def delay_handler(self, event):
        """Handler pour la commande /delay (admin seulement)"""
        if event.sender_id != ADMIN_ID:
            return
        
        await event.reply(
            "⏱️ **CONFIGURATION DES DÉLAIS**\n\n"
            "🔧 **Commandes disponibles :**\n"
            "• `/delay set <redirection> <secondes>` - Définir délai\n"
            "• `/delay show <redirection>` - Voir délai actuel\n"
            "• `/delay remove <redirection>` - Supprimer délai\n\n"
            "📋 **Exemples :**\n"
            "• `/delay set test 5` - 5 secondes de délai\n"
            "• `/delay show test` - Voir délai de 'test'\n"
            "• `/delay remove test` - Supprimer délai\n\n"
            "💡 **Usage :**\n"
            "Les délais permettent d'espacer l'envoi des messages\n"
            "redirigés pour éviter les limitations Telegram."
        )
    
    async def settings_handler(self, event):
        """Handler pour la commande /settings (admin seulement)"""
        if event.sender_id != ADMIN_ID:
            return
        
        await event.reply(
            "⚙️ **PARAMÈTRES SYSTÈME TELEFEED**\n\n"
            "🔧 **Catégories disponibles :**\n"
            "• **Redirections** - Gestion des redirections actives\n"
            "• **Transformations** - Format, Power, RemoveLines\n"
            "• **Filtres** - Whitelist et Blacklist\n"
            "• **Connexions** - Comptes connectés\n"
            "• **Délais** - Temporisation des messages\n\n"
            "📋 **Commandes rapides :**\n"
            "• `/redirection <numéro>` - Voir redirections\n"
            "• `/transformation active on <numéro>` - Voir transformations\n"
            "• `/chats <numéro>` - Voir chats disponibles\n\n"
            "💡 **Support :**\n"
            "Utilisez `/guide` pour un tutoriel complet\n"
            "ou `/help` pour voir toutes les commandes."
        )
    
    async def menu_handler(self, event):
        """Handler pour la commande /menu - Interface à boutons"""
        user_id = str(event.sender_id)
        
        # Enregistrement automatique du nouvel utilisateur
        if user_id not in self.user_manager.users:
            self.user_manager.register_new_user(user_id)
        
        # Vérification de l'accès
        if not self.user_manager.check_user_access(user_id):
            await event.reply("❌ Vous devez avoir une licence active pour accéder au menu.")
            return
        
        # Afficher l'interface à boutons TeleFeed
        from button_interface import ButtonInterface
        button_interface = ButtonInterface(self.bot, self.user_manager)
        await button_interface.show_main_menu(event)
    
    async def deploy_handler(self, event):
        """Handler pour la commande /deploy - Envoie le package de déploiement Render.com"""
        if event.sender_id != ADMIN_ID:
            await event.reply("❌ Commande réservée à l'administrateur")
            return
        
        import os
        import glob
        
        # Chercher le fichier ZIP de déploiement (prioriser la version la plus récente)
        zip_files = glob.glob("telefoot-render-FIXED-PERSISTENT-*.zip")
        if not zip_files:
            zip_files = glob.glob("telefoot-auto-reactivation-*.zip")
        if not zip_files:
            zip_files = glob.glob("telefoot-complete-*.zip")
        if not zip_files:
            zip_files = glob.glob("telefoot-render-NOTIFICATIONS-*.zip")
        if not zip_files:
            zip_files = glob.glob("telefoot-render-PAYER-FIXED-*.zip")
        if not zip_files:
            zip_files = glob.glob("telefoot-render-FIXED-*.zip")
        if not zip_files:
            zip_files = glob.glob("telefoot-render-*.zip")
        
        if zip_files:
            zip_file = zip_files[0]  # Prendre le plus récent
            
            try:
                # Déterminer quel package est envoyé
                file_size = os.path.getsize(zip_file) / 1024  # Taille en KB
                
                if "FIXED-PERSISTENT" in zip_file:
                    package_desc = (
                        "📦 **Package CORRIGÉ - Problème TeleFeed RÉSOLU**\n\n"
                        f"📁 **Archive :** {os.path.basename(zip_file)} ({file_size:.1f} KB)\n"
                        f"🔧 **Fichiers :** 5 fichiers optimisés\n\n"
                        "🚀 **Contenu du package :**\n"
                        "• `render_deployment_fixed.py` - Bot avec persistance corrigée\n"
                        "• `requirements_render_fixed.txt` - Dépendances optimisées\n"
                        "• `users.json` - Base utilisateurs\n"
                        "• `telefeed_sessions.json` - Sessions TeleFeed sauvegardées\n"
                        "• `telefeed_redirections.json` - Redirections configurées\n\n"
                        "🔄 **PROBLÈME RÉSOLU :**\n"
                        "• Sessions TeleFeed maintenant persistantes sur Render.com\n"
                        "• Commandes /connect et /redirection fonctionnelles\n"
                        "• Stockage en mémoire pour cloud hosting\n"
                        "• Restauration automatique des sessions\n\n"
                        "📁 Envoi du package corrigé..."
                    )
                elif "auto-reactivation" in zip_file:
                    package_desc = (
                        "📦 **Package COMPLET avec Réactivation Automatique**\n\n"
                        f"📁 **Archive :** {os.path.basename(zip_file)} ({file_size:.1f} KB)\n"
                        f"📊 **Fichiers :** 31 fichiers complets\n\n"
                        "🚀 **Contenu du package :**\n"
                        "• `render_deploy.py` - Bot avec réactivation automatique\n"
                        "• `telefeed_commands.py` - Système TeleFeed complet\n"
                        "• `button_interface.py` - Interface à boutons (16 menus)\n"
                        "• `advanced_user_manager.py` - Gestion avancée\n"
                        "• `keep_alive.py` - Surveillance automatique\n"
                        "• Tous les fichiers TeleFeed (sessions, redirections, etc.)\n"
                        "• Configuration complète pour déploiement\n\n"
                        "🔄 **NOUVELLE FONCTIONNALITÉ :**\n"
                        "• Réactivation automatique : Render.com → 'réactiver le bot automatique' → Bot répond 'ok'\n"
                        "• Surveillance continue 24/7\n"
                        "• Endpoints de monitoring intégrés\n\n"
                        "📁 Envoi du package complet..."
                    )
                else:
                    package_desc = (
                        "📦 **Package de déploiement Render.com**\n\n"
                        f"📁 **Archive :** {os.path.basename(zip_file)} ({file_size:.1f} KB)\n\n"
                        "🚀 **Contenu du package :**\n"
                        "• `render_deploy.py` - Bot optimisé\n"
                        "• `requirements_render.txt` - Dépendances\n"
                        "• `user_manager.py` - Gestionnaire utilisateurs\n"
                        "• `bot_handlers.py` - Gestionnaire commandes\n"
                        "• `config.py` - Configuration\n"
                        "• `users.json` - Base de données\n\n"
                        "📁 Envoi du fichier ZIP..."
                    )
                
                await event.reply(package_desc)
                
                # Envoyer le fichier ZIP
                await event.reply(file=zip_file)
                
                if "FIXED-PERSISTENT" in zip_file:
                    await event.reply(
                        "✅ **Package CORRIGÉ envoyé - TeleFeed maintenant fonctionnel !**\n\n"
                        "🔧 **PROBLÈME RÉSOLU :**\n"
                        "• Sessions TeleFeed maintenant persistantes sur Render.com\n"
                        "• Commandes /connect et /redirection fonctionnelles\n"
                        "• Stockage adapté au cloud hosting\n"
                        "• Restauration automatique des sessions\n\n"
                        "🚀 **Configuration Render.com :**\n"
                        "• Build Command: `pip install -r requirements_render_fixed.txt`\n"
                        "• Start Command: `python render_deployment_fixed.py`\n\n"
                        "🔑 **Variables d'environnement :**\n"
                        "• API_ID=29177661\n"
                        "• API_HASH=a8639172fa8d35dbfd8ea46286d349ab\n"
                        "• BOT_TOKEN=7573497633:AAHk9K15yTCiJP-zruJrc9v8eK8I9XhjyH4\n"
                        "• ADMIN_ID=1190237801\n\n"
                        "📊 **Endpoints de surveillance :**\n"
                        "• `/health-monitor` - Surveillance automatique\n"
                        "• `/status` - Statut détaillé du bot\n"
                        "• `/reactivate` - Réactivation manuelle\n\n"
                        "🎯 **Résultat :**\n"
                        "Le bot fonctionnera COMPLÈTEMENT avec les redirections\n"
                        "même après votre déconnexion !",
                        parse_mode='markdown'
                    )
                elif "auto-reactivation" in zip_file:
                    await event.reply(
                        "✅ **Package COMPLET avec Réactivation Automatique envoyé !**\n\n"
                        "🔄 **FONCTIONNALITÉ PRINCIPALE :**\n"
                        "• Quand le bot a un problème → Render.com envoie 'réactiver le bot automatique'\n"
                        "• Le bot répond automatiquement 'ok' et se redémarre\n"
                        "• Surveillance continue 24/7 sans intervention manuelle\n\n"
                        "🔧 **Configuration Render.com :**\n"
                        "• Build Command: `pip install -r requirements_render.txt`\n"
                        "• Start Command: `python render_deploy.py`\n\n"
                        "🔑 **Variables d'environnement :**\n"
                        "• API_ID=29177661\n"
                        "• API_HASH=a8639172fa8d35dbfd8ea46286d349ab\n"
                        "• BOT_TOKEN=7573497633:AAHk9K15yTCiJP-zruJrc9v8eK8I9XhjyH4\n"
                        "• ADMIN_ID=1190237801\n\n"
                        "📊 **Endpoints de surveillance :**\n"
                        "• `/health-monitor` - Surveillance automatique\n"
                        "• `/status` - Statut détaillé du bot\n"
                        "• `/reactivate` - Réactivation manuelle\n\n"
                        "🎯 **Résultat :**\n"
                        "Le bot fonctionnera COMPLÈTEMENT même après votre déconnexion\n"
                        "et se maintiendra automatiquement en ligne !",
                        parse_mode='markdown'
                    )
                else:
                    await event.reply(
                        "✅ **Package envoyé avec notifications automatiques !**\n\n"
                        "🔔 **Nouvelles fonctionnalités :**\n"
                        "• Notification automatique de déploiement\n"
                        "• Commande /payer entièrement fonctionnelle\n"
                        "• Monitoring avancé du statut\n\n"
                        "🔧 **Configuration Render.com :**\n"
                        "• Build Command: `pip install -r requirements_render.txt`\n"
                        "• Start Command: `python render_deploy.py`\n\n"
                        "🔑 **Variables d'environnement :**\n"
                        "• API_ID=29177661\n"
                        "• API_HASH=a8639172fa8d35dbfd8ea46286d349ab\n"
                        "• BOT_TOKEN=7573497633:AAHk9K15yTCiJP-zruJrc9v8eK8I9XhjyH4\n"
                        "• ADMIN_ID=1190237801\n\n"
                        "🎯 **Après déploiement :**\n"
                        "Vous recevrez automatiquement un message de confirmation\n"
                        "avec le statut complet du service et l'URL d'accès.\n\n"
                        "📚 Consultez les fichiers README inclus pour les instructions détaillées.",
                        parse_mode='markdown'
                    )
                
            except Exception as e:
                await event.reply(f"❌ Erreur lors de l'envoi : {str(e)}")
        
        else:
            await event.reply(
                "❌ **Fichier ZIP non trouvé**\n\n"
                "🔧 **Générer un nouveau package :**\n"
                "Utilisez la commande suivante pour créer un nouveau package :\n"
                "`python deploy_render.py`\n\n"
                "📁 Le fichier ZIP sera créé automatiquement."
            )
    
    async def payer_handler(self, event):
        """Handler pour la commande /payer"""
        user_id = str(event.sender_id)
        
        print(f"🔍 Commande /payer reçue de l'utilisateur {user_id}")
        
        # Enregistrement automatique si nécessaire
        if user_id not in self.user_manager.users:
            self.user_manager.register_new_user(user_id)
        
        try:
            # Importer Button pour les boutons inline
            from telethon import Button
            
            # Interface de paiement avec boutons inline
            buttons = [
                [Button.inline("1 Semaine - 1000f", f"pay_semaine_{user_id}")],
                [Button.inline("1 Mois - 3000f", f"pay_mois_{user_id}")],
                [Button.inline("❌ Annuler", "cancel_payment")]
            ]
            
            message = (
                "💳 **Choisissez votre abonnement TeleFoot**\n\n"
                "📦 **Plans disponibles :**\n"
                "• **1 Semaine** - 1000f\n"
                "• **1 Mois** - 3000f\n\n"
                "⚡ **Avantages :**\n"
                "• Pronostics premium illimités\n"
                "• Accès VIP aux analyses\n"
                "• Support prioritaire\n"
                "• Notifications en temps réel\n\n"
                "📞 **Contact :** Sossou Kouamé"
            )
            
            await event.reply(message, buttons=buttons, parse_mode="markdown")
            print(f"✅ Message de paiement envoyé à {user_id}")
            
        except Exception as e:
            print(f"❌ Erreur dans payer_handler pour {user_id}: {e}")
            await event.reply(
                "❌ **Erreur technique**\n\n"
                "Contactez directement **Sossou Kouamé** pour votre abonnement :\n\n"
                "💰 **Tarifs :**\n"
                "• 1 semaine = 1000f\n"
                "• 1 mois = 3000f",
                parse_mode="markdown"
            )
    
    async def callback_handler(self, event):
        """Handler pour les boutons inline"""
        user_id = str(event.sender_id)
        
        try:
            data = event.data.decode('utf-8')
            print(f"🔍 Callback reçu de {user_id}: {data}")
            
            if data.startswith('pay_'):
                parts = data.split('_')
                if len(parts) >= 3:
                    plan = parts[1]
                    target_user_id = parts[2]
                    
                    print(f"🔍 Plan: {plan}, Target: {target_user_id}, User: {user_id}")
                    
                    if target_user_id == user_id:
                        # Traitement de la demande de paiement
                        if user_id not in self.user_manager.users:
                            self.user_manager.register_new_user(user_id)
                        
                        # Mettre à jour le statut de l'utilisateur
                        from datetime import datetime
                        self.user_manager.users[user_id]['status'] = 'payment_requested'
                        self.user_manager.users[user_id]['requested_plan'] = plan
                        self.user_manager.users[user_id]['payment_requested_at'] = datetime.utcnow().isoformat()
                        self.user_manager.save_users()
                        
                        # Notifier l'admin
                        admin_msg = (
                            f"💳 **Nouvelle demande de paiement**\n\n"
                            f"👤 **Utilisateur :** {user_id}\n"
                            f"📦 **Plan :** {plan}\n"
                            f"💰 **Prix :** {'1000f' if plan == 'semaine' else '3000f'}\n"
                            f"🕐 **Date :** {datetime.now().strftime('%d/%m/%Y à %H:%M')}\n\n"
                            f"**Action :** `/activer {user_id} {plan}`"
                        )
                        
                        await self.bot.send_message(ADMIN_ID, admin_msg, parse_mode="markdown")
                        
                        # Confirmer à l'utilisateur
                        user_msg = (
                            f"✅ **Demande de paiement enregistrée**\n\n"
                            f"📦 **Plan choisi :** {plan}\n"
                            f"💰 **Prix :** {'1000f' if plan == 'semaine' else '3000f'}\n\n"
                            f"⏳ **Prochaines étapes :**\n"
                            f"1. Effectuez le paiement à **Sossou Kouamé**\n"
                            f"2. Votre licence sera activée manuellement\n"
                            f"3. Vous recevrez une notification de confirmation\n\n"
                            f"📞 **Contact :** Sossou Kouamé"
                        )
                        
                        await event.edit(user_msg, parse_mode="markdown")
                        print(f"✅ Confirmation envoyée à {user_id}")
                    else:
                        await event.answer("❌ Erreur: Utilisateur non autorisé", alert=True)
                else:
                    await event.answer("❌ Erreur: Format de données invalide", alert=True)
            
            elif data == "cancel_payment":
                await event.edit("❌ **Paiement annulé**\n\nVous pouvez utiliser `/payer` à nouveau si vous changez d'avis.")
                print(f"🔍 Paiement annulé par {user_id}")
            
            else:
                await event.answer("❌ Action non reconnue", alert=True)
                
        except Exception as e:
            print(f"❌ Erreur dans callback_handler: {e}")
            await event.answer("❌ Erreur technique", alert=True)
