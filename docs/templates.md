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
examples/ai-hero-certificate.json
```

Render it with:

```bash
make render-certificate-example
```

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
examples/content-event.json
examples/content-event-jpeg.json
examples/content-workshop.json
examples/content-blog.json
examples/content-course.json
examples/content-project.json
examples/content-resource.json
examples/content-long-title.json
```

Alternate content banner variants:

```text
examples/content-variants/blueprint-path-course.json
examples/content-variants/editorial-pulse-blog.json
examples/content-variants/event-stage-live.json
examples/content-variants/event-series-long-title.json
examples/content-variants/project-dossier-showcase.json
examples/content-variants/resource-stack-download.json
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
examples/content-event-series.json
examples/lambda-content-event-series.json
examples/content-variants/event-series-long-title.json
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
image_url        optional image URL; initials remain the deterministic fallback
```

The named `luma` size is deliberately 1000 x 1000. Event banners also have `og` (1200 x
630) and explicit YouTube (1280 x 720) examples; YouTube omits event dates so thumbnails
remain evergreen. Render the complete sample set with `make render-dtc-examples`.
