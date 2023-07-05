# Eduka DB Backup Automation


## Add your files

- [ ] [Create](https://docs.gitlab.com/ee/user/project/repository/web_editor.html#create-a-file) or [upload](https://docs.gitlab.com/ee/user/project/repository/web_editor.html#upload-a-file) files
- [ ] [Add files using the command line](https://docs.gitlab.com/ee/gitlab-basics/add-file.html#add-a-file-using-the-command-line) or push an existing Git repository with the following command:

```
cd existing_repo
git remote add origin https://gitlab.com/enkoeducation/eduka-db-backup-automation.git
git branch -M main
git push -uf origin main
```

## Integrate with your tools

- [ ] [Set up project integrations](https://gitlab.com/enkoeducation/eduka-db-backup-automation/-/settings/integrations)

## Collaborate with your team

- [ ] [Invite team members and collaborators](https://docs.gitlab.com/ee/user/project/members/)
- [ ] [Create a new merge request](https://docs.gitlab.com/ee/user/project/merge_requests/creating_merge_requests.html)
- [ ] [Automatically close issues from merge requests](https://docs.gitlab.com/ee/user/project/issues/managing_issues.html#closing-issues-automatically)
- [ ] [Enable merge request approvals](https://docs.gitlab.com/ee/user/project/merge_requests/approvals/)
- [ ] [Set auto-merge](https://docs.gitlab.com/ee/user/project/merge_requests/merge_when_pipeline_succeeds.html)

## Test and Deploy

Use the built-in continuous integration in GitLab.

- [ ] [Get started with GitLab CI/CD](https://docs.gitlab.com/ee/ci/quick_start/index.html)
- [ ] [Analyze your code for known vulnerabilities with Static Application Security Testing(SAST)](https://docs.gitlab.com/ee/user/application_security/sast/)
- [ ] [Deploy to Kubernetes, Amazon EC2, or Amazon ECS using Auto Deploy](https://docs.gitlab.com/ee/topics/autodevops/requirements.html)
- [ ] [Use pull-based deployments for improved Kubernetes management](https://docs.gitlab.com/ee/user/clusters/agent/)
- [ ] [Set up protected environments](https://docs.gitlab.com/ee/ci/environments/protected_environments.html)

***

## Name
Automatisation de la sauvegarde des bases de données Eduka

## Description
Le client souhaite que chaque plateforme Eduka ait sa base de données sauvegardée toutes les semaines (le lundi à 3:00 GMT) avec envoi d’une notification pour signifier quelles sauvegardes sont effectuées, et lesquelles ne l’ont pas été.

### Travail à faire
**Remarque :** Les plateformes sont a priori identiques. Le code écrit pour une plateforme marchera pour toutes les autres. 

1. Faire en sorte que de mettre dans un fichier de configuration (TXT, JSON) partagé en ligne via Google Drive (afin de pouvoir modifier des paramètres sans toucher au code)
    - les accès (URLs d’accès, logins, passwords)
    - les emails de notification pour chaque plateforme (avec séparateurs ;)
    - L’âge des bases de données sauvegardées (**YY jours**)

2. Accéder à chaque plateforme Eduka dont l’URL est dans ce fichier
    - Aller sur le répertoire _{URL-DOMAIN}/configuration/manage/database_
    - Aller sur “Sauvegarder et Restaurer”
    - Cliquer sur “Effectuer une sauvegarde”
    - Cliquer sur “OK” pour valider la sauvegarde
    - Aller sur “Sauvegardes Existantes”
    - Supprimer les sauvegardes dont la date de sauvegarde est supérieure à **YY jours** (tel que défini dans le fichier de configuration)

3. Planifier un lancement automatique tous les lundis dès 3:00 GMT

4. Pour chaque plateforme, envoyer un email de notification pour signifier que la sauvegarde s’est bien passée, ou signaler l’erreur empêchant la sauvegarde dans l’email

5. Dans le même email ci-dessus, signaler les sauvegardes qui ont été supprimées.

## Technologies Used
- Eduka DB Backup Automation need only Python 3 to function.
- Requirements will be available in the requirements.txt

## Installation
TODO: Installation will be writen later...


## Project status
Project is: _in development_ IT Team has started working on it and will continously add features and updates
