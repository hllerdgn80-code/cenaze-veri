#!/usr/bin/env python3
"""L13 logosunu (marka/svg/L13.svg) ek kütüphane olmadan PNG'ye çizer (saf Python: zlib + struct).
Çıktı:
  uygulama/assets/ikon/ikon.png       1024x1024, kömür zemin + logo (uygulama simgesi)
  uygulama/assets/ikon/ikon_on.png    1024x1024, saydam zemin, logo güvenli alanda (Android uyarlanır simge ön katmanı)
  deploy/magaza/ikon-512.png          512x512 (Play Console yüksek çözünürlüklü simge)
Logo geometrisi L13.svg ile birebir aynıdır (yarım çizim + aynalama)."""
import math, pathlib, struct, zlib
U = pathlib.Path(__file__).resolve().parent.parent
K = U.parent
KOMUR, ALTIN, KREM = (0x25, 0x28, 0x2D), (0xC9, 0xA4, 0x5C), (0xF2, 0xEB, 0xDD)

def bezier(p0, p1, p2, p3, n=400):
    for i in range(n + 1):
        t = i / n; m = 1 - t
        yield (m**3*p0[0] + 3*m*m*t*p1[0] + 3*m*t*t*p2[0] + t**3*p3[0],
               m**3*p0[1] + 3*m*m*t*p1[1] + 3*m*t*t*p2[1] + t**3*p3[1])

def yarim():
    """L13 sol yarısı: (tür, veri, renk)"""
    a = list(bezier((512, 214), (430, 256), (326, 306), (318, 456))) + [(318, 456 + i) for i in range(0, 351)]
    b = list(bezier((512, 322), (462, 350), (398, 384), (394, 476))) + [(394, 476 + i) for i in range(0, 331)]
    return [("cizgi", (a, 22), ALTIN), ("cizgi", (b, 12), ALTIN),
            ("dikdortgen", (276, 806, 236, 22), ALTIN),
            ("dikdortgen", (420, 690, 92, 44), KREM), ("dikdortgen", (436, 734, 18, 72), KREM)]

def sekiller():
    out = []
    for tur, v, renk in yarim():
        out.append((tur, v, renk))
        if tur == "cizgi":
            out.append((tur, ([(1024 - x, y) for x, y in v[0]], v[1]), renk))
        else:
            x, y, w, h = v
            out.append((tur, (1024 - x - w, y, w, h), renk))
    return out

def ciz(boyut, olcek, zemin):
    """boyut: çıktı kenarı; olcek: logo ölçeği (1 = SVG kadar); zemin: None = saydam"""
    W = boyut
    k = W / 1024 * olcek
    ox = oy = W / 2 - 512 * k
    katman = {ALTIN: [0.0] * (W * W), KREM: [0.0] * (W * W)}
    for tur, v, renk in sekiller():
        A = katman[renk]
        if tur == "dikdortgen":
            x0, y0 = ox + v[0] * k, oy + v[1] * k
            x1, y1 = x0 + v[2] * k, y0 + v[3] * k
            for py in range(max(0, int(y0)), min(W, int(math.ceil(y1)))):
                cy = max(0.0, min(py + 1, y1) - max(py, y0))
                for px in range(max(0, int(x0)), min(W, int(math.ceil(x1)))):
                    cx = max(0.0, min(px + 1, x1) - max(px, x0))
                    i = py * W + px
                    A[i] = min(1.0, A[i] + cx * cy)
        else:
            nok, gen = v
            r = gen * k / 2
            onceki = None
            for x, y in nok:
                x, y = ox + x * k, oy + y * k
                if onceki and math.hypot(x - onceki[0], y - onceki[1]) < 0.35:
                    continue
                onceki = (x, y)
                for py in range(max(0, int(y - r - 1)), min(W, int(y + r + 2))):
                    for px in range(max(0, int(x - r - 1)), min(W, int(x + r + 2))):
                        d = math.hypot(px + 0.5 - x, py + 0.5 - y)
                        c = r + 0.5 - d
                        if c > 0:
                            i = py * W + px
                            if c > 1: c = 1.0
                            if c > A[i]: A[i] = c
    satirlar = []
    for py in range(W):
        s = bytearray([0])
        for px in range(W):
            i = py * W + px
            if zemin:
                rgb, al = list(zemin), 1.0
            else:
                rgb, al = [0, 0, 0], 0.0
            for renk in (ALTIN, KREM):
                c = katman[renk][i]
                if c:
                    if al == 0:
                        rgb, al = list(renk), c
                    else:
                        rgb = [rgb[j] * (1 - c) + renk[j] * c for j in range(3)]
                        al = al + c * (1 - al)
            s += bytes([int(round(rgb[0])), int(round(rgb[1])), int(round(rgb[2])), int(round(al * 255))])
        satirlar.append(bytes(s))
    return W, b"".join(satirlar)

def png(yol, W, ham):
    def parca(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    veri = b"\x89PNG\r\n\x1a\n" + parca(b"IHDR", struct.pack(">IIBBBBB", W, W, 8, 6, 0, 0, 0)) + \
        parca(b"IDAT", zlib.compress(ham, 9)) + parca(b"IEND", b"")
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_bytes(veri)
    print(yol.relative_to(K), len(veri), "bayt")

if __name__ == "__main__":
    png(U / "assets/ikon/ikon.png", *ciz(1024, 1.0, KOMUR))
    png(U / "assets/ikon/ikon_on.png", *ciz(1024, 0.78, None))   # uyarlanır simge: logo %66 güvenli dairenin içinde
    png(K / "deploy/magaza/ikon-512.png", *ciz(512, 1.0, KOMUR))
