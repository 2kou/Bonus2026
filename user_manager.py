import json
import datetime
import uuid
from typing import Dict, Any, Tuple, Optional
from config import USERS_FILE, PLANS

class UserManager:
    """Gestionnaire des utilisateurs et licences"""
    
    def __init__(self):
        self.users = self.load_users()
    
    def load_users(self) -> Dict[str, Any]:
        """Charge les utilisateurs depuis le fichier JSON"""
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            print(f"Erreur de lecture du fichier {USERS_FILE}, création d'un nouveau fichier")
            return {}
    
    def save_users(self) -> None:
        """Sauvegarde les utilisateurs dans le fichier JSON"""
        try:
            with open(USERS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde : {e}")
    
    def register_new_user(self, user_id: str) -> Dict[str, Any]:
        """Enregistre un nouvel utilisateur avec statut d'attente"""
        user_data = {
            "status": "waiting",
            "plan": "trial",
            "license_key": None,
            "start_time": None,
            "expires": None,
            "created_at": datetime.datetime.utcnow().isoformat()
        }
        
        self.users[user_id] = user_data
        self.save_users()
        return user_data
    
    def activate_user(self, user_id: str, plan: str) -> Tuple[str, datetime.date]:
        """Active un utilisateur avec un plan donné"""
        if plan not in PLANS:
            raise ValueError(f"Plan invalide. Plans disponibles : {', '.join(PLANS.keys())}")
        
        now = datetime.datetime.utcnow()
        delta = datetime.timedelta(days=PLANS[plan]["duration_days"])
        expires = now + delta
        
        # Génération d'une clé de licence unique
        license_key = str(uuid.uuid4()).split("-")[0].upper()
        
        # Mise à jour des données utilisateur
        self.users[user_id] = {
            "status": "active",
            "plan": plan,
            "license_key": license_key,
            "start_time": now.isoformat(),
            "expires": expires.isoformat(),
            "activated_at": now.isoformat()
        }
        
        self.save_users()
        return license_key, expires.date()
    
    def check_user_access(self, user_id: str) -> bool:
        """Vérifie si l'utilisateur a accès au service"""
        if user_id not in self.users:
            return False
        
        user_data = self.users[user_id]
        
        # Vérification du statut
        if user_data["status"] != "active":
            return False
        
        # Vérification de la date d'expiration
        if user_data["expires"] is None:
            return False
        
        try:
            expires_date = datetime.datetime.fromisoformat(user_data["expires"])
            return expires_date > datetime.datetime.utcnow()
        except (ValueError, TypeError):
            return False
    
    def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Récupère les informations d'un utilisateur"""
        return self.users.get(user_id)
    
    def get_user_status(self, user_id: str) -> str:
        """Retourne le statut d'un utilisateur"""
        user_data = self.get_user_info(user_id)
        if not user_data:
            return "non_enregistré"
        
        if user_data["status"] != "active":
            return user_data["status"]
        
        if self.check_user_access(user_id):
            return "actif"
        else:
            return "expiré"
    
    def get_expiration_date(self, user_id: str) -> Optional[str]:
        """Retourne la date d'expiration d'un utilisateur"""
        user_data = self.get_user_info(user_id)
        if user_data and user_data.get("expires"):
            try:
                expires_date = datetime.datetime.fromisoformat(user_data["expires"])
                return expires_date.strftime("%d/%m/%Y")
            except (ValueError, TypeError):
                return None
        return None
    
    def cleanup_expired_users(self) -> int:
        """Nettoie les utilisateurs expirés (optionnel)"""
        cleaned_count = 0
        current_time = datetime.datetime.utcnow()
        
        for user_id, user_data in list(self.users.items()):
            if user_data["status"] == "active" and user_data["expires"]:
                try:
                    expires_date = datetime.datetime.fromisoformat(user_data["expires"])
                    if expires_date < current_time:
                        self.users[user_id]["status"] = "expired"
                        cleaned_count += 1
                except (ValueError, TypeError):
                    continue
        
        if cleaned_count > 0:
            self.save_users()
        
        return cleaned_count
