# MOTU AVB Websocket Bridge

A service to bridge HTTP messages from a MOTU AVB interface's datastore API to an OSC Server, such as TouchOSC.

* For Datastore API, see [MOTU AVB Datastore API Docs](https://cdn-data.motu.com/downloads/audio/AVB/docs/MOTU%20AVB%20Web%20API.pdf)
* For OSC Reference, see [MOTU AVB OSC Reference](https://cdn-data.motu.com/downloads/audio/AVB/docs/OSC%20Quick%20Reference.pdf)

# Usage

In the command line at the project root, run:

```
./run <OSC SERVER NAME> --avbserver http://localhost:8888
```

The "OSC SERVER NAME" is the ZeroConf (Bonjour) name of the OSC server that will be listening for messages, e.g. for  touchOSC this might be "iPhone [iPhone] (TouchOSC)". The application will wait for this server to become available, connect to it and begin long-polling the MOTU AVB device to listen for changes. The service will relay any changes to the OSC server as OSC messages. For TouchOSC Configuration, see [OSC Connection](https://hexler.net/touchosc-mk1/manual/configuration-connections-osc#:~:text=Port%20(incoming),receiving%20OSC%20messages%20with%20TouchOSC.)

The "AVB Server" is the URI of the MOTU AVB device to which the service will connect and relay any datastore updates. For a 1248, this might be http://1248.local. For testing connectivity to a virtual MOTU AVB device, use my [MOTU Development AVB Server](https://github.com/ChristopherJohnston/motu_server) repository.

# Reference

* [Python-ZeroConf Async Browser](https://github.com/python-zeroconf/python-zeroconf/blob/master/examples/async_browser.py)
* [Python-OSC Client/Server](https://pypi.org/project/python-osc/)