#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestionnaire d'utilisateurs avancé avec système d'approbation et licences personnalisées
"""

import json
import os
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional

class AdvancedUserManager:
    """Gestionnaire avancé avec approbation admin et licences personnalisées"""
    
    def __init__(self, users_file='users.json'):
        self.users_file = users_file
        self.users = self.load_users()
        self.plans = {
            "trial": {"duration_hours": 24, "price": "Gratuit", "max_redirections": 1},
            "semaine": {"duration_days": 7, "price": "1000f", "max_redirections": 10},
            "mois": {"duration_days": 30, "price": "3000f", "max_redirections": 50}
        }
        self.messages = {
            "welcome_pending": (
                "🤖 **Bienvenue sur TeleFoot Bot !**\n\n"
                "⏳ Votre demande d'accès a été envoyée à l'administrateur.\n"
                "Vous recevrez une notification dès validation.\n\n"
                "💡 **Une fois approuvé, vous aurez :**\n"
                "• 24h d'essai gratuit\n"
                "• Accès à 1 redirection\n"
                "• Pronostics football premium\n\n"
                "📞 **Contact :** Sossou Kouamé"
            ),
            "trial_activated": (
                "🎉 **Essai gratuit activé !**\n\n"
                "⏰ **Durée :** 24 heures\n"
                "🔄 **Redirections :** 1 canal maximum\n"
                "⚽ **Pronostics :** Accès complet\n\n"
                "💳 **Pour continuer après l'essai :**\n"
                "Utilisez `/payer` pour souscrire\n\n"
                "🕐 **Expire le :** {expires}"
            ),
            "payment_request": (
                "💳 **Demande de paiement envoyée !**\n\n"
                "⏳ Votre demande d'abonnement **{plan}** a été transmise à l'administrateur.\n"
                "💰 **Prix :** {price}\n\n"
                "Vous serez notifié une fois le paiement confirmé."
            ),
            "license_validation": (
                "🔐 **Validation de licence**\n\n"
                "Votre licence personnelle a été générée !\n"
                "Utilisez `/valider_licence` puis envoyez votre clé.\n\n"
                "⚠️ **Important :** Cette licence est strictement personnelle."
            ),
            "access_expired": (
                "⛔ **Accès expiré**\n\n"
                "Votre période d'essai/abonnement est terminée.\n"
                "Utilisez `/payer` pour renouveler.\n\n"
                "💰 **Tarifs :**\n"
                "• 1 semaine = 1000f\n"
                "• 1 mois = 3000f"
            ),
            "license_invalid": (
                "❌ **Licence invalide**\n\n"
                "La licence fournie ne correspond pas à votre compte.\n"
                "Contactez l'administrateur si vous pensez qu'il y a une erreur."
            )
        }
    
    def load_users(self) -> Dict:
        """Charge les utilisateurs depuis le fichier JSON"""
        try:
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Erreur lecture utilisateurs: {e}")
            return {}
    
    def save_users(self) -> bool:
        """Sauvegarde les utilisateurs"""
        try:
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Erreur sauvegarde utilisateurs: {e}")
            return False
    
    def generate_personal_license(self, user_id: str) -> str:
        """Génère une licence personnalisée : user_id + moitié_id + date + 7 + 23 + 90"""
        user_id_str = str(user_id)
        half_id = user_id_str[:len(user_id_str)//2]
        date_str = datetime.now().strftime("%Y%m%d")
        
        # Combiner selon le format demandé
        license_data = f"{user_id_str}{half_id}{date_str}72390"
        
        # Hacher pour créer une clé unique
        license_hash = hashlib.sha256(license_data.encode()).hexdigest()[:16].upper()
        
        return f"{user_id_str[:4]}-{license_hash[:4]}-{date_str[-4:]}-{license_hash[-4:]}"
    
    def validate_personal_license(self, user_id: str, provided_license: str) -> bool:
        """Valide une licence personnelle"""
        expected_license = self.generate_personal_license(user_id)
        return provided_license.strip() == expected_license
    
    def register_new_user(self, user_id: str, username: str = None) -> Dict:
        """Enregistre un nouvel utilisateur avec statut pending"""
        user_data = {
            "status": "pending_approval",
            "username": username,
            "plan": None,
            "license_key": None,
            "start_time": None,
            "expires": None,
            "created_at": datetime.now().isoformat(),
            "max_redirections": 0,
            "current_redirections": 0,
            "payment_requests": [],
            "license_validated": False
        }
        
        self.users[str(user_id)] = user_data
        self.save_users()
        return user_data
    
    def approve_trial(self, user_id: str) -> Tuple[bool, str]:
        """Approuve un utilisateur pour l'essai gratuit"""
        user_data = self.users.get(str(user_id))
        if not user_data:
            return False, "Utilisateur non trouvé"
        
        if user_data["status"] != "pending_approval":
            return False, "Utilisateur déjà traité"
        
        now = datetime.now()
        expires = now + timedelta(hours=24)
        
        # Mettre à jour les données utilisateur
        self.users[str(user_id)].update({
            "status": "trial",
            "plan": "trial",
            "start_time": now.isoformat(),
            "expires": expires.isoformat(),
            "max_redirections": 1,
            "approved_at": now.isoformat()
        })
        
        self.save_users()
        return True, expires.strftime("%d/%m/%Y à %H:%M")
    
    def request_payment(self, user_id: str, plan: str) -> Tuple[bool, str]:
        """Enregistre une demande de paiement"""
        if plan not in ["semaine", "mois"]:
            return False, "Plan invalide"
        
        user_data = self.users.get(str(user_id))
        if not user_data:
            return False, "Utilisateur non trouvé"
        
        # Enregistrer la demande
        payment_request = {
            "plan": plan,
            "price": self.plans[plan]["price"],
            "requested_at": datetime.now().isoformat(),
            "status": "pending"
        }
        
        if "payment_requests" not in self.users[str(user_id)]:
            self.users[str(user_id)]["payment_requests"] = []
        
        self.users[str(user_id)]["payment_requests"].append(payment_request)
        self.save_users()
        
        return True, self.plans[plan]["price"]
    
    def approve_payment(self, user_id: str, plan: str) -> Tuple[bool, str]:
        """Approuve un paiement et génère la licence"""
        if plan not in ["semaine", "mois"]:
            return False, "Plan invalide"
        
        user_data = self.users.get(str(user_id))
        if not user_data:
            return False, "Utilisateur non trouvé"
        
        now = datetime.now()
        duration_days = self.plans[plan]["duration_days"]
        expires = now + timedelta(days=duration_days)
        
        # Générer la licence personnelle
        license_key = self.generate_personal_license(user_id)
        
        # Mettre à jour les données utilisateur
        self.users[str(user_id)].update({
            "status": "payment_approved",
            "plan": plan,
            "license_key": license_key,
            "start_time": now.isoformat(),
            "expires": expires.isoformat(),
            "max_redirections": self.plans[plan]["max_redirections"],
            "license_validated": False,
            "payment_approved_at": now.isoformat()
        })
        
        # Marquer la demande comme approuvée
        if "payment_requests" in self.users[str(user_id)]:
            for request in self.users[str(user_id)]["payment_requests"]:
                if request["plan"] == plan and request["status"] == "pending":
                    request["status"] = "approved"
                    request["approved_at"] = now.isoformat()
                    break
        
        self.save_users()
        return True, license_key
    
    def validate_license(self, user_id: str, provided_license: str) -> bool:
        """Valide une licence et active l'utilisateur"""
        user_data = self.users.get(str(user_id))
        if not user_data:
            return False
        
        if user_data["status"] != "payment_approved":
            return False
        
        if not self.validate_personal_license(user_id, provided_license):
            return False
        
        # Activer l'utilisateur
        self.users[str(user_id)].update({
            "status": "active",
            "license_validated": True,
            "activated_at": datetime.now().isoformat()
        })
        
        self.save_users()
        return True
    
    def check_user_access(self, user_id: str) -> bool:
        """Vérifie l'accès d'un utilisateur"""
        user_data = self.users.get(str(user_id))
        if not user_data:
            return False
        
        if user_data["status"] not in ["trial", "active"]:
            return False
        
        if not user_data.get("expires"):
            return False
        
        try:
            expires_date = datetime.fromisoformat(user_data["expires"])
            return expires_date > datetime.now()
        except:
            return False
    
    def get_user_max_redirections(self, user_id: str) -> int:
        """Retourne le nombre maximum de redirections pour un utilisateur"""
        user_data = self.users.get(str(user_id))
        if not user_data or not self.check_user_access(user_id):
            return 0
        
        return user_data.get("max_redirections", 0)
    
    def can_add_redirection(self, user_id: str) -> bool:
        """Vérifie si l'utilisateur peut ajouter une redirection"""
        user_data = self.users.get(str(user_id))
        if not user_data or not self.check_user_access(user_id):
            return False
        
        current = user_data.get("current_redirections", 0)
        max_allowed = user_data.get("max_redirections", 0)
        
        return current < max_allowed
    
    def add_redirection(self, user_id: str) -> bool:
        """Ajoute une redirection si possible"""
        if not self.can_add_redirection(user_id):
            return False
        
        current = self.users[str(user_id)].get("current_redirections", 0)
        self.users[str(user_id)]["current_redirections"] = current + 1
        self.save_users()
        return True
    
    def remove_redirection(self, user_id: str) -> bool:
        """Supprime une redirection"""
        user_data = self.users.get(str(user_id))
        if not user_data:
            return False
        
        current = user_data.get("current_redirections", 0)
        if current > 0:
            self.users[str(user_id)]["current_redirections"] = current - 1
            self.save_users()
            return True
        
        return False
    
    def get_user_info(self, user_id: str) -> Optional[Dict]:
        """Récupère les informations d'un utilisateur"""
        return self.users.get(str(user_id))
    
    def get_user_status(self, user_id: str) -> str:
        """Retourne le statut d'un utilisateur"""
        user_data = self.get_user_info(user_id)
        if not user_data:
            return "non_enregistré"
        
        if user_data["status"] == "pending_approval":
            return "en_attente"
        elif user_data["status"] == "trial":
            if self.check_user_access(user_id):
                return "essai_actif"
            else:
                return "essai_expiré"
        elif user_data["status"] == "payment_approved":
            return "paiement_approuvé"
        elif user_data["status"] == "active":
            if self.check_user_access(user_id):
                return "actif"
            else:
                return "expiré"
        else:
            return user_data["status"]
    
    def get_pending_approvals(self) -> Dict:
        """Retourne les utilisateurs en attente d'approbation"""
        pending = {}
        for user_id, data in self.users.items():
            if data["status"] == "pending_approval":
                pending[user_id] = data
        return pending
    
    def get_pending_payments(self) -> Dict:
        """Retourne les demandes de paiement en attente"""
        pending = {}
        for user_id, data in self.users.items():
            if "payment_requests" in data:
                for request in data["payment_requests"]:
                    if request["status"] == "pending":
                        if user_id not in pending:
                            pending[user_id] = []
                        pending[user_id].append(request)
        return pending
    
    def get_stats(self) -> Dict:
        """Statistiques détaillées"""
        stats = {
            "total_users": len(self.users),
            "pending_approval": 0,
            "trial_users": 0,
            "active_users": 0,
            "expired_users": 0,
            "payment_requests": 0
        }
        
        for user_id, data in self.users.items():
            status = self.get_user_status(user_id)
            
            if status == "en_attente":
                stats["pending_approval"] += 1
            elif status == "essai_actif":
                stats["trial_users"] += 1
            elif status == "actif":
                stats["active_users"] += 1
            elif status in ["essai_expiré", "expiré"]:
                stats["expired_users"] += 1
            
            # Compter les demandes de paiement
            if "payment_requests" in data:
                stats["payment_requests"] += len([r for r in data["payment_requests"] if r["status"] == "pending"])
        
        return stats