"""
Creates the sections of the About page, which used to be written in its
templates (one per language). Their pictures are copied from the static files
to the media storage, resized and converted to WebP like the ones uploaded in
the editor. From then on, they're edited at /about/ (or in the admin).
"""
from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import migrations
from PIL import Image, ImageOps

STATIC_IMAGES = Path(__file__).resolve().parent.parent / 'static' / 'img'

# Same as base.forms.ABOUT_IMAGE_MAX_SIZE when this migration was written
IMAGE_MAX_SIZE = 1200

SECTIONS = [
    {
        'slug': 'about-me',
        'image': 'IMG_9126.jpeg',
        'translations': {
            'en': {
                'title': 'About me',
                'image_caption': 'Photo at the Grand Canyon.',
                'content': """\
My name is Daniel Lavedonio de Lima and I'm curious by nature. I'm an electrical engineer working with data, and I've always been excited about technology and its power to change the world.

That curiosity is what brought me here: I'm always looking for new things to learn and, whenever I can, for ways to put them into practice and make a difference, even a small one. If something on this website helps you somehow, I'll be one step closer to that.

This website is itself a result of that: a place to keep and share my projects and ideas, and a project in its own right, which taught me how the internet works from the side of who runs a website, not just who visits it.

Below you'll find more about my education, my career, my projects and how to work with me.
""",
            },
            'pt-br': {
                'title': 'Sobre mim',
                'image_caption': 'Foto no Grand Canyon.',
                'content': """\
Meu nome é Daniel Lavedonio de Lima e sou um curioso por natureza. Sou engenheiro eletricista, trabalho com dados e sempre fui muito empolgado com tecnologia e seu poder de transformar o mundo.

Foi essa curiosidade que me trouxe até aqui: estou sempre buscando aprender coisas novas e, quando possível, colocá-las em prática para causar alguma mudança, mesmo que pequena. Se algo neste site puder te ajudar de alguma forma, já estarei um passo mais perto disso.

Este site é, ele mesmo, fruto disso: um lugar para guardar e compartilhar meus projetos e ideias e também um projeto por si só, com o qual aprendi como a internet funciona do lado de quem mantém um site, e não só de quem o visita.

Abaixo você encontra mais sobre a minha formação, a minha carreira, os meus projetos e como trabalhar comigo.
""",
            },
        },
    },
    {
        'slug': 'education',
        'image': 'about-education.jpeg',
        'translations': {
            'en': {
                'title': 'Education',
                'image_caption': 'At the Electrical Engineering building of Poli-USP.',
                'content': """\
I studied Electrical Engineering with an emphasis on Computing at the [Polytechnic School of the University of São Paulo (Poli-USP)](https://www.poli.usp.br/), graduating in 2020.

In my first semester, I joined [Poli Júnior](https://www.polijunior.com.br/), the first engineering junior enterprise in Brazil, where I worked on Production Engineering and Computer Engineering projects, in the latter also as a manager. I was also one of the organizers of the 12th Ser Empreendedor, an event that promotes entrepreneurship among university students.

In my 5th and 6th semesters, I was the Systems Coordinator at [FEJESP](https://www.fejesp.org.br/), the Federation of Junior Enterprises of the State of São Paulo, where I was responsible for migrating its website and its e-mail system.

Towards the end of my degree, I took part in *BioGadget*, an undergraduate research project that used *Bluetooth Low Energy (BLE)* to build trackers for studies of wild animals. Although I didn't stay until the end, it gave me the chance to get to know the academic world.

I'm currently pursuing a master's degree at the [Department of Electronic Systems Engineering](https://www.psi.poli.usp.br/) of Poli-USP, researching the robustness of Natural Language Processing (NLP) systems against character-based adversarial attacks.
""",
            },
            'pt-br': {
                'title': 'Educação',
                'image_caption': 'No prédio da Engenharia Elétrica da Poli-USP.',
                'content': """\
Estudei Engenharia Elétrica com ênfase em Computação na [Escola Politécnica da USP (Poli-USP)](https://www.poli.usp.br/), tendo me formado em 2020.

Já no 1º semestre, entrei para a [Poli Júnior](https://www.polijunior.com.br/), a primeira empresa júnior de engenharia do Brasil, onde participei de projetos de Engenharia de Produção e de Computação, nesta última também como gerente. Também fui um dos organizadores do 12º Ser Empreendedor, um evento de fomento ao empreendedorismo universitário.

Nos 5º e 6º semestres, fui Coordenador de Sistemas da [FEJESP](https://www.fejesp.org.br/), a Federação das Empresas Juniores do Estado de São Paulo, onde fui o responsável pela mudança do site e do sistema de e-mails.

Na parte final da graduação, participei do projeto de Iniciação Científica *BioGadget*, que usava a tecnologia *Bluetooth Low Energy (BLE)* para criar rastreadores para estudos de animais silvestres. Apesar de não ter ficado até o final, ele me permitiu conhecer melhor o mundo acadêmico.

Atualmente curso um mestrado acadêmico (*stricto sensu*) no [Departamento de Engenharia de Sistemas Eletrônicos](https://www.psi.poli.usp.br/) da Poli-USP (PSI), pesquisando a robustez de sistemas de Processamento de Linguagem Natural (PLN) contra ataques adversários baseados em caracteres.
""",
            },
        },
    },
    {
        'slug': 'career',
        'image': 'IMG_2777.jpeg',
        'translations': {
            'en': {
                'title': 'Career',
                'image_caption': 'Photo at my first internship.',
                'content': """\
I started my career in data and have stayed in it ever since, going from automating spreadsheets to building data platforms in the cloud.

**Marisa** (December 2017 – January 2018): in my first internship, I watched analysts and interns put together the same Excel reports by hand every single day. After a talk with my boss, I spent the rest of my summer internship automating them with VBA.

**Medcel** (January – June 2019): besides more VBA automation, I helped the data analyst with SQL queries, Tableau dashboards and Python scripts. I also built a web scraper with Selenium to find everyone who passed medical residency exams and which of them had been our customers, in time for a board meeting two weeks later.

**Mobly** (July – November 2019): in a bigger team, I got to know the work of a data engineer up close, along with tools like Apache Airflow and Pentaho and, for the first time, the cloud, on AWS. That's when I decided to move fully into data engineering.

**Revelo** (December 2019 – February 2021): I joined as a "senior intern" and was soon promoted to data engineer, the only one in the company. My main project took the analysts' queries off the production database: an Airflow instance on GCP copied a replica of the Postgres database on AWS to Google Cloud Storage and loaded it into BigQuery, all built from scratch. At the end of 2020, I also took on SRE duties, automating my projects with GitHub Actions and adding observability with Prometheus and Grafana.

**InfoPrice** (from March 2021): in my first job after graduating, I joined a data engineering team whose data was, for the first time, the company's main product instead of the back office. There I worked on one of the projects I'm proudest of: cutting the cost of the Spark jobs on AWS EMR by moving their machines from On-Demand to Spot instances.
""",
            },
            'pt-br': {
                'title': 'Carreira',
                'image_caption': 'Foto no primeiro estágio.',
                'content': """\
Comecei minha carreira na área de dados e sigo nela desde então, indo da automação de planilhas à construção de plataformas de dados na nuvem.

**Marisa** (dezembro de 2017 – janeiro de 2018): no meu primeiro estágio, via analistas e estagiários montarem à mão os mesmos relatórios de Excel todos os dias. Depois de uma conversa com o meu chefe, passei o resto do estágio de férias automatizando esses relatórios com VBA.

**Medcel** (janeiro – junho de 2019): além de mais automações em VBA, ajudei a analista de dados com queries SQL, dashboards no Tableau e scripts em Python. Também criei um web scraper com Selenium para buscar todos os aprovados em provas de residência médica e quais deles tinham sido nossos clientes, a tempo de serem apresentados na reunião de diretoria duas semanas depois.

**Mobly** (julho – novembro de 2019): numa equipe maior, conheci de perto o trabalho do engenheiro de dados, ferramentas como Apache Airflow e Pentaho e, pela primeira vez, a nuvem, na AWS. Foi aí que decidi entrar de vez na área de engenharia de dados.

**Revelo** (dezembro de 2019 – fevereiro de 2021): entrei como "estagiário sênior" e logo fui promovido a engenheiro de dados, o único da empresa. Meu principal projeto tirou as queries dos analistas do banco de dados de produção: uma instância do Airflow na GCP copiava uma réplica do banco Postgres da AWS para o Google Cloud Storage e carregava os dados no BigQuery, tudo construído do zero. No final de 2020, também assumi atribuições de SRE, automatizando meus projetos com GitHub Actions e adicionando observabilidade com Prometheus e Grafana.

**InfoPrice** (a partir de março de 2021): no meu primeiro emprego depois de formado, entrei num time de engenharia de dados em que, pela primeira vez, os dados não eram o backoffice, e sim o produto principal da empresa. Lá trabalhei em um dos projetos de que mais me orgulho: reduzir o custo dos jobs Spark no AWS EMR, trocando as máquinas On-Demand por Spot.
""",
            },
        },
    },
    {
        'slug': 'projects',
        'image': 'IMG_9205.jpeg',
        'translations': {
            'en': {
                'title': 'Projects',
                'image_caption': 'Debugging a project.',
                'content': """\
Building things is one of the ways I learn best, which is why I keep personal projects going: to make my own work easier, to practice and learn new concepts, or simply because I felt like it.

The biggest one is this website. In August 2019, I decided to make an old dream come true: a place on the internet that's truly mine, where I can share my projects and ideas without the limits of social networks. I built it from scratch with Python and Django, and it went live in April 2020. Its code is open source and this is its second version.

Another one is Pong, a recreation of the greatest video game classic, which started in an online JavaScript course and that I reworked so it can also be played on phones and other touch screens.

You'll find them, and the stories behind them, on the [Projects](/projects/) page and in the [Blog](/blog/). More of my code is on my [GitHub](https://github.com/Lavedonio).
""",
            },
            'pt-br': {
                'title': 'Projetos',
                'image_caption': 'Debugando um projeto.',
                'content': """\
Construir coisas é uma das formas como eu mais aprendo, por isso costumo manter projetos pessoais: para facilitar meu próprio trabalho, para praticar e aprender novos conceitos ou simplesmente porque deu vontade.

O maior deles é este site. Em agosto de 2019, decidi colocar em prática um sonho antigo: ter um espaço na internet legitimamente meu, onde eu pudesse mostrar meus projetos e pensamentos sem as limitações das redes sociais. Construí tudo do zero, com Python e Django, e o site foi ao ar em abril de 2020. O código é aberto e esta é a sua segunda versão.

Outro é o Pong, uma recriação do maior clássico dos videogames, que começou num curso online de JavaScript e que adaptei para ser jogado também no celular e em outras telas touch.

Você encontra esses projetos, e as histórias por trás deles, na página de [Projetos](/projetos/) e no [Blog](/blog/). Outros códigos meus estão no meu [GitHub](https://github.com/Lavedonio).
""",
            },
        },
    },
    {
        'slug': 'hiring',
        'image': 'about-contract2.jpeg',
        'translations': {
            'en': {
                'title': 'How to hire me',
                'image_caption': 'Graduation photo.',
                'content': """\
I'm a data engineer: I design, build and maintain data pipelines and platforms, automate processes and make the most of cloud services. Over the years I've worked with Python, SQL, Apache Airflow, Spark, AWS and Google Cloud, and I also build web applications with Django, like this website.

If you have a job opportunity, a project or an idea you'd like to talk about, [send me a message](/contact/) or reach out on [LinkedIn](https://www.linkedin.com/in/daniel-lavedonio-de-lima/). A few lines about the problem you want to solve and your timeline help me give you a useful answer.
""",
            },
            'pt-br': {
                'title': 'Como contratar',
                'image_caption': 'Foto da formatura.',
                'content': """\
Sou engenheiro de dados: projeto, construo e mantenho pipelines e plataformas de dados, automatizo processos e tiro o melhor proveito de serviços em nuvem. Ao longo da carreira, trabalhei com Python, SQL, Apache Airflow, Spark, AWS e Google Cloud, e também desenvolvo aplicações web com Django, como este site.

Se você tem uma oportunidade de trabalho, um projeto ou uma ideia sobre a qual gostaria de conversar, [me mande uma mensagem](/contato/) ou me chame no [LinkedIn](https://www.linkedin.com/in/daniel-lavedonio-de-lima/). Algumas linhas sobre o problema que você quer resolver e o seu prazo me ajudam a dar uma resposta útil.
""",
            },
        },
    },
]

