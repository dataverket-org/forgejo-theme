#!/usr/bin/env python3
"""Generate the Dataverket Forgejo themes from the design system's tokens.

    python3 make-theme.py

Reads the palette out of ../org/design/build/theme.css and writes
public/assets/css/theme-dataverket-{light,dark}.css.

Each theme imports Forgejo's own and overrides variables only. The neutral
system is re-tinted by replacing --zinc-*: Forgejo derives box, border, text
and secondary from that scale, so one substitution carries the whole surface.
Forgejo's lightness per step is kept; only hue and saturation become ours.
"""
import colorsys
import io
import os
import re
import shutil
import subprocess
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
DESIGN_BUILD = os.path.join(HERE, '..', 'org', 'design', 'build')
DESIGN = os.path.join(DESIGN_BUILD, 'theme.css')
OUT = os.path.join(HERE, 'public', 'assets', 'css')
IMG = os.path.join(HERE, 'public', 'assets', 'img')

# Forgejo draws logo.svg at 30px in the navbar and 220px on the landing page,
# from one square file.
BOX = 212
INK = (29, 120, 820, 1147)   # what the design system's logo actually covers
FILL = 0.76                  # of the square, leaving room for rounded crops

# Forgejo's neutral steps. Lightness is theirs, hue and saturation ours.
#
# There are two scales and they are not interchangeable: the light theme
# derives from --zinc-*, the dark theme from --steel-*, and the dark theme
# does not define zinc at all. Overriding only zinc leaves dark untouched.
ZINC_L = {
    50: .98, 100: .96, 150: .93, 200: .90, 250: .87, 300: .84,
    350: .74, 400: .65, 450: .55, 500: .46, 550: .40, 600: .34,
    650: .30, 700: .26, 750: .21, 800: .16, 850: .13, 900: .10,
}
STEEL_L = {
    100: .882, 150: .816, 200: .749, 250: .684, 300: .618, 350: .555,
    400: .494, 450: .437, 500: .378, 550: .324, 600: .267, 650: .214,
    700: .180, 750: .149, 800: .120, 850: .102, 900: .088,
}


def tokens(scheme):
    if not os.path.exists(DESIGN):
        raise SystemExit('%s not found - run `task build` in the design '
                         'system first' % DESIGN)
    css = io.open(DESIGN, encoding='utf-8').read()
    m = re.search(r'@layer ds\.theme\.color-scheme\.' + scheme + r' \{(.*?)\n\}',
                  css, re.S)
    return dict(re.findall(r'(--ds-color-[a-z0-9-]+):\s*([^;]+)', m.group(1)))


def rgb(h):
    h = h.strip().lstrip('#')
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def hexs(r, g, b):
    return '#%02x%02x%02x' % tuple(round(max(0, min(1, c)) * 255) for c in (r, g, b))


def retint(hue, sat, lightness):
    return hexs(*colorsys.hls_to_rgb(hue, lightness, sat))


def ramp(anchors):
    """Seven steps from a list of hex anchors, repeating the last one."""
    out = list(anchors)
    while len(out) < 7:
        out.append(out[-1])
    return out[:7]


def alpha(hex_colour, pct):
    return '%s%02x' % (hex_colour, round(255 * pct / 100))


