// Çizgi ikonlar (prototipteki SVG'ler birebir): 24×24, 1.6 çizgi, yuvarlak uç; dolgu yok.
import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';

const Map<String, String> _yollar = {
  'ay': '<path d="M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z"/>',
  'gunes': '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
  'ok': '<path d="M9 6l6 6-6 6"/>',
  'geri': '<path d="M15 5l-7 7 7 7"/>',
  'asagi': '<path d="M7 10l5 5 5-5"/>',
  'ara': '<circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/>',
  'isaret': '<path d="M7 3h10v18l-5-4-5 4z"/>',
  'kemer': '<path d="M6 21V11a6 6 0 0 1 12 0v10M4 21h16M10 21v-4h4v4"/>',
  'tik': '<circle cx="12" cy="12" r="9"/><path d="M8 12.5l3 3 5-6"/>',
  'uyari': '<path d="M12 3l10 18H2z"/><path d="M12 10v5M12 18v.01"/>',
  'konum': '<path d="M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/>',
  'cb': '<path d="M7 21h10M8 18h8M9 18V9M15 18V9M12 18V9M8 9h8M7 6h10l-1 3H8z"/>',
  'bb': '<path d="M7 21h10M8 18h8M9 18V9M15 18V9M12 18V9M8 9h8M7 6h10l-1 3H8z"/>',
  'bak': '<path d="M10 4h4v4.5c0 .8.4 1.5 1 2l1 .8V13H8v-1.7l1-.8c.6-.5 1-1.2 1-2z"/><path d="M5 16h14v3H5zM8 21h8"/>',
  'siy': '<path d="M5 8h14l-2 4H7z"/><path d="M10 12v8M14 12v8M8 21h8M12 8V5"/>',
  'kitap': '<path d="M12 6c-2-1.5-5-2-8-1.5V19c3-.5 6 0 8 1.5 2-1.5 5-2 8-1.5V4.5c-3-.5-6 0-8 1.5z"/><path d="M12 6v14.5"/>',
  'hadis': '<path d="M7 4h10a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H7z"/><path d="M7 4H6a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h1M10 9h6M10 13h6M10 17h3"/>',
  'kandil': '<path d="M12 3c1.5 2 2 3 2 4a2 2 0 0 1-4 0c0-1 .5-2 2-4z"/><path d="M9 11h6v10H9zM7 21h10"/>',
  'takvim': '<rect x="4" y="5" width="16" height="15" rx="2"/><path d="M4 10h16M8 3v4M16 3v4"/><circle cx="12" cy="15" r="1.5"/>',
  'lale': '<path d="M12 13c-2-3-6-5-6-8a3 3 0 0 1 6 0 3 3 0 0 1 6 0c0 3-4 5-6 8z"/><path d="M12 13l-4 8M12 13l4 8"/>',
  'zil': '<path d="M6 16v-5a6 6 0 0 1 12 0v5l2 2H4z"/><path d="M10 21a2 2 0 0 0 4 0"/>',
  'san': '<path d="M12 21c-4-2.5-6.5-6.5-6.5-12M12 21c4-2.5 6.5-6.5 6.5-12"/><path d="M5.5 9C4 8 3.6 6.4 4 5.2c1.4.2 2.4 1.4 2.2 3M6.3 13c-1.8-.3-3-1.6-3-3 1.4-.4 2.8.5 3.3 2M8.5 16.8c-1.8.3-3.4-.5-4-1.9 1.3-.8 3-.3 4 1.2M18.5 9c1.5-1 1.9-2.6 1.5-3.8-1.4.2-2.4 1.4-2.2 3M17.7 13c1.8-.3 3-1.6 3-3-1.4-.4-2.8.5-3.3 2M15.5 16.8c1.8.3 3.4-.5 4-1.9-1.3-.8-3-.3-4 1.2"/>',
  'menu': '<circle cx="12" cy="5.5" r="1.3" fill="#000" stroke="none"/><circle cx="12" cy="12" r="1.3" fill="#000" stroke="none"/><circle cx="12" cy="18.5" r="1.3" fill="#000" stroke="none"/>',
  'paylas': '<circle cx="18" cy="5" r="2.5"/><circle cx="6" cy="12" r="2.5"/><circle cx="18" cy="19" r="2.5"/><path d="M8.2 10.8l7.6-4.4M8.2 13.2l7.6 4.4"/>',
  'mektup': '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3.5 6.5l8.5 6.5 8.5-6.5"/>',
  'bilgi': '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5v.01"/>',
  'kilit': '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>',
  // Alt sekmeler
  'sk_ilan': '<path d="M7 3h7l4 4v14H7z"/><path d="M14 3v4h4M10 12h5M10 16h5"/>',
  'sk_tam': '<rect x="4" y="4" width="16" height="16" rx="2"/><path d="M8 8h8M8 12h3M8 16h3M14 12h2v4h-2z"/>',
  'sk_sayfam': '<path d="M7 3h10v18l-5-4-5 4z"/>',
  'sk_dua': '<path d="M12 6c-2-1.5-5-2-8-1.5V19c3-.5 6 0 8 1.5 2-1.5 5-2 8-1.5V4.5c-3-.5-6 0-8 1.5z"/><path d="M12 6v14.5"/>',
  'sk_hatirla': '<path d="M12 13c-2-3-6-5-6-8a3 3 0 0 1 6 0 3 3 0 0 1 6 0c0 3-4 5-6 8z"/><path d="M12 13l-4 8M12 13l4 8"/>',
};

String ikonSvg(String ad) =>
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><g fill="none" stroke="#000" stroke-width="1.6" '
    'stroke-linecap="round" stroke-linejoin="round">${_yollar[ad] ?? ''}</g></svg>';

class Ikon extends StatelessWidget {
  final String ad;
  final double boyut;
  final Color renk;
  const Ikon(this.ad, {super.key, this.boyut = 24, required this.renk});

  @override
  Widget build(BuildContext context) => SizedBox(
        width: boyut,
        height: boyut,
        child: SvgPicture.string(
          ikonSvg(ad),
          width: boyut,
          height: boyut,
          colorFilter: ColorFilter.mode(renk, BlendMode.srcIn),
        ),
      );
}

/// L13 logo (marka/svg/L13.svg; ayna yarısı açık yazılmıştır)
const String _l13Yarim =
    '<path d="M512,214 C430,256 326,306 318,456 L318,806" fill="none" stroke="#C9A45C" stroke-width="22"/>'
    '<path d="M512,322 C462,350 398,384 394,476 L394,806" fill="none" stroke="#C9A45C" stroke-width="12"/>'
    '<rect x="276" y="806" width="236" height="22" fill="#C9A45C"/>'
    '<rect x="420" y="690" width="92" height="44" fill="#F2EBDD"/>'
    '<rect x="436" y="734" width="18" height="72" fill="#F2EBDD"/>';
const String l13Svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024">'
    '<rect width="1024" height="1024" fill="#25282D"/><g>$_l13Yarim</g>'
    '<g transform="matrix(-1 0 0 1 1024 0)">$_l13Yarim</g></svg>';

class Logo extends StatelessWidget {
  final double boyut;
  final double yaricap;
  const Logo({super.key, this.boyut = 40, this.yaricap = 12});

  @override
  Widget build(BuildContext context) => ClipRRect(
        borderRadius: BorderRadius.circular(yaricap),
        child: SvgPicture.string(l13Svg, width: boyut, height: boyut),
      );
}
