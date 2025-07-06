import os

# Configuration du bot Telegram
API_ID = int(os.getenv('API_ID', '29177661'))
API_HASH = os.getenv('API_HASH', 'a8639172fa8d35dbfd8ea46286d349ab')
BOT_TOKEN = os.getenv('BOT_TOKEN', '7573497633:AAHk9K15yTCiJP-zruJrc9v8eK8I9XhjyH4')
ADMIN_ID = int(os.getenv('ADMIN_ID', '1190237801'))

# Fichiers de données
USERS_FILE = "users.json"

# Plans et tarifs
PLANS = {
    "semaine": {
        "duration_days": 7,
        "price": "1000f"
    },
    "mois": {
        "duration_days": 30,
        "price": "3000f"
    }
}

# Messages
MESSAGES = {
    "welcome_active": "✅ *Bienvenue ! Votre accès est actif.*",
    "access_expired": (
        "⛔ *Accès expiré ou non activé.*\n"
        "Contactez *Sossou Kouamé* pour activer votre licence.\n"
        "💵 *1 semaine = 1000f | 1 mois = 3000f*"
    ),
    "license_activated": (
        "🎉 *Votre licence a été activée*\n"
        "🔐 Clé : `{license_key}`\n"
        "⏳ Expire : *{expires}*"
    ),
    "admin_activation_success": "✅ Utilisateur {user_id} activé pour 1 {plan}",
    "invalid_plan": "❌ Plan invalide. Choisissez `semaine` ou `mois`",
    "activation_error": "❌ Erreur : {error}"
}
