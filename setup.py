from setuptools import setup

setup(
    name="baku-mailgun",
    version="1.0.0",
    description="Módulo que permite enviar correos por mailgun",
    author="Rodrigo Arriaza",
    author_email="hello@lastseal.com",
    url="https://www.lastseal.com",
    packages=['baku'],
    install_requires=[ 
        i.strip() for i in open("requirements.txt").readlines() 
    ]
)
