# Arduino — capteur DHT22

Ce dossier est pour le code qui tourne **sur l'Arduino lui-même** (pas sur le
serveur). Rien à voir avec `backend/` : ici c'est du C++ qui va être flashé
sur la carte avec l'IDE Arduino, pas du Python.

## À quoi ça sert

Besoin STA-01 du cahier des charges : relever température et humidité via un
capteur DHT22 (AM2302) branché sur l'Arduino. L'Arduino lit le capteur et
envoie les valeurs au PC par le câble USB (liaison série).

## Ce qu'il reste à faire

- `dht22_reader/dht22_reader.ino` : le sketch Arduino qui lit le DHT22
  (bibliothèque `DHT sensor library` d'Adafruit) et envoie les valeurs sur le
  port série, à un intervalle régulier.
- Décider du format envoyé (ex: une ligne JSON `{"temperature":22.5,"humidite":45.2}`)
  et le documenter ici une fois choisi — c'est ce format que le service Python
  côté `backend/` devra lire.
- Câblage : DHT22 sur une broche digitale de l'Arduino (+ résistance de
  pull-up ~10kΩ entre data et VCC si le module n'en a pas déjà une intégrée).

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