def variables(scheme):
    """The :root body for one scheme, as a list of lines."""
    dark = scheme == 'dark'
    t = tokens(scheme)
    g = lambda grp, var: t['--ds-color-%s-%s' % (grp, var)].strip()

    hue, _, sat = colorsys.rgb_to_hls(*rgb(g('neutral', 'base-default')))

    if dark:
        # Not the design system's dark accent token: that one is a surface
        # colour, and a button filled with it reads as disabled. The brand
        # navy's hue and saturation, lifted to L=0.50 - 3.5:1 against the dark
        # surface and 5.1:1 for the white label, both passing.
        h0, _, s0 = colorsys.rgb_to_hls(
            *rgb(tokens('light')['--ds-color-accent-base-default'].strip()))
        primary = retint(h0, s0, 0.50)
        lights = ramp([retint(h0, s0, l) for l in
                       (.57, .64, .71, .78, .84, .89, .93)])
        darks = ramp([retint(h0, s0, l) for l in
                      (.44, .38, .32, .26, .21, .16, .12)])
        hover, active = retint(h0, s0, .57), retint(h0, s0, .44)
        small = retint(h0, s0, .22)
    else:
        primary = g('accent', 'base-default')
        hover, active = g('accent', 'base-hover'), g('accent', 'base-active')
        lights = ramp([g('accent', 'base-hover'), g('accent', 'base-active'),
                       g('accent', 'border-strong'), g('accent', 'border-default'),
                       g('accent', 'border-subtle'), g('accent', 'surface-tinted'),
                       g('accent', 'background-tinted')])
        h2, l2, s2 = colorsys.rgb_to_hls(*rgb(primary))
        darks = ramp([retint(h2, s2, max(0.02, l2 - step)) for step in
                      (.02, .04, .06, .08, .10, .12, .14)])
        small = g('accent', 'surface-tinted')

    v = []
    add = v.append
    add('--fonts-proportional: Inter, -apple-system, "Segoe UI", system-ui, sans-serif;')
    add('--fonts-monospace: "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, monospace;')
    add('')
    add('/* Neutral surface, re-tinted to the Dataverket slate. Both scales:')
    add('   light derives from zinc, dark from steel. */')
    for k in sorted(ZINC_L):
        add('--zinc-%d: %s;' % (k, retint(hue, sat, ZINC_L[k])))
    for k in sorted(STEEL_L):
        add('--steel-%d: %s;' % (k, retint(hue, sat, STEEL_L[k])))
    add('')
    add('/* Accent: Dataverket navy. */')
    add('--color-primary: %s;' % primary)
    add('--color-primary-contrast: %s;' % g('accent', 'base-contrast-default'))
    add('--color-primary-hover: %s;' % hover)
    add('--color-primary-active: %s;' % active)
    for i, c in enumerate(lights, 1):
        add('--color-primary-light-%d: %s;' % (i, c))
    for i, c in enumerate(darks, 1):
        add('--color-primary-dark-%d: %s;' % (i, c))
    for pct in range(10, 100, 10):
        add('--color-primary-alpha-%d: %s;' % (pct, alpha(primary, pct)))
    add('--color-accent: %s;' % primary)
    add('--color-small-accent: %s;' % small)
    add('')
    add('/* Flag red, across the whole red family. The navy and red together')
    add('   are the identity, and keeping one hue wherever red appears means')
    add('   labels, badges and errors all read as Dataverket rather than as')
    add('   two different reds. */')
    add('--color-red: %s;' % g('brand1', 'base-default'))
    add('--color-red-dark-1: %s;' % g('brand1', 'base-hover'))
    add('--color-red-dark-2: %s;' % g('brand1', 'base-active'))
    add('--color-red-light: %s;' % g('brand1', 'border-default'))
    add('--color-red-badge: %s;' % g('brand1', 'border-strong'))
    add('--color-red-badge-bg: %s;' % alpha(g('brand1', 'base-default'), 13))
    add('--color-red-badge-hover-bg: %s;' % alpha(g('brand1', 'base-default'), 27))
    add('--color-error-bg: %s;' % g('brand1', 'background-tinted'))
    add('--color-error-bg-hover: %s;' % g('brand1', 'surface-tinted'))
    add('--color-error-bg-active: %s;' % g('brand1', 'surface-hover'))
    add('--color-error-border: %s;' % g('brand1', 'border-subtle'))
    add('--color-error-text: %s;' % g('brand1', 'text-default'))
    return v


def fontfaces():
    out = []
    for weight in (400, 500, 600):
        out += ['@font-face {', '  font-family: "Inter";', '  font-style: normal;',
                '  font-weight: %d;' % weight, '  font-display: swap;',
                '  src: url("/assets/fonts/inter-latin-%d-normal.woff2") format("woff2");' % weight,
                '}']
    for weight in (400, 500):
        out += ['@font-face {', '  font-family: "JetBrains Mono";', '  font-style: normal;',
                '  font-weight: %d;' % weight, '  font-display: swap;',
                '  src: url("/assets/fonts/jetbrains-mono-latin-%d-normal.woff2") format("woff2");' % weight,
                '}']
    return out


def logo_swap(scheme, indent=''):
    return [indent + '/* Forgejo renders the logo as <img>, which CSS cannot recolour. */',
            indent + 'img[src$="/img/logo.svg"] {',
            indent + '  content: url("/assets/img/logo-dataverket-%s.svg");' % scheme,
            indent + '}']


def block(lines, selector=':root', indent=''):
    out = [indent + selector + ' {']
    for line in lines:
        out.append((indent + '  ' + line) if line else '')
    out.append(indent + '}')
    return out


