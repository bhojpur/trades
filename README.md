# Bhojpur Trades - Data Processing Engine

The `Bhojpur Trades` is a secure, high performance, electronic trading system applied
within the [Bhojpur.NET Platform](https://github.com/bhojpur/platform/) ecosystem for
delivery of `applications` or `services`.

## Python-based Trading Server

Firstly, you need to install `Python` >= 3.8 runtime to be able to run the server. Also,
install [TA-Lib](https://mrjbq7.github.io/ta-lib/) framework for technical analysis.

```bash
brew install ta-lib
pip3 install TA-Lib numpy plotly pymongo websocket
```

Additionally, you need `numpy`, `plotly`, `pymongo`, `websocket` libraries.

then, set environment variables and run the trading server using the following commands.

```bash
export BITMEX_API_KEY=test
export BITMEX_API_SECRET=test
python3 pkg/server/server.py
```
