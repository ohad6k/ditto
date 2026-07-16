# ditto-cli is now emulo

This package is a redirect, not a product.

`ditto` was renamed to **emulo** in v0.5.0. The old name collided with several
existing products, including [heyditto.ai](https://heyditto.ai) (agent memory,
the same category), [ditto.live](https://ditto.live) (an edge-sync database),
and a `ditto` skill already on ClawHub.

## What you should do

```
pip install emulo
```

Then run `emulo` instead of `ditto`.

## What this package does

It depends on `emulo`, prints a one-line notice, and forwards your command
through, so anything you already had scripted keeps working:

```
ditto --card      # still works, still prints your card, just tells you to move
```

Nothing about your data changes. Your existing `~/.ditto` home, `DITTO_HOME`,
`ditto-out/` directory, and old profile markers are all still read by emulo.

Full notes: <https://github.com/ohad6k/emulo/releases/tag/v0.5.0>
