# Pull base image.
FROM ubuntu:20.04

# Set default WORKDIR in container
WORKDIR /usr/src/app

# For log message in container
ENV PYTHONUNBUFFERED 1

# Update apt-get and apt
RUN apt-get update -y

# Install Firefox.deb
RUN apt-get install -y software-properties-common
RUN add-apt-repository ppa:mozillateam/ppa
RUN echo 'Package: * Pin: release o=LP-PPA-mozillateam Pin-Priority: 1001' | tee /etc/apt/preferences.d/mozilla-firefox
RUN echo 'Unattended-Upgrade::Allowed-Origins:: "LP-PPA-mozillateam:${distro_codename}";' | tee /etc/apt/apt.conf.d/51unattended-upgrades-firefox
RUN apt-get install -y firefox

# Install python 3
RUN apt-get install -y python3 python3-pip
RUN pip3 install requests BeautifulSoup4 selenium webdriver_manager

# Update the repository
COPY baha_crawler.py /home/Crawler/baha_crawler.py
COPY dcard_selenium_crawler.py /home/Crawler/dcard_selenium_crawler.py
COPY main.py /home/Crawler/main.py
COPY ptt_crawler.py /home/Crawler/ptt_crawler.py
