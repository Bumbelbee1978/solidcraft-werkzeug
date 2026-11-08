"""Vorschaubilder auf den Inhalt zuschneiden (Hintergrund-Verlauf erkennen) und mit Rand speichern."""
import numpy as np
from PIL import Image


def zuschneiden(pfad, ziel=None, rand=30, schwelle=14):
    im = Image.open(pfad).convert("RGB")
    a = np.asarray(im).astype(int)
    hg = np.median(np.concatenate([a[:, :6], a[:, -6:]], axis=1), axis=1)      # Hintergrund je Zeile
    diff = np.abs(a - hg[:, None, :]).sum(axis=2)
    maske = diff > schwelle
    ys, xs = np.where(maske)
    if len(xs) == 0:
        im.save(ziel or pfad)
        return
    x0, x1 = max(xs.min() - rand, 0), min(xs.max() + rand, a.shape[1])
    y0, y1 = max(ys.min() - rand, 0), min(ys.max() + rand, a.shape[0])
    im.crop((x0, y0, x1, y1)).save(ziel or pfad)
