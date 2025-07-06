
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Système de maintien d'activité pour Replit
"""

import asyncio
import time
from datetime import datetime

class KeepAlive:
    def __init__(self):
        self.running = False
    
    async def ping_system(self):
        """Ping régulier pour maintenir l'activité"""
        ping_count = 0
        while self.running:
            try:
                # Ping simple
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ping_count += 1
                print(f"🔄 KeepAlive #{ping_count} - {current_time}")
                
                # Vérifier si le bot principal fonctionne
                try:
                    with open("bot_status.txt", "w") as f:
                        f.write(f"Active: {current_time}\nPing: {ping_count}")
                except:
                    pass
                
                # Ping plus fréquent (toutes les 10 minutes au lieu de 30)
                await asyncio.sleep(600)
                
            except Exception as e:
                print(f"❌ Erreur KeepAlive : {e}")
                await asyncio.sleep(60)  # Attendre 1 minute en cas d'erreur
    
    def start(self):
        """Démarre le système keep-alive"""
        self.running = True
        asyncio.create_task(self.ping_system())
    
    def stop(self):
        """Arrête le système keep-alive"""
        self.running = False

# Instance globale
keep_alive = KeepAlive()
