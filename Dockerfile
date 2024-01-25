FROM httpd:bookworm

RUN apt-get update -y
RUN apt-get install -y \
       apache2 \
       apache2-utils \
       apt-utils \
       curl \
       libapache2-mod-wsgi-py3 \
       locales \
       python3 \
       python3-flask \
       python3-mysqldb \
       python3-repoze.lru \
       python3-requests \
       python3-wtforms \
       vim

RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales

RUN a2enmod remoteip && \
    a2enmod headers

ADD app /srv/app
ADD apache-site.conf /etc/apache2/sites-available/000-default.conf

RUN a2enmod auth_basic

RUN ls -l /etc/apache2/mods-enabled

ENV LANG en_US.UTF-8

EXPOSE 80
CMD ["apache2ctl", "-D", "FOREGROUND"]

