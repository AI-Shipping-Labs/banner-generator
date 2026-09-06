from banner_generator.renderer import render_html, resolve_template


def test_course_artwork_is_independent_from_the_speaker_photo():
    html = render_html(
        resolve_template("dtc-social"),
        {
            "variant": "course",
            "theme": "dark",
            "image_url": "https://example.test/speaker.jpg",
            "course_image_url": 'https://example.test/course.webp?x=1&y="2"',
            "course_image_dark_url": "https://example.test/course-dark.webp",
        },
        1200,
        630,
    )
    assert "theme-dark has-course-image" in html
    assert 'class="course-art-light" src="https://example.test/course.webp?x=1&amp;y=&quot;2&quot;"' in html
    assert 'class="course-art-dark" src="https://example.test/course-dark.webp"' in html
    assert 'src="https://example.test/speaker.jpg"' in html


def test_course_without_artwork_keeps_full_width_layout():
    html = render_html(resolve_template("dtc-social"), {"variant": "course"}, 1200, 630)
    assert "has-course-image" not in html
    assert "theme-light" in html
    assert "${course_image" not in html


def test_theme_safe_course_art_can_be_shared_explicitly():
    html = render_html(
        resolve_template("dtc-social"),
        {"course_image_url": "assets/course.webp", "theme": "dark"},
        1200,
        630,
    )
    assert 'class="course-art-dark" src="assets/course.webp"' in html
