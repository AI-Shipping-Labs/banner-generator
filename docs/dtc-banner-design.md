# DTC social banners

The DTC family shares Quicksand, cream/navy surfaces, lavender, mint and gold
accents with the website design system. A thin accent band identifies the family;
headline scale and content determine the composition.

The earlier cards used a heavy perimeter, several competing outlined containers,
and a tall time panel that reduced headline width. Website previews had no course
artwork, and repeated the community identity as initials in an avatar. The revised
layout gives more room to the headline and separates supporting details with rules.

- **Open Graph events:** headline and description on the left, compact timing on
  the right, speaker identity below.
- **Square events:** large editorial headline and a shared speaker/timing footer.
- **YouTube:** a short headline and large speaker photograph. The subtitle is
  omitted because it does not survive thumbnail scale. Initials remain a fallback.
- **Articles:** full-width typography. A decorative course robot would compete
  with the article topic, so it is reserved for courses.
- **Courses:** a dedicated illustration field alongside the title. The footer
  identifies the course/community without a redundant initials avatar.

## Course images and themes

Set `course_image_url` to the light course illustration and
`course_image_dark_url` to its separately generated dark companion. These accept
URLs, data URLs, or paths relative to the template directory. Keep speaker
photographs in `image_url`; the two fields have different jobs. Set `theme` to
`light` (default) or `dark`.

At 1200 × 630, the illustration has a 390px-wide field and uses `object-fit:
contain`, so the robot and its book remain visible. Use transparent artwork with
intentional internal fills, comfortable edge clearance, and similar composition
in both themes. Never filter a light illustration to manufacture a dark companion.
The website's `_docs/design/illustration-assets.md` defines asset production.

If no course image is supplied, the title uses the full width. If no dark companion
is supplied, the light asset is reused: only rely on this for artwork already
reviewed on navy. Otherwise supply the dedicated companion.

Render the sample family with `uv run python scripts/render_dtc_examples.py`.
Outputs are written to `output/dtc/`; these generated review files are not committed.
