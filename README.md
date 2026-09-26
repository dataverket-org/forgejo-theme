# Forgejo theme

Dataverket's light, dark and auto themes for Forgejo, generated from the
design system in the [org repo](https://git.dataverket.org/dataverket/org),
which `task` clones for you.

## What it gives you

- **A branded forge without a fork.** Themes, logo, favicon and landing page
  copy, all through Forgejo's custom path. No patched binary, no forked
  templates.
- **Palette that cannot drift.** Every colour is generated from the design
  system's tokens; change the palette there and regenerate.
- **The same fonts as every other Dataverket surface.** Inter and JetBrains
  Mono, served from the instance.
- **Mirrors work.** Nothing names the host: internal links are relative and the
  copy does not mention the instance.

## Try it

```sh
brew install forgejo go-task

task              # list the targets
task dev          # fetch, generate, run on http://localhost:3000
task reset        # throw the instance away and start over
```

`task dev` clones the design system into `vendor/`, regenerates, then runs
Forgejo against this directory. Everything it writes lives in `.dev/` and
`vendor/`, both gitignored; no real instance is touched.

**Everything under `public/` and `options/` is generated.** Edit
`make-theme.py`, not its output. That is the one way this repo differs from a
hand-authored custom directory.

`dataverket-auto` follows the operating system and is the default.
`dataverket-light` and `dataverket-dark` are fixed. Pick per user under
**Settings -> Appearance**, or set `DEFAULT_THEME`.

## Use it on a real instance

Point Forgejo at this directory and list the themes:

```ini
[ui]
DEFAULT_THEME = dataverket-auto
THEMES = dataverket-auto,dataverket-light,dataverket-dark
```

```sh
forgejo web --custom-path /path/to/forgejo-theme
```

Run `task build` on the target first: the locale is patched against the
Forgejo version installed there, and is not committed.

## What lives here

| File | What it is |
|---|---|
| `make-theme.py` | The source. Generates everything below. |
| `Taskfile.yaml` | Fetch, generate, run. |
| `public/assets/css/` | The three themes. Generated. |
| `public/assets/img/` | Logo, favicon, touch icon. Generated; the PNGs need a headless browser and are left alone without one. |
| `public/assets/fonts/` | Inter and JetBrains Mono. Copied from the design system. |
| `options/locale/` | Patched `en-US`. Generated, gitignored. |

## The themes

Each imports Forgejo's own and overrides variables only:

```css
@import url("/assets/css/theme-forgejo-light.css");
```

Four groups are overridden, and nothing else:

- **`--zinc-*` and `--steel-*`** - the neutral scales everything derives from.
  Forgejo's lightness per step is kept; hue and saturation become the
  Dataverket slate. **Both are needed**: light derives from zinc, dark from
  steel, and the dark theme does not define zinc at all.
- **`--color-primary*`** - the accent ramp, alphas, hover and active.
- **`--color-red*` and `--color-error-*`** - the flag red.
- **`--fonts-proportional` and `--fonts-monospace`** - Inter and JetBrains Mono.

`dataverket-auto` carries both sets: light at `:root`, dark behind
`@media (prefers-color-scheme: dark)`, the same shape as Forgejo's own auto
theme.

**The dark accent is not the design system's accent token.** That one is a
surface colour, and a button filled with it reads as disabled. Dark uses the
brand navy's hue and saturation lifted to L=0.50: 3.5:1 against the dark
surface, 5.1:1 for the white label.

**Flag red runs through the whole red family.** The design system keeps brand1
for identity only, because it sits close to `danger`. Here the navy and the red
together are the identity, so every red Forgejo shows is the same one.

## The logo

| File | What it is |
|---|---|
| `logo.svg` | Shadows Forgejo's own. Navy. |
| `logo-dataverket-light.svg` / `-dark.svg` | One per theme. |
| `favicon.svg` | Carries its own `prefers-color-scheme` switch. |
| `*.png` | Raster fallbacks. Forgejo asks for `favicon.png`; iOS wants a touch icon. |

Forgejo draws the logo at 30 px in the navbar and 220 px on the landing page,
from one square file. The design system's shapes are re-wrapped into a 212x212
box at 76% fill, so rounded crops cannot clip it.

> **Forgejo renders the logo as `<img>`.** CSS cannot reach inside one, and
> `fill="currentColor"` does nothing there, so each theme swaps the file with
> `content: url(...)`. The favicon cannot use that - it sits on browser chrome
> the page theme cannot reach - so it carries a media query instead.

## The landing page

> **Forgejo replaces `options/locale`, it does not merge it.** A nine-key
> override leaves every other string missing and the server will not start.

`make-theme.py` extracts the 3300-line `en-US` from the installed binary and
patches the `[startpage]` section. It is gitignored, so it always matches the
version running rather than drifting.

**Two strings take link arguments** - `install_desc` three, `license_desc` two
- and Go prints `%!(EXTRA ...)` on the page if they go unused. `license_desc`
is handed the Forgejo and contributing URLs, so the free-software copy lives in
that card and uses both. `install_desc` gets three download URLs with no use
here; they are swallowed by a comment.

Copy lives in `STARTPAGE` at the top of `make-theme.py`.

## Regenerating

```sh
task build        # fetches the design system if needed, then generates
task update       # pull the latest design system
```

`DESIGN_BUILD` points the generator at a working copy instead of the clone.

Three steps degrade rather than fail, each with a note: the locale needs the
`forgejo` binary, the PNGs need a headless browser, and refreshing the fonts
needs `task vendor` to have run in the design system. The committed copies are
kept when a step is skipped.

## Known limits

- **Forgejo 16.0.5 lists custom themes by slug.** There is no
  `theme-display-name` parsing and no locale key, so the switcher reads
  `dataverket-auto`. The `gitea-theme-meta-info` block is there for forward
  compatibility.
- **Images are served without a cache-busting query**, unlike the CSS. A
  visitor who saw the old logo keeps it for up to six hours.
- **Two filenames are ours, not Forgejo's**: `logo-dataverket-light.svg` and
  `-dark.svg`, which the themes swap between. Everything else shadows a file
  Forgejo already ships.

## Reference

- [Blender's gitea-custom](https://projects.blender.org/infrastructure/gitea-custom/src/branch/main)
  - the same custom-path mechanism, with a standalone theme rather than an
  import.
