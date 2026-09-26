# Dataverket Forgejo theme

Light and dark Forgejo themes carrying the Dataverket palette and fonts, from
the design system in `../org/design`.

Proof of concept.

## Try it

```sh
brew install forgejo
./dev.sh              # http://localhost:3000
./dev.sh reset        # throw the instance away and start over
```

Three themes ship: `dataverket-auto` follows the operating system,
`dataverket-light` and `dataverket-dark` are fixed. Auto is the default. Pick
per user under **Settings -> Appearance**, or change `DEFAULT_THEME` in
`.dev/conf/app.ini`.

## What lives here

| File | What it is |
|---|---|
| `make-theme.py` | Generates everything below from the design system. |
| `public/assets/css/theme-dataverket-*.css` | Generated. Never edit by hand. |
| `public/assets/img/` | Logo, favicon and touch icon. Generated; the PNGs need a headless browser, and are left alone without one. |
| `public/assets/fonts/` | Inter and JetBrains Mono. Copied from the design system. |
| `options/locale/` | Generated from the installed binary. Gitignored. |
| `dev.sh` | Throwaway instance. Writes only to `.dev/`. |

## How it hooks in

Forgejo loads `theme-<name>.css` from `<custom-path>/public/assets/css/`, so
`--custom-path` pointing at this directory is the whole integration. No patched
binary, no forked templates.

Each theme imports Forgejo's own and overrides variables only:

```css
@import url("/assets/css/theme-forgejo-light.css");
```

Four groups of variables are overridden, and nothing else:

- **`--zinc-*` and `--steel-*`** - the neutral scales everything else derives
  from. Forgejo's lightness per step is kept; hue and saturation become the
  Dataverket slate. One substitution carries box, border, text and secondary.
  Both scales are needed: the light theme derives from zinc, the dark theme
  from steel, and the dark theme does not define zinc at all.
- **`--color-primary*`** - the accent ramp, alphas, hover and active.
- **`--color-red*` / `--color-error-*`** - the flag red.
- **`--fonts-proportional` / `--fonts-monospace`** - Inter and JetBrains Mono,
  served from this directory.

The rest of the rebrand is files, not code: `logo.svg`, `favicon.svg` and the
touch icon shadow Forgejo's own from the custom path, and the landing page
strings come from a patched locale.

## Decisions

**The dark accent is not the design system's accent token.** That token is
`#9facc0`, a surface colour, and a button filled with it reads as disabled.
Dark uses the brand navy's hue and saturation lifted to L=0.50, `#1967e6`:
3.5:1 against the dark surface, 5.1:1 for the white label.

**Flag red is used, across the whole red family.** The design system keeps
brand1 for identity only, on the grounds that it sits too close to `danger`.
Here the navy and the red together are the identity, so every red Forgejo
shows - labels, badges, errors - is the flag red rather than a second,
unrelated one.

**Forgejo replaces the locale, it does not merge it.** A nine-key override
leaves every other string missing and the server refuses to start. The full
file is 3300 lines, so `make-theme.py` extracts it from the installed binary
and patches the landing page. It is gitignored: generated against whatever
version is actually running, so it cannot go stale on upgrade.

**Two landing-page strings take link arguments** (`install_desc` three,
`license_desc` two) and Go renders `%!(EXTRA ...)` on the page if they go
unused. `license_desc` is handed the Forgejo and contributing URLs, so the
"Fri programvare" copy lives in that card and uses both. `install_desc` gets
three download URLs we have no use for, swallowed by an HTML comment.

**Nothing names the host.** Internal links are relative and the copy avoids
the instance hostname, so a mirror serves itself rather than pointing back at
the original.

**The logo is swapped per theme from CSS.** Forgejo renders it as `<img>`,
which CSS cannot recolour and where `currentColor` does nothing, so each theme
sets `content: url(...)` to its own file. The favicon instead carries its own
`prefers-color-scheme` switch, since it sits on browser chrome the page theme
cannot reach.

**Forgejo 16.0.5 shows custom themes by slug.** The `gitea-theme-meta-info`
block is there for forward compatibility, but this version has no
`theme-display-name` parsing and no locale key, so the switcher reads
`dataverket-light`, not "Dataverket Light".

**`dataverket-auto` is built the way Forgejo builds its own**: light at
`:root`, dark behind `@media (prefers-color-scheme: dark)`, including the logo
swap.

## Reference

- [Blender's gitea-custom](https://projects.blender.org/infrastructure/gitea-custom/src/branch/main)
  - the same `--custom-path` mechanism, with a standalone theme rather than an
  import.
