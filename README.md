
# The Beer Machine

Another fermentation temperature controller designed to run on the raspberry-pi family.
I'm currently using and testing it on a Raspberry pi zero W, but it should also work out of box for models 2 and 3.

## Quick start

```bash
git clone http://github.com/g-aubertin/beer_machine
ln -s beer_machine/systemd/beer_machine.service /lib/systemd/system/
ln -s beer_machine/systemd/node_server.service /lib/systemd/system/
systemctl enable beer_machine
systemctl enable node_server
```
then reboot.

## What's next for v0.2

#### UI
* print batch name and temperature from DB
* refresh chart when new data is available
* Update John Doe bar
* add login screen
* For new recipes, display proper message on page instead of no chart
* add 'Brew history' feature
* add true statistics
* json transfer too slow / try other options
* try preview bar below chart

#### hydrometer
* update DB architecture to get density and liquid temperature
* update Highchart to support 2 more datasets

#### daemon
* rework IPC with dedicated thread
* fix status field in DB when calling 'stop' from the UI
* to check fields in the DB when starting : if more than 1 is started, return error

#### build and deployment
* use docker
