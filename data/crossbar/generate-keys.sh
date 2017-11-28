#!/usr/bin/env bash


CBDIR='.'
openssl dhparam -out ${CBDIR}/dhparam.pem 4096
openssl req -nodes -newkey rsa:4096 -x509 -days 9999 -keyout ${CBDIR}/server_key.pem \
        -subj '/C=NL/ST=Amsterdam/L=Amsterdam/O=VU/CN=MDStudio/' \
        -out ${CBDIR}/server_cert.pem