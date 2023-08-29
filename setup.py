from setuptools import setup

setup(
    name="baku-api",
    version="1.0.1",
    description="Módulo que permite realizar consultas a los servicios REST/API",
    author="Rodrigo Arriaza",
    author_email="hello@lastseal.com",
    url="https://www.lastseal.com",
    packages=['baku'],
    install_requires=[ 
        i.strip() for i in open("requirements.txt").readlines() 
    ]
)
