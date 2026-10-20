# Site Lavedonio

#### [ENGLISH / INGLÊS]
This is the source code of the [lavedonio.com](https://www.lavedonio.com/) (English) and [lavedonio.com.br](https://www.lavedonio.com.br/) (Brazilian Portuguese) Django website. [Read it in English](#readme---english).

#### [BRAZILIAN PORTUGUESE / PORTUGUÊS BRASILEIRO]
Este é o código fonte do site Django [lavedonio.com](https://www.lavedonio.com/) (inglês) e [lavedonio.com.br](https://www.lavedonio.com.br/) (português brasileiro). [Leia em português](#leiame---português-brasileiro-pt-br).

> The first version of the site (v1) is kept in the [`v1`](https://github.com/Lavedonio/site_lavedonio_django/tree/v1) branch. / A primeira versão do site (v1) está na branch [`v1`](https://github.com/Lavedonio/site_lavedonio_django/tree/v1).

# README - English

## About

My personal website, made with **Python** and **Django**. It's an *open-source* project: feel free to use it as a base for your own, as long as this repository is credited. See the license for other legal questions.

It has:

- Home, About and Contact pages;
- A blog, written in Markdown with a WYSIWYG editor, with tags, an archive and sharing buttons;
- A projects portfolio, written in HTML with a WYSIWYG editor, with categories and optional custom CSS/JavaScript for interactive projects (e.g. games);
- English and Brazilian Portuguese versions, each on its own domain, with a banner suggesting the visitor's language. Each post and project can be in one or both languages, under the same address;
- Editors that work on phones, with image uploads (resized and converted to WebP);
- Light and dark modes, and cookie consent for analytics.

## Project structure

The Django project is in the `site_lavedonio_django/` folder (where `manage.py` is):

- `base/`: home, about and contact pages, plus what the other apps share (language handling, editor forms, Markdown rendering, image optimization);
- `blog/`, `projects/`: the blog and the projects portfolio;
- `uploads/`: images uploaded through the editors;
- `users/`: login and logout (kept in sync across the domains of every language);
- `locale/`: translations.

## Requirements

- **Python 3.12** (`requirements.txt` has the packages);
- [gettext](https://www.gnu.org/software/gettext/), only to update the translations.

## Setup

1. Install the packages: `pip install -r requirements.txt`;
2. Create a `.env` file in the repository root:

   ```
   ENVIRONMENT=development
   SECRET_KEY=<a long random string>
   DEBUG_VALUE=True
   ```

   `ENVIRONMENT` picks the settings in `site_lavedonio_django/site_lavedonio_django/env_settings.py`: `development` (SQLite), `docker_development` (PostgreSQL, also needs `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST` and optionally `DB_PORT`), `staging` or `production`. `ANALYTICS_ID` (Google Analytics) is optional and only loaded for visitors who allow cookies.

   The contact form sends its messages to `CONTACT_EMAIL` through an SMTP server, set with `EMAIL_HOST`, `EMAIL_PORT` (default `587`), `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` and `EMAIL_USE_TLS` (default `True`). The sender is `DEFAULT_FROM_EMAIL` (default: `EMAIL_HOST_USER`) and `CONTACT_EMAIL` also defaults to it. Replies go to the visitor's address. In development the e-mails are printed in the terminal instead, unless `EMAIL_BACKEND` is set (e.g. `django.core.mail.backends.smtp.EmailBackend`):

   ```
   EMAIL_HOST=smtp.example.com
   EMAIL_HOST_USER=site@example.com
   EMAIL_HOST_PASSWORD=<password>
   CONTACT_EMAIL=me@example.com
   ```

   The contact form is protected from bots by [Cloudflare Turnstile](https://developers.cloudflare.com/turnstile/). Development uses Cloudflare's test keys, whose challenge always passes. In `staging` and `production`, `TURNSTILE_SITE_KEY` and `TURNSTILE_SECRET_KEY` are required, with the keys of a widget that includes the site's domains;
3. From the `site_lavedonio_django/` folder, create the database and an admin user:

   ```
   python manage.py migrate
   python manage.py createsuperuser
   ```

## Running in development

```
python manage.py runserver
```

Open [localhost:8000](http://localhost:8000) for the English version and [127.0.0.1:8000](http://127.0.0.1:8000) for the Brazilian Portuguese one. Log in at `/accounts/login/` to create and edit posts and projects.

## Languages

Each language is served by its own domain, set in `LANGUAGE_DOMAINS` (`env_settings.py`). To add a language, add it to `LANGUAGES` (`settings.py`), give it a domain and create its translations. No database change is needed.

To update the translations after changing the texts:

```
python manage.py makemessages -l pt_BR --no-location
python manage.py compilemessages
```

## Images

Photos added to `base/static/img` should be optimized with `python manage.py optimize_static_images` and used in the templates with `{% static_image 'img/photo.jpeg' %}` (from `{% load site_tags %}`).

## Tests

```
python manage.py test
```

## License

[Mozilla Public License 2.0](LICENSE).

# LEIAME - Português Brasileiro (pt-br)

## Sobre

Meu site pessoal, feito em **Python** com **Django**. É um projeto *open-source*: fique à vontade para usá-lo como base para os seus, desde que citado este repositório. Para demais questões legais, veja a licença.

Ele tem:

- Páginas inicial, Sobre e Contato;
- Um blog, escrito em Markdown com um editor WYSIWYG, com tags, arquivo e botões de compartilhamento;
- Um portfólio de projetos, escritos em HTML com um editor WYSIWYG, com categorias e CSS/JavaScript personalizados opcionais para projetos interativos (ex.: jogos);
- Versões em inglês e português brasileiro, cada uma em seu domínio, com um aviso sugerindo o idioma do visitante. Cada publicação e projeto pode estar em um ou nos dois idiomas, no mesmo endereço;
- Editores que funcionam no celular, com envio de imagens (redimensionadas e convertidas para WebP);
- Modos claro e escuro e consentimento de cookies para análise de visitas.

## Estrutura do projeto

O projeto Django está na pasta `site_lavedonio_django/` (onde está o `manage.py`):

- `base/`: páginas inicial, Sobre e Contato, além do que os outros apps compartilham (idiomas, formulários dos editores, Markdown, otimização de imagens);
- `blog/`, `projects/`: o blog e o portfólio de projetos;
- `uploads/`: imagens enviadas pelos editores;
- `users/`: login e logout (sincronizados entre os domínios de todos os idiomas);
- `locale/`: traduções.

## Requisitos

- **Python 3.12** (os pacotes estão no `requirements.txt`);
- [gettext](https://www.gnu.org/software/gettext/), apenas para atualizar as traduções.

## Configuração

1. Instale os pacotes: `pip install -r requirements.txt`;
2. Crie um arquivo `.env` na raiz do repositório:

   ```
   ENVIRONMENT=development
   SECRET_KEY=<um texto aleatório longo>
   DEBUG_VALUE=True
   ```

   `ENVIRONMENT` escolhe as configurações em `site_lavedonio_django/site_lavedonio_django/env_settings.py`: `development` (SQLite), `docker_development` (PostgreSQL, que também precisa de `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST` e opcionalmente `DB_PORT`), `staging` ou `production`. `ANALYTICS_ID` (Google Analytics) é opcional e só é carregado para visitantes que permitirem cookies.

   O formulário de contato envia as mensagens para `CONTACT_EMAIL` por um servidor SMTP, definido com `EMAIL_HOST`, `EMAIL_PORT` (padrão `587`), `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` e `EMAIL_USE_TLS` (padrão `True`). O remetente é `DEFAULT_FROM_EMAIL` (padrão: `EMAIL_HOST_USER`), que também é o padrão de `CONTACT_EMAIL`. As respostas vão para o endereço do visitante. Em desenvolvimento, os e-mails são mostrados no terminal em vez de enviados, a não ser que `EMAIL_BACKEND` seja definido (ex.: `django.core.mail.backends.smtp.EmailBackend`):

   ```
   EMAIL_HOST=smtp.example.com
   EMAIL_HOST_USER=site@example.com
   EMAIL_HOST_PASSWORD=<senha>
   CONTACT_EMAIL=eu@example.com
   ```

   O formulário de contato é protegido contra bots pelo [Cloudflare Turnstile](https://developers.cloudflare.com/turnstile/). Em desenvolvimento são usadas as chaves de teste da Cloudflare, cujo desafio sempre passa. Em `staging` e `production`, `TURNSTILE_SITE_KEY` e `TURNSTILE_SECRET_KEY` são obrigatórias, com as chaves de um widget que inclua os domínios do site;
3. Na pasta `site_lavedonio_django/`, crie o banco de dados e um usuário administrador:

   ```
   python manage.py migrate
   python manage.py createsuperuser
   ```

## Executando em ambiente de desenvolvimento

```
python manage.py runserver
```

Abra [localhost:8000](http://localhost:8000) para a versão em inglês e [127.0.0.1:8000](http://127.0.0.1:8000) para a versão em português. Entre em `/accounts/login/` para criar e editar publicações e projetos.

## Idiomas

Cada idioma é servido por um domínio, definido em `LANGUAGE_DOMAINS` (`env_settings.py`). Para adicionar um idioma, inclua-o em `LANGUAGES` (`settings.py`), defina seu domínio e crie suas traduções. Nenhuma mudança no banco de dados é necessária.

Para atualizar as traduções depois de mudar os textos:

```
python manage.py makemessages -l pt_BR --no-location
python manage.py compilemessages
```

## Imagens

Fotos adicionadas em `base/static/img` devem ser otimizadas com `python manage.py optimize_static_images` e usadas nos templates com `{% static_image 'img/foto.jpeg' %}` (de `{% load site_tags %}`).

## Testes

```
python manage.py test
```

## Licença

[Mozilla Public License 2.0](LICENSE).