def build(scheme):
    """light and dark are fixed; auto follows prefers-color-scheme."""
    name = {'light': 'Light', 'dark': 'Dark', 'auto': 'Auto'}[scheme]
    lines = ['/* Generated by make-theme.py. Do not edit. */',
             '@import url("/assets/css/theme-forgejo-%s.css");' % scheme,
             '',
             'gitea-theme-meta-info {',
             '  --theme-display-name: "Dataverket %s";' % name,
             '  --theme-color-scheme: "%s";' % scheme,
             '}',
             ''] + fontfaces() + ['']

    if scheme == 'auto':
        # Same shape as Forgejo's own auto theme: light at :root, dark behind
        # the media query.
        lines += block(variables('light')) + ['']
        lines += logo_swap('light') + ['']
        lines += ['@media (prefers-color-scheme: dark) {']
        lines += block(variables('dark'), indent='  ') + ['']
        lines += logo_swap('dark', indent='  ')
        lines += ['}', '']
    else:
        lines += block(variables(scheme)) + ['']
        lines += logo_swap(scheme) + ['']

    path = os.path.join(OUT, 'theme-dataverket-%s.css' % scheme)
    io.open(path, 'w', encoding='utf-8').write('\n'.join(lines))
    print('  public/assets/css/theme-dataverket-%s.css' % scheme)


A = 'target="_blank" rel="noopener noreferrer" href='

STARTPAGE = {
    'app_desc': 'Kunnskap, åpen kildekode, suverenitet',

    # Cards render in this order. Which text goes where is driven by the
    # arguments the template passes: license_desc is handed the Forgejo and
    # contributing URLs, which is exactly what the "Fri programvare" copy
    # needs, so that text lives in the last card rather than the first.
    #
    # Links are relative and the copy does not name the host, so a mirror
    # serves its own instance rather than pointing back at the original.

    # install_desc is handed three Forgejo download URLs we have no use for.
    # Dropping them makes Go print %!(EXTRA ...) on the page, so they are
    # swallowed by a comment that renders nothing.
    'install': 'Samvirke',
    'install_desc': ('Dataverket foreslår et samvirke av norske leverandører, '
                     'kunder og ildsjeler som modell for norsk sky.'
                     '<!--%[1]s%[2]s%[3]s-->'),

    'platform': 'Åpne prosesser',
    'platform_desc': ('Kode, veikart og dokumentasjon diskuteres åpent og '
                      'lagres versjonert.'),

    'lightweight': 'Forankret',
    'lightweight_desc': ('Arkitektur og kode <a href="/dataverket/org/src/'
                         'branch/main/docs/forankring">er forankret</a> i '
                         'nasjonale og europeiske lover og rammeverk.'),

    'license': 'Fri programvare',
    'license_desc': ('Denne tjenesten kjører på <a {a}"%[1]s">Forgejo</a> som '
                     'er fri programvare du kan <a {a}"%[2]s">bidra til</a>.'
                     ).format(a=A),
}



def locale(forgejo):
    """Extract en-US from the running binary and patch the landing page."""
    rel = 'options/locale/locale_en-US.ini'
    tmp = tempfile.mkdtemp()
    try:
        subprocess.run([forgejo, 'embedded', 'extract', '--destination', tmp, rel],
                       check=True, capture_output=True)
        src = io.open(os.path.join(tmp, rel), encoding='utf-8').read()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    def patch(m):
        block = m.group(2)
        for k, v in STARTPAGE.items():
            block = re.sub(r'(?m)^%s\s*=.*$' % re.escape(k), '%s = %s' % (k, v), block)
        return m.group(1) + block

    out = re.sub(r'(\[startpage\]\n)((?:.*\n)*?)(?=\[)', patch, src, count=1)
    dest = os.path.join(HERE, rel)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    io.open(dest, 'w', encoding='utf-8').write(out)
    print('  %s (patched %d keys)' % (rel, len(STARTPAGE)))


def shapes():
    """The logo's drawing commands, lifted from the design system's own file."""
    svg = io.open(os.path.join(DESIGN_BUILD, 'logo.svg'), encoding='utf-8').read()
    inner = re.search(r'</title>(.*?)</svg>', svg, re.S).group(1).strip()
    return re.sub(r'\s+', ' ', inner)


