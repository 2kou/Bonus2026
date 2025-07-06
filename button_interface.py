"""
Interface à boutons pour TeleFeed Bot
Basé sur les captures d'écran et la documentation fournie
"""

from telethon import Button, events
from telethon.tl.types import KeyboardButtonCallback
import json

class ButtonInterface:
    """Gestionnaire des interfaces à boutons pour TeleFeed"""
    
    def __init__(self, bot, user_manager):
        self.bot = bot
        self.user_manager = user_manager
        self.register_button_handlers()
    
    def register_button_handlers(self):
        """Enregistre tous les handlers de boutons"""
        # Handler pour tous les callbacks
        self.bot.add_event_handler(self.button_callback_handler, events.CallbackQuery)
    
    async def button_callback_handler(self, event):
        """Handler principal pour tous les callbacks de boutons"""
        try:
            data = event.data.decode('utf-8')
            user_id = str(event.sender_id)
            
            # Vérifier l'accès pour certaines fonctions
            if not self.user_manager.check_user_access(user_id) and not data.startswith('start_'):
                await event.answer("❌ Licence requise", alert=True)
                return
            
            # Router vers les handlers appropriés
            if data == 'main_menu':
                await self.show_main_menu(event)
            elif data == 'connect_menu':
                await self.show_connect_menu(event)
            elif data == 'getting_started':
                await self.show_getting_started(event)
            elif data == 'redirection_menu':
                await self.show_redirection_menu(event)
            elif data == 'transformation_menu':
                await self.show_transformation_menu(event)
            elif data == 'whitelist_menu':
                await self.show_whitelist_menu(event)
            elif data == 'blacklist_menu':
                await self.show_blacklist_menu(event)
            elif data == 'delay_menu':
                await self.show_delay_menu(event)
            elif data == 'select_users_menu':
                await self.show_select_users_menu(event)
            elif data == 'scheduler_menu':
                await self.show_scheduler_menu(event)
            elif data == 'watermark_menu':
                await self.show_watermark_menu(event)
            elif data == 'chats_menu':
                await self.show_chats_menu(event)
            elif data == 'clone_menu':
                await self.show_clone_menu(event)
            elif data == 'settings_menu':
                await self.show_settings_menu(event)
            elif data == 'faq_menu':
                await self.show_faq_menu(event)
            elif data == 'contact_support':
                await self.show_contact_support(event)
            elif data.startswith('phone_'):
                await self.handle_phone_selection(event, data)
            elif data.startswith('redirection_'):
                await self.handle_redirection_action(event, data)
            elif data.startswith('transformation_'):
                await self.handle_transformation_action(event, data)
            else:
                await event.answer("Action non reconnue", alert=True)
                
        except Exception as e:
            await event.answer(f"Erreur: {str(e)}", alert=True)
    
    async def show_main_menu(self, event):
        """Affiche le menu principal avec boutons"""
        buttons = [
            [Button.inline("📱 Connect", b"connect_menu")],
            [Button.inline("📚 Getting Started Guide", b"getting_started")],
            [
                Button.inline("🔄 Redirection", b"redirection_menu"),
                Button.inline("🔧 Transformation", b"transformation_menu")
            ],
            [
                Button.inline("✅ Whitelist", b"whitelist_menu"),
                Button.inline("❌ Blacklist", b"blacklist_menu")
            ],
            [
                Button.inline("⏰ Delay", b"delay_menu"),
                Button.inline("👥 Select Users", b"select_users_menu")
            ],
            [
                Button.inline("📅 Scheduler", b"scheduler_menu"),
                Button.inline("🖼️ Watermark", b"watermark_menu")
            ],
            [
                Button.inline("💬 Chats", b"chats_menu"),
                Button.inline("📋 Clone", b"clone_menu")
            ],
            [
                Button.inline("💰 Earn Money", b"earn_money"),
                Button.inline("⭐ Buy Premium", b"buy_premium")
            ],
            [
                Button.inline("❓ FAQ", b"faq_menu"),
                Button.inline("🆘 Contact Support", b"contact_support")
            ],
            [Button.inline("⚙️ Settings »", b"settings_menu")]
        ]
        
        message = (
            "📱 **TeleFeed: Auto Forward Bot**\n\n"
            "👆 Click here 👉 to read the documentation\n"
            "👆 Click here 👉 to watch youtube tutorial\n\n"
            "❓ If you have any issues or questions about this bot, contact us"
        )
        
        # Toujours envoyer un nouveau message pour éviter les erreurs
        await event.reply(message, buttons=buttons, parse_mode='markdown')
    
    async def show_connect_menu(self, event):
        """Affiche le menu de connexion"""
        buttons = [
            [Button.inline("🔙 Retour", b"main_menu")]
        ]
        
        message = (
            "📱 **Connect Help Menu**\n\n"
            "Use it to connect your account with TeleFeed. You will need at least one connected account with TeleFeed to use other commands such as /transformation /whitelist /selectusers etc.\n\n"
            "**Command Arguments**\n"
            "`/connect PHONE_NUMBER`\n\n"
            "**Connect with 2759205517**\n"
            "`/connect 2759205517`\n"
            "`/connect 15417543010`\n"
            "`/connect 447890123456`\n"
            "`/connect 918477812345`\n\n"
            "Remember to add **international prefix** to your phone number before using TeleFeed. You can find every country prefix code by clicking here"
        )
        
        await event.edit(message, buttons=buttons, parse_mode='markdown')
    
    async def show_getting_started(self, event):
        """Affiche le guide de démarrage"""
        buttons = [
            [Button.inline("🔙 Retour", b"main_menu")]
        ]
        
        message = (
            "📚 **GUIDE DE DÉMARRAGE TELEFEED**\n\n"
            "**Étape 1: Connecter un compte**\n"
            "• Cliquez sur Connect\n"
            "• Entrez votre numéro avec préfixe international\n"
            "• Confirmez avec le code reçu par SMS\n\n"
            "**Étape 2: Configurer une redirection**\n"
            "• Cliquez sur Redirection\n"
            "• Créez une nouvelle redirection\n"
            "• Sélectionnez source et destination\n\n"
            "**Étape 3: Personnaliser (optionnel)**\n"
            "• Transformation: Modifier les messages\n"
            "• Whitelist/Blacklist: Filtrer le contenu\n"
            "• Delay: Espacer les messages\n\n"
            "**Étape 4: Tester**\n"
            "• Envoyez un message test\n"
            "• Vérifiez la redirection\n"
            "• Ajustez si nécessaire"
        )
        
        await event.edit(message, buttons=buttons, parse_mode='markdown')
    
    async def show_redirection_menu(self, event):
        """Affiche le menu de redirection"""
        # Récupérer les numéros connectés
        connected_phones = self.get_connected_phones()
        
        buttons = []
        for phone in connected_phones:
            buttons.append([Button.inline(f"📱 {phone}", f"phone_{phone}".encode())])
        
        buttons.append([Button.inline("🔙 Retour", b"main_menu")])
        
        message = (
            "🔄 **Redirection Help Menu**\n\n"
            "Command used to setup redirections. You need to use the /chats commands to get the channels/groups or user id's to use with this command.\n\n"
            "**Command Arguments**\n"
            "`/redirection ACTION REDIRECTIONID on PHONE_NUMBER`\n"
            "`/redirection PHONE_NUMBER`\n\n"
            "**Sélectionnez un numéro connecté:**"
        )
        
        await event.edit(message, buttons=buttons, parse_mode='markdown')
    
    async def show_transformation_menu(self, event):
        """Affiche le menu de transformation"""
        buttons = [
            [Button.inline("📝 Format", b"transformation_format")],
            [Button.inline("💪 Power", b"transformation_power")],
            [Button.inline("🗑️ Remove Lines", b"transformation_remove_lines")],
            [Button.inline("🔙 Retour", b"main_menu")]
        ]
        
        message = (
            "🔧 **Transformation Menu**\n\n"
            "This command is used for setting up transformations for your redirections on TeleFeed.\n\n"
            "**Available Features:**\n"
            "• **Format**: Change message format (header/footer)\n"
            "• **Power**: Advanced text replacement with regex\n"
            "• **Remove Lines**: Remove lines containing keywords\n\n"
            "Choisissez une option:"
        )
        
        await event.edit(message, buttons=buttons, parse_mode='markdown')
    
    async def show_whitelist_menu(self, event):
        """Affiche le menu whitelist"""
        buttons = [
            [Button.inline("➕ Ajouter Whitelist", b"whitelist_add")],
            [Button.inline("📋 Voir Active", b"whitelist_active")],
            [Button.inline("🗑️ Supprimer", b"whitelist_remove")],
            [Button.inline("🔙 Retour", b"main_menu")]
        ]
        
        message = (
            "✅ **Whitelist Menu**\n\n"
            "You can set a list of words or regex patterns that tell the bot to process message you receive from source channel only if it has at least one of the whitelisted word or regex pattern match.\n\n"
            "**Commands:**\n"
            "• Add: Create new whitelist\n"
            "• Active: Show current whitelist\n"
            "• Remove: Delete whitelist\n\n"
            "⚠️ **Important**: Using whitelist incorrectly can stop redirections from working."
        )
        
        await event.edit(message, buttons=buttons, parse_mode='markdown')
    
    async def show_blacklist_menu(self, event):
        """Affiche le menu blacklist"""
        buttons = [
            [Button.inline("➕ Ajouter Blacklist", b"blacklist_add")],
            [Button.inline("📋 Voir Active", b"blacklist_active")],
            [Button.inline("🗑️ Supprimer", b"blacklist_remove")],
            [Button.inline("🔙 Retour", b"main_menu")]
        ]
        
        message = (
            "❌ **Blacklist Menu**\n\n"
            "You can set a list of words or regex patterns which tells the bot that if the message received from source channel has any of the blacklisted words or regex pattern match the bot should ignore that message.\n\n"
            "**Commands:**\n"
            "• Add: Create new blacklist\n"
            "• Active: Show current blacklist\n"
            "• Remove: Delete blacklist\n\n"
            "⚠️ **Important**: Using blacklist incorrectly can stop redirections from working."
        )
        
        await event.edit(message, buttons=buttons, parse_mode='markdown')
    
    async def show_delay_menu(self, event):
        """Affiche le menu de délai"""
        buttons = [
            [Button.inline("⏰ Configurer Délai", b"delay_set")],
            [Button.inline("📋 Voir Délais", b"delay_show")],
            [Button.inline("🗑️ Supprimer Délai", b"delay_remove")],
            [Button.inline("🔙 Retour", b"main_menu")]
        ]
        
        message = (
            "⏰ **Delay Menu**\n\n"
            "Control the timing of message forwarding to avoid Telegram rate limits.\n\n"
            "**Options:**\n"
            "• Set: Configure delay for redirection\n"
            "• Show: View current delays\n"
            "• Remove: Delete delay setting\n\n"
            "💡 **Tip**: Use delays to spread out message forwarding and avoid flooding."
        )
        
        await event.edit(message, buttons=buttons, parse_mode='markdown')
    
    async def show_select_users_menu(self, event):
        """Affiche le menu de sélection d'utilisateurs"""
        buttons = [
            [Button.inline("👥 Gérer Utilisateurs", b"select_users_manage")],
            [Button.inline("📋 Voir Sélection", b"select_users_show")],
            [Button.inline("🔙 Retour", b"main_menu")]
        ]
        
        message = (
            "👥 **Select Users Menu**\n\n"
            "Control which users can trigger your redirections.\n\n"
            "**Features:**\n"
            "• Manage: Add/remove specific users\n"
            "• Show: View current user selection\n\n"
            "💡 **Use case**: Limit redirections to specific users only."
        )
        
        await event.edit(message, buttons=buttons, parse_mode='markdown')
    
    async def show_scheduler_menu(self, event):
        """Affiche le menu du programmateur"""
        buttons = [
            [Button.inline("📅 Programmer", b"scheduler_set")],
            [Button.inline("📋 Voir Programmations", b"scheduler_show")],
            [Button.inline("🔙 Retour", b"main_menu")]
        ]
        
        message = (
            "📅 **Scheduler Menu**\n\n"
            "Schedule your redirections to work at specific times.\n\n"
            "**Options:**\n"
            "• Set: Create new schedule\n"
            "• Show: View active schedules\n\n"
            "💡 **Example**: Only redirect messages during business hours."
        )
        
        await event.edit(message, buttons=buttons, parse_mode='markdown')
    
    async def show_watermark_menu(self, event):
        """Affiche le menu du watermark"""
        buttons = [
            [Button.inline("🖼️ Ajouter Watermark", b"watermark_add")],
            [Button.inline("📋 Voir Watermarks", b"watermark_show")],
            [Button.inline("🔙 Retour", b"main_menu")]
        ]
        
        message = (
            "🖼️ **Watermark Menu**\n\n"
            "Add watermarks to images and videos in your redirections.\n\n"
            "**Features:**\n"
            "• Add: Create watermark settings\n"
            "• Show: View current watermarks\n\n"
            "💡 **Tip**: Protect your content with custom watermarks."
        )
        
        await event.edit(message, buttons=buttons, parse_mode='markdown')
    
    async def show_chats_menu(self, event):
        """Affiche le menu des chats"""
        buttons = [
            [Button.inline("💬 Voir Chats", b"chats_show")],
            [Button.inline("🔍 Filtrer", b"chats_filter")],
            [Button.inline("🔙 Retour", b"main_menu")]
        ]
        
        message = (
            "💬 **Chats Menu**\n\n"
            "View and manage your connected chats.\n\n"
            "**Options:**\n"
            "• Show: Display all available chats\n"
            "• Filter: Filter chats by type\n\n"
            "💡 **Tip**: Use chat IDs in redirection commands."
        )
        
        await event.edit(message, buttons=buttons, parse_mode='markdown')
    
    async def show_clone_menu(self, event):
        """Affiche le menu de clonage"""
        buttons = [
            [Button.inline("📋 Cloner Messages", b"clone_messages")],
            [Button.inline("📊 Statut Clone", b"clone_status")],
            [Button.inline("🔙 Retour", b"main_menu")]
        ]
        
        message = (
            "📋 **Clone Menu**\n\n"
            "Clone messages from one chat to another.\n\n"
            "**Features:**\n"
            "• Clone: Start message cloning\n"
            "• Status: View clone progress\n\n"
            "💡 **Use case**: Copy chat history to new channels."
        )
        
        await event.edit(message, buttons=buttons, parse_mode='markdown')
    
    async def show_settings_menu(self, event):
        """Affiche le menu des paramètres"""
        buttons = [
            [Button.inline("🔧 Paramètres Redirection", b"settings_redirection")],
            [Button.inline("🎛️ Filtres", b"settings_filters")],
            [Button.inline("🧹 Nettoyeur", b"settings_cleaner")],
            [Button.inline("🔙 Retour", b"main_menu")]
        ]
        
        message = (
            "⚙️ **Settings Menu**\n\n"
            "Configure advanced settings for your redirections.\n\n"
            "**Categories:**\n"
            "• Redirection: Reply, Edit, Delete settings\n"
            "• Filters: Message type filtering\n"
            "• Cleaner: Content removal settings\n\n"
            "💡 **Tip**: Fine-tune your redirection behavior."
        )
        
        await event.edit(message, buttons=buttons, parse_mode='markdown')
    
    async def show_faq_menu(self, event):
        """Affiche le menu FAQ"""
        buttons = [
            [Button.inline("❓ Questions Fréquentes", b"faq_questions")],
            [Button.inline("🔧 Résolution de Problèmes", b"faq_troubleshooting")],
            [Button.inline("🔙 Retour", b"main_menu")]
        ]
        
        message = (
            "❓ **FAQ Menu**\n\n"
            "Find answers to common questions about TeleFeed.\n\n"
            "**Sections:**\n"
            "• Questions: Common TeleFeed questions\n"
            "• Troubleshooting: Fix common issues\n\n"
            "💡 **Tip**: Check here before contacting support."
        )
        
        await event.edit(message, buttons=buttons, parse_mode='markdown')
    
    async def show_contact_support(self, event):
        """Affiche les informations de contact"""
        buttons = [
            [Button.inline("🔙 Retour", b"main_menu")]
        ]
        
        message = (
            "🆘 **Contact Support**\n\n"
            "Need help with TeleFeed? Contact us:\n\n"
            "📧 **Email**: support@telefeed.com\n"
            "💬 **Telegram**: @TeleFeedSupport\n"
            "🌐 **Website**: https://telefeed.com\n\n"
            "**For faster support, please include:**\n"
            "• Your phone number\n"
            "• Description of the issue\n"
            "• Screenshots if applicable\n\n"
            "⏰ **Response time**: Usually within 24 hours"
        )
        
        await event.edit(message, buttons=buttons, parse_mode='markdown')
    
    def get_connected_phones(self):
        """Récupère la liste des numéros connectés"""
        # Placeholder - à implémenter selon votre logique
        try:
            with open('telefeed_sessions.json', 'r') as f:
                sessions = json.load(f)
                return list(sessions.keys())
        except:
            return ["2759205517", "15417543010"]  # Exemples
    
    async def handle_phone_selection(self, event, data):
        """Gère la sélection d'un numéro de téléphone"""
        phone = data.replace('phone_', '')
        
        buttons = [
            [Button.inline(f"➕ Ajouter Redirection", f"redirection_add_{phone}".encode())],
            [Button.inline(f"📋 Voir Redirections", f"redirection_list_{phone}".encode())],
            [Button.inline(f"🔄 Modifier Redirection", f"redirection_change_{phone}".encode())],
            [Button.inline(f"🗑️ Supprimer Redirection", f"redirection_remove_{phone}".encode())],
            [Button.inline("🔙 Retour", b"redirection_menu")]
        ]
        
        message = (
            f"🔄 **Redirection - {phone}**\n\n"
            f"**Add, Change or Remove group1 redirections**\n\n"
            f"`/redirection add group1 on {phone}`\n"
            f"`/redirection change group1 on {phone}`\n"
            f"`/redirection remove group1 on {phone}`\n\n"
            f"Sélectionnez une action:"
        )
        
        await event.edit(message, buttons=buttons, parse_mode='markdown')
    
    async def handle_redirection_action(self, event, data):
        """Gère les actions de redirection"""
        parts = data.split('_')
        action = parts[1]
        phone = parts[2] if len(parts) > 2 else None
        
        if action == 'add':
            message = (
                f"➕ **Ajouter Redirection - {phone}**\n\n"
                f"**Syntax Variables**\n"
                f"`SOURCE - DESTINATION`\n\n"
                f"**Examples:**\n"
                f"One to One: `708415014 - 642797040`\n"
                f"Many to One: `53469647,708415014 - 20801978`\n"
                f"One to Many: `20801978 - 53469647,708415014`\n\n"
                f"Envoyez maintenant la configuration source-destination:"
            )
        elif action == 'list':
            message = (
                f"📋 **Redirections Actives - {phone}**\n\n"
                f"• group1: 708415014 → 642797040\n"
                f"• stats: 2370795564 → 2646551216\n\n"
                f"Total: 2 redirections actives"
            )
        else:
            message = f"🔄 **{action.title()} Redirection - {phone}**\n\nFonctionnalité en cours de développement..."
        
        buttons = [
            [Button.inline("🔙 Retour", f"phone_{phone}".encode())]
        ]
        
        await event.edit(message, buttons=buttons, parse_mode='markdown')
    
    async def handle_transformation_action(self, event, data):
        """Gère les actions de transformation"""
        action = data.replace('transformation_', '')
        
        if action == 'format':
            message = (
                "📝 **Format Feature**\n\n"
                "This feature is used to change the output format for the message. "
                "You can add text on the message (header or footer etc).\n\n"
                "**Keywords Supported:**\n"
                "• `[[Message.Text]]` - Source message text\n"
                "• `[[Message.Username]]` - User username\n"
                "• `[[Message.Group]]` - Source group name\n"
                "• `[[Message.First_Name]]` - User first name\n\n"
                "**Example:**\n"
                "Header: `📢 NEWS FLASH`\n"
                "Content: `[[Message.Text]]`\n"
                "Footer: `🔔 Subscribe for more`"
            )
        elif action == 'power':
            message = (
                "💪 **Power Feature**\n\n"
                "This is one of the most powerful features. It is used to remove "
                "and change keywords from the message. You can use regex.\n\n"
                "**Simple Syntax:**\n"
                "• `\"red\",\"blue\"` - Change red to blue\n"
                "• `\"bad\",\"\"` - Remove word 'bad'\n\n"
                "**Advanced Regex:**\n"
                "• `(@|www|https?)\\S+=@tg_feedbot` - Replace URLs\n"
                "• `gr[ae]y=red` - Change gray/grey to red\n\n"
                "**URL Affiliate:**\n"
                "• `url:tag=client1` - Change URL parameters"
            )
        elif action == 'remove_lines':
            message = (
                "🗑️ **Remove Lines Feature**\n\n"
                "This feature is used to remove lines from the message. "
                "You will use keywords to check message lines.\n\n"
                "**How it works:**\n"
                "If a keyword is found on the line, TeleFeed will remove that entire line.\n\n"
                "**Input Syntax:**\n"
                "• `good, bad` - Remove lines with 'good' AND 'bad'\n"
                "• `apple` - Remove lines with 'apple' only\n\n"
                "**Important:** This removes the whole line, not just the keyword."
            )
        else:
            message = "🔧 **Transformation Feature**\n\nSélectionnez une option dans le menu."
        
        buttons = [
            [Button.inline("🔙 Retour", b"transformation_menu")]
        ]
        
        await event.edit(message, buttons=buttons, parse_mode='markdown')