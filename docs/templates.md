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
examples/content-variants/project-dossier-showcase.json
examples/content-variants/resource-stack-download.json
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