def logo(name, fill, style=''):
    """Re-wrap the logo into Forgejo's square box, centred."""
    w, h = INK[2] - INK[0], INK[3] - INK[1]
    scale = (FILL * BOX) / h
    dx = (BOX - w * scale) / 2 - INK[0] * scale
    dy = (BOX - h * scale) / 2 - INK[1] * scale
    body = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d"'
            ' width="%d" height="%d" role="img">\n  <title>Dataverket</title>\n'
            '%s  <g transform="translate(%.2f %.2f) scale(%.4f)" fill="%s">%s</g>\n'
            '</svg>\n') % (BOX, BOX, BOX, BOX, style, dx, dy, scale, fill, shapes())
    io.open(os.path.join(IMG, name), 'w', encoding='utf-8').write(body)
    print('  public/assets/img/%s' % name)


FONTS = ['inter-latin-%d-normal.woff2' % w for w in (400, 500, 600)] + \
        ['jetbrains-mono-latin-%d-normal.woff2' % w for w in (400, 500)]


BROWSERS = ['/Applications/Brave Browser.app/Contents/MacOS/Brave Browser',
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            'chromium', 'google-chrome']


def rasters():
    """PNG fallbacks, rendered from the SVGs.

    Forgejo asks for favicon.png, and iOS wants a touch icon; neither takes an
    SVG. A headless browser is the rasteriser because one is already needed to
    look at the result. Without it the committed PNGs are left alone, so this
    is a refresh step rather than a build dependency.
    """
    browser = next((b for b in BROWSERS
                    if os.path.isabs(b) and os.path.exists(b)
                    or not os.path.isabs(b) and shutil.which(b)), None)
    if not browser:
        print('  rasters: no headless browser, keeping the committed PNGs')
        return

    jobs = [('logo.png', 'logo-dataverket-light.svg', 'transparent'),
            ('favicon.png', 'logo-dataverket-dark.svg', '#0f1216'),
            ('apple-touch-icon.png', 'logo-dataverket-dark.svg', '#0f1216')]
    tmp = tempfile.mkdtemp()
    try:
        for name, svg, bg in jobs:
            page = os.path.join(tmp, name + '.html')
            io.open(page, 'w', encoding='utf-8').write(
                '<!doctype html><html><head><style>html,body{margin:0;'
                'width:512px;height:512px}body{display:grid;place-items:center;'
                'background:%s}img{width:512px}</style></head><body>'
                '<img src="%s"></body></html>'
                % (bg, os.path.join(IMG, svg)))
            subprocess.run([browser, '--headless', '--disable-gpu',
                            '--no-sandbox', '--hide-scrollbars',
                            '--default-background-color=00000000',
                            '--window-size=512,512',
                            '--virtual-time-budget=4000',
                            '--screenshot=' + os.path.join(IMG, name),
                            'file://' + page],
                           check=True, capture_output=True)
            print('  public/assets/img/%s' % name)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def fonts():
    """Copy the fonts the design system has already fetched."""
    src = os.path.join(DESIGN_BUILD, '..', 'vendor', 'fonts', 'files')
    dest = os.path.join(HERE, 'public', 'assets', 'fonts')
    if not os.path.isdir(src):
        print('  fonts: %s not found, keeping the committed copies' % src)
        return
    os.makedirs(dest, exist_ok=True)
    for name in FONTS:
        shutil.copyfile(os.path.join(src, name), os.path.join(dest, name))
    print('  public/assets/fonts/ (%d files)' % len(FONTS))


def logos():
    light = tokens('light')['--ds-color-accent-base-default'].strip()
    dark = tokens('dark')['--ds-color-accent-text-default'].strip()
    logo('logo.svg', light)                      # shadows Forgejo's own
    logo('logo-dataverket-light.svg', light)
    logo('logo-dataverket-dark.svg', dark)
    # A favicon sits on browser chrome we do not control, so it carries its
    # own scheme switch rather than relying on the page theme.
    style = ('  <style>g{fill:%s}'
             '@media(prefers-color-scheme:dark){g{fill:%s}}</style>\n' % (light, dark))
    logo('favicon.svg', light, style)


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(IMG, exist_ok=True)
    for scheme in ('light', 'dark', 'auto'):
        build(scheme)
    logos()
    rasters()
    fonts()
    forgejo = os.environ.get('FORGEJO', '/opt/homebrew/opt/forgejo/bin/forgejo')
    if os.path.exists(forgejo):
        locale(forgejo)
    else:
        print('  skipping locale: %s not found' % forgejo)
