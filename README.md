# Site Lavedonio

#### [ENGLISH / INGLÊS]
This is the source code for [lavedonio.com](https://www.lavedonio.com/) and [lavedonio.com.br](https://www.lavedonio.com.br/) (pt-br) Django Websites. To see the english version of this README, [click here](#index).

#### [BRAZILIAN PORTUGUESE / PORTUGUÊS BRASILEIRO]
Este é o código fonte para os sites Django [lavedonio.com](https://www.lavedonio.com/) e [lavedonio.com.br](https://www.lavedonio.com.br/) (pt-br). Para ver a versão em português deste arquivo README (LEIAME), [clique aqui](#sumário).

# LEIAME - Português Brasileiro (pt-br)

## Sumário

 - [Sobre](#sobre)
 - [Requisitos](#requisitos)
 - [Download e configuração inicial](#download-e-configura%C3%A7%C3%A3o-inicial)
 - [Executando em ambiente de desenvolvimento](#executando-em-ambiente-de-desenvolvimento)
 - [Deployment](#deployment)
 - [Leitura complementar](#leitura-complementar)

## Sobre

Este site é feito em **Python**, utilizando a framework **Django**. Trata-se do meu site pessoal, um projeto *open-source* que pode ser utilizado como base para outros projetos.

Este projeto é livre para ser copiado, modificado e comercializado, desde que citado este repositório do GitHub. Para demais questões legais, verifique a licença neste repositório.

#### Versão atual: 0.1.0 (beta)

Este projeto contém:

 - Homepage com a lista dos projetos e publicações em destaque, além de links para as páginas de sobre e contato;
 - Página estática de "Sobre", dizendo um pouco mais do autor e do site;
 - Página de Projetos, um portfólio com projetos relevantes e em destaque;
 - Página de Blog, com artigos com total flexibilidade de colocar um código HTML qualquer;
 - Página de Contato, que tem proteção de SPAM com RECAPTCHA e envia um email com as informações passadas;
 - Upload e redirecionamento de Imagens e Arquivos;
 - Encurtador de Links;
 - Site Admin para coordenar todo o processo.

Afazeres:

 - Dashboard customizável;
 - Template da página de Login;
 - Editor WYSIWYG para Blog e Projetos;
 - Sendgrid como email de envio para Contato.

## Requisitos

#### Para ambiente de desenvolvimento:

- **Python 3.6** ou superior;
- Conta no Gmail ou outro serviço de email.

#### Para ambiente de *staging*:

- **Python 3.6** ou superior;
- Conta no Gmail ou outro serviço de email;
- RECAPTCHA ativo;
- Conta na AWS.

#### Para ambiente de produção:

- **Python 3.6** ou superior;
- Conta no Gmail ou outro serviço de email;
- RECAPTCHA ativo;
- Conta na AWS;
- Conta no Google Analytics.

## Download e configuração inicial

Baixe os arquivos deste projeto, seja baixando o arquivo ZIP e descompactando-o, utilizando o comando `git clone https://github.com/Lavedonio/site_lavedonio_django.git` diretamente deste repositório ou fazendo um *Fork* deste e utilizar o comando `git clone` de lá.

Uma vez baixado, considerando que você já tenha o [Python 3.6 ou superior](https://www.python.org/downloads/) instalado, abra o Terminal (Prompt de Comando no caso do Windows), navegue até a pasta onde está o projeto e digite o comando:

`pip install -r requirements.txt`

Se a instalação do pacote `psycopg2` falhar, você pode tirá-lo da lista deste arquivo txt e rodar o comando novamente (ele é importante para o Postgres, mas não é necessário para o ambiente de desenvolvimento).

**Pronto!** Ele já pode ser executado em ambiente de desenvolvimento. **MAS...** recomenda-se mais um passo (obrigatório para ambientes de *staging* e produção) que é configurar as variáveis de segredos e senhas. Para fazer esta configuração existem 2 opções:

#### 1. Configurar o arquivo `secrets.py` (Recomendado)

Abra o projeto e vá para a pasta `site_core/settings`. Em seguida, copie e cole o arquivo `secrets_example.py` na mesma pasta e renomeie-o para `secrets.py`.

> **Obs:** Renomeie o arquivo **exatamente** para `secrets.py`, isto é importante não só para que o projeto funcione, mas para garantir que você não dê *commit* por engano suas chaves privadas, segredos e senhas para terceiros.

Abra o arquivo `secrets.py` com um editor de texto e coloque seus segredos e chaves correspondentes em cada campo. (Mais informações no tópico a seguir **Variáveis de segredo**).

#### 2. Configurar variáveis de ambiente

Apesar de não ser a melhor recomendação, alguns serviços de hospedagem obrigam que todos os arquivos que pertencem ao projeto estejam no projeto do git (ex.: Heroku). Isso é ruim pois chaves privadas, segredos e senhas que forem *commitadas* sempre estarão no histórico, para qualquer um que tenha acesso ao código ver. Portanto, a alternativa neste caso é utilizar variáveis de ambiente.

##### MacOS e Linux
1. Vá ao terminal, digite `cd` e dê Enter, para garantir que esteja no diretório home;
2. Digite o comando `sudo nano .bashrc` e em seguida digite sua senha;
3. Para cada chave do dicionário *secrets* dentro do arquivo `secrets_example.py` (localizado na pasta `site_core/settings`), digite ao final do arquivo o seguinte comando:
`export KEY="VALUE"`
Lembrando de substituir KEY pelo valor da chave que será adicionada (ex.: ENVIRONMENT, SECRET_KEY, SERVER_TYPE, etc...), VALUE pelo valor correspondente (sempre estando entre parênteses) e de não deixar espaços entre o sinal de igual. Coloque um comando por linha.
4. Salve o arquivo usando `Ctrl-X`, em seguida aperte `Y` e depois Enter para salvar as alterações;
5. Reinicie o terminal.

##### Windows
1. Abra o **Painel de Controle**;
2. Vá para **Sistema e Segurança** e depois para **Sistema**;
3. Clique em **Configurações avançadas do sistema**;
4. Clique no botão **Variáveis de Ambiente...**;
5. Na área de Variáveis de usuário para USER (sendo USER o nome de usuário do seu computador), clique no botão **Novo...**;
6. Para cada chave do dicionário *secrets* dentro do arquivo `secrets_example.py` (localizado na pasta `site_core/settings`), digite o valor da chave do dicionário em **Nome da Variável** e o seu respectivo valor em **Valor da Variável**. Ao final, aperte o botão **OK**;
7. Repita os passos 5 e 6 para quantas variáveis você deseja adicionar;
8. Dê **OK** nas duas janelas abertas e feche o **Painel de Controle**.

##### Heroku e serviços de hospedagem do tipo
Neste caso, não insira diretamente as variáveis no terminal. Procure como adicionar variáveis de ambiente nesses serviços.

### Variáveis de segredo
Cada variável possui um propósito específico dentro do projeto. Elas estão especificadas abaixo, classificadas de acordo com seu tipo.

#### Categoria 1: Django

##### ENVIRONMENT
Esta variável serve para especificar qual ambiente o programa está rodando e, portanto, qual conjunto de configurações deve ser importado.

Valores possíveis: **development**, **staging**, **production**.

##### SECRET_KEY
Esta variável é importantíssima para a segurança de autenticação do sistema. Para o ambiente de desenvolvimento, esta variável não é necessária pois já existe uma fixa em código (que não deve ser reutilizada em servidores).

Para os ambientes de staging e produção, recomenda-se abra o terminal, para MacOS e Linux, ou o Prompt de Comando, para Windows, e digite o comando:

    python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

Pegue o resultado e use este valor para a variável SECRET_KEY.

##### DEBUG_VALUE
Este valor define se o Django irá detalhar os erros de execução direto no navegador ou não. Isso é ótimo para o desenvolvimento, mas péssimo para ambientes de produção.

Para o ambiente de desenvolvimento, este valor já possui em código o valor True, então esta configuração não é necessária. Para ambientes de *staging* e produção, essa variável deve ser configurada para a execução correta do sistema.

**Para o ambiente de produção, em específico, esse valor deve, necessariamente, ser False, pois o log detalhado de erros pode ser um risco à segurança do sistema.**

Valores possíveis: **True**, **False**.

##### SERVER_TYPE
Esta configuração tem efeito apenas nos ambientes de *staging* e produção.

Ela serve especificamente para o Heroku e faz todo o setup necessário automaticamente. Para outros tipos de servidores, deve-se colocar os valores do banco de dados nas variáveis DB_NAME, DB_USER e DB_PASS.

Valores possíveis: **heroku**, ***Vazio***.

##### HTTPS_TRAFFIC_ONLY
Esta configuração tem efeito apenas nos ambientes de *staging* e produção.

Ela serve para forçar o tráfego do site a usar o protocolo HTTPS em vez do HTTP.

Valores possíveis: **True**, **False**.

#### Categoria 2: E-mail

##### EMAIL_USER
É o usuário de e-mail do qual partirá o envio da mensagem no formulário de Contato. O código está configurado para e-mails do gmail. Para outros provedores, é necessário alterar o código.

##### EMAIL_PASS
A senha de acesso do seu e-mail. Para o Gmail, existem 2 formas de se fazer:

1. Ativando senhas de app (veja como [aqui](https://support.google.com/accounts/answer/185833?hl=pt)) e utilizando a senha gerada.
2. Ativando login por apps menos seguros e utilizando sua senha de acesso padrão (não recomendado).

#### Categoria 3: RECAPTCHA
Entre no [site do RECAPTCHA](https://www.google.com/recaptcha) e adicione um site no console. Preencha o que for pedido e certifique-se que estará usando a versão 3. Adicione `localhost` e `127.0.0.1` na seção de sites para que seja possível testar em ambiente de desenvolvimento. Você irá ter 2 chaves, que devem ser utilizadas nas variáveis a seguir.

**ATENÇÃO:** este site utiliza a versão 3. Se você criar chaves pra versão 2, a autenticação irá falhar.

##### RECAPTCHA_PUBLIC_KEY
No console do RECAPTCHA, esta variável deve ser preenchida com o valor de `site_key`.

##### RECAPTCHA_PRIVATE_KEY
No console do RECAPTCHA, esta variável deve ser preenchida com o valor de `secret_key`.

#### Categoria 4: Banco de Dados Postgres
Nos ambientes de *staging* e produção, recomenda-se usar um banco de dados mais robusto que o sqlite3 que é colocado por padrão no Django. Este projeto está configurado para usar o Postgres fora do ambiente de desenvolvimento.

Caso esteja rodando no Heroku, estas variáveis não serão utilizadas e podem ser deixadas em branco.

Para o banco de dados funcionar, você deve instalá-lo e configurá-lo. Para o download e instalação, eu recomendo seguir os passos da [página de downloads do Postgres](https://www.postgresql.org/download/linux/ubuntu/). Para a configuração inicial, recomendo ler a seção "Getting Started" do [manual oficial](https://www.postgresql.org/docs/manuals/). Deve ser o suficiente para este projeto, pois o Django cria as tabelas manualmente.

Uma vez que o banco esteja configurado, popule as variáveis a seguir:

##### DB_NAME
Nome do banco de dados criado.

##### DB_USER
Nome do usuário de acesso.

##### DB_PASS
Senha para o usuário da variável acima.

#### Categoria 5: AWS (Amazon Web Services)
Para melhorar o desempenho do site e para contornar limitações impostas por serviços como o Heroku, é necessário utilizar um serviço externo para entregar os arquivos de mídia registrado pelos usuários.

Para criar uma conta e configurá-la, recomendo assistir este tutorial: [Python Django Tutorial: Full-Featured Web App Part 13 - Using AWS S3 for File Uploads](https://www.youtube.com/watch?v=kt3ZtW9MXhw).

Uma vez que o serviço da AWS esteja configurado, preencha as variáveis a seguir:

##### AWS_ACCESS_KEY_ID
Nas credenciais baixadas do usuário, procure a chave correspondente ao mesmo nome desta variável.

##### AWS_SECRET_ACCESS_KEY
Nas credenciais baixadas do usuário, procure a chave correspondente ao mesmo nome desta variável.

##### AWS_STORAGE_BUCKET_NAME
Nome do *Bucket* devidamente configurado onde o Django deverá colocar os arquivos.

#### Categoria 6: Google Analytics
Recomendado para o ambiente de produção, apesar de estar disponível para *staging*, se julgar necessário verificar a utilização deste site também.

Entre na página do [Google Analytics](https://analytics.google.com/analytics/web/) e crie um novo projeto. Não é necessário copiar o código, apenas o ID de acompanhamento. Use-o para configurar a variável a seguir:

##### ANALYTICS_ID
ID de acompanhamento do Google Analytics.

## Executando em ambiente de desenvolvimento
Com o projeto baixado e devidamente configurado, execute os seguintes comandos no Terminal (ou Prompt de Comando):

1. `python manage.py migrate`
2. `python manage.py createsuperuser` (neste comando, crie um usuário, e-mail e senha)
3. `python manage.py runserver`
4. Abra o navegador e digite `localhost:8000` ou `127.0.0.1:8000`
5. Aproveite!
6. **P.S.:** entre em `localhost:8000/admin/` para cadastrar usuários, publicações, projetos, etc...

## Deployment
**Obs.:** Não se esqueça de mudar os valores de ALLOWED_HOSTS nas configurações de staging/produção pra os domínios ou endereços IPs que sejam os seus.

### Heroku
Para fazer o deploy deste projeto no Heroku, siga os passos abaixo:

 1. Crie uma conta no [Heroku](https://www.heroku.com/);
 2. Instale o [CLI do Heroku](https://devcenter.heroku.com/articles/heroku-cli) no seu computador;
 3. Crie um app com o comando `heroku apps:create example` (trocando example pelo nome do seu app, que deve possuir um nome único);
 4. Entre no seu dashboard e insira as variáveis de segredo configuradas anteriormente na seção *Config Vars*;
 5. Execute o comando `git push heroku master` no Terminal (ou Prompt de Comando) na pasta do projeto.

Talvez ocorra um erro na primeira vez que o app for colocado no ar. Isso se deve ao módulo django_heroku não encontrar a configuração inicial do banco de dados. Para resolver esse problema, dentro da pasta `site_core/settings`, abra o código da `staging.py` ou `production.py` (dependendo se vocês estiver fazendo deploy para um ou outro), copie o código da configuração da variável DATABASES e coloque antes da linha que contém `if config.get("SERVER_TYPE") == "heroku":`. Dê *commit* e rode o passo 5 de novo. O site não irá funcionar, mas o banco estará criado. Volte ao que estava antes, dê *commit* e rode novamente o passo 5. Após isso, o site deverá funcionar normalmente.

### Servidor Linux
Este é um processo bem mais complexo e com muitos passos. Recomendo seguir este tutorial passo a passo do Corey Schafer que está muito bem explicado: [Python Django Tutorial: Deploying Your Application (Option #1) - Deploy to a Linux Server](https://www.youtube.com/watch?v=Sa_kQheCnds).

De quebra, para configurar um domínio e habilitar um certificado SSL (para habilitar navegação por HTTPS), recomendo estes dois vídeos também do Corey Schafer:

 - [Python Django Tutorial: How to Use a Custom Domain Name for Our Application](https://www.youtube.com/watch?v=D2lwk1Ukgz0);
 - [Python Django Tutorial: How to enable HTTPS with a free SSL/TLS Certificate using Let's Encrypt](https://www.youtube.com/watch?v=NhidVhNHfeU).

## Leitura complementar
Para entender mais sobre este projeto e Django em geral, recomendo esses links:

 - [Documentação oficial do Django](https://docs.djangoproject.com/pt-br/2.2/) (sério, é muito util e essencial pros primeiros passos);
 - [Django Tutorials - Corey Schafer](https://www.youtube.com/playlist?list=PL-osiE80TeTtoQCKZ03TU5fNfx2UY6U4p).

