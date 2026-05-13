# Templates

Templates are plain HTML files with linked CSS/assets under `banner_generator/templates/`.
The renderer injects a `<base>` tag for the template directory, so relative asset paths work
both locally and when the package is installed.

## Certificate

The AI Hero certificate uses:

```text
banner_generator/templates/ai-hero-certificate.html
banner_generator/templates/assets/ai-hero/
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
banner_generator/templates/asl-content-card.html
banner_generator/templates/assets/asl/content-card.css
```

Current examples:

```text
examples/content-event.json
examples/content-workshop.json
examples/content-blog.json
examples/content-course.json
examples/content-project.json
examples/content-resource.json
examples/content-long-title.json
```

Render them with:

```bash
make render-content-examples
```

The generated images are written to:

```text
output/content/
```

Use `title_size` and `subtitle_size` in a JSON spec when a title needs explicit fitting.
The long-title example exists to keep that pressure visible during template work.
