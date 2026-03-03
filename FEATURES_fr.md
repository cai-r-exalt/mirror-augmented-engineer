# Fonctionnalités de la Buvette de Bel'Air

Bienvenue dans le projet La Buvette de Bel'Air ! Ce document présente les fonctionnalités clés du backend conçu pour gérer efficacement les boissons et les snacks.

## Fonctionnalités

### En tant que festivalier·ère, je veux consulter le solde restant de mes jetons

Règles :
- Un festivalier dispose de deux types de jetons : jetons boisson et jetons nourriture
- Un festivalier peut avoir zéro ou plusieurs jetons boisson
- Un festivalier peut avoir zéro ou plusieurs jetons nourriture
- Un festivalier ne peut pas avoir un solde négatif de jetons
- Un festivalier reçoit 9 jetons nourriture et 6 jetons boisson par jour de festival
- Les jetons non dépensés ne sont pas reportés au jour suivant

### En tant que festivalier·ère, je veux passer une commande de boisson

Règles :
- Une boisson peut être alcoolisée ou non alcoolisée
- Une boisson non alcoolisée ne coûte aucun jeton boisson
- Une boisson alcool normale coûte un jeton boisson
- Une boisson alcool premium coûte deux jetons boisson

### En tant que festivalier·ère, je veux passer une commande de nourriture

Règles :
- Il existe deux types d'articles alimentaires : snacks et repas
- Les repas coûtent 3 jetons nourriture
- Les snacks coûtent 1 jeton nourriture

### En tant que festivalier·ère, je veux pouvoir commander plusieurs articles dans une seule commande

Règles :
- Un festivalier peut commander plusieurs articles dans une même commande
- Le coût total de la commande ne doit pas dépasser le solde de jetons du festivalier, ni pour les jetons boisson ni pour les jetons nourriture

### En tant que groupe de festivaliers, nous voulons pouvoir mutualiser nos jetons pour passer une commande de groupe

Règles :
- La commande de groupe ne peut être passée que si la somme des jetons mis en commun couvre le coût total
- Chaque festivalier peut contribuer une quantité quelconque de ses jetons à la commande de groupe
- La commande de groupe est traitée comme une seule commande et suit les mêmes règles

### En tant que festivalier·ère, je veux pouvoir modifier ma commande

Règles :
- Une commande ne peut être modifiée que si elle n'a pas encore été prise en charge (acknowledged) par le·la barman·barmaid
- Le festivalier peut ajouter ou retirer des articles de la commande
- Le coût total de la commande modifiée ne doit pas dépasser le solde de jetons du festivalier (boisson ou nourriture)
- Si la commande est déjà prise en charge, le·la barman·barmaid doit être informée des changements demandés

### En tant que festivalier·ère, je veux pouvoir annuler ma commande

Règles :
- Une commande ne peut être annulée que si elle n'a pas encore été prise en charge par le·la barman·barmaid
- Lors de l'annulation, les jetons utilisés pour la commande sont remboursés au solde du festivalier
- Le festivalier reçoit une confirmation de l'annulation

### En tant que barman·barmaid, je veux acquitter une commande afin que le festivalier sache que sa commande est en cours de préparation, et fournir un temps estimé de préparation

Règles :
- Une fois qu'une commande est acquittée, le festivalier est notifié que sa commande est en cours de préparation
- Un temps estimé de préparation est fourni au festivalier en fonction de la charge actuelle et de la commande
- Le temps estimé de préparation est calculé ainsi :
  - Pour une commande contenant uniquement des boissons non alcoolisées : 1 minute par type de boisson (ex. 3 boissons non alcoolisées différentes = 3 minutes)
  - Pour une commande contenant des boissons alcool normales : 2 minutes par boisson
  - Pour une commande contenant des boissons alcool premium : 3 minutes par boisson
  - Pour les commandes mixtes, le temps total est la somme des temps de chaque type (non alcoolisé, alcool normal, alcool premium)
  - Pour une commande contenant des snacks : 2 minutes par type de snack
  - Pour une commande contenant des repas : 10 minutes par type de repas plus le temps de préparation le plus long de n'importe quelle boisson de la commande

L'idée est que les repas prennent plus de temps à préparer, mais peuvent être préparés en parallèle avec les boissons.
Les commandes contenant le même type d'articles sont préparées ensemble, donc seul le nombre de types différents d'articles importe pour le temps de préparation.

### En tant que barman·barmaid, je veux marquer une commande comme prête afin que le festivalier sache qu'il peut venir la récupérer

Règles :
- Une commande ne peut être marquée comme prête que s'il y a suffisamment d'articles préparés pour satisfaire la commande
- Une fois la commande marquée comme prête, le festivalier est notifié qu'il peut la récupérer

### En tant que barman·barmaid, lors de la réception d'une demande de modification d'une commande déjà acquittée, je veux examiner et accepter ou refuser les changements

Règles :
- La demande de changement ne peut être acceptée que si au moins un des articles déjà préparés peut être transféré vers une autre commande
- Une fois la demande acceptée, le festivalier est notifié du nouveau temps estimé de préparation

### En tant que festivalier·ère, je veux pouvoir transférer des jetons à un·e autre festivalier·ère

Règles :
- Le festivalier peut transférer jusqu'à trois jetons de chaque type à un·e autre festivalier·ère
- Le transfert de jetons doit être confirmé par le·la festivalier·ère destinataire
- Le solde de jetons du·de la festivalier·ère ne peut pas devenir négatif à la suite du transfert

### En tant que barman·barmaid, je veux que des notifications régulières soient envoyées aux festivaliers pour leur rappeler de boire de l'eau, car il fait chaud !

Règles :
- Toutes les heures, une notification est envoyée à tous les festivaliers leur rappelant de boire de l'eau
- La notification contient un message amical et encourage une consommation responsable
- Si un festivalier a consommé plus de 3 boissons alcoolisées au cours de la dernière heure, la notification doit être envoyée plus fréquemment, toutes les 30 minutes
- La notification ne doit être envoyée qu'entre 11h00 et 19h00 chaque jour du festival (parce qu'après 19h00, c'est l'heure de faire la fête, et avant 11h00, espérons-le, personne ne boit autre chose que des jus de fruits !)
