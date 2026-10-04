# Notebook in Docker and VS Code

The committed [examples.ipynb](../examples.ipynb) shows the generated samples.
Its AI-enabled cells make paid calls when rerun; approve that cost before running
the whole notebook. CLI `--no-ai` is the free starting point.

```bash
docker compose up -d jupyter
```

In VS Code, open `examples.ipynb`, choose **Select Kernel → Existing Jupyter
Server**, then connect to `http://127.0.0.1:8888/?token=everymd` and select
**everymd (Docker)**. A browser can use the same local address.

The port is bound to loopback. The default token is a documented local
development value, not a private credential; use a private `JUPYTER_TOKEN`
for your own setup. Do not expose the server to a public network.

Stop it with `docker compose stop jupyter`.
Notebook output regeneration changes committed sample artifacts; review rights,
private paths and estimated spend before committing them.
