# vanmarcke-softener
Home Assistant integration (ConnectMySoftener)

# Intégration Adoucisseur Van Marcke (Pentair) pour Home Assistant

⚠️ **Note importante** :  
Ce projet **n'est pas affilié** à Van Marcke ou Pentair. Développé par un particulier pour usage personnel, partagé publiquement à titre informatif. L'intégration peut présenter des bugs et n'est pas maintenue professionnellement.

## Fonctionnalités principales
- **Données en temps réel** :
  - Débit d'eau (L/min)
  - Niveau de sel (%)
  - Volume d'eau restant (L)
  
- **Historique et maintenance** :
  - Consommation journalière
  - Dernière régénération (date/heure)
  - Jours restants avant régénération
  - Nombre total de régénérations
  
- **Informations système** :
  - Version du logiciel
  - Volume total traité
 

![Exemple de dashboard](https://raw.githubusercontent.com/lemick007/vanmarcke-softener/main/preview.png) *Interface indicative*

## Installation via HACS
1. Installer [HACS](https://hacs.xyz/) si ce n'est pas déjà fait
2. Dans HACS > **Intégrations** :
URL du dépôt : https://github.com/lemick007/vanmarcke-softener
Catégorie : Intégration
3. Redémarrer Home Assistant
4. Ajouter via `Configuration > Appareils & Services > + Ajouter une intégration`

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=lemick007&repository=vanmarcke-softener&category=Integrations)
## Pré-requis
Il faut avoir installé l'application de votre adoucisseur (connectmysoftener ou autre) pour avoir un compte, et le connecter au wi-fi !

## Dépannage courant
| Problème | Solution |
|----------|----------|
| Entités non créées | Vérifier les logs HA (`/config/home-assistant.log`) |
| Données non mises à jour | Redémarrer l'adoucisseur et HA |
| Erreur d'authentification | Réinitialiser votre mot de passe |

## Mentions légales
ℹ️ Van Marcke® et Pentair® sont des marques déposées de leurs propriétaires respectifs. Ce projet n'implique aucune relation commerciale ou technique avec ces sociétés. Utilisation à vos risques.

## Licence
Copyright (c) 2025
Permission d'utilisation accordée sous conditions :
1. Usage non-commercial autorisé avec attribution
2. Interdiction de vendre/intégrer dans produits payants
3. Modifications obligatoirement partagées sous même licence

---

❤️ **Contributions bienvenues** :  
[Ouvrir une issue] | [Proposer une PR] | [Support via GitHub Discussions]
