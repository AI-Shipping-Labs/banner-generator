# Placing Generated Banners in the Content Repos

When you generate a cover banner with the banner-generator, you need to drop the
file into the right place in one of the AI Shipping Labs content repos so that
the website sync pipeline picks it up and the cover renders on the site.

This guide describes the layout convention. Every content type follows the same
shape: the cover image is named `cover.<ext>` and lives in an `images/` folder
that sits next to the content item itself.

## TL;DR

| Content type | Repo | Cover destination | Frontmatter `cover_image:` |
|---|---|---|---|
| Blog post | `AI-Shipping-Labs/content` | `blog/<slug>/images/cover.<ext>` | `"images/cover.<ext>"` |
| Project | `AI-Shipping-Labs/content` | `projects/<slug>/images/cover.<ext>` | `"images/cover.<ext>"` |
| Course (root) | `AI-Shipping-Labs/content` or course-specific repo | `courses/<slug>/images/cover.<ext>` (in `content`) or `images/cover.<ext>` (in a single-course repo like `python-course`) | `"images/cover.<ext>"` |
| Event | `AI-Shipping-Labs/content` | `events/<slug>/images/cover.<ext>` | `"<slug>/images/cover.<ext>"` (yaml stays at `events/<slug>.yaml`) |
| Workshop | `AI-Shipping-Labs/workshops-content` | `<YYYY-MM-DD-slug>/images/cover.<ext>` | `"images/cover.<ext>"` |

The website CDN is `https://cdn.aishippinglabs.com`, and the sync pipeline rewrites
`images/cover.jpg` (or wherever the frontmatter points) into a full CDN URL using
the repo short name as the first path component. You do not need to think about
S3 keys — only about the in-repo path.

## Folder Conventions

Every blog post, project, and workshop is a folder named after its slug. The
markdown or yaml file inside the folder is also named after the slug, so the
slug default (`os.path.splitext(filename)[0]`) works without needing an explicit
`slug:` field.

```
blog/
  my-post/
    my-post.md           # cover_image: "images/cover.jpg"
    images/
      cover.jpg          # the banner you generated
      inline-1.png       # any inline images referenced from the body

projects/
  my-project/
    my-project.md        # cover_image: "images/cover.jpg"
    images/
      cover.jpg

courses/
  aihero/
    course.yaml          # cover_image: "images/cover.jpg"
    images/
      cover.jpg
    01-day-1/
    02-day-2/
    ...

events/
  community-launch.yaml  # cover_image: "community-launch/images/cover.jpg"
  community-launch/
    images/
      cover.jpg
    recap.md             # event recap and other assets live here too

workshops/
  2026-05-04-agentic-rag/
    workshop.yaml        # cover_image: "images/cover.jpg"
    images/
      cover.jpg
    01-overview.md
    ...
```

Notes:
- Use lowercase, hyphenated filenames — `cover.jpg`, not `Cover.JPG` or `cover image.jpg`.
- Allowed extensions: `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`, `.svg`. Use whichever matches what the generator produced.
- For events, the yaml stays at `events/<slug>.yaml` (not inside a folder) but the cover and other assets live in the sibling `events/<slug>/` directory. The yaml path therefore needs the `<slug>/` prefix.

## Workflow: Generate, Copy, Sync

1. Render the banner with this generator. The default output lives under
   `output/content/`:

   ```bash
   uv run banner-generator render examples/content-blog.json
   # -> output/content/blog-ai-engineer-learning-path.png
   ```

2. Copy it into the target content repo at the path from the table above. For
   example, for a new blog post `my-new-post`:

   ```bash
   mkdir -p ~/git/ai-shipping-labs-content/blog/my-new-post/images
   cp output/content/blog-my-new-post.png \
      ~/git/ai-shipping-labs-content/blog/my-new-post/images/cover.png
   ```

3. Add `cover_image: "images/cover.png"` to the frontmatter of
   `blog/my-new-post/my-new-post.md`.

4. Commit and push the content repo. The next sync (manual via the studio
   `/studio/sync/` page, or automatic via the GitHub App webhook) will pick up
   the cover and populate `cover_image_url` in the database.

5. To verify locally without S3:

   ```bash
   cd ~/git/ai-shipping-labs
   uv run python manage.py sync_content --from-disk ~/git/ai-shipping-labs-content
   ```

   Then check the DB row's `cover_image_url` — it should be a
   `cdn.aishippinglabs.com/...` URL pointing at the new image path.

## Why This Layout

The Django sync pipeline at `integrations/services/github_sync/media.py` resolves
relative cover paths against the directory containing the markdown/yaml file.
Co-locating the image with its content item means:

- Frontmatter references stay short: `"images/cover.jpg"` instead of
  `"../../banner-images/<type>/<slug>.jpg"`.
- Renaming or deleting a piece of content moves/removes its cover automatically.
- The S3 key in the CDN bucket mirrors the repo path one-to-one, so the URL
  structure is predictable and stable.

There is no longer a top-level `banner-images/` folder in any of the content
repos. If you see one in a stale checkout, it has been removed upstream — pull
and adjust.
