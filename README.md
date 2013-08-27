radiothon
=========
A donation taking and tracking system

## Introduction

This Django application, called _radiothon_, implements a donation-taking system.

If an organization wants to have a fundraiser, it needs some sort of form to take donors' information.

Donors contact the fundraising organization asking to donate a pledge to the organization,
and their pledge may be rewarded with a premium.

## Requirements
  - Python 2.6
  - MySQL server

## Installation Instructions

    git clone https://github.com/cvializ/radiothon
    
  In your MySQL server, create a `radiothon` database
  Create a virtual clean Python 2.6 environment for the Apache mod_wsgi module to use
    
    cd radiothon
    virtualenv venv
    
  Activate the virtual Python environment and install the Python modules that radiothon needs
    
    source venv/bin/activate
    pip install -r requirements.txt

## Configuration

### Configuring _radiothon_

  python manage.py sqlall radiothon

### Configuring Apache

## 


