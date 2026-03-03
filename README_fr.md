# La Buvette de Bel'Air : construire un backend pour la célèbre buvette du festival eXalt. Avec Python, IA, et amour.

Version anglaise : [README.md](README.md)  
Version española : [README_es.md](README_es.md)

>[!note]
> 
> Ce projet fait partie du parcours d'apprentissage eXalt IT augmented engineer, disponible dans son [academy](https://example.com).

Bonjour et bienvenue dans le dépôt du projet La Buvette de Bel'Air !

Ce projet est votre terrain de jeu pour créer un backend robuste de gestion des boissons et snacks !

Vous allez construire le meilleur backend possible en utilisant Python.

Mais plus important encore, votre nouveau meilleur ami : GitHub Copilot, votre canard en caoutchouc / stagiaire trop enthousiaste pour le pair programming !

## Structure du projet

```
augmented-engineer-python-starter/
 application/      # Point d'entrée — relie le domaine et l'infrastructure
 domain/           # Logique métier et modèle de domaine
 infrastructure/   # Adaptateurs, persistance, intégrations externes
```

## Packages

### `domain`

Le cœur de l'application. Contient toute la logique métier, les entités, les objets valeur et les services de domaine.  
Ce package ne dépend d'aucun autre package local — c'est du Python pur, sans framework.

### `application`

Le point d'entrée. Orchestre les cas d'usage en coordonnant les objets du domaine.  
Il définit les **ports** (classes abstraites / protocoles) que la couche infrastructure doit implémenter (ex. : repositories, contrats de services externes).  
Dépend uniquement de `domain`.

### `infrastructure`

Fournit les implémentations concrètes des ports définis dans `application`.  
C'est ici que résident la persistance, les clients d'API externes, la messagerie et autres préoccupations techniques.  
Dépend de `domain` et de `application`.

## Installation de la chaîne d'outils

| Outil | Version | Documentation |
|-------|---------|---------------|
| Python | 3.13+ | [python.org](https://www.python.org/downloads/) |
| uv | latest | [docs.astral.sh/uv](https://docs.astral.sh/uv/) |
| Git | latest | [git-scm.com](https://git-scm.com/downloads) |

> Installez uv via `pip install uv` ou via le [script d'installation officiel](https://docs.astral.sh/uv/getting-started/installation/).

## Démarrage

### Prérequis

- Python 3.13+
- uv
- Git

### Fork & Clone

Forkez ce dépôt sur votre propre compte Gitlab (branche main uniquement), puis clonez-le :

```bash
git clone <URL_DE_VOTRE_FORK>
cd augmented-engineer-python-starter
```

### Miroir vers GitHub

Pour pouvoir utiliser correctement les fonctionnalités IA avancées avec Copilot, miroir ce dépôt sur votre compte GitHub :

```bash
git remote add github <the URL of your new GitHub repository>
git branch -M main
git push -u github main
```

### Installer les dépendances

```bash
uv sync
```

### Lancer les tests

```bash
uv run pytest
```

### Lancer l'application

```bash
uv run python -m application.main
```

## Étapes suivantes

Commencez par suivre le reste du matériel de formation dans l'[academy](https://example.com).

Consultez le fichier [FEATURES_fr.md](./FEATURES_fr.md) pour la liste des user stories et des critères d'acceptation.

Bon codage !
