# Arduino — capteur DHT22

Ce dossier est pour le code qui tourne **sur l'Arduino lui-même** (pas sur le
serveur). Rien à voir avec `backend/` : ici c'est du C++ qui va être flashé
sur la carte avec l'IDE Arduino, pas du Python.

## À quoi ça sert

Besoin STA-01 du cahier des charges : relever température et humidité via un
capteur DHT22 (AM2302) branché sur l'Arduino. L'Arduino lit le capteur et
envoie les valeurs au PC par le câble USB (liaison série).

## Format envoyé sur le port série

Le sketch (`carte_complete.ino`, ESP32) envoie une ligne texte, pas du
JSON :

```
Temperature: 22.4 C | Humidite: 45 % | Gaz: 612
```

Il envoie aussi, de temps en temps, une ligne `ALERTE ...` séparée — ce
n'est pas une mesure, `backend/services/dht22.py` l'ignore et essaie la
ligne suivante.

Le "Gaz" (capteur MQ, qualité de l'air) est lu par la carte mais pas
encore utilisé côté `backend/` — pas de colonne dédiée pour l'instant.

## Câblage

DHT22 sur une broche digitale de l'Arduino/ESP32 (+ résistance de pull-up
~10kΩ entre data et VCC si le module n'en a pas déjà une intégrée).

## Qui s'en occupe

Rôle "Matériel et capteurs" (section 12 du cahier des charges).

## Config côté serveur

Le port série et le débit (baud rate) auquel le serveur écoute sont dans
`config.yaml` (section `dht22`). Le nom du port dépend de l'OS et de la
machine :

- Windows : `COM3`, `COM4`... (visible dans le Gestionnaire de périphériques)
- Linux : `/dev/ttyUSB0` ou `/dev/ttyACM0` (visible avec `ls /dev/tty*` avant/après avoir branché l'Arduino)

Chacun met la valeur qui correspond à sa propre machine dans son
`config.yaml` local (pas besoin de la committer si elle change d'un poste à
l'autre).
