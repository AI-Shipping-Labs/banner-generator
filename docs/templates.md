# Templates

Templates are plain HTML files with linked CSS/assets under `banner_generator/templates/`.
The renderer injects a `<base>` tag for the template directory, so relative asset paths work
both locally and when the package is installed.

Each template lives in its own directory:

```text
banner_generator/templates/<template-name>/template.html
```

## Certificate

The AI Hero certificate uses:

```text
banner_generator/templates/ai-hero-certificate/template.html
banner_generator/templates/ai-hero-certificate/assets/
examples/aisl/ai-hero-certificate.json
```

Render it with:

```bash
make render-certificate-example
```

The certificate spec uses the named `certificate` size (1536 x 1024). The AI Shipping
Labs content-banner specs use the named `og` size (1200 x 630). A CLI or Lambda caller
can explicitly override a spec's size, but normal clients should preserve the size from
the spec.

## Content Banners

The first banner family uses the Canva reference direction from `docs/references/`:
black background, white type, and lime accents.

Shared template:

```text
banner_generator/templates/asl-content-card/template.html
banner_generator/templates/asl-content-card/content-card.css
```

Current examples:

```text
examples/aisl/content-event.json
examples/aisl/content-event-jpeg.json
examples/aisl/content-workshop.json
examples/aisl/content-blog.json
examples/aisl/content-course.json
examples/aisl/content-project.json
examples/aisl/content-resource.json
examples/aisl/content-long-title.json
```

The DTC social kit has multiple card specs under `examples/dtc/`, including article,
book, course, podcast, webinar, and workshop cards across Luma, Open Graph, YouTube,
and website sizes.

Alternate content banner variants:

```text
examples/aisl/content-variants/blueprint-path-course.json
examples/aisl/content-variants/editorial-pulse-blog.json
examples/aisl/content-variants/event-stage-live.json
examples/aisl/content-variants/event-series-long-title.json
examples/aisl/content-variants/project-dossier-showcase.json
examples/aisl/content-variants/resource-stack-download.json
```

## Event Series

`asl-event-series` is for recurring (weekly / bi-weekly) event series, as opposed to
the single-occurrence `asl-event-stage`. The design reuses the AI Shipping Labs
black/lime brand and adds recurring-series cues: stacked offset cards behind the
poster (multiple occurrences), a three-dot repeat marker beside the cadence kicker,
and concentric accent rings.

```text
banner_generator/templates/asl-event-series/template.html
banner_generator/templates/asl-event-series/style.css
examples/aisl/content-event-series.json
examples/aisl/lambda-content-event-series.json
examples/aisl/content-variants/event-series-long-title.json
```

Data slots (the website auto-banner pipeline sends these `data` field names):

```text
kind            "Event Series"                      (badge, top-right)
kicker          cadence label, e.g. "Weekly series" (mono uppercase + repeat dots)
title           series name
subtitle        series description (truncated)
meta_primary    cadence / day + time, e.g. "Wednesdays / 18:00 CEST"
meta_secondary  occurrence count or tags, e.g. "12 sessions / Members"
footer          "AI Shipping Labs Events"
title_size      optional explicit title fit (px)
subtitle_size   optional explicit subtitle fit (px)
```

Render them with:

```bash
make render-content-examples
make render-content-variants
```

The generated images are written to:

```text
output/content/
output/content-variants/
```

Use `title_size` and `subtitle_size` in a JSON spec when a title needs explicit fitting.
The long-title example exists to keep that pressure visible during template work.

## DataTalks.Club social kit

The `dtc-social` template is the DataTalks.Club counterpart to the AI Shipping Labs
templates. It is based on the supplied social banner canvas and supports the same data
shape across event, podcast, workshop, article, book, and course artwork.

Data slots:

```text
variant          webinar / podcast / workshop / article / book / course
channel          luma / og / youtube / site
kind             visible badge, e.g. "Workshop"
kicker           cadence or editorial label
title            primary title
subtitle         supporting copy; hidden for YouTube thumbnails
person            speaker, guest, author, or instructor
person_initials  fallback avatar text when no image_url is supplied
person_role      supporting person label
meta_primary     date or primary metadata
meta_secondary   time or secondary metadata
meta_tertiary    small metadata line
footer           small destination/brand line
image_url        optional URL or complete data URL; initials remain the fallback
image_base64     API-only raw PNG base64 alias when image_url is omitted
```

For image inputs, use `image_url` for an `https://` URL or a complete
`data:image/...;base64,...` value. Callers that only have raw base64 can send it as
`image_base64`; the renderer wraps it as a PNG data URL. The isolated HTML renderer
accepts inline data URLs but blocks network requests, so use base64 there.

The named `luma` size is deliberately 1000 x 1000. Event banners also have `og` (1200 x
630) and explicit YouTube (1280 x 720) examples; YouTube omits event dates so thumbnails
remain evergreen. Render the complete sample set with
`uv run python scripts/render_dtc_examples.py`.