# Leaves room to add sections in between later
ORDER_STEP = 10


def save_image(filename):
    """Saves a WebP version of a static image as about/<name>.webp and returns (name, width, height)."""
    name = f'about/{Path(filename).stem}.webp'

    # Reused if it's already there (e.g. the test database is created from the migrations at every run)
    if default_storage.exists(name):
        with default_storage.open(name) as stored, Image.open(stored) as image:
            return name, image.width, image.height

    with Image.open(STATIC_IMAGES / filename) as image:
        image = ImageOps.exif_transpose(image).convert('RGB')
        image.thumbnail((IMAGE_MAX_SIZE, IMAGE_MAX_SIZE), Image.Resampling.LANCZOS)
        output = BytesIO()
        image.save(output, format='WEBP', quality=85, method=6)
        size = image.size

    return default_storage.save(name, ContentFile(output.getvalue())), *size


def create_sections(apps, schema_editor):
    AboutSection = apps.get_model('base', 'AboutSection')
    AboutSectionTranslation = apps.get_model('base', 'AboutSectionTranslation')
    if AboutSection.objects.exists():
        return

    for index, data in enumerate(SECTIONS, start=1):
        image, width, height = save_image(data['image'])
        section = AboutSection.objects.create(
            order=index * ORDER_STEP, slug=data['slug'], image=image, image_width=width, image_height=height,
        )
        for language, texts in data['translations'].items():
            AboutSectionTranslation.objects.create(section=section, language=language, **texts)


def delete_sections(apps, schema_editor):
    AboutSection = apps.get_model('base', 'AboutSection')
    AboutSection.objects.filter(slug__in=[data['slug'] for data in SECTIONS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_sections, delete_sections),
    ]
