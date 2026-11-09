"""Schnittbild Innenstange mit Klemmbock (Erklärgrafik)."""
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
fig, ax = plt.subplots(figsize=(9, 5.2))
def R(x0, z0, x1, z1, f):
    ax.add_patch(Rectangle((x0, z0), x1 - x0, z1 - z0, fc=f, ec="black", lw=0.8))
R(237, -14, 243, 24, "#B8B8B8"); ax.text(240, 24.8, "M6-Stange\nR 240", ha="center", fontsize=9)
R(234.25, -10.6, 245.75, -5.6, "#8C8C8C"); R(234.25, -5.6, 245.75, -0.6, "#8C8C8C"); R(234.8, -0.6, 245.2, 0, "#C8C8C8")
ax.text(229, -6, "Mutter +\nKontermutter\n(gegeneinander)", ha="right", va="center", fontsize=9)
R(232, 0, 262, 6, "#D85A30"); ax.text(247, -2.5, "Innenkonsole", ha="left", va="center", fontsize=9)
R(250, 6, 275, 9.9, "#9EC1E6"); R(250, 9.9, 254, 13.9, "#9EC1E6")
R(255.8, 6, 260.2, 9.4, "white"); R(256, 6, 260, 9, "#D85A30")
ax.text(268, 8, "Wendelplatte 3,9 mm", ha="center", va="center", fontsize=9)
ax.annotate("Randleiste", (252.5, 12), (262, 13.5), fontsize=9, arrowprops=dict(arrowstyle="-", lw=0.7))
ax.annotate("Stift im Langloch", (258, 7.5), (264, -7), fontsize=9, arrowprops=dict(arrowstyle="-", lw=0.7))
R(234, 6, 249.5, 13.7, "#2E6FB0"); R(234, 13.7, 255, 16.7, "#2E6FB0"); R(237, 6, 243, 16.7, "#B8B8B8")
ax.text(246, 10, "Klemm-\nbock", ha="center", va="center", fontsize=9, color="white")
ax.annotate("drückt mit 0,2 mm\nVorspannung", (253, 15.2), (259, 22), fontsize=9, color="#2E6FB0",
            arrowprops=dict(arrowstyle="->", lw=0.9, color="#2E6FB0"))
R(234.8, 16.7, 245.2, 17.3, "#C8C8C8"); R(234.25, 17.3, 245.75, 22.3, "#8C8C8C")
ax.text(229, 19.5, "Scheibe + Mutter\n(nur hier oben)", ha="right", va="center", fontsize=9)
ax.set_xlim(205, 285); ax.set_ylim(-16, 30); ax.set_aspect("equal"); ax.axis("off")
ax.set_title("Innenstange im Schnitt: Klemmbock hält Platte und Konsole fest", fontsize=11)
fig.savefig("Klemmbock_Schnitt.png", dpi=120, bbox_inches="tight", facecolor="white")
